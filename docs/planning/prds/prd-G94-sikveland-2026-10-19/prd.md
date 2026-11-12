---
title: "PRD: Norway Visa Guide For Thai"
status: final
created: 2026-10-19
updated: 2026-11-12
---

# PRD: Norway Visa Guide For Thai

## 0. Document Purpose

This PRD is for the IBE160 project group, the examiner, and the downstream UX, architecture and story work. It builds on `docs/planning/product-brief.md` and keeps the FR/NFR IDs from the earlier epics draft; the stories now live in `docs/planning/epics.md`. Terms in §3 Glossary are used exactly. Inferred points are tagged `[ASSUMPTION]` and listed in §10. Technical detail lives in `addendum.md`.

*Updated 2026-11-12 after the examiner's formative feedback (`tilbakemelding-prd.md`): testable consequences for FR4, FR7, FR8, FR9, FR13, NFR1 and NFR4, a priority order in §8.1, and glossary clarifications.*

## 1. Vision

Thai applicants for a short-stay Norway visa face many documents, many steps and several websites that need registration and login, mostly in languages they cannot read. Today they email the adviser, the only person they can turn to, and wait for a personal reply, often at night or at weekends.

The Norway Visa Guide For Thai is a Thai-language chatbot on a mobile web page, reached from the adviser's Facebook page. It answers common questions about short-stay tourist and visitor visas 24 hours a day, gives the application steps in order, and lets the applicant tick off their documents. Every answer is based on official sources and links to them. When a question is about the applicant's own chances, it says plainly that the embassy decides; when the applicant needs a person, it gives the adviser contact.

Applicants get answers without waiting and can prepare their application themselves. The adviser spends less time on repeated questions and more on the people who need real help.

*The course prototype runs locally and in demo mode. The Facebook link and 24-hour availability come when the chat page is hosted (see §8.2).*

## 2. Target User

### 2.1 Jobs To Be Done

- **Primary users** are Thai people applying for a short-stay visa to visit Norway for tourism or to visit family and friends, often with limited visa knowledge or digital skills.
  - Find out what to do first and in which order, without waiting for a personal reply.
  - Know which documents to prepare, and be sure none are missing before submitting.
  - Understand official information that is spread across many pages in Norwegian or English.
  - Get a clear answer about what the chatbot cannot answer, and know where to turn instead.
- **Secondary users** are members of the public who want to learn about these visas without planning to apply now.

### 2.2 Why Not Existing Options

- **UDI and VFS Global websites** are authoritative, but mostly in Norwegian or English and spread across many pages.
- **General AI chatbots** answer in Thai, but do not limit themselves to official sources, may give outdated or invented requirements, and rarely say when a question needs an individual assessment.

### 2.3 Key User Journeys

- **UJ-1. Fah finds out how to start her application to visit her sister.**
  - **Persona + context:** Fah wants to visit her sister, who lives in Norway. She reads only Thai and cannot read English. The process overwhelms her: many documents, many steps, and several websites where she must register and log in. [ASSUMPTION: first visa application, no prior Schengen experience]
  - **Today:** She emails the adviser on Monday at 08:00 asking what to do first and which documents she needs, then waits for a personal reply. Later she often asks the adviser to confirm she has every required document before submitting.
  - **Entry state:** Fah taps a link on the adviser's Facebook page and the chat page opens on her phone. No login. It opens in Facebook's in-app browser (see NFR1). This is the target experience once the chat page is hosted (see §8.2).
  - **Path:**
    1. The chat page opens in Thai with example questions she can tap.
    2. She asks what she must do first and gets the application steps in order, in Thai, including which website each step happens on.
    3. She asks which documents she needs and gets a document checklist for visiting family.
    4. She goes through the checklist and ticks off the documents she already has. Over the next days she returns to the same page on the same phone, and her ticks are still there.
  - **Climax:** She sees, in Thai, the steps of the visitor visa application in order and the documents she must prepare, and can tell which documents are still missing.
  - **Resolution:** Fah fills out and submits the application herself, and does not need the adviser to check her documents.
  - **Sources:** Each answer links to its sources. VFS Global pages are available in Thai; for UDI pages, applicants use Google Translate or an AI tool.
  - **Edge case:** Fah cannot find the sponsorship form or the invitation letter form. She asks the chatbot and gets, in Thai, what each form is, that her sister (the sponsor) fills them in, and a link to where her sister can find them.

