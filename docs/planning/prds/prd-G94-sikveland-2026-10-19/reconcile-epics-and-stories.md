# Reconciliation: epics-and-stories.md vs PRD

- **Input:** `docs/planning/epics-and-stories.md` (earlier draft, written before the PRD: FR1–FR11, NFR1–NFR7, 9 epics, 26 stories)
- **Checked against:** `prd.md` (updated 2026-11-02), `addendum.md`, `.memlog.md`
- **Date:** 2026-11-02

---

## 1. FR/NFR ID check

Every ID FR1–FR11 and NFR1–NFR7 appears in the PRD under the same ID. FR12 and FR13 are new. No ID was dropped or reused for something else.

### 1.1 Same or compatible meaning

| ID | Draft (epics) | PRD | Verdict | Memlog |
|---|---|---|---|---|
| FR1 | Ask in Thai, answer in Thai | Same, plus: questions with typos or mixed Thai/English get a Thai answer; the chat page opens in Thai | Compatible (sharper) | Not needed (the typo case was already in draft NFR4) |
| FR2 | Answers only from the knowledge base, show sources | Same, plus: at least one source link per answer; no facts that are not in the sources | Compatible (sharper) | Not needed |
| FR4 | No answer → say so and "refer the user onward" | No answer → say so and **give the adviser contact**; do not make up an answer | Compatible (narrower: "onward" is now the adviser) | Yes: lines 31, 34 |
| FR7 | English translation | Same | Same | Line 35 (kept) |
| FR8 | Example questions to tap | Same | Same | n/a |
| FR9 | Do not share personal info + warning | Same, plus a definition: passport number, ID number, phone number, full address | Compatible (sharper) | Yes: lines 35, 39 |
| FR10 | Demo mode without API key | Same | Same | Line 35 (kept) |
| FR11 | 10–20 official sources with URL, publisher, retrieval date; script update | Same, plus required coverage: application steps, checklists per visit purpose, sponsorship form and invitation letter, relationship proof, visa fee | Compatible (sharper) | Yes: lines 18, 26, 29 |
| NFR1 | Mobile, large touch targets, simple language | Same, plus: must work in **Facebook's in-app browser** | Compatible (sharper) | Yes: lines 13, 40; addendum |
| NFR2 | Run locally via README, own key or demo | Same | Same | n/a |
| NFR3 | Tests never call real API, run in GitHub Actions | Same | Same | n/a |
| NFR5 | Conversation text not stored; no secrets or real enquiries in repo | Same, plus: only the Yes/No feedback answer and its time are stored on the server; checklist ticks stay on the phone | Compatible (sharper) | Yes: line 40 ("unchanged in substance"), line 17 |
| NFR6 | Cost per question measured and reported | Same | Same | n/a |
| NFR7 | Prompts as versioned files | Same | Same | n/a |

### 1.2 Changed meaning

| ID | Draft (epics) | PRD | What changed | Explained in memlog? |
|---|---|---|---|---|
| **FR3** | Individual-assessment questions are **referred to a human adviser or the relevant authority** | The chatbot answers that **the embassy decides** and no one else can answer it; it never estimates the applicant's chances | The response is now "the embassy decides" instead of a referral to the adviser. The adviser contact is no longer part of this case. It now comes only through FR4 and FR13. | **Yes.** Line 32 says this replaces the earlier assumption of referral to the adviser. Line 28 (an assumption) is superseded by line 32. Line 27: no UJ-3 for this case. FR3 has no "Realizes UJ-x" line in the PRD. |
| **FR5** | **After an answer**, ask "Did you receive all the information you needed?" and store Yes/No | Asked when the applicant gives a **done signal**. "Yes" ends the conversation. "No" leads to "What would you still like to know?" and the question is asked again at the next done signal. Wording: "Have you **received** all the information you **need**?" | The trigger moved from "after an answer" to "on a done signal". There is a new No → follow-up → ask-again loop. "Yes" ends the conversation. The question text changed slightly. | **Yes.** Line 24 (timing; it says FR5 must be reworded), line 38 (assumption), line 49 (confirmed). The wording change is not logged, but it follows the UJ-2 dialogue in the addendum. |
| **FR6** | Select visit purpose → get a document checklist | Select purpose, get the checklist, **tick off documents**. Ticks are **kept between visits on the same phone/browser, no account, not on the server**. The family-visit checklist includes the sponsorship form and invitation letter, says the **sponsor** fills them in, and links to where the sponsor finds them. | Persistent ticks and sponsor forms were added. The checklist now replaces the adviser's document check. It also changed from an **extension** (Epic 6) to **MVP in scope** (PRD §8.1). | **Partly.** Lines 15, 17, 18, 29 and 37 explain the ticks, the purpose, the forms and the term "sponsor". The move from extension to MVP scope is **not logged explicitly**. It is only implied by line 15 and UJ-1. |
| **NFR4** | ≥90% correct with correct source; **100% of individual-assessment questions referred**; Thai answers also with typos or mixed language | ≥90% **of general questions** correct with correct source; 100% of individual-assessment questions get **the answer that the embassy decides**; Thai with typos or mixed language; the test set **must cover** application steps, checklists, sponsorship form and invitation letter, relationship proof, visa fee | The pass criterion for individual questions changed from "referred" to "embassy decides". The 90% base is now general questions only. A test-set coverage list was added. | **Yes.** Line 40 (confirmed), line 32. |

