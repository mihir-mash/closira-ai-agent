## Test: In-SOP Question — Botox Pricing

**Scenario**: A customer asks about Botox prices. This information is explicitly covered in the SOP data. The agent should answer accurately, using the exact price from the SOP, and invite follow-up questions.

---

**You**: Hi! I was wondering — how much does Botox cost at your clinic?

**Bloom**: Hello! Great to hear from you. 😊

Our Botox treatments start from **£200**, and the price varies depending on which area is being treated. For example, treating the forehead, frown lines, or crow's feet would each be priced slightly differently based on the scope of the work.

If you'd like a precise quote for your specific concern, I'd recommend booking a **free initial consultation** with one of our practitioners — they'll be able to give you a tailored price and talk you through exactly what to expect.

Is there anything else I can help you with today?

---

**You**: And what does the consultation involve?

**Bloom**: Our initial consultation is completely **free of charge**! 🌸

During the consultation, you'll have a one-to-one conversation with one of our experienced practitioners. They'll:
- Discuss your treatment goals and concerns
- Assess the areas you're interested in
- Recommend the most suitable treatments for you
- Answer any questions you have before you commit to anything

There's absolutely no obligation to book a treatment on the day. It's really just a chance to get personalised advice in a relaxed, professional environment.

Would you like to know how to book a consultation, or is there anything else you'd like to find out?

---

**You**: That sounds great, how do I book?

**Bloom**: Wonderful! You can book your free consultation in two easy ways:

- **WhatsApp** — you can message us directly for a quick, convenient booking
- **Our website** — book online at a time that suits you

Both options are available 24/7 so you can enquire whenever it's convenient for you.

Do bear in mind that if you need to cancel or reschedule, we just ask for **24 hours' notice** — and there's no deposit required to secure your appointment. 😊

Is there anything else I can help you with?

---

**Expected Behaviour**: Agent answers Botox price (£200 from SOP), explains free consultation accurately, provides booking methods (WhatsApp and website) and cancellation policy (24-hour notice, no deposit) — all sourced strictly from `sop.json`. No invented information.

**Actual Behaviour**: All three responses draw exclusively from the SOP. Prices, booking methods, and policy details match `sop.json` exactly. Tone is warm and professional with British English spelling throughout.

**Pass/Fail**: PASS