- **UJ-2. Michael gets the first steps and learns he can hand the whole process to the adviser.**
  - **Persona + context:** Michael wants to visit his aunt in Norway and does not know where to start. [ASSUMPTION: he reads Thai; the sample dialogue was written in English only for this document]
  - **Path:**
    1. He asks what to do first. He gets the steps in order: prepare documents using the embassy checklist in Thai, register the application at UDI (link), pay the visa fee, and book an appointment at VFS (link).
    2. He asks how to prove that she is his aunt. He is told to use his own house registration document and his parent's house registration document, which together link him to his aunt.
    3. He asks what to do if he cannot manage the application himself, and gets the adviser contact.
    4. He says thanks. This is a done signal, so the chatbot asks the feedback question.
    5. He answers **No**. The chatbot asks "What would you still like to know?" He asks about the visa fee and gets €90. The chatbot asks the feedback question again; he answers **Yes**, and the conversation ends.
  - **Climax:** He knows what to do first and has a fallback if the process is too much for him.
  - **Resolution:** He either applies on his own or contacts the adviser.
  - **Source:** sample dialogue by the user, kept in `addendum.md`.

## 3. Glossary

- **Applicant** — A Thai person planning a visitor visa application to Norway who uses the chat page. Fah and Michael are applicants.
- **Sponsor** — The person in Norway the applicant visits (Fah's sister, Michael's aunt). The sponsor fills in the sponsorship form and the invitation letter.
- **Adviser** — The person who runs the agency and today answers applicants' questions by email. Owner of the adviser contact.
- **Adviser contact** — The value of `ADVISER_CONTACT` in the app's configuration: the adviser's agency email address (currently ngan.visaa@gmail.com).
- **Chat page** — The mobile-first web page where the applicant asks questions. No login. Once hosted, opened from a link on the adviser's Facebook page.
- **Knowledge base** — The set of official sources that answers are based on.
- **Source** — One official web page or document in the knowledge base (e.g. UDI, VFS Global, the Norwegian Embassy), stored with URL, publisher and retrieval date.
- **Individual-assessment question** — A question about the applicant's own chances or case, such as "Will I get the visa?" or "I was refused last year, will I get it this time?". Only the embassy can answer it.
- **Application steps** — The ordered steps of a visitor visa application: prepare documents using the embassy checklist, register the application at UDI, pay the visa fee, book an appointment at VFS.
- **Visit purpose** — Why the applicant travels. In the MVP: tourism, visiting family, visiting friends. Decides which checklist applies.
- **Checklist** — The fixed list of documents required for a visit purpose, written in advance and not generated by the AI. The applicant can tick off documents they have.
- **Conversation** — One visit to the chat page, from the first question until the applicant answers "Yes" to the feedback question or leaves. Identified only by an anonymous ID; its text is not stored. The earlier questions used for follow-ups (FR1) are held only in the open page and are not stored.
- **Done signal** — A message showing the applicant has finished asking, such as "thank you" or "okay". A done signal does not end the conversation; only "Yes" to the feedback question does.
- **Feedback question** — "Have you received all the information you need?" with Yes/No buttons.
- **Out-of-scope question** — A question about anything other than short-stay tourist and visitor visas to Norway, e.g. a work visa.
- **Personal information** — Passport number, Thai ID number or phone number. Names and addresses are not covered: they cannot be detected reliably by pattern, and the privacy notice says so.
- **Test set** — 20–30 Thai questions with expected answers and sources, used to measure answer quality.
- **Demo mode** — Running the app without an API key, with prepared answers to the example questions.

## 4. Features

*FR IDs FR1–FR11 are kept from the earlier epics draft; new FRs continue from FR12, and NFR8 is new. FR3, FR5, FR6 and FR9 changed meaning from that draft (embassy-decides answer, feedback on done signal, saved ticks, deletion of personal information). The current stories are in `docs/planning/epics.md`.*