### 1.3 New IDs

| ID | PRD | Memlog |
|---|---|---|
| FR12 | Application steps in order: documents (embassy checklist) → register at UDI → pay the visa fee → book an appointment at VFS, with a link to the website for each step | Lines 36, 50 (confirmed as a separate FR) |
| FR13 | Reach a person: the applicant asks for a person, or for help with the whole process → the chatbot gives the adviser contact | Lines 31, 34 |

### 1.4 Other notes

- The term **"sponsor"** (PRD §3, memlog line 37) is not used anywhere in the epics. The epics name no role for the person in Norway.
- **Adviser contact** is now fixed as `ngan.visaa@gmail.com` (memlog line 25). In the draft it was a configurable `ADVISER_CONTACT` env var (Story 1.2). These do not conflict.
- **Visit purposes:** the draft has `tourism` and `family_friends`. The PRD §8.1 has tourism and visiting family and friends. The Glossary says "e.g. visiting family". Compatible.
- The **"Brief section"** traceability column in the draft has no counterpart in the PRD. The PRD instead traces to UJ-1 and UJ-2.

---

## 2. Requirement-level details in story acceptance criteria that the PRD lacks

Only behaviour or limits that a product owner or examiner would expect to find in the PRD are listed. Purely technical ACs (file paths, SDK, `/health`, `pyproject.toml`, cache breakpoints) belong in the architecture and are left out.

### 2.1 Likely PRD gaps (behaviour the PRD does not state at all)

| # | Detail in the stories | Story | PRD status |
|---|---|---|---|
| G1 | **Out-of-scope questions** (e.g. other visa types) get a Thai message explaining that the chatbot only covers short-stay tourist and visitor visas to Norway. The classifier has an `out_of_scope` category. | 4.1, 4.2 | **Missing.** No FR covers it. §7 and §8.2 list other visa types as out of scope, but no FR says how the chatbot replies. NFR4 does not cover it either, while the test set in 8.1 has ≥3 out-of-scope questions. |
| G2 | The privacy notice also says that **questions are sent to an AI service (the language model provider) to generate answers**. | 4.3 | **Missing.** FR9 covers only "don't share personal info" and the warning. Nothing tells the user that their text leaves the app. |
| G3 | **Personal data in a question → the question is not answered.** The user is asked to remove the details and ask in general terms. | 4.3 | **Partly.** FR9 only says "warns them". It does not say the question goes unanswered. |
| G4 | **Follow-up questions** build on earlier answers. The browser keeps the conversation and sends it with each question. Reloading the page starts a new conversation. | 3.4 | **Missing as an FR.** UJ-2 depends on it (follow-ups, the "What would you still like to know?" loop), and FR5 talks about "the conversation", but no FR requires context to carry across turns. The PRD also does not say what "the conversation ends" looks like after "Yes", or how that relates to a page reload. |
| G5 | Each checklist document has a **source link**. The checklist page states that the list is **general and that UDI's (or the embassy's) checklist is the authority**. | 6.1, 6.2 | **Missing from FR6.** FR2 covers source links for chat *answers*, not checklist items. There is no disclaimer requirement. This matters because the PRD now presents the checklist as a *replacement* for the adviser's document check. |
| G6 | **Demo mode fallback:** a question that has no stored answer gets a Thai message that demo mode only answers the example questions. Demo mode shows a visible "Demo mode" label and uses stored translations. | 7.1, 7.2 | **PRD Open Question 2 is unresolved, but the story already answers it.** Consider adopting the story's answer and closing the question. |
| G7 | User-facing **Thai text is checked by the domain expert** (Definition of Done). Referral texts and the test-set answers are reviewed by the domain expert. | DoD, 4.2, 8.1 | **Missing.** No NFR covers quality review of the Thai text or the content. It is the main safeguard for the language quality of a Thai-only product. |
| G8 | **API error → a friendly Thai message, and the user can try again.** A Thai loading message is shown while waiting. | 3.3 | **Missing.** The PRD has no error-handling or failure-state requirement. |
| G9 | **Sources come only from** UDI, VFS Global, the Royal Norwegian Embassy in Bangkok and the European Commission. | 2.1 | **Partly.** The Glossary "Source" lists examples ("e.g."), not a closed list. FR11 says only "official". |

