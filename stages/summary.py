"""
stages/summary.py

Stage 4 — Conversation Summary.

This module defines the instructions injected into the system prompt when the
agent generates the end-of-session structured summary.

The summary is always produced at the end of a session — whether the session
ended normally, via escalation, or by the user typing an exit command.

Design rationale:
  - A structured format (fixed section headers, "Not collected" fallback) makes
    the summary machine-readable as well as human-readable.
  - This output can later be piped into a CRM or ticketing system.
"""


# ---------------------------------------------------------------------------
# Stage instruction constant
# Injected into SYSTEM_PROMPT at {stage_instructions} placeholder in agent.py
# ---------------------------------------------------------------------------
SUMMARY_STAGE_INSTRUCTIONS = """
Generate a structured end-of-session summary in this EXACT format:
---
CONVERSATION SUMMARY
====================
Customer Intent: <what the customer wanted>
Treatment Interest: <which services they asked about>
Qualification Answers:
  - Treatment interested in: <answer or "Not collected">
  - Previous treatments: <answer or "Not collected">
  - Availability preference: <answer or "Not collected">
SOP Gaps Identified: <any questions the AI couldn't answer from the SOP, or "None">
Escalation Required: <Yes/No — and reason if Yes>
Recommended Next Action: <e.g., "Book a free consultation", "Human follow-up required", etc.>
Session Duration: <number of exchanges>
---
"""


def get_instructions() -> str:
    """
    Return the summary stage instruction string.

    Returns
    -------
    str
        The SUMMARY_STAGE_INSTRUCTIONS constant, ready to be injected into the
        system prompt.
    """
    return SUMMARY_STAGE_INSTRUCTIONS
