# Prompt Design Document

This document explains the prompt engineering decisions made in building the Closira AI agent for Bloom Aesthetics Clinic.

---

## System Prompt (Full Text)

```
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
{
  "action": "ESCALATE",
  "reason": "<brief reason for escalation>",
  "sentiment": "<neutral|frustrated|angry|urgent>",
  "message_to_customer": "<a warm message telling the customer a human will follow up>"
}

CONFIDENCE DETECTION:
If you are unsure about any answer, respond in this EXACT JSON format:
{
  "action": "LOW_CONFIDENCE",
  "topic": "<what the customer asked about>",
  "message_to_customer": "<honest message saying you're not sure and will get help>"
}

For all normal responses, reply as plain conversational text only — no JSON.

CURRENT STAGE: {current_stage}
STAGE INSTRUCTIONS: {stage_instructions}
```

---

## Design Decisions

### 1. Why a single system prompt with stage injection?

**The alternative** would be to maintain four entirely separate system prompts — one for each stage — and swap them out as the conversation progresses.

**The chosen approach** uses a single template with three runtime placeholders (`{sop_data}`, `{current_stage}`, `{stage_instructions}`):

- **Consistency**: The agent's identity (name "Bloom"), tone guidelines, British English requirement, and safety/escalation rules are defined *once*. There is no risk of accidentally omitting the escalation rules from the lead-qualification prompt, for example.
- **Maintainability**: Adding a fifth stage only requires creating a new `stages/newstage.py` file and registering it in the `stage_instruction_map` inside `agent.py`. The base prompt never needs touching.
- **Debuggability**: A single source of truth for the core prompt makes it trivial to audit exactly what the model receives at each turn.

The `{stage_instructions}` block is intentionally kept short and focused — it supplements, rather than replaces, the base prompt.

---

### 2. Hallucination Prevention

Hallucination is the highest-risk failure mode for a business-facing AI chatbot. A fabricated price or medical claim can damage customer trust or create legal liability.

**Techniques used:**

| Technique | Where in the prompt |
|---|---|
| Explicit SOP boundary statement | `"You may ONLY answer questions using the information provided in the SOP data below"` |
| Enumerated "never" directives | `"NEVER invent prices, services, staff names, policies, or medical information"` |
| Honest fallback instruction | `"an honest 'I don't know' is always better"` |
| Out-of-scope → escalation | The JSON LOW_CONFIDENCE path routes out-of-scope questions to a human |
| SOP injected directly into prompt | The model sees the actual data, not a retrieval summary |

By injecting the full SOP JSON directly into the system prompt, the model has no need to "guess" — everything it is allowed to say is laid out explicitly. This is a simpler and more reliable approach than retrieval-augmented generation (RAG) at this scale.

---

### 3. Confidence-Based Escalation

**Problem**: Even with strict SOP boundaries, a customer may ask questions that are partially in scope but where the model lacks certainty. Without a mechanism to detect this, the model might give a vague or slightly wrong answer.

**Solution — the two-strike rule**:

1. The model is instructed to return `{"action": "LOW_CONFIDENCE", ...}` whenever it is unsure.
2. The agent maintains `self.unanswered_count`, a counter of consecutive LOW_CONFIDENCE responses.
3. On the **first** LOW_CONFIDENCE response: the honest customer-facing message is delivered and the counter increments.
4. On the **second** consecutive LOW_CONFIDENCE response: `handle_escalation()` is called automatically with a pre-written message explaining the hand-off.

**Why this threshold?**  
One unanswered question is acceptable and may simply be an unusual enquiry. Two consecutive unknowns suggests a systematic gap in the SOP — the customer deserves human help at that point.

**Why JSON format for the signal?**  
Plain-text confidence signals (e.g., "I'm not sure about this") would require fragile regex matching. A structured JSON object with a known `"action"` key can be detected with a single `try_parse_json()` call — zero false positives or negatives.

---

### 4. Tone & Persona

**Persona: "Bloom" — a warm, professional receptionist**

This persona was chosen for several reasons specific to the SMB aesthetics clinic context:

- **Warmth is commercially important**: Aesthetic treatments are personal and often anxiety-inducing for first-time clients. A cold or robotic tone would undermine the clinic's premium brand positioning.
- **Professionalism builds trust**: The clinic is dealing with medical-adjacent services. A tone that is *too* casual would feel inappropriate and potentially reduce trust in the safety of treatments.
- **British English is culturally relevant**: The clinic uses GBP pricing (£200, £250), strongly implying a UK-based business. British English spelling (`"colour"`, `"enquiry"`, `"cancelled"`) signals authenticity and avoids jarring localisation mismatches.

The receptionist metaphor is deliberately chosen over "chatbot" or "assistant" — receptionists are expected to:
- Know the basics thoroughly (SOP questions)
- Say "I'll find out" rather than guessing (LOW_CONFIDENCE)
- Escalate to a doctor or manager for complex issues (ESCALATION)

This mental model maps directly onto the four-stage pipeline.

---

### 5. Structured Output for Escalation

**Why JSON for escalation signals?**

When the model needs to escalate, the agent must do three things simultaneously:
1. Display a warm, reassuring message to the customer
2. Log structured metadata (reason, sentiment, timestamp) to `logs/escalation_log.json`
3. Change internal state (`self.current_stage = "escalation"`)

A plain-text escalation response (e.g., "I'll connect you with a human") cannot reliably carry the `reason` and `sentiment` fields needed for the log. Embedding that data in natural language would require parsing — fragile and error-prone.

**JSON is the right tool because:**
- It is **parseable in a single call**: `json.loads()` either succeeds or fails, no ambiguity.
- It is **self-describing**: each field (`action`, `reason`, `sentiment`, `message_to_customer`) has a clear purpose.
- It is **loggable without transformation**: the `reason` and `sentiment` values can be written directly to the JSON log file.
- It **separates concerns**: the customer-facing message (`message_to_customer`) is decoupled from the system metadata (`reason`, `sentiment`), so a human reviewing the log can understand the context without reading the full conversation.

The prompt instructs the model to return "this EXACT JSON format (and nothing else)" — the strictness is intentional, ensuring the `try_parse_json()` detection in `agent.py` always works correctly.