### 2.2 Limits and thresholds the PRD states only qualitatively

| # | Detail in the stories | Story | PRD status |
|---|---|---|---|
| L1 | Mobile thresholds: no horizontal scroll at 360 px, touch targets ≥44×44 px, base font ≥16 px with a font that renders Thai well, WCAG AA contrast, checked on a real phone | 9.1 | NFR1 says "large touch targets" and gives no numbers. |
| L2 | Test set: 20–30 questions; ≥5 individual-assessment, ≥3 out of scope, ≥3 with typos or mixed language, ≥2 not in the sources; each with expected category, key facts and source IDs | 8.1 | NFR4 gives targets and a coverage list but no size or composition. It has no target for out-of-scope or not-in-sources questions. |
| L3 | Evaluation checks that the answer is "mainly in Thai script". Key facts are graded by a model, with the reasoning shown for human review. Each run is logged (date, prompt versions, scores, what changed and why). | 8.2, 8.3 | NFR4 does not say how "correct" is judged. No requirement covers the evaluation log, which documents how AI use was controlled (relevant to grading). |
| L4 | 4–6 example questions shown as large buttons in an empty chat, stored in one data file shared with demo mode and the README | 3.5 | FR8 gives no number. |
| L5 | Sources shown as **numbered links** below each answer | 3.3 | FR2 says "links", no format. UX-level; can stay out of the PRD. |

### 2.3 Details now covered or partly covered by the PRD (for completeness)

- **Feedback stored with a timestamp** (5.1). This is covered by NFR5 ("Yes/No answer and its time"). FR5's bullet says "only the Yes/No answer is stored" and does not mention the time, so FR5 and NFR5 should match. The thank-you message after answering (5.1) is not in the PRD (UX).
- **Feedback statistics** (Yes/No counts and % Yes, total and per week; a message when there is no feedback yet) (5.2). SM-1 defines the metric and the 80% target, but no FR or NFR says how it is read out. This is a possible gap if SM-1 must be reported to the examiner.
- **No question or answer text in logs** (4.3). NFR5 covers this in spirit ("conversation text is not stored"). Logs are not named.
- **Translations not stored** (7.1). Covered by NFR5 in spirit.
- **Cost logged per request** (tokens and $) and reported in the README (3.2, 9.2). Covered by NFR6. There is no cost target or budget in either document.
- **Prompts carry a version number at the top** (3.1, 4.1). Covered by NFR7.
- **The system prompt asks for simple language** (3.1). Covered by NFR1 ("simple language").
- **README contents**: example questions with English and Norwegian translations; a newcomer can start demo mode unaided (9.2). NFR2 covers the core of this.
- **Checklist built without calling the language model** (6.2). This is an architecture choice, but it supports FR2 (no invented facts). It could be noted in the addendum.
- **Startup fails clearly if there is no API key and demo mode is off** (1.2). Architecture or ops detail.
- **Definition of Done**: tests use the mock (NFR3), no keys or personal data committed (NFR5), README kept current (NFR2). All covered.

---

## 3. Stories that need updating because of PRD changes (for later; not PRD gaps)

### 3.1 Must update (12 stories)

