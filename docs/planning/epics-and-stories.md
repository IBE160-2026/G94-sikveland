# Epics and User Stories: Norway Visa Guide For Thai

Based on `product-brief.md` and `implementation-plan.md`. There is no PRD yet, so the requirements below are derived directly from the brief and given IDs. Each story lists the requirements it covers, so the path from brief to code can be traced. If a PRD is written later, the requirements move there and the IDs stay the same.

## Requirements

### Functional requirements

| ID | Requirement | Brief section |
|---|---|---|
| FR1 | The user can ask a question in Thai in a chat and gets an answer in Thai. | The Solution |
| FR2 | Answers are based only on the knowledge base and show which sources they come from. | The Solution, Knowledge Base |
| FR3 | Questions that need an individual assessment are referred to a human adviser or the relevant authority. | Scope |
| FR4 | When the knowledge base does not contain the answer, the chatbot says so and refers the user onward. | Success Criteria |
| FR5 | After an answer, the user is asked "Did you receive all the information you needed?" and the Yes/No answer is stored. | Success Criteria |
| FR6 | The user can select the purpose of the visit and get a document checklist. | Scope |
| FR7 | The user can show an English translation of an answer. | Technology, Cost and Running the App |
| FR8 | The chat page shows example questions the user can tap. | Where users meet the chatbot |
| FR9 | The chat page asks users not to share personal information and warns them if they do. | Privacy |
| FR10 | The app can run in demo mode without an API key. | Technology, Cost and Running the App |
| FR11 | The knowledge base consists of 10–20 official sources stored with URL, publisher and retrieval date, and can be updated by a script. | Knowledge Base |

### Non-functional requirements

| ID | Requirement | Brief section |
|---|---|---|
| NFR1 | The chat page works well on a phone, with large touch targets and simple language. | Who This Serves |
| NFR2 | The app can be run locally by following the README, with your own API key or in demo mode. | Technology, Cost and Running the App |
| NFR3 | Automated tests never call the real API and run in GitHub Actions. | Technology, Cost and Running the App |
| NFR4 | On the test set: at least 90% correct answers with correct source, 100% of individual-assessment questions referred, answers in Thai also with typos or mixed Thai/English. | Success Criteria |
| NFR5 | Conversation text is not stored. No secrets or real applicant enquiries are stored in the repository. | Privacy |
| NFR6 | The cost per question is measured and reported. | Technology, Cost and Running the App |
| NFR7 | Prompts are stored as versioned files in the repository. | Feedback, criterion 1 |

## Definition of Done (all stories)

- Acceptance criteria are met and covered by automated tests where possible.
- Tests run with the mock LLM client and pass in GitHub Actions.
- No API keys, personal data or real applicant enquiries are committed.
- User-facing text is in Thai and has been checked by the domain expert.
- The README is updated if the story changes how the app is set up or run.

## Overview

| Epic | Title | Stories | Priority |
|---|---|---|---|
| 1 | Foundation | 4 | Core |
| 2 | Knowledge base | 3 | Core |
| 3 | Core chat flow | 5 | Core |
| 4 | Limits and referral | 3 | Core |
| 5 | Feedback | 2 | Core |
| 6 | Document checklist | 2 | Extension |
| 7 | Examiner support | 2 | Core |
| 8 | Quality assurance | 3 | Core |
| 9 | Design and README | 2 | Core |

Epics 1–3 come first, so a working question → answer with sources flow exists as early as possible. Epic 6 is started only when epics 1–5 are stable.

---

## Epic 1: Foundation

Set up the project so that everything else can be built and tested without an API key.

### Story 1.1: Project skeleton

**As a** developer, **I want** a FastAPI project with a standard structure, **so that** later stories have a clear place for code, prompts, data and tests.

**Acceptance criteria**
- Given a fresh clone, when I follow the install command in the README, then dependencies install from `pyproject.toml`.
- Given the app is running, when I open `/health`, then I get `{"status": "ok"}`.
- The folders `app/`, `app/static/`, `prompts/`, `knowledge-base/`, `scripts/`, `eval/` and `tests/` exist.
- `pytest` runs and passes with at least one test of `/health`.

**Covers:** NFR2

### Story 1.2: Configuration

**As a** developer, **I want** all settings read from environment variables with a documented example file, **so that** keys never end up in the code and the examiner knows what to set.

**Acceptance criteria**
- `.env.example` lists `ANTHROPIC_API_KEY`, `MODEL` (default `claude-opus-5-5`), `MOCK_LLM` and `ADVISER_CONTACT`.
- Given `MOCK_LLM` is not `true` and `ANTHROPIC_API_KEY` is missing, when the app starts, then it stops with a clear error message explaining how to set the key or enable demo mode.
- `.env` is ignored by git.

