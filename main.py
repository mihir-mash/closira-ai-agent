import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent import ClosiraAgent

SOP_PATH = "data/sop.json"

FAQ_EXCHANGE_THRESHOLD = 3

# Keywords that trigger an early advance to the lead-qualification stage
BOOKING_KEYWORDS = {"book", "appointment", "schedule", "booking", "reserve", "slot"}


def print_banner() -> None:

    print("\n" + "=" * 60)
    print("   🌸  BLOOM AESTHETICS CLINIC — AI Support Agent  🌸")
    print("=" * 60)
    print("   Powered by Closira  |  Type 'exit' to end the session")
    print("=" * 60 + "\n")


def print_opening_message() -> None:

    opening = (
        "Hello! Welcome to Bloom Aesthetics Clinic. 🌸\n"
        "I'm Bloom, your virtual assistant. I'm here to help with any questions "
        "about our treatments, prices, and bookings.\n"
        "How can I help you today?"
    )
    print(f"Bloom: {opening}\n")


def should_advance_to_lead(agent: ClosiraAgent, user_input: str) -> bool:

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

    # Step 1 — Visual welcome
    print_banner()

    # Step 2 — Instantiate agent and load SOP
    agent = ClosiraAgent()
    try:
        agent.load_sop(SOP_PATH)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


    print_opening_message()

    # Step 3 — Main conversation loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
           
            print("\n[INFO] Session interrupted by user.")
            break

        if user_input.lower() in {"exit", "quit", "bye", "done"}:
            print("\nBloom: Thank you for chatting with us today! We hope to see you at Bloom soon. 🌸\n")
            break

        if not user_input:
            continue

        # Stage advancement check
        if should_advance_to_lead(agent, user_input):
            agent.advance_stage()

            print(
                "\nBloom: That's great — I'd love to help you get set up! "
                "I just have a few quick questions to help us find the perfect "
                "appointment for you.\n"
            )

        # Send message to agent and get response
        response = agent.chat(user_input)
        print(f"\nBloom: {response}\n")

        # Escalation check
        if agent.is_escalated():
            print("[SYSTEM] This conversation has been flagged for human follow-up.")
            print("[SYSTEM] Escalation logged to logs/escalation_log.json")
            break

    # Step 4 — End-of-session summary (always generated, even on escalation)
    print("\n" + "=" * 60)
    print("SESSION ENDED — GENERATING SUMMARY")
    print("=" * 60 + "\n")

    summary = agent.generate_summary()
    print(summary)

    # Step 5 — Persist conversation transcript
    agent.save_conversation_log()

if __name__ == "__main__":
    main()