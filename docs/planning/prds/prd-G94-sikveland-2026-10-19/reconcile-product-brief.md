# Reconcile: product-brief.md vs PRD + addendum

- **Input:** `docs/planning/product-brief.md`
- **Compared against:** `prd.md`, `addendum.md` (both as of 2026-11-02), with `.memlog.md` used to spot deliberate changes
- **Date:** 2026-11-02
- **Scope:** Content in the brief that the PRD and addendum drop, contradict or weaken. Things the PRD added (ticks saved on the phone, Facebook entry, FR12, FR13) are not listed unless they conflict with the brief.

Severity: **high** = affects requirements, privacy or grading traceability; **medium** = a missing requirement detail or positioning that downstream work needs; **low** = wording, nice-to-have or detail that is easy to restore.

---

## A. Real gaps (not explained by the memlog)

### G1. Telling users that questions go to the language model provider
- **Input (Privacy):** "Questions are sent to the language model provider to generate answers, and this will be stated on the page."
- **PRD:** Missing. FR9 only covers the personal-information warning. NFR5 only covers what is stored.
- **Severity:** high (privacy transparency; users are told not to share data, but not told where their text goes)
- **Suggested home:** FR9 (extra acceptance criterion) or NFR5
- **Intentional change:** No. The memlog does not mention it (line 40 says NFR5 is "unchanged in substance").

### G2. Rules for building and reviewing the knowledge base
- **Input (Knowledge Base):** The chatbot answers "only from a fixed collection of 10–20 selected pages". Sources are limited to four publishers: UDI, VFS Global, the Royal Norwegian Embassy in Bangkok, and European Commission Schengen pages "where UDI refers to them". Each source is stored "as a Markdown copy" in the repository. "A list of all sources is kept in one file, so every answer can be traced to a specific version of a source." When the script fetches sources again, "I review the changes before they are used. I will make the final selection of pages and check them against my own experience."
- **PRD:** FR11 keeps 10–20 sources, URL/publisher/date and the update script. Missing: the list of allowed publishers (the Glossary gives examples only, and the EC Schengen pages and their condition are absent), the Markdown copy in the repository, the single sources-list file, tracing answers to a specific source version, the adviser's review before changes are used, and the adviser's final selection.
- **Severity:** high (the human review step is the main protection against outdated or wrong answers, and it is what sets the product apart from general chatbots)
- **Suggested home:** FR11 acceptance criteria (review before use, allowed publishers, traceability). Storage format and the sources-list file go in the addendum under "For architecture".
- **Intentional change:** No

### G3. Definition of the test set and when it is re-run
- **Input (Success Criteria):** "a fixed test set of 20–30 questions written in Thai, each with an English translation, the expected key facts, the expected source, and whether the chatbot should answer or refer the user onward". "The test set will be run again every time the prompts or sources change."
- **PRD:** NFR4 says "On the test set" and lists what the test set covers. It does not give the size, the fields for each question, or the rule to re-run it after prompt or source changes.
- **Severity:** high (NFR4 cannot be tested without a defined test set, and NFR7 versioned prompts depend on the re-run rule)
- **Suggested home:** NFR4 (or a Glossary entry for "Test set")
- **Intentional change:** No

### G4. Explaining visa terms
- **Input (Exec Summary, Solution, Scope):** the chatbot explains "visa terms in clear Thai" / "common visa terms"; scope includes "visa terminology"; the UDI source covers "common terms".
- **PRD:** Missing. There is no FR, no MVP scope bullet, and FR11 coverage lists no terms. The PRD covers steps, checklists, forms, relationship proof and the fee.
- **Severity:** medium
- **Suggested home:** §4.1 (an FR or an acceptance criterion under FR1/FR2), §8.1, FR11 coverage list, NFR4 test-set coverage
- **Intentional change:** No

### G5. Target users: primary user description, digital skills and secondary users
- **Input (Who This Serves, Problem):** The primary users are Thai short-stay applicants (tourism, family and friends) with "limited knowledge of visa procedures" who "lack the digital skills needed to find and understand information online". "Secondary users are members of the public who want to learn about these visas, even if they are not currently planning to apply."
- **PRD:** §2 starts at §2.3 Key User Journeys, so §2.1 and §2.2 (user description) are missing. Low digital skills appear only indirectly, through NFR1 (large touch targets, simple language) and FR8. Secondary users are missing.
- **Severity:** medium (also a structural hole in the PRD)
- **Suggested home:** §2.1 Primary user, §2.2 Secondary user
- **Intentional change:** No. The memlog records only the journey decisions.

