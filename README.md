# Closira AI Agent — Bloom Aesthetics Clinic

A Python-based, multi-stage AI customer support workflow built for the Closira internship assignment.  
The agent simulates a full inbound chat experience for **Bloom Aesthetics Clinic**, powered by the Groq API (`llama3-70b-8192`).

---

## Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd closira_agent
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

### 3. Activate the virtual environment
**macOS / Linux**
```bash
source venv/bin/activate
```
**Windows**
```bash
venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure your API key
```bash
cp .env.example .env
```
Open `.env` and replace `your_groq_api_key_here` with your real key from  
[https://console.groq.com/keys](https://console.groq.com/keys)

> **Never commit the `.env` file.**  It is already excluded in `.gitignore`.

### 6. Run the agent
```bash
python main.py
```

Type `exit`, `quit`, `bye`, or `done` to end the session.

---

## How It Works

The agent runs a linear four-stage pipeline within a single CLI conversation loop.

### Stage 1 — FAQ Answering (`faq`)
The agent answers inbound questions **strictly** from the SOP data in `data/sop.json`.  
If a question is out of scope, it escalates rather than hallucinating.  
After 3 exchanges, or when the user mentions booking intent, the agent advances to Stage 2.

### Stage 2 — Lead Qualification (`lead`)
The agent asks three structured questions, **one at a time**:
1. What treatment are you most interested in?
2. Have you had aesthetic treatments before?
3. What days / times work for you?

Answers are stored in `agent.lead_data` for the session summary.

### Stage 3 — Escalation Detection (`escalation`)
At **any point** in the conversation, if the model detects:
- A complaint or angry language
- A medical question (side effects, contraindications)
- A pricing negotiation attempt
- An explicit request for a human
- 2+ consecutive unanswered questions (the "two-strike rule")
- Any safety or adverse reaction concern

…it returns a structured JSON response (`"action": "ESCALATE"`).  The agent:
1. Transitions to the escalation stage
2. Logs the event to `logs/escalation_log.json` (append-only)
3. Prints the warm customer-facing message
4. Exits the conversation loop

### Stage 4 — Conversation Summary (`summary`)
Always generated at session end (normal exit *or* escalation).  
A structured report is produced by Llama 3 using the full conversation history and includes:
- Customer intent and treatment interest
- All 3 qualification answers
- SOP gaps identified
- Whether escalation occurred and why
- Recommended next action

The full transcript is also saved to a timestamped JSON file in `logs/`.

---

## Project Structure

```
closira_agent/
├── main.py                    # CLI entry point and conversation loop
├── agent.py                   # ClosiraAgent class — all core logic
├── stages/
│   ├── __init__.py
│   ├── faq.py                 # Stage 1 instructions constant
│   ├── lead_qualification.py  # Stage 2 instructions constant
│   ├── escalation.py          # Stage 3 instructions constant
│   └── summary.py             # Stage 4 instructions constant
├── data/
│   └── sop.json               # Clinic knowledge base
├── logs/
│   └── .gitkeep               # Runtime logs go here (excluded from git)
├── test_transcripts/          # Five realistic test conversations
├── prompt_design.md           # Prompt engineering rationale
├── README.md                  # This file
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Architecture Decisions

### Single system prompt with stage injection
Rather than maintaining four separate system prompts, a single template is used with three runtime placeholders: `{sop_data}`, `{current_stage}`, and `{stage_instructions}`.  This keeps the agent's identity, tone, and safety rules consistent across all stages while allowing stage-specific behaviour to be swapped in cleanly.

### Structured JSON escalation signals
The model is instructed to return a specific JSON object (`"action": "ESCALATE"` or `"action": "LOW_CONFIDENCE"`) rather than plain text when special handling is needed.  This makes detection completely reliable — a simple `try_parse_json()` check is all that is needed, with no regex or fragile text matching.

### External SOP JSON
Business data is stored in `data/sop.json` rather than hardcoded in Python.  This means the clinic can update prices, services, or policies without a code change, and the SOP can be validated independently.

### Append-only escalation log
`logs/escalation_log.json` is never overwritten — new events are appended.  This preserves a complete audit trail for CRM integration and quality assurance.

---

## Known Limitations

- **No persistent memory across sessions** — each run starts fresh.  A real system would store conversation history in a database.
- **Stage transitions are rule-based** — the FAQ→lead transition is triggered by exchange count or keyword matching, not by semantic understanding of conversation readiness.
- **SOP is static JSON** — a production system would use a vector database (e.g. Pinecone, Chroma) for semantic retrieval over a much larger knowledge base.
- **No authentication** — the CLI has no concept of user identity.

---

## Trade-offs

1. **Simplicity vs. flexibility on stage transitions.**  
   Using a fixed exchange count (3 FAQ turns) to trigger the lead stage is simple and predictable but can feel abrupt.  A more sophisticated approach would use intent classification to detect when the customer is ready to book — but this would add latency and complexity.

2. **Single API call per turn vs. multi-step chain-of-thought.**  
   Each user message results in exactly one Groq API call.  A chain-of-thought or multi-step reasoning approach might improve accuracy on edge cases but would significantly increase response latency and API costs — a poor fit for a real-time support chat.
