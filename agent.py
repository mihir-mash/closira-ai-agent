import json
import os
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

from stages.faq import get_instructions as faq_instructions
from stages.lead_qualification import get_instructions as lead_instructions
from stages.escalation import get_instructions as escalation_instructions
from stages.summary import get_instructions as summary_instructions

load_dotenv()

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

    text = text.strip()
    # Only attempt JSON parse if the response looks like a JSON object
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


class ClosiraAgent:
    
    def __init__(self) -> None:

        self.conversation_history: list[dict] = []
        self.current_stage: str = "faq"
        self.sop_data: dict = {}
        self.lead_data: dict = {}
        self.escalation_log: list[dict] = []
        self.unanswered_count: int = 0
        self.exchange_count: int = 0

        self.client = Groq()

    # SOP Loading
    def load_sop(self, path: str) -> None:

        sop_path = Path(path)
        if not sop_path.exists():
            raise FileNotFoundError(
                f"SOP file not found at '{path}'.  "
                "Please ensure data/sop.json exists before running the agent."
            )
        with open(sop_path, "r", encoding="utf-8") as f:
            self.sop_data = json.load(f)

    # System Prompt Construction
    def build_system_prompt(self) -> str:
    
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

    # Main Chat Method

    def chat(self, user_message: str) -> str:
        
        # Step 1: Record the user's message in history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Step 2: Build stage-aware system prompt
        system_prompt = self.build_system_prompt()

        # Step 3: Call the Groq API
        messages_for_api = [{"role": "system", "content": system_prompt}] + self.conversation_history
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",  
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
            self.unanswered_count = 0
            final_reply = reply_text

        # Step 5: Record assistant reply in history (always use the customer-facing text)
        self.conversation_history.append({"role": "assistant", "content": final_reply})

        # Step 6: Increment exchange counter
        self.exchange_count += 1

        return final_reply

    # Escalation Handler

    def handle_escalation(self, parsed_json: dict) -> str:
        
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

        self.escalation_log.append(log_entry)

        self._write_escalation_log(log_entry)

        return parsed_json.get("message_to_customer", "A member of our team will be in touch shortly.")

    def _write_escalation_log(self, log_entry: dict) -> None:
        
        log_path = Path("logs/escalation_log.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)

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

    # Low-Confidence Handler

    def handle_low_confidence(self, parsed_json: dict) -> str:
        
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
\
    # Stage Advancement

    def advance_stage(self) -> None:

        transitions = {
            "faq": "lead",
            "lead": "summary",
        }

        next_stage = transitions.get(self.current_stage)
        if next_stage:
            self.current_stage = next_stage

   
    # Summary Generation

    def generate_summary(self) -> str:
        
        # Switch to summary stage so the correct instructions are injected
        self.current_stage = "summary"
        system_prompt = self.build_system_prompt()

        
        summary_trigger = (
            "Please generate the full end-of-session conversation summary now, "
            "following the exact format specified in your instructions."
        )

        # Build a temporary history that includes the trigger without mutating
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


    # State Checks


    def is_escalated(self) -> bool:
        return self.current_stage == "escalation"

    # Conversation Log Saving

    def save_conversation_log(self) -> None:
        
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