"""
stages/escalation.py

Stage 3 — Escalation Detection & Handling.

This module defines the instructions injected into the system prompt once the
agent has detected an escalation trigger.  After an escalation, the
conversation loop is terminated and a human agent is expected to follow up.

Escalation can be triggered by:
  - The model returning a JSON block with "action": "ESCALATE"
  - The model returning a JSON block with "action": "LOW_CONFIDENCE" twice in a row
  - The customer explicitly asking to speak to a human
  - Angry, abusive, or medically sensitive language

Design rationale:
  - Using a JSON-structured escalation signal (rather than plain text) means the
    agent loop can reliably detect it with a simple JSON parse — no regex needed.
  - The escalation log is append-only to preserve a full audit trail.
"""


# ---------------------------------------------------------------------------
# Stage instruction constant
# Injected into SYSTEM_PROMPT at {stage_instructions} placeholder in agent.py
# ---------------------------------------------------------------------------
ESCALATION_STAGE_INSTRUCTIONS = """
A human agent will follow up with the customer. 
Acknowledge the situation warmly and reassure the customer.
"""


def get_instructions() -> str:
    """
    Return the escalation stage instruction string.

    Returns
    -------
    str
        The ESCALATION_STAGE_INSTRUCTIONS constant, ready to be injected into
        the system prompt.
    """
    return ESCALATION_STAGE_INSTRUCTIONS
