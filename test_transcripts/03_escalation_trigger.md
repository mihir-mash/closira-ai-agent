## Test: Escalation Trigger — Customer Frustration / Complaint

**Scenario**: A customer expresses frustration about a previous appointment and makes a complaint. This should immediately trigger an ESCALATE response from the model — no further FAQ processing should occur. The escalation is logged and the loop terminates.

---

**You**: Hi, I need to talk to someone. I booked an appointment last week and it was an absolute disaster. The practitioner was rude to me and I'm really not happy at all.

**Bloom** *(ESCALATE signal detected — customer-facing message)*:
I'm so sorry to hear that you had such an upsetting experience — that is absolutely not the standard we hold ourselves to at Bloom, and I completely understand how you must be feeling right now.

I want to make sure this is handled properly and with the care it deserves. A member of our team will be in touch with you very shortly to speak with you directly and make things right. 💙

Thank you for taking the time to let us know — your feedback is genuinely important to us.

`[SYSTEM] This conversation has been flagged for human follow-up.`  
`[SYSTEM] Escalation logged to logs/escalation_log.json`

---

**Escalation Log Entry** (written to `logs/escalation_log.json`):

```json
{
  "timestamp": "2026-05-23T14:32:00",
  "exchange_number": 1,
  "reason": "Customer made a formal complaint about a previous appointment and expressed significant frustration",
  "sentiment": "frustrated",
  "conversation_snippet": "Hi, I need to talk to someone. I booked an appointment last week and it was an absolute disaster. The practitioner was rude to me and I'm really not happy at all."
}
```

---

**SESSION ENDED — GENERATING SUMMARY**

```
---
CONVERSATION SUMMARY
====================
Customer Intent: Making a complaint about a previous appointment and rude practitioner
Treatment Interest: Not applicable (complaint session)
Qualification Answers:
  - Treatment interested in: Not collected
  - Previous treatments: Not collected (customer had a previous appointment)
  - Availability preference: Not collected
SOP Gaps Identified: None — question did not relate to SOP content
Escalation Required: Yes — customer expressed significant frustration and made a formal complaint about a practitioner
Recommended Next Action: Human follow-up required urgently — complaint must be handled by clinic management
Session Duration: 1 exchange
---
```

---

**Expected Behaviour**:
- First message is a clear complaint with frustrated sentiment
- Agent immediately returns ESCALATE JSON (not a normal reply)
- Customer-facing message is warm and empathetic, not defensive
- Escalation is logged with reason, sentiment, and conversation snippet
- Conversation loop terminates after escalation
- Summary reflects the complaint nature of the session

**Actual Behaviour**: The model correctly identified complaint language and frustrated sentiment in the very first message and returned an ESCALATE JSON response. The customer-facing message was genuinely empathetic. The escalation event was logged, the loop exited, and the summary accurately described the situation.

**Pass/Fail**: PASS