**Covers:** FR10, NFR2, NFR5

### Story 1.3: LLM client with mock

**As a** developer, **I want** one interface for calling the language model, with a real and a mock implementation, **so that** tests and demo mode run without the API.

**Acceptance criteria**
- The real client uses the official Anthropic Python SDK.
- Given `MOCK_LLM=true`, the app uses the mock client, and no network calls are made.
- The mock returns answers in the same shape as the real client (text, citations, usage).
- Tests can configure the mock to return a specific answer.

**Covers:** FR10, NFR3

### Story 1.4: Continuous integration

**As a** developer, **I want** tests to run automatically on every push, **so that** errors are caught before they reach `main`.

**Acceptance criteria**
- A GitHub Actions workflow installs dependencies and runs `pytest` on push and pull request.
- The workflow sets `MOCK_LLM=true` and has no API key.
- A failing test makes the workflow fail.

**Covers:** NFR3

---

## Epic 2: Knowledge base

Build the fixed collection of official sources that every answer is based on.

### Story 2.1: Source list

**As the** domain expert, **I want** one file listing all sources with their metadata, **so that** it is clear what the chatbot knows and where it comes from.

**Acceptance criteria**
- `knowledge-base/sources.yaml` lists 10–20 sources, each with `id`, `title`, `publisher`, `url`, `language` and `type` (html or pdf).
- Sources come only from UDI, VFS Global, the Royal Norwegian Embassy in Bangkok and the European Commission.
- A test checks that every entry has all required fields and that IDs are unique.

**Covers:** FR11

### Story 2.2: Ingestion script

**As the** domain expert, **I want** a script that fetches every source and saves it as Markdown, **so that** I can update the knowledge base and review changes before they are used.

**Acceptance criteria**
- `python scripts/ingest.py` fetches each source in `sources.yaml` and saves it as `knowledge-base/sources/<id>.md`.
- Each file starts with front matter containing `id`, `title`, `publisher`, `url` and `retrieved` (date).
- HTML navigation, menus and footers are removed; PDF text is extracted.
- Given a source cannot be fetched, the script reports it and continues with the rest.
- Changes are reviewed with `git diff` before committing; the README describes this.

**Covers:** FR11

### Story 2.3: Knowledge base loader

**As a** developer, **I want** the app to load the stored sources at startup, **so that** they can be sent to the model with each question.

**Acceptance criteria**
- At startup the app loads all files in `knowledge-base/sources/` and checks them against `sources.yaml`.
- Given a file is missing or has invalid front matter, the app stops with an error naming the file.
- The loader returns the sources in a fixed order, so the prompt cache is not invalidated between requests.
- The total size of the knowledge base in tokens is logged at startup.

**Covers:** FR2, FR11

---

## Epic 3: Core chat flow

Ask a question in Thai and get a correct answer with sources.

### Story 3.1: Answer with citations

**As an** applicant, **I want** to ask a question and get an answer in Thai based on official sources, **so that** I can trust the information.

**Acceptance criteria**
- `POST /api/chat` takes the question and returns the answer text and a list of sources (title, publisher, URL, quoted text).
- The request sends the knowledge base as document blocks with citations enabled.
- The system prompt is stored in `prompts/answer-system.md`, with a version number at the top.
- The system prompt tells the model to answer in Thai, use only the sources, and keep language simple.
- Given the mock returns an answer with two citations, the endpoint returns both sources with correct titles and URLs.

**Covers:** FR1, FR2, NFR7

### Story 3.2: Prompt caching and cost logging

**As the** project owner, **I want** the knowledge base cached between requests and the cost of each question logged, **so that** running the chatbot stays affordable and the cost can be reported.

**Acceptance criteria**
- The request places a cache breakpoint after the knowledge base, and nothing that changes per request (date, IDs) appears before it.
- Each request logs input, cached and output tokens and an estimated cost in dollars.
- Given two questions in a row against the real API, the second shows cached input tokens greater than zero (checked manually and noted in the README).

**Covers:** NFR6

### Story 3.3: Chat page

**As an** applicant, **I want** a simple chat page on my phone, **so that** I can ask questions without technical knowledge.

**Acceptance criteria**
- `/` shows a chat page with a text field, a send button and the conversation.
- Each answer shows its sources as numbered links below the text.
- While waiting for an answer, a Thai loading message is shown.
- Given the API returns an error, a friendly message in Thai is shown and the user can try again.
- The page has no frameworks that need a build step.

**Covers:** FR1, FR2, NFR1

### Story 3.4: Follow-up questions

