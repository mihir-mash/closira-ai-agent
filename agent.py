"""
agent.py

Core AI agent for the Closira / Bloom Aesthetics Clinic support workflow.

This module defines the ClosiraAgent class, which:
  - Loads the clinic's SOP (Standard Operating Procedure) from data/sop.json
  - Manages the four-stage conversation pipeline:
      Stage 1  faq           — answers questions strictly from the SOP
      Stage 2  lead          — collects qualification data via structured questions
      Stage 3  escalation    — handles hand-off to a human agent
      Stage 4  summary       — generates a structured end-of-session report
  - Calls the Anthropic Claude API for every customer turn
  - Detects structured JSON signals (ESCALATE, LOW_CONFIDENCE) in model replies
  - Logs escalation events to logs/escalation_log.json (append-only)
  - Saves the full conversation transcript to a timestamped log file

Usage:
    from agent import ClosiraAgent
    agent = ClosiraAgent()
    agent.load_sop("data/sop.json")
    reply = agent.chat("What are your Botox prices?")
"""

import json
import os
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

# Import stage instruction helpers
from stages.faq import get_instructions as faq_instructions
from stages.lead_qualification import get_instructions as lead_instructions
from stages.escalation import get_instructions as escalation_instructions
from stages.summary import get_instructions as summary_instructions

# ---------------------------------------------------------------------------
# Load environment variables from .env so that ANTHROPIC_API_KEY is available
# without hardcoding it anywhere in source code.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# SYSTEM PROMPT TEMPLATE
#
# Design philosophy:
#   - A single system prompt template keeps the model's identity, tone, and
#     safety rules consistent across all four stages.
#   - Three placeholders are injected at runtime:
#       {sop_data}          — the full SOP JSON, so the model ONLY knows what
#                             the clinic has officially declared.
#       {current_stage}     — lets the model know which stage it's in for
#                             self-awareness and debugging.
#       {stage_instructions}— stage-specific behaviour injected from the
#                             relevant stages/*.py module.
#   - Separating stage instructions from the base prompt avoids rewriting the
#     entire prompt for each stage transition.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are Bloom, a warm, professional AI assistant for Bloom Aesthetics Clinic. 
You handle inbound customer enquiries via chat.

IDENTITY & TONE:
- You are friendly, reassuring, and professional — like a knowledgeable receptionist
- Use clear, simple language suitable for a general audience
- Never be dismissive, cold, or overly clinical in tone
- Use British English spelling (e.g., "colour", "enquiry", "cancelled")

YOUR KNOWLEDGE BOUNDARIES — CRITICAL:
- You may ONLY answer questions using the information provided in the SOP data below
- If a customer asks something not covered in the SOP, you MUST say you don't have 
  that information and offer to connect them with a human team member
- NEVER invent prices, services, staff names, policies, or medical information
- NEVER make up information to seem helpful — an honest "I don't know" is always better

SOP DATA:
{sop_data}

ESCALATION RULES — you must escalate immediately if:
1. The customer makes a complaint or expresses anger/frustration
2. The customer asks a medical question (e.g., side effects, contraindications, allergies)
3. The customer tries to negotiate pricing
4. You cannot answer more than 2 consecutive questions from the SOP
5. The customer explicitly asks for a human or manager
6. There is any mention of adverse reactions, emergencies, or safety concerns

When escalating, respond in this EXACT JSON format (and nothing else):
{{
  "action": "ESCALATE",
  "reason": "<brief reason for escalation>",
  "sentiment": "<neutral|frustrated|angry|urgent>",
  "message_to_customer": "<a warm message telling the customer a human will follow up>"
}}

CONFIDENCE DETECTION:
If you are unsure about any answer, respond in this EXACT JSON format:
{{
  "action": "LOW_CONFIDENCE",
  "topic": "<what the customer asked about>",
  "message_to_customer": "<honest message saying you're not sure and will get help>"
}}

For all normal responses, reply as plain conversational text only — no JSON.