| Story | Why | PRD driver |
|---|---|---|
| 2.1 Source list | Sources must cover the application steps, checklists per purpose, the sponsorship form and invitation letter, relationship proof (own and parent's house registration for an aunt or uncle), and the visa fee. | FR11, FR12, FR6 |
| 3.1 Answer with citations | The system prompt must give the application steps in order with the website and link for each step (or add a new story, see 3.3 below). "No facts not in sources" must become an explicit check. | FR12, FR2 |
| 4.1 Question classifier | `individual_assessment` now leads to an "embassy decides" reply, not a referral. The classifier must also detect a **request for a person** (FR13) and a **done signal** (FR5), or another mechanism must do this. | FR3, FR13, FR5 |
| 4.2 Referral replies | The `individual_assessment` reply must say **the embassy decides, no one else can answer, no estimate of chances**. Remove the adviser contact and UDI link from this reply. The no-answer reply must give the **adviser contact** (not just "refer onward"). Add a **reach-a-person** reply with the adviser contact. | FR3, FR4, FR13 |
| 4.3 Privacy notice | Add the PRD definition of personal information (passport number, ID number, phone number, full address) as the detection rule and test cases. | FR9 |
| 5.1 Feedback question | Trigger it on a **done signal**, not after each answer. Use the new wording "Have you received all the information you need?". "No" leads to "What would you still like to know?", and the question is **asked again at the next done signal** (this conflicts with the current AC "at most once per conversation"). "Yes" **ends the conversation**. | FR5 |
| 6.1 Checklist data | The family-visit checklist must include the **sponsorship form** and **invitation letter**, say the **sponsor** fills them in, and link to where the sponsor finds them. Add relationship-proof documents. Use the term "sponsor". | FR6, Glossary |
| 6.2 Checklist page | Ticks must be **saved between visits on the same phone/browser** (local storage), with no account and nothing on the server. The PRD's UJ-1 reaches the checklist by **asking in chat**, not only through a button. | FR6, NFR5, UJ-1 |
| 7.2 Demo mode | The stored "referral example" must become an **"embassy decides"** example. Add demo answers for the application steps (FR12) and the reach-a-person case (FR13). Consider adding the done-signal and feedback flow. | FR3, FR12, FR13, FR5 |
| 8.1 Test set | The expected result for individual-assessment questions is now "embassy decides". The test set must cover the **application steps, checklists, the sponsorship form and invitation letter, relationship proof, and the visa fee**. Add cases for reach-a-person and done signals. | NFR4, FR12, FR13 |
| 8.2 Evaluation script | Score the 90% target over **general questions only**. Score individual-assessment questions as "embassy decides" (not "referred"). | NFR4 |
| 9.1 Mobile design | Check the page in **Facebook's in-app browser** as well as on a real phone. | NFR1 |

### 3.2 Should check or minor update (4 stories)

| Story | Why |
|---|---|
| 1.2 Configuration | `ADVISER_CONTACT` now has a known value (`ngan.visaa@gmail.com`). It could be used as the example or default in `.env.example`. |
| 3.4 Follow-up questions | Define what "the conversation ends" (after "Yes", FR5) means for the client-side history and how it relates to a reload. |
| 3.5 Example questions | The examples should include "What do I do first?" (UJ-1, FR12) and a checklist or document question (UJ-1, FR6). |
| 5.2 Feedback statistics | Could show the result against the SM-1 target of at least 80% Yes. |

### 3.3 New stories likely needed

- **FR12 Application steps in order.** There is no story today. It could be folded into 3.1 or 4.x, but a separate story keeps the traceability clean.
- **FR13 Reach a person.** There is no story today. It could be folded into 4.1 and 4.2.
- **Done-signal detection and conversation end** (FR5), if it is not handled inside 5.1.

### 3.4 Document-level updates to `epics-and-stories.md`

- The intro still says "There is no PRD yet". Point it to the PRD as the source of requirements.
- Requirements tables: update the text of FR3, FR4, FR5, FR6, FR9, FR11, NFR1, NFR4 and NFR5, and add FR12 and FR13.
- Overview and Epic 6: the priority "Extension" and the note "Epic 6 is started only when epics 1–5 are stable" conflict with PRD §8.1, where the checklist is in the MVP.
- Traceability table: add FR12 and FR13.
- Definition of Done: no change needed.