### G6. How it differs from general AI chatbots and the official websites
- **Input (What Makes This Different):** UDI and VFS sites are authoritative but "mostly in Norwegian or English … spread across many pages". "General AI chatbots answer in Thai, but they do not limit themselves to official sources, may give outdated or invented requirements, and rarely say when a question needs an individual assessment." "This chatbot combines the strengths of both."
- **PRD:** Missing. §1 Vision describes the problem with the websites but never compares the product with general AI chatbots. UJ-1 even says applicants use "Google Translate or an AI tool" for UDI pages, with no positioning against that.
- **Severity:** medium (needed to justify FR2 and FR3, and expected by the examiner)
- **Suggested home:** §1 Vision (a short "Why this, not a general chatbot" paragraph)
- **Intentional change:** No

### G7. Tech, cost and running the app are missing from the addendum
- **Input (Technology, Cost and Running the App):**
  - Stack: Python and FastAPI, a simple HTML/JS chat page, SQLite for feedback.
  - Model: Claude Opus 5.5, "set in a configuration file and can be changed without code changes".
  - Answers: the whole knowledge base goes into the prompt with prompt caching, and the Citations feature makes "each answer quote the source text it is based on". "A separate search database is not needed."
  - Cost: $4 / $20 per million tokens, with cost per question reported in the README.
  - `.env.example` for your own key. Demo mode "returns stored answers to the example questions". Automated tests always use demo mode.
  - The README lists the example questions with English **and Norwegian** translations.
- **PRD/addendum:** Only NFR2, NFR3, NFR6 and FR10 at a high level. The addendum has none of these points. The model being configurable without code changes is missing. The citation and quoting behaviour is weakened to "links". The demo behaviour for example questions is not recorded, although §9 Q2 asks only about questions that are not prepared, which suggests the brief's answer for prepared questions was lost. The Norwegian translations are missing.
- **Severity:** medium
- **Suggested home:** addendum "For architecture" (stack, model config, full-context and caching, Citations, no vector DB, cost figures, demo-mode stored answers, `.env.example`, README translations). Optionally add an acceptance criterion to FR10: "demo mode returns stored answers to the example questions".
- **Intentional change:** No

### G8. 24-hour availability needs the app to be hosted
- **Input:** "available 24 hours a day"; users open a link from their phone.
- **PRD:** §1 Vision keeps "24 hours a day", but there is no NFR for availability or hosting. NFR2 only covers running the app locally. Users following a Facebook link need a publicly hosted app.
- **Severity:** medium (the vision promises something no NFR covers; this may be an IBE160 scope decision that should be stated)
- **Suggested home:** NFR (availability/deployment) or §9 Open Questions ("is a hosted deployment part of the course deliverable?")
- **Intentional change:** No

### G9. Answers quote their sources with numbered citations
- **Input (Example conversation, Tech):** Numbered in-text references [1] with a source list under the answer. Citations "quote the source text it is based on". Every answer "can be traced to a specific version of a source".
- **PRD:** FR2 asks for "at least one source link" and "no facts not in its sources". Citations at claim level and version traceability are missing.
- **Severity:** low–medium
- **Suggested home:** FR2 acceptance criterion; the mechanism goes in the addendum
- **Intentional change:** No

### G10. Clear, everyday Thai: tone and voice
- **Input:** "Users will be able to ask questions in everyday language and receive clear explanations"; "clear Thai"; "explain its limitations"; polite apology in the example ("ขออภัย…").
- **PRD:** NFR1 mentions "simple language" only as a mobile/UX point. FR1 has no criterion on plain, clear Thai or on tone (polite, honest about limits).
- **Severity:** low–medium
- **Suggested home:** FR1 acceptance criterion or a new NFR (Voice: clear, polite, everyday Thai; explains its limits). Detail goes to UX.
- **Intentional change:** No