CURRENT STAGE: {current_stage}
STAGE INSTRUCTIONS: {stage_instructions}
"""


def try_parse_json(text: str) -> dict | None:
    """
    Attempt to parse the model's response as JSON.

    We check for JSON because escalation and low-confidence signals are
    returned by the model as structured JSON objects — this lets the agent
    loop handle them programmatically rather than relying on fragile text
    matching.

    Parameters
    ----------
    text : str
        The raw text returned by the Claude API.

    Returns
    -------
    dict | None
        Parsed dictionary if the text is valid JSON starting with '{',
        otherwise None.
    """
    text = text.strip()
    # Only attempt JSON parse if the response looks like a JSON object
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


class ClosiraAgent:
    """
    Multi-stage AI customer support agent for Bloom Aesthetics Clinic.

    This class orchestrates the four-stage conversation pipeline, manages
    all state, and interfaces with the Anthropic Claude API.

    Attributes
    ----------
    conversation_history : list[dict]
        Full message history in {"role": str, "content": str} format,
        passed directly to the Claude API on every call.
    current_stage : str
        Active pipeline stage.  One of: "faq", "lead", "escalation", "summary".
    sop_data : dict
        Parsed content of data/sop.json — the clinic's knowledge base.
    lead_data : dict
        Structured answers collected during the lead-qualification stage.
    escalation_log : list[dict]
        In-memory list of escalation events (also persisted to JSON).
    unanswered_count : int
        Counter for consecutive LOW_CONFIDENCE responses.
        Auto-escalates when this reaches 2 (the "two-strike rule").
    exchange_count : int
        Total number of user↔assistant exchanges in this session.
    """

    def __init__(self) -> None:
        """Initialise the agent with empty state.  Call load_sop() before chat()."""
        self.conversation_history: list[dict] = []
        self.current_stage: str = "faq"
        self.sop_data: dict = {}
        self.lead_data: dict = {}
        self.escalation_log: list[dict] = []
        self.unanswered_count: int = 0
        self.exchange_count: int = 0

        # Initialise the Groq client.
        # The SDK automatically reads GROQ_API_KEY from the environment.
        # load_dotenv() above ensures .env is sourced first.
        self.client = Groq()

    # ------------------------------------------------------------------
    # SOP Loading
    # ------------------------------------------------------------------

    def load_sop(self, path: str) -> None:
        """
        Load and parse the clinic's SOP from a JSON file.

        The SOP is kept as external JSON (rather than hardcoded) so that
        the business can update prices, services, and policies without
        touching Python source code.  This also makes it easy to validate
        the data file independently.

        Parameters
        ----------
        path : str
            Relative or absolute path to the SOP JSON file.

        Raises
        ------
        FileNotFoundError
            With a clear message if the file does not exist.
        json.JSONDecodeError
            If the file exists but is not valid JSON.
        """
        sop_path = Path(path)
        if not sop_path.exists():
            raise FileNotFoundError(
                f"SOP file not found at '{path}'.  "
                "Please ensure data/sop.json exists before running the agent."
            )
        with open(sop_path, "r", encoding="utf-8") as f:
            self.sop_data = json.load(f)

    # ------------------------------------------------------------------
    # System Prompt Construction
    # ------------------------------------------------------------------

    def build_system_prompt(self) -> str:
        """
        Construct the full system prompt for the current stage.

        Injects three values into SYSTEM_PROMPT:
          - sop_data           (prettified JSON of the clinic's knowledge base)
          - current_stage      (e.g. "faq", "lead", "summary")
          - stage_instructions (fetched from the relevant stages/*.py module)

        Returns
        -------
        str
            The complete, ready-to-send system prompt string.
        """
        # Map stage name → instruction getter function
        stage_instruction_map = {
            "faq": faq_instructions,
            "lead": lead_instructions,
            "escalation": escalation_instructions,
            "summary": summary_instructions,
        }

        # Retrieve the correct stage instructions; default to FAQ if unknown
        instruction_fn = stage_instruction_map.get(self.current_stage, faq_instructions)
        stage_instructions = instruction_fn()

        return SYSTEM_PROMPT.format(
            sop_data=json.dumps(self.sop_data, indent=2, ensure_ascii=False),
            current_stage=self.current_stage,
            stage_instructions=stage_instructions,
        )

    # ------------------------------------------------------------------
    # Main Chat Method
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """
        Process one user message and return the assistant's reply.

        Workflow:
          1. Append the user message to conversation_history.
          2. Build the system prompt for the current stage.
          3. Call the Claude API with the full history.
          4. Attempt to parse the response as JSON.
             - If ESCALATE → call handle_escalation()
             - If LOW_CONFIDENCE → call handle_low_confidence()
             - Otherwise → use the plain-text reply directly.
          5. Append the assistant reply to conversation_history.
          6. Increment exchange_count.
          7. Return the reply string.

        Parameters
        ----------
        user_message : str
            The customer's raw input text.

        Returns
        -------
        str
            The assistant's response, ready to print to the terminal.
        """
        # Step 1: Record the user's message in history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Step 2: Build stage-aware system prompt
        system_prompt = self.build_system_prompt()

        # Step 3: Call the Groq API
        # We prepend the system prompt to the conversation history
        messages_for_api = [{"role": "system", "content": system_prompt}] + self.conversation_history
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Llama 3.3 70B — current Groq model
            max_tokens=1024,
            messages=messages_for_api,
        )

        # Extract the plain text from the API response object
        reply_text = response.choices[0].message.content

        # Step 4: Check if the reply is a structured JSON signal
        # (ESCALATE or LOW_CONFIDENCE) — these need special handling
        parsed = try_parse_json(reply_text)

        if parsed and parsed.get("action") == "ESCALATE":
            # Escalation detected — hand off to human agent handler
            final_reply = self.handle_escalation(parsed)

        elif parsed and parsed.get("action") == "LOW_CONFIDENCE":
            # Model is unsure — apply the two-strike escalation rule
            final_reply = self.handle_low_confidence(parsed)

        else:
            # Normal conversational reply — use as-is
            # Reset unanswered_count since this question was answered successfully
            self.unanswered_count = 0
            final_reply = reply_text

        # Step 5: Record assistant reply in history (always use the customer-facing text)
        self.conversation_history.append({"role": "assistant", "content": final_reply})

        # Step 6: Increment exchange counter
        self.exchange_count += 1

        return final_reply

    # ------------------------------------------------------------------
    # Escalation Handler
    # ------------------------------------------------------------------

    def handle_escalation(self, parsed_json: dict) -> str:
        """
        Handle an ESCALATE signal from the model.

        Actions:
          1. Transition the agent to the "escalation" stage.
          2. Build a structured log entry with timestamp, reason, and sentiment.
          3. Append the entry to logs/escalation_log.json (never overwrite).
          4. Return the customer-facing message from the JSON payload.

        The escalation log uses an append-only design so that every event is
        preserved for audit and CRM integration purposes.

        Parameters
        ----------
        parsed_json : dict
            The parsed ESCALATE JSON object returned by the model, containing:
              - reason              : why escalation was triggered
              - sentiment           : customer emotional state
              - message_to_customer : what to say to the customer

        Returns
        -------
        str
            The customer-facing escalation message.
        """
        # Transition stage to escalation — no further FAQ or lead Q&A
        self.current_stage = "escalation"

        # Build the structured log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "exchange_number": self.exchange_count + 1,
            "reason": parsed_json.get("reason", "Unspecified"),
            "sentiment": parsed_json.get("sentiment", "neutral"),
            # Record the last user message as context snippet
            "conversation_snippet": (
                self.conversation_history[-1]["content"]
                if self.conversation_history
                else ""
            ),
        }

        # Store in memory
        self.escalation_log.append(log_entry)

        # Persist to logs/escalation_log.json (append-only — never overwrite)
        self._write_escalation_log(log_entry)

        return parsed_json.get("message_to_customer", "A member of our team will be in touch shortly.")

    def _write_escalation_log(self, log_entry: dict) -> None:
        """
        Append a single escalation event to logs/escalation_log.json.

        If the file does not exist, it is created with a JSON array containing
        the new entry.  If it exists, the entry is appended to the existing
        array.  This append-only design preserves the full audit trail.

        Parameters
        ----------
        log_entry : dict
            The escalation event to persist.
        """
        log_path = Path("logs/escalation_log.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing entries (or start with an empty list)
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = []
                except json.JSONDecodeError:
                    existing = []
        else:
            existing = []

        existing.append(log_entry)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Low-Confidence Handler
    # ------------------------------------------------------------------

    def handle_low_confidence(self, parsed_json: dict) -> str:
        """
        Handle a LOW_CONFIDENCE signal from the model.

        Implements the "two-strike rule":
          - First unanswered question: increment counter, return honest fallback.
          - Second consecutive unanswered question: auto-escalate to human.

        This prevents the agent from repeatedly admitting ignorance, which
        erodes customer trust and wastes their time.

        Parameters
        ----------
        parsed_json : dict
            The parsed LOW_CONFIDENCE JSON object returned by the model,
            containing:
              - topic               : what the customer asked about
              - message_to_customer : honest reply about uncertainty

        Returns
        -------
        str
            Either the low-confidence message (first miss) or the escalation
            message (second consecutive miss).
        """
        # Increment the consecutive-unanswered counter
        self.unanswered_count += 1

        # Two-strike rule: escalate automatically after 2 consecutive unknowns
        if self.unanswered_count >= 2:
            auto_escalate_payload = {
                "action": "ESCALATE",
                "reason": "More than 2 consecutive questions could not be answered from the SOP",
                "sentiment": "neutral",
                "message_to_customer": (
                    "I'm sorry — I've reached the limits of what I can help with today. "
                    "I'll make sure one of our team members follows up with you promptly "
                    "to answer all your questions properly."
                ),
            }
            return self.handle_escalation(auto_escalate_payload)

        # First miss — return the honest fallback message
        return parsed_json.get(
            "message_to_customer",
            "I'm not sure about that — let me check with the team and get back to you.",
        )

    # ------------------------------------------------------------------
    # Stage Advancement
    # ------------------------------------------------------------------

    def advance_stage(self) -> None:
        """
        Advance the pipeline to the next stage.

        Stage order:  faq → lead → summary
        Escalation can interrupt from any stage at any time (handled separately
        via handle_escalation, not this method).

        Called by main.py at the appropriate moments:
          - After 3 FAQ exchanges OR when the user mentions booking/appointment
            → advance faq → lead
          - After lead qualification is complete → advance lead → summary
        """
        # Stage transition map (linear progression)
        transitions = {
            "faq": "lead",
            "lead": "summary",
        }

        next_stage = transitions.get(self.current_stage)
        if next_stage:
            self.current_stage = next_stage

    # ------------------------------------------------------------------
    # Summary Generation
    # ------------------------------------------------------------------

    def generate_summary(self) -> str:
        """
        Generate a structured end-of-session summary using the Claude API.

        Switches the agent to the summary stage and makes a special API call
        with the full conversation history so Claude can produce an accurate,
        context-aware report in the exact format defined in summary.py.

        Returns
        -------
        str
            The formatted summary string, ready to print to the terminal.
        """
        # Switch to summary stage so the correct instructions are injected
        self.current_stage = "summary"
        system_prompt = self.build_system_prompt()

        # Add a trigger message to prompt Claude to generate the summary now.
        # We append it to history so Claude has the full session context.
        summary_trigger = (
            "Please generate the full end-of-session conversation summary now, "
            "following the exact format specified in your instructions."
        )

        # Build a temporary history that includes the trigger without mutating
        # self.conversation_history — we don't want the trigger in the real log.
        temp_history = self.conversation_history + [
            {"role": "user", "content": summary_trigger}
        ]

        # Call the API specifically for summary generation
        messages_for_api = [{"role": "system", "content": system_prompt}] + temp_history
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=messages_for_api,
        )

        return response.choices[0].message.content

    # ------------------------------------------------------------------
    # State Checks
    # ------------------------------------------------------------------

    def is_escalated(self) -> bool:
        """
        Return True if the conversation has been escalated to a human.

        Used by main.py to decide whether to break out of the conversation
        loop immediately after printing the escalation message.

        Returns
        -------
        bool
        """
        return self.current_stage == "escalation"

    # ------------------------------------------------------------------
    # Conversation Log Saving
    # ------------------------------------------------------------------

    def save_conversation_log(self) -> None:
        """
        Save the full conversation transcript to a timestamped JSON file.

        The file is written to logs/ with the format:
            conversation_YYYY-MM-DDTHH-MM-SS.json

        This gives operations teams a complete record of every session for
        quality assurance and CRM integration.
        """
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_filename = logs_dir / f"conversation_{timestamp}.json"

        payload = {
            "session_timestamp": timestamp,
            "exchange_count": self.exchange_count,
            "final_stage": self.current_stage,
            "lead_data": self.lead_data,
            "escalation_events": self.escalation_log,
            "conversation_history": self.conversation_history,
        }

        with open(log_filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"\n[SYSTEM] Conversation saved to {log_filename}")