**As an** applicant, **I want** to ask follow-up questions that build on earlier answers, **so that** I don't have to repeat myself.

**Acceptance criteria**
- The browser keeps the conversation and sends earlier messages with each new question.
- The server does not store the conversation (see NFR5).
- Given a follow-up like "and for children?" after a document question, the request includes the earlier question and answer.
- Reloading the page starts a new conversation.

**Covers:** FR1, NFR5

### Story 3.5: Example questions

**As an** applicant with limited digital skills, **I want** to tap an example question, **so that** I can start without typing.

**Acceptance criteria**
- An empty chat shows 4–6 example questions in Thai as large buttons.
- Tapping a button sends that question.
- The example questions are stored in one data file, also used by demo mode and the README.

**Covers:** FR8, NFR1

---

## Epic 4: Limits and referral

Make sure the chatbot knows what it must not answer.

### Story 4.1: Question classifier

**As the** project owner, **I want** each question classified before it is answered, **so that** individual cases are reliably referred onward.

**Acceptance criteria**
- Before answering, a separate model call classifies the question as `general`, `individual_assessment`, `out_of_scope` or `personal_data`, using structured output.
- The classifier prompt is stored in `prompts/classifier-system.md` with a version number.
- Only `general` questions go on to the answering step.
- The category is returned by the API (for testing and evaluation) but not shown to the user.

**Covers:** FR3, NFR7

### Story 4.2: Referral replies

**As an** applicant, **I want** a clear explanation when the chatbot can't help, and where I can get help instead, **so that** I'm not left without an answer.

**Acceptance criteria**
- `individual_assessment` → a Thai message explaining that the question depends on personal circumstances, with the adviser contact from `ADVISER_CONTACT` and a link to UDI.
- `out_of_scope` → a Thai message explaining that the chatbot only covers short-stay tourist and visitor visas to Norway.
- Given the answering step finds no support in the sources, the reply says the information is not in the sources and refers the user onward, without guessing.
- Referral texts are stored in one file and reviewed by the domain expert.

**Covers:** FR3, FR4

### Story 4.3: Privacy notice and personal data warning

**As an** applicant, **I want** to be told not to share personal information, **so that** my private details are protected.

**Acceptance criteria**
- The chat page shows a short Thai notice: do not share personal information, and questions are sent to an AI service to generate answers.
- `personal_data` → the user is asked to remove the personal details and ask the question in general terms; the question is not answered.
- No question or answer text is written to logs or the database.

**Covers:** FR9, NFR5

---

## Epic 5: Feedback

Measure whether users got what they needed.

### Story 5.1: Feedback question

**As the** project owner, **I want** users to say whether they got the information they needed, **so that** I can measure whether the chatbot helps.

**Acceptance criteria**
- After an answer, the page shows "Did you receive all the information you needed?" in Thai with Yes and No buttons.
- Clicking a button sends `POST /api/feedback`, which stores only the answer and a timestamp in SQLite.
- The question is shown at most once per conversation; after answering, a thank-you message is shown.
- The database file is ignored by git.

**Covers:** FR5, NFR5

### Story 5.2: Feedback statistics

**As the** project owner, **I want** to see the share of Yes answers, **so that** I can follow the success criterion over time.

**Acceptance criteria**
- `python scripts/feedback_stats.py` prints the number of Yes and No answers and the percentage of Yes, in total and per week.
- Given an empty database, the script says there is no feedback yet.

**Covers:** FR5

---

## Epic 6: Document checklist (extension)

Give applicants a concrete list of what to prepare.

### Story 6.1: Checklist data

**As the** domain expert, **I want** the document requirements stored as structured data with sources, **so that** the checklist is correct and easy to update.

**Acceptance criteria**
- `knowledge-base/checklist.yaml` lists documents per visit purpose (`tourism`, `family_friends`), each with Thai text, English text and a source ID from `sources.yaml`.
- A test checks that every source ID exists and that each purpose has at least one document.

**Covers:** FR6, FR2

### Story 6.2: Checklist page

**As an** applicant, **I want** to choose why I'm travelling and see what documents I need, **so that** I can prepare my application.

**Acceptance criteria**
- The chat page has a "Document checklist" button that opens a choice between tourism and visiting family or friends.
- After choosing, the matching list is shown with tick boxes and a source link for each document.
- The list is built from `checklist.yaml` without calling the language model.
- The page states that the list is general and that UDI's checklist is the authority.

**Covers:** FR6, NFR1

---

## Epic 7: Examiner support

Let people who don't read Thai, or have no API key, run and follow the app.

### Story 7.1: English translation

