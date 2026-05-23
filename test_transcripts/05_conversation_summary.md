## Test: Conversation Summary — Full Session End-to-End

**Scenario**: A customer completes a full session — asks SOP questions in the FAQ stage, moves through lead qualification, then types "done" to exit. The system generates a structured summary covering all four stages.

---

**You**: Hello! What's the difference between Botox and dermal fillers?

**Bloom**: Great question! They're both very popular treatments but work in quite different ways. 😊

**Botox** (starting from **£200**):
- Botox is an anti-wrinkle injection that temporarily relaxes the muscles that cause lines and wrinkles
- It's ideal for dynamic wrinkles — the kind caused by facial expressions, such as frown lines, forehead lines, and crow's feet
- Results typically last 3–4 months

**Dermal Fillers** (starting from **£250**):
- Fillers add volume and structure beneath the skin using a gel-like substance
- They're brilliant for lip enhancement, cheek contouring, and jawline definition
- Results can last 12–18 months depending on the area and product used

In short: Botox *relaxes*, fillers *add volume*. Many clients actually combine the two for a more complete result!

Would you like to know more about either treatment, or shall I tell you about how to book a consultation?

---

**You**: That's really helpful. Are there any other treatments you offer?

**Bloom**: Right now, our main treatments are **Botox** and **Dermal Fillers**, along with a **free initial consultation** with one of our practitioners.

The consultation is a brilliant starting point — our practitioners will listen to your goals, assess your face, and recommend the most suitable approach for you personally. There's no pressure to book anything on the day.

Is there a specific concern or area you'd like to address? That might help me point you in the right direction!

---

**You**: Perfect. I think I'd like to book an appointment.

*[SYSTEM advances stage: faq → lead — booking keyword detected]*

**Bloom** *(stage transition)*: That's great — I'd love to help you get set up! I just have a few quick questions to help us find the perfect appointment for you.

**Bloom** *(Question 1)*: Brilliant! Let's get the ball rolling. First of all: **What treatment are you most interested in?**

---

**You**: Botox, I think. I have forehead lines I want to sort out.

**Bloom** *(Question 2)*: Botox is a wonderful choice for forehead lines — one of the most effective and popular treatments we offer! 😊

**Have you had any aesthetic treatments before, or would this be your first time?**

---

**You**: I've had Botox once before, about two years ago, at a different clinic.

**Bloom** *(Question 3)*: That's great to know — having had a previous treatment means you'll have a good idea of what to expect. Our practitioners will be able to build on that experience.

Last question: **Would you prefer a morning or afternoon appointment, and are there any days that don't work for you?**

---

**You**: Morning would be ideal. Thursdays and Fridays don't work for me.

**Bloom**: Perfect — here's a quick summary of everything I've noted:

- **Treatment**: Botox (forehead lines)
- **Previous experience**: Yes — Botox at another clinic two years ago
- **Appointment preference**: Morning, not available Thursdays or Fridays

Does that all look right? Whenever you're ready, you can book your **free consultation** via WhatsApp or our website — our team will match you with a suitable slot. 🌸

---

**You**: done

**Bloom**: Thank you for chatting with us today! We hope to see you at Bloom soon. 🌸

---

**SESSION ENDED — GENERATING SUMMARY**

```
---
CONVERSATION SUMMARY
====================
Customer Intent: Enquiring about Botox vs. dermal fillers, then booking a Botox appointment for forehead lines
Treatment Interest: Botox (forehead lines); also asked about dermal fillers for comparison
Qualification Answers:
  - Treatment interested in: Botox for forehead lines
  - Previous treatments: Yes — Botox at a different clinic approximately two years ago
  - Availability preference: Morning appointments, not available on Thursdays or Fridays
SOP Gaps Identified: None — all questions were answered from the SOP
Escalation Required: No
Recommended Next Action: Book a free consultation to discuss Botox for forehead lines; flag returning client status to practitioner
Session Duration: 5 exchanges
---
```

---

**Expected Behaviour**:
- FAQ stage handles two SOP questions correctly
- Stage advances to lead on booking keyword
- All three qualification questions asked one at a time
- Answers collected and confirmed
- On "done" command: summary generated with all sections populated
- No escalation in this session

**Actual Behaviour**: Full end-to-end session completed successfully. The FAQ stage answered both questions accurately from the SOP. Stage transitioned cleanly to lead qualification. All three qualification answers were collected. The structured summary correctly reflected the full conversation, the treatment interest, qualification data, and the "no escalation" status. The "done" command triggered a graceful exit with the summary generated immediately after.

**Pass/Fail**: PASS
