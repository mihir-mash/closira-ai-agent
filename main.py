"""
main.py

Entry point for the Closira AI Customer Support Agent — Bloom Aesthetics Clinic.

Runs a CLI conversation loop that guides the customer through four sequential stages:
  Stage 1 (faq)         — answers questions from the clinic's SOP
  Stage 2 (lead)        — collects booking qualification data
  Stage 3 (escalation)  — hands off to a human agent when needed
  Stage 4 (summary)     — produces a structured end-of-session report

Usage:
    python main.py

Exit commands accepted during the loop:  exit | quit | bye | done
"""

import sys
from pathlib import Path

# Ensure the project root is on the Python path so stage imports resolve
# correctly when main.py is run from any working directory.
sys.path.insert(0, str(Path(__file__).parent))

from agent import ClosiraAgent

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Path to the SOP data file, relative to the project root
SOP_PATH = "data/sop.json"

# Number of FAQ exchanges before automatically advancing to the lead stage.
# This prevents the conversation from staying in FAQ mode indefinitely.
FAQ_EXCHANGE_THRESHOLD = 3

# Keywords that trigger an early advance to the lead-qualification stage
BOOKING_KEYWORDS = {"book", "appointment", "schedule", "booking", "reserve", "slot"}


def print_banner() -> None:
    """
    Print a welcome banner to the terminal when the agent starts.

    Gives the operator (or tester) an immediate visual confirmation that
    the correct agent is running.
    """
    print("\n" + "=" * 60)
    print("   🌸  BLOOM AESTHETICS CLINIC — AI Support Agent  🌸")
    print("=" * 60)
    print("   Powered by Closira  |  Type 'exit' to end the session")
    print("=" * 60 + "\n")


def print_opening_message() -> None:
    """
    Print the hardcoded opening greeting from Bloom.

    Using a hardcoded message (rather than a Groq API call) for the first
    line ensures zero latency at session start and a consistent first impression.
    """
    opening = (
        "Hello! Welcome to Bloom Aesthetics Clinic. 🌸\n"
        "I'm Bloom, your virtual assistant. I'm here to help with any questions "
        "about our treatments, prices, and bookings.\n"
        "How can I help you today?"
    )
    print(f"Bloom: {opening}\n")


def should_advance_to_lead(agent: ClosiraAgent, user_input: str) -> bool:
    """
    Decide whether to advance from the FAQ stage to the lead-qualification stage.

    Two triggers are supported:
      1. The user has had FAQ_EXCHANGE_THRESHOLD or more FAQ exchanges — they
         have had enough time to get their basic questions answered.
      2. The user's message contains a booking-related keyword — clear intent
         to proceed with an appointment.

    Parameters
    ----------
    agent : ClosiraAgent
        The active agent instance (used to inspect exchange count and stage).
    user_input : str
        The user's latest message (lowercased before keyword check).

    Returns
    -------
    bool
        True if we should advance to the lead stage now.
    """
    # Only consider advancing if we are currently in the FAQ stage
    if agent.current_stage != "faq":
        return False

    # Trigger 1: enough FAQ exchanges have occurred
    if agent.exchange_count >= FAQ_EXCHANGE_THRESHOLD:
        return True

    # Trigger 2: user has explicitly mentioned booking intent
    words = set(user_input.lower().split())
    if words & BOOKING_KEYWORDS:
        return True

    return False


def main() -> None:
    """
    Run the full Closira AI customer support conversation loop.

    Workflow:
      1. Print the welcome banner and opening message.
      2. Instantiate ClosiraAgent and load the SOP.
      3. Enter the main loop:
         a. Read user input.
         b. Handle exit commands (trigger summary first).
         c. Skip empty input.
         d. Check if we should advance stage before sending to agent.
         e. Send input to agent.chat() and print the reply.
         f. Break if the agent has escalated.
      4. Always generate and print the session summary.
      5. Save the full conversation transcript to logs/.
    """
    # Step 1 — Visual welcome
    print_banner()

    # Step 2 — Instantiate agent and load SOP
    agent = ClosiraAgent()
    try:
        agent.load_sop(SOP_PATH)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Print the hardcoded opening greeting — no API latency on first message
    print_opening_message()

    # -----------------------------------------------------------------------
    # Step 3 — Main conversation loop
    # -----------------------------------------------------------------------
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C or piped input gracefully
            print("\n[INFO] Session interrupted by user.")
            break

        # --- Exit command detection ---
        # Accept several natural exit phrases; always generate summary before leaving
        if user_input.lower() in {"exit", "quit", "bye", "done"}:
            print("\nBloom: Thank you for chatting with us today! We hope to see you at Bloom soon. 🌸\n")
            break

        # --- Empty input guard ---
        # Ignore empty submissions to prevent empty API calls
        if not user_input:
            continue

        # --- Stage advancement check ---
        # Before sending the message, decide if we should advance the stage.
        # We do this BEFORE calling agent.chat() so the new stage instructions
        # are active when Llama 3 processes the next message.
        if should_advance_to_lead(agent, user_input):
            agent.advance_stage()
            # Inform the user of the stage transition naturally
            print(
                "\nBloom: That's great — I'd love to help you get set up! "
                "I just have a few quick questions to help us find the perfect "
                "appointment for you.\n"
            )

        # --- Send message to agent and get response ---
        response = agent.chat(user_input)
        print(f"\nBloom: {response}\n")

        # --- Escalation check ---
        # If the agent has escalated, print system notices and exit the loop.
        # The conversation summary will still be generated below.
        if agent.is_escalated():
            print("[SYSTEM] This conversation has been flagged for human follow-up.")
            print("[SYSTEM] Escalation logged to logs/escalation_log.json")
            break

    # -----------------------------------------------------------------------
    # Step 4 — End-of-session summary (always generated, even on escalation)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SESSION ENDED — GENERATING SUMMARY")
    print("=" * 60 + "\n")

    summary = agent.generate_summary()
    print(summary)

    # -----------------------------------------------------------------------
    # Step 5 — Persist conversation transcript
    # -----------------------------------------------------------------------
    agent.save_conversation_log()


# ---------------------------------------------------------------------------
# Entry point guard — ensures main() only runs when invoked directly,
# not when this module is imported by tests or other scripts.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
