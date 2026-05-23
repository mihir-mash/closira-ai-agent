## Test: Out-of-Scope Question — Unavailable Treatment

**Scenario**: A customer asks about a treatment (laser hair removal) that does not appear anywhere in the SOP. The agent should **not** invent information, should honestly acknowledge the gap, and should offer to connect the customer with a human team member — triggering a LOW_CONFIDENCE or ESCALATE response.

---

**You**: Do you offer laser hair removal at Bloom?

**Bloom** *(LOW_CONFIDENCE response — customer-facing message)*:
That's a great question! I'm afraid I don't have any information about laser hair removal in the details available to me right now, so I wouldn't want to give you inaccurate information.

I'd recommend speaking directly with one of our team members who can give you a definitive answer and let you know about any upcoming services. Shall I arrange for someone to get in touch with you?

---

**You**: What about skin peels or microneedling?

**Bloom** *(second consecutive LOW_CONFIDENCE — auto-escalation triggered)*:
I'm sorry — I've reached the limits of what I can help with today. I'll make sure one of our team members follows up with you promptly to answer all your questions properly.

`[SYSTEM] This conversation has been flagged for human follow-up.`  
`[SYSTEM] Escalation logged to logs/escalation_log.json`

---

**SESSION ENDED — GENERATING SUMMARY**

```
---
CONVERSATION SUMMARY
====================
Customer Intent: Enquiring about treatments not listed in the SOP (laser hair removal, skin peels, microneedling)
Treatment Interest: Laser hair removal, skin peels, microneedling (none available in SOP)
Qualification Answers:
  - Treatment interested in: Not collected
  - Previous treatments: Not collected
  - Availability preference: Not collected
SOP Gaps Identified: Laser hair removal, skin peels, microneedling — none of these services are listed in the clinic's current SOP
Escalation Required: Yes — more than 2 consecutive questions could not be answered from the SOP
Recommended Next Action: Human follow-up required — customer has specific service enquiries that exceed the SOP knowledge base
Session Duration: 2 exchanges
---
```

---

**Expected Behaviour**:
- First out-of-scope question → LOW_CONFIDENCE response (honest, no hallucination)
- Second consecutive out-of-scope question → automatic escalation (two-strike rule)
- Escalation logged to `logs/escalation_log.json`
- Summary reflects SOP gaps and escalation

**Actual Behaviour**: Agent correctly responded with a LOW_CONFIDENCE message on the first unknown question and auto-escalated on the second, exactly as the two-strike rule specifies. No invented service information appeared in either response.

**Pass/Fail**: PASS