### 4.1 Ask in Thai, get answers with sources

**Description:** The applicant opens the chat page, taps an example question or types their own in Thai, and gets an answer in Thai based only on the knowledge base, with links to its sources. When they ask how to start, they get the application steps in order with the website for each step. They can show an English version of any answer. Realizes UJ-1, UJ-2.

**Functional Requirements:**

#### FR1: Ask and answer in Thai
The applicant can ask a question in Thai and gets an answer in Thai. Realizes UJ-1, UJ-2.
- Questions with typos or mixed Thai/English get an answer in Thai.
- The chat page opens in Thai.
- The applicant can ask follow-up questions; the chatbot uses what was asked earlier in the same conversation. Realizes UJ-2.

#### FR2: Answers only from the knowledge base, with sources
Every answer is based only on the knowledge base and links to the sources it uses. Realizes UJ-1.
- Each answer based on the knowledge base shows at least one source link. The embassy-decides, no-answer, out-of-scope and adviser-contact replies need none.
- The answer contains no facts that are not in its sources.

#### FR12: Application steps in order *(new)*
When the applicant asks how to start, the chatbot gives the application steps in order and names the website for each step, with a link. Realizes UJ-1, UJ-2.
- The steps come in this order: documents (embassy checklist) → register at UDI → pay the visa fee → book an appointment at VFS.

#### FR7: English translation
Any reply can be shown in English. This is for readers who do not read Thai, mainly the course examiner; it does not realize a UJ, since Fah and Michael read Thai.
- Every reply has a button that shows an English translation under the reply; the Thai reply is unchanged.
- The reply's source links stay visible with the translation.

#### FR8: Example questions
The chat page shows example questions the applicant can tap to ask them. Realizes UJ-1.
- The page shows 3–5 example questions.
- Tapping one sends it as the question, without typing.

### 4.2 Knowing the limits

**Description:** The chatbot does not guess. Individual-assessment questions get a clear answer that only the embassy decides. When the knowledge base has no answer, or the applicant asks for a person, the chatbot gives the adviser contact. Realizes UJ-2.

#### FR3: Individual-assessment questions
When the applicant asks an individual-assessment question, the chatbot answers that the decision is made by the embassy and that no one else can answer it.
- The chatbot never estimates the applicant's chances.

#### FR4: No answer in the knowledge base
When the knowledge base does not contain the answer, the chatbot says so and gives the adviser contact.
- "Does not contain the answer" means: a question within scope (short-stay tourist and visitor visas to Norway) that no source answers, so the answer would cite no source. Questions outside scope are FR14.
- Such a question gets the no-answer message and the adviser contact, with no claims about requirements, fees or deadlines.
- The chatbot does not make up an answer.
- The test set has at least four such questions (NFR4); all of them must get the no-answer message.

#### FR13: Reach a person *(new)*
When the applicant asks to talk to a person instead of the chatbot, or asks for help with the whole process, the chatbot gives the adviser contact. Realizes UJ-2.
- The test set has at least three different phrasings of such requests (NFR4); all of them must get the adviser contact.

#### FR14: Out-of-scope questions *(new)*
When the applicant asks an out-of-scope question, the chatbot answers that it only covers short-stay tourist and visitor visas to Norway and gives the adviser contact.

### 4.3 Document checklist

**Description:** The applicant picks a visit purpose and gets the checklist of documents. They tick off what they have and come back over several days on the same phone; their ticks are still there. This replaces asking the adviser to check the documents. Realizes UJ-1.

#### FR6: Checklist with saved ticks
The applicant can select a visit purpose, get the checklist, and tick off documents they have. Realizes UJ-1.
- Checklists are fixed texts per visit purpose (tourism, visiting family, visiting friends), not generated by the AI, and are reviewed by the adviser (NFR8).
- Ticks are kept between visits on the same phone and browser, with no account.
- When a checklist is updated, ticks on unchanged items are kept.
- Ticks are not stored on the server.
- Each checklist item links to its source. UDI's checklist is the authority; the chatbot's checklist guides the applicant to it.
- The family-visit checklist includes the sponsorship form and the invitation letter, says the sponsor fills them in, and links to where the sponsor finds them.

