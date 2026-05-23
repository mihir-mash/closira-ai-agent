## Test: Lead Qualification — Full 3-Question Flow

**Scenario**: The customer asks about booking an appointment. After enough FAQ exchanges (or detecting the word "book"), the system advances to the lead-qualification stage. The agent asks all three questions one at a time, collects answers, and produces a qualification summary.

> **Note**: The system prints a stage-transition message before the first lead question.

---

**You**: Hi there! I'm interested in getting some fillers done. What do you offer?

**Bloom**: Hello and welcome to Bloom Aesthetics Clinic! 🌸

We offer a lovely range of **Dermal Filler** treatments, starting from **£250**. Our fillers can be used to enhance:
- **Lips** — for a fuller, more defined look
- **Cheeks** — to restore volume and contour
- **Jawline** — for a sharper, more sculpted profile

The exact price will depend on the area being treated and the amount of filler used, so it does vary per person. The best way to get an accurate quote is through a **free consultation** with one of our practitioners — there's no obligation to book on the day!

Is there a particular area you're most interested in, or would you like to know more?

---

**You**: I'd love to know more about lip fillers specifically. And how do I book?

*[SYSTEM advances stage: faq → lead — booking keyword detected]*

**Bloom** *(stage transition message)*: That's great — I'd love to help you get set up! I just have a few quick questions to help us find the perfect appointment for you.

**Bloom** *(Question 1)*: Wonderful! Lip fillers are one of our most popular treatments. 💋

To help me point you in the right direction, I have a few quick questions — I'll take them one at a time so we can have a proper chat.

First: **What treatment are you most interested in?** From what you've mentioned, it sounds like lip fillers, but is that right — or are there other areas you'd like to explore as well?

---

**You**: Yes, definitely lip fillers. I want a more natural, subtle look.

**Bloom** *(Question 2)*: Lovely — a natural, subtle enhancement is a really popular choice and our practitioners are wonderful at achieving that look. ✨

Next question: **Have you had any aesthetic treatments before, or would this be your first time?**

---

**You**: This would be my first time, I'm a little nervous to be honest!

**Bloom** *(Question 3)*: Oh, that's completely understandable — it's very normal to feel nervous before your first treatment! I can assure you our practitioners are incredibly gentle and will walk you through every step beforehand, so there are no surprises.

One last question: **Would you prefer a morning or afternoon appointment, and are there any days that don't work for you?**

---

**You**: I'd prefer an afternoon, and I can't do Mondays.

**Bloom** *(Qualification summary and confirmation)*: Perfect — thank you so much for sharing that! Here's a quick summary of what I've noted down for you:

- **Treatment**: Lip fillers (natural, subtle result)
- **First-time client**: Yes 🌸
- **Appointment preference**: Afternoon appointments, any day except Mondays

Does that all sound right? If so, I'd love to help you take the next step — you can book your **free consultation** via WhatsApp or our website whenever you're ready. Our team will make sure everything is explained to you beforehand so you feel completely at ease. 💙

---

**Expected Behaviour**:
- Booking keyword ("book") detected → advance to lead stage after FAQ reply
- Agent asks 3 questions strictly one at a time
- Each question waits for an answer before proceeding
- After all 3 answers, agent summarises and confirms with the customer
- Lead data is stored in `agent.lead_data` for the summary stage

**Actual Behaviour**: Stage transitioned correctly on booking keyword. All three questions were asked sequentially with appropriate conversational bridging. The agent validated understanding with a confirmation summary. Tone remained warm and reassuring throughout — particularly appropriate given the customer's first-timer nerves.

**Pass/Fail**: PASS
