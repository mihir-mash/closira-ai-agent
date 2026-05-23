"""
stages/lead_qualification.py

Stage 2 — Lead Qualification.

This module defines the instructions injected into the system prompt when the
agent has moved into the lead-qualification stage.

The agent must ask exactly three structured questions, ONE AT A TIME, to
gather booking intent and availability.  Collected answers are stored on the
ClosiraAgent instance (self.lead_data) by the agent loop in agent.py.

Design rationale:
  - Asking questions one at a time mimics a natural conversation and avoids
    overwhelming the customer.
  - Storing answers in self.lead_data (not the conversation history alone)
    gives main.py and the summary stage a structured dictionary to work with.
"""


# ---------------------------------------------------------------------------
# Stage instruction constant
# Injected into SYSTEM_PROMPT at {stage_instructions} placeholder in agent.py
# ---------------------------------------------------------------------------
LEAD_STAGE_INSTRUCTIONS = """
You are in the lead qualification stage. Ask the customer these questions ONE AT A TIME.
Do not ask all questions at once. Wait for each answer before asking the next.
Questions to ask:
1. "What treatment are you most interested in?" 
2. "Have you had any aesthetic treatments before, or would this be your first time?"
3. "Would you prefer a morning or afternoon appointment, and are there any days that \
don't work for you?"
After collecting all 3 answers, summarise what you've learned and confirm with the customer.
"""

# Track which question we are on (0-indexed; 3 means all collected)
TOTAL_QUESTIONS = 3


def get_instructions() -> str:
    """
    Return the lead-qualification stage instruction string.

    Returns
    -------
    str
        The LEAD_STAGE_INSTRUCTIONS constant, ready to be injected into the
        system prompt.
    """
    return LEAD_STAGE_INSTRUCTIONS