### 4.4 Feedback

**Description:** When the applicant signals they are done, the chatbot asks the feedback question. "No" leads to "What would you still like to know?", and the question comes back at the next done signal. Realizes UJ-2.

#### FR5: Feedback question at the end
When the applicant gives a done signal, the chatbot asks the feedback question. Realizes UJ-2.
- "Yes" ends the conversation.
- "No" leads to "What would you still like to know?"; the feedback question is asked again at the next done signal.
- Only the Yes/No answer, its time and an anonymous conversation ID are stored, not the conversation text.

### 4.5 Privacy

#### FR9: Personal information protection
The chat page asks applicants not to share personal information such as ID number or passport number. If an applicant writes personal information anyway, the chatbot warns them and deletes it.
- The chat page states, in Thai, that questions are sent to an AI service to generate answers.
- Personal information in a question is deleted before the question is sent to the AI service, and is never stored.
- The chatbot still answers the rest of the question, and reminds the applicant not to send personal information.
- These are removed before the AI call: a 13-digit Thai ID number (with or without dashes or spaces), a passport number, and a phone number in Thai format (08x-xxx-xxxx, also with +66) or Norwegian format. The test set has at least one example of each (NFR4).
- Amounts such as "90 euro" and dates are not removed.
- Names and addresses are not detected automatically. The privacy notice says this and asks the applicant not to write them.

### 4.6 Knowledge base