**As an** examiner who doesn't read Thai, **I want** to see an English translation of an answer, **so that** I can judge whether it is correct.

**Acceptance criteria**
- Each answer has a "Show English translation" button.
- Clicking it calls `POST /api/translate`, which returns an English translation, shown below the Thai answer.
- Translations are not stored.
- In demo mode, stored translations are used.

**Covers:** FR7

### Story 7.2: Demo mode with example answers

**As an** examiner without an API key, **I want** the app to answer the example questions in demo mode, **so that** I can see how it works.

**Acceptance criteria**
- `eval/demo-answers.yaml` contains a Thai answer, sources and English translation for each example question, plus one referral example.
- Given `MOCK_LLM=true`, tapping an example question returns its stored answer with sources.
- Given `MOCK_LLM=true` and a question with no stored answer, a Thai message explains that demo mode only answers the example questions.
- The page shows a visible "Demo mode" label.

**Covers:** FR10, NFR2

---

## Epic 8: Quality assurance

Show systematically that the chatbot meets the success criteria.

### Story 8.1: Test set

**As the** domain expert, **I want** a fixed set of test questions with expected results, **so that** the chatbot can be checked the same way every time.

**Acceptance criteria**
- `eval/testset.yaml` contains 20–30 questions, each with: Thai question, English translation, expected category, expected key facts, and expected source IDs.
- At least 5 questions require an individual assessment, at least 3 are out of scope, at least 3 have typos or mix Thai and English, and at least 2 ask about something not in the sources.
- The expected answers are written and checked by the domain expert.

**Covers:** NFR4

### Story 8.2: Evaluation script

**As a** developer, **I want** a script that runs the test set against the real model and reports the results, **so that** I can see the effect of every prompt or source change.

**Acceptance criteria**
- `python scripts/run_eval.py` runs all test questions against the real API and writes a report to `eval/reports/<date>.md`.
- Automatic checks per question: correct category, at least one expected source cited, answer mainly in Thai script.
- Key facts are checked by a grading model call, and the report shows its reasoning so a human can review it.
- The report shows totals against the targets in NFR4, the prompt versions used, and the total cost.
- The script asks for confirmation before running, since it costs money.

**Covers:** NFR4, NFR6, NFR7

### Story 8.3: Evaluation log

**As the** examiner, **I want** to see how the results changed as prompts and sources were adjusted, **so that** I can follow how AI was used and controlled.

**Acceptance criteria**
- `eval/README.md` has a table with one row per evaluation run: date, prompt versions, score per criterion, and what was changed and why.
- Reports from each run are committed.

**Covers:** NFR4, NFR7

---

## Epic 9: Design and README

Make the app easy to use and easy to run.

### Story 9.1: Mobile design

**As an** applicant using a phone, **I want** a clean page with large text and buttons, **so that** I can use it easily.

**Acceptance criteria**
- The page works without horizontal scrolling on a 360 px wide screen.
- Buttons and links are at least 44 × 44 px.
- Base font size is at least 16 px, with a font that renders Thai well.
- Colour contrast meets WCAG AA.
- The page is checked on a real phone, with screenshots in `docs/`.

**Covers:** NFR1

### Story 9.2: README

**As an** examiner, **I want** a README that explains how to run and test the app, **so that** I can do it without help.

**Acceptance criteria**
- The README explains: what the app does, installation, running in demo mode, running with your own API key, running tests, and running the evaluation.
- It lists the example questions with English and Norwegian translations.
- It reports the measured cost per question and links to the latest evaluation report.
- It links to the planning documents.
- A person who has not seen the project can start the app in demo mode by following the README.

**Covers:** NFR2, NFR6

---

## Traceability

| Requirement | Stories |
|---|---|
| FR1 | 3.1, 3.3, 3.4 |
| FR2 | 2.3, 3.1, 3.3, 6.1 |
| FR3 | 4.1, 4.2 |
| FR4 | 4.2 |
| FR5 | 5.1, 5.2 |
| FR6 | 6.1, 6.2 |
| FR7 | 7.1 |
| FR8 | 3.5 |
| FR9 | 4.3 |
| FR10 | 1.2, 1.3, 7.2 |
| FR11 | 2.1, 2.2, 2.3 |
| NFR1 | 3.3, 3.5, 6.2, 9.1 |
| NFR2 | 1.1, 1.2, 7.2, 9.2 |
| NFR3 | 1.3, 1.4 |
| NFR4 | 8.1, 8.2, 8.3 |
| NFR5 | 1.2, 3.4, 4.3, 5.1 |
| NFR6 | 3.2, 8.2, 9.2 |
| NFR7 | 3.1, 4.1, 8.2, 8.3 |