### G11. Visit purposes listed explicitly, and KB coverage of the example facts
- **Input (Scope):** The checklist covers "tourism, or visiting family or friends". The example answer covers passport validity (3 months after leaving Schengen) and travel insurance (€30,000).
- **PRD:** The Glossary says "Visit purpose … e.g. visiting family". FR6 does not list the purposes. FR11 coverage and the NFR4 test-set coverage do not mention a tourism checklist, passport or insurance requirements.
- **Severity:** low
- **Suggested home:** FR6 (list the purposes: tourism, family, friends), FR11 coverage list
- **Intentional change:** No

### G12. Long-term vision: tailored guidance with human support kept
- **Input (Vision):** Expansion over 2–3 years to more visa types and "guidance that is more relevant to each user's circumstances"; accounts and a paid service; "Complex cases will still require support from a human adviser"; a sustainable service.
- **PRD:** §8.2 mentions accounts, payment and other visa types as long-term vision. §1 Vision does not carry the long-term direction, and the "human support for complex cases" principle is missing.
- **Severity:** low
- **Suggested home:** §1 Vision (one closing sentence)
- **Intentional change:** No

### G13. Scale of the problem
- **Input:** "questions from dozens of people each day, at different times of the day and night"; "As the only adviser".
- **PRD:** §1 says applicants wait "often at night or at weekends" but gives no volume. That volume is the baseline for SM-C1.
- **Severity:** low
- **Suggested home:** §1 Vision or §6 (baseline for SM-C1)
- **Intentional change:** No

---

## B. Intentional changes (decided later, per the memlog)

### I1. Where individual-assessment questions are sent
- **Input:** These questions are "referred to a human adviser or the relevant authority". The example says "contact a visa adviser or UDI directly".
- **PRD:** FR3 and NFR4 say "the decision is made by the embassy and no one else can answer it"; the chatbot never estimates chances.
- **Intentional change:** Yes. Memlog line 32 replaced referral with "embassy decides".
- **Residual note (low):** FR3 does not say whether the answer links to the embassy or UDI. Consider adding a link so the user is not left at a dead end.

### I2. When the feedback question is asked
- **Input:** "The feedback question is shown after an answer", and elsewhere "At the end of each conversation".
- **PRD:** FR5 asks it on a done signal. "No" leads to "What would you still like to know?" and "Yes" ends the conversation.
- **Intentional change:** Yes (memlog lines 24, 38, 49)

### I3. Wording of the feedback question
- **Input:** "Did you receive all the information you needed?"
- **PRD:** "Have you received all the information you need?"
- **Intentional change:** Yes, implicitly. The wording comes from the user's UJ-2 sample dialogue (memlog line 21). Low impact.

### I4. Measuring the adviser's workload
- **Input:** "compare the number of common questions answered manually and the time spent answering them before and after introducing the chatbot". A reduced workload is a success criterion.
- **PRD:** SM-C1 is a counter-metric: a weekly hand count of emails the chatbot could have answered. There is no before/after baseline and no time spent.
- **Intentional change:** Yes (memlog lines 41, 42, 44).
- **Residual note (low):** the "time spent" measure and the before-introduction baseline were dropped without an explicit decision. Consider recording a baseline count before launch.

### I5. Where users find the chat page
- **Input:** "from a link I share when people contact me".
- **PRD:** a link on the adviser's Facebook page, which must work in Facebook's in-app browser.
- **Intentional change:** Yes (memlog line 13)

### I6. What counts as personal information
- **Input:** examples include "passport numbers, family situations, or finances".
- **PRD:** FR9 defines personal information as passport number, ID number, phone number and full address. FR9 also adds a warning when the user shares it.
- **Intentional change:** Yes (memlog line 39). Low impact.

### I7. Handing users to a human adviser
- **Input:** a generic "human adviser or the relevant authority".
- **PRD:** a specific adviser contact (ngan.visaa@gmail.com), given when the KB has no answer (FR4) or the user asks for a person or full-process help (FR13).
- **Intentional change:** Yes (memlog lines 25, 31, 34)

---

## Summary

- Real gaps: 13 (3 high, 5 medium, 2 low–medium, 3 low)
- Intentional changes: 7 (2 with small residual notes)