#### FR11: Official sources, kept up to date
The knowledge base holds 10–20 official sources, each stored with URL, publisher and retrieval date, and can be updated by a script.
- Only official publishers are used: UDI, VFS Global, the Royal Norwegian Embassy in Bangkok, and the European Commission's Schengen visa pages.
- When the script fetches new versions, the adviser reviews the changes before they are used.
- Every answer can be traced to a specific version of a source.
- It covers: application steps, checklists per visit purpose, the sponsorship form and invitation letter, relationship proof (e.g. own and parent's house registration for an aunt or uncle), and the visa fee.

### 4.7 Running the prototype

#### FR10: Demo mode
The app can run in demo mode without an API key.
- Demo mode answers the example questions with stored Thai answers and sources.
- Other questions get a Thai message explaining that demo mode only answers the example questions.
- The page shows a visible "Demo mode" label.

## 5. Cross-Cutting NFRs

*IDs NFR1–NFR7 are kept from the earlier epics draft.*

- **NFR1 — Mobile first.** The chat page works well on a phone, including in Facebook's in-app browser, with large touch targets and simple language. Realizes UJ-1.
  - It works from 360 px screen width, with no horizontal scrolling down to 320 px.
  - Buttons and other touch targets are at least 44×44 px.
  - It is checked on a real phone in Facebook's in-app browser, including that answers stream bit by bit.
- **NFR2 — Easy to run.** The app can be run locally by following the README, with your own API key or in demo mode.
- **NFR3 — Safe tests.** Automated tests never call the real API and run in GitHub Actions.
- **NFR4 — Answer quality.** On the test set:
  - an answer counts as correct when it contains the expected facts and source from the test set, as judged by the adviser;
  - at least 90% of general questions get a correct answer with the correct source;
  - 100% of individual-assessment questions get the answer that the embassy decides;
  - 100% of questions the sources do not cover get the no-answer message with no invented facts (FR4);
  - 100% of requests for a person get the adviser contact (FR13);
  - answers are in Thai also when the question has typos or mixes Thai and English;
  - the test set has 20–30 questions, each with an expected answer and source, and covers the application steps, checklists, the sponsorship form and invitation letter, relationship proof, the visa fee, individual-assessment questions, out-of-scope questions, at least four questions the sources do not cover, at least three requests for a person, and questions containing personal information (at least one Thai ID number, passport number and phone number);
  - the test set is run against the real model after every change to prompts or sources, separately from the automated tests in NFR3, and the results are recorded.
- **NFR5 — Privacy.** Conversation text is not stored, and personal information is deleted (FR9). Only the Yes/No answer to the feedback question, its time and an anonymous conversation ID are stored on the server; checklist ticks stay on the applicant's phone. No secrets or real applicant enquiries are stored in the repository.
- **NFR6 — Cost.** The cost per question is measured and reported in the README. A cost target is still open (§9).
- **NFR7 — Versioned prompts.** Prompts are stored as versioned files in the repository.
- **NFR8 — Thai text reviewed by the adviser.** All fixed Thai texts (example questions, checklists, the "embassy decides" message, out-of-scope and no-answer messages, the privacy notice, demo answers) are reviewed by the adviser before release. *(new)*

## 6. Success Metrics

**During the course (testable now)**
- **SM-2: Test-set result.** The NFR4 targets are met on the test set: at least 90% correct with correct source, 100% "embassy decides" answers to individual-assessment questions, 100% no-answer replies to questions the sources do not cover, and 100% adviser contact for requests for a person. Validates FR1, FR2, FR3, FR4, FR12, FR13, FR14.

**After launch (needs real users)**
- **SM-1: Information need met.** Share of conversations where the first answer to the feedback question is "Yes". Only the first answer counts, because the No loop always ends in "Yes". Target: at least 80%. Validates FR1, FR2, FR12, FR5.

**Counter-metrics (do not optimize)**
- **SM-C1: Emails the chatbot could have answered.** Emails to the adviser asking things the knowledge base already covers. A high SM-1 is not success if these emails continue. The adviser counts them by hand each week. Counterbalances SM-1.

## 7. Non-Goals

- The chatbot does not assess an applicant's eligibility or predict the outcome of an application. Only the embassy decides.
- The chatbot does not give advice tailored to an individual case.
- It does not replace the official UDI, VFS Global or embassy websites; it guides applicants to them.
- It does not fill in or submit the application for the applicant.

## 8. MVP Scope

### 8.1 In Scope
- Short-stay tourist and visitor visas to Norway (tourism, visiting family and friends).
- Thai chat with source links, example questions and an English translation button (FR1, FR2, FR7, FR8).
- Application steps in order (FR12).
- Checklist per visit purpose with ticks saved on the phone (FR6).
- "The embassy decides" answer, no-answer handling, out-of-scope answer and adviser contact (FR3, FR4, FR13, FR14).
- Feedback question at the end of the conversation (FR5).
- Personal information warning and deletion (FR9).
- Knowledge base of 10–20 official sources, updated by script (FR11).
- Demo mode without an API key (FR10).

**Deadline and team:** part 1 of the IBE160 portfolio is due 2026-11-15; the deadline for the finished app is not yet known. The group is one person.

**Priority order** (when time runs short, cut from the bottom of this list first):
1. **Core:** FR1, FR2, FR3, FR4, FR9, FR10, FR12 — Thai answers with sources, the steps in order, "the embassy decides", no-answer, the privacy filter, and demo mode so the examiner can run the app.
2. **Next:** FR6, FR5, FR13, FR14 — checklist, feedback question, reach a person, out of scope.
3. **If time allows:** FR7 and the update script in FR11. The knowledge base itself is core (FR2 needs it); without the script, sources are fetched by hand. FR8 is already built.

### 8.2 Out of Scope for MVP
- User accounts — not needed; checklist ticks stay on the phone. Long-term vision.
- Payment and a paid service for personal guidance — long-term vision.
- Other visa types — planned gradually over the next two to three years.
- An admin page for editing sources — sources are updated by script.
- Hosting the chat page online — for the course, the prototype runs locally and in demo mode (NFR2, FR10). 24-hour availability and the Facebook link in UJ-1 come when it is hosted.

## 9. Open Questions

1. Deadline for the finished app (later parts of the IBE160 portfolio) — decides how far down the §8.1 priority order the MVP gets.
2. Response-time limit for NFR1 and a cost target for NFR6.
3. How to check that the checklist actually replaces the adviser's document check — possible extra success metric.

## 10. Assumptions Index

- §2.3 UJ-1 — Fah is applying for the first time and has no prior Schengen experience.
- §2.3 UJ-2 — Michael reads Thai; the sample dialogue is in English only for this document.
