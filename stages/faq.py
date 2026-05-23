"""
stages/faq.py

Stage 1 — FAQ Answering.

This module defines the instructions injected into the system prompt when the
agent is operating in FAQ mode.  The agent is constrained to answer ONLY from
the SOP data that is also injected into the system prompt.

Design rationale:
  - Keeping stage instructions separate from agent.py makes it easy to edit
    or extend each stage without touching core agent logic.
  - The instruction explicitly forbids hallucination and tells the model what
    to do when a question is out of scope (escalate via JSON).
"""


# ---------------------------------------------------------------------------
# Stage instruction constant
# Injected into SYSTEM_PROMPT at {stage_instructions} placeholder in agent.py
# ---------------------------------------------------------------------------
FAQ_STAGE_INSTRUCTIONS = """
You are in the FAQ stage. Answer the customer's question using only the SOP data.
If the question is answered, ask if they have any other questions.
If the question is out of scope, escalate.
"""


def get_instructions() -> str:
    """
    Return the FAQ stage instruction string.

    Returns
    -------
    str
        The FAQ_STAGE_INSTRUCTIONS constant, ready to be injected into the
        system prompt.
    """
    return FAQ_STAGE_INSTRUCTIONS
