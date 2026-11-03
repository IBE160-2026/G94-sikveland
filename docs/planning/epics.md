---
status: final
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md
  - docs/planning/prds/prd-G94-sikveland-2026-10-19/addendum.md
  - docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md
---

# Norway Visa Guide For Thai - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Norway Visa Guide For Thai, decomposing the requirements from the PRD and the architecture spine into implementable stories. There is no UX design document; visual design is decided inside the stories, bound by NFR1.

## Requirements Inventory

### Functional Requirements

- FR1: The applicant can ask a question in Thai and gets an answer in Thai, also when the question has typos or mixes Thai and English; the chat page opens in Thai; the applicant can ask follow-up questions and the chatbot uses earlier questions in the same conversation.
- FR2: Every answer is based only on the knowledge base and links to the sources it uses; answers based on the knowledge base show at least one source link (fixed replies need none); the answer contains no facts that are not in its sources.
- FR3: When the applicant asks an individual-assessment question, the chatbot answers that the embassy makes the decision and no one else can answer it; it never estimates the applicant's chances.
- FR4: When the knowledge base does not contain the answer, the chatbot says so and gives the adviser contact; it does not make up an answer.
- FR5: When the applicant gives a done signal, the chatbot asks the feedback question; "Yes" ends the conversation; "No" leads to "What would you still like to know?" and the question is asked again at the next done signal; only the Yes/No answer, its time and an anonymous conversation ID are stored.
- FR6: The applicant can select a visit purpose (tourism, visiting family, visiting friends), get its fixed checklist, and tick off documents; ticks are kept on the same phone and browser with no account, are not stored on the server, and survive checklist updates for unchanged items; each item links to its source; the family-visit checklist includes the sponsorship form and invitation letter, says the sponsor fills them in, and links to where the sponsor finds them.
- FR7: The applicant can show an English translation of an answer.
- FR8: The chat page shows example questions the applicant can tap to ask them.
- FR9: The chat page asks applicants not to share personal information and states that questions are sent to an AI service; personal information (passport, ID and phone number) in a question is deleted before it is sent to the AI service and never stored; the chatbot warns the applicant, still answers the rest of the question, and reminds them not to send personal information.
- FR10: The app can run in demo mode without an API key: it answers the example questions with stored Thai answers and sources, gives a Thai message for other questions, and shows a visible "Demo mode" label.
- FR11: The knowledge base holds 10–20 official sources (UDI, VFS Global, the Royal Norwegian Embassy in Bangkok, the EU Schengen pages), each with URL, publisher and retrieval date; a script updates it; the adviser reviews changes before they are used; every answer can be traced to a source version; it covers application steps, checklists, the sponsorship form and invitation letter, relationship proof and the visa fee.
- FR12: When the applicant asks how to start, the chatbot gives the application steps in order (documents → register at UDI → pay the visa fee → book an appointment at VFS) and names and links the website for each step.
- FR13: When the applicant asks to talk to a person or asks for help with the whole process, the chatbot gives the adviser contact.
- FR14: When the applicant asks an out-of-scope question, the chatbot answers that it only covers short-stay tourist and visitor visas to Norway and gives the adviser contact.

### NonFunctional Requirements

- NFR1: The chat page works well on a phone, including in Facebook's in-app browser, with large touch targets and simple language.
- NFR2: The app can be run locally by following the README, with your own API key or in demo mode.
- NFR3: Automated tests never call the real API and run in GitHub Actions.
- NFR4: On the test set of 20–30 Thai questions with expected answers and sources (covering application steps, checklists, sponsor forms, relationship proof, visa fee, individual-assessment, out-of-scope and personal-information questions): at least 90% of general questions correct with correct source, as judged by the adviser; 100% of individual-assessment questions get the embassy-decides answer; answers in Thai also for typos and mixed Thai/English. The test set runs against the real model after every prompt or source change, separately from NFR3, and results are recorded.
- NFR5: Conversation text is not stored and personal information is deleted; only the feedback Yes/No, its time and an anonymous conversation ID are stored on the server; checklist ticks stay on the phone; no secrets or real applicant enquiries are stored in the repository.
- NFR6: The cost per question is measured and reported.
- NFR7: Prompts are stored as versioned files in the repository.
- NFR8: All fixed Thai texts (example questions, checklists, embassy-decides, out-of-scope and no-answer messages, privacy notice, demo answers) are reviewed by the adviser before release.

### Additional Requirements

From the architecture spine (AD numbers in brackets):

- No starter template: greenfield Python project managed with uv (`pyproject.toml`, `uv.lock`), started with `uv run uvicorn app.main:app`; layout `app/{web,pipeline,ports,adapters,static}`, `content/`, `prompts/`, `knowledge-base/`, `scripts/`, `eval/`, `tests/`, `data/`.
- Stack: Python 3.12, FastAPI 0.162, uvicorn 0.54, anthropic 2.4.0, pydantic-settings 2.16, PyYAML 6.0, httpx 0.28, markdownify 1.2, pypdf 6.21, pytest 9.2, SQLite; plain HTML/CSS/JS page.
- Fixed pipeline order: filter personal info → classify → route → answer or fixed reply; nothing reaches the LLM before the filter; the eval script uses the same pipeline entry (AD-1).
- Only `app/adapters/anthropic_llm.py` imports the SDK; `MOCK_LLM=true` wires the demo adapter (AD-2).
- LLM port: `classify(question, recent_history) -> (Category, Usage)`, `answer(question, history) -> stream of {text, source_ids} + Usage`, `translate(text) -> (str, Usage)`; Usage includes thinking and cache tokens; adapters return no SDK types; refusal is an error; answers use `MODEL_ANSWER` (Claude Opus 5.5), classify and translate use `MODEL_SMALL` (Claude Haiku 5.5) (AD-14).
- Stateless server: the conversation lives in the page's `sessionStorage`; requests are `{question, history: [{question, answer}]}`, max 10 exchanges; the page stores an exchange only after `done`, using `clean_question`; history is sent as plain text (AD-3).
- Personal-information filter runs on the question, all history turns and translate input; `meta.personal_info_removed` refers to the new question only (AD-4).
- Classifier: separate structured-output call (no forced tool use), closed categories `general`, `individual_assessment`, `out_of_scope`, `reach_person`, `done`; sees the question plus the last 2 exchanges (AD-5).
- Fixed texts: `content/texts.yaml`, a closed key list with `th` and `en`, category → key mapping, `{ADVISER_CONTACT}` filled at load; `GET /api/texts` returns `{demo_mode, texts, example_questions}`; no hard-coded Thai in the page (AD-6).
- Answer call: system prompt → all KB documents sorted by id with Citations and a cache breakpoint → history → question; text held back until the first citation; zero citations → `reply-no-answer`; a started reply is never replaced (AD-7).
- Stream contract: `POST /api/chat` returns JSON Lines; events `meta` → `text`* → `sources` (with `checklist` flag and `checklist_purposes`) → `done`, or `error`; read with `fetch` + `getReader()` + streaming `TextDecoder`; only `app/web` builds events (AD-8).
- Knowledge base: `knowledge-base/sources.yaml` (id, title, url, publisher, retrieved, file) + Markdown snapshots; `scripts/ingest.py` offline; the adviser reviews diffs; the app never fetches at runtime; every shown link is a source (AD-9).
- Feedback: SQLite table `feedback(conversation_id, answer, created_at)` written only by `POST /api/feedback`; flow ownership and `conversation_id` lifecycle as in AD-10; SM-1 counts the first answer per conversation.
- Checklists: `content/checklists.yaml`, item ids stable, sources resolved to `{title, url}` by `GET /api/checklists/{purpose}`; ticks in `localStorage` under `checklist:{purpose}`; a permanent checklist button plus an "open checklist" button when the `sources` event has `checklist: true`, opening the purpose in `checklist_purposes` directly when there is one (AD-11).
- Prompts in `prompts/` with a `version:` line; logs and eval reports record prompt versions (AD-12).
- Tests: pytest with a scripted fake in `tests/fakes/`; `scripts/run_eval.py` runs `eval/testset.yaml` through the full pipeline and writes `eval/reports/` (AD-13).
- Demo mode: `content/demo-answers.yaml` keyed by example-question id, NFC + trim matching, `done_phrases`, non-match → `reply-demo-only`; in demo mode, startup fails if an example question lacks a demo answer (AD-15).
- Conventions: endpoints `POST /api/chat`, `POST /api/translate` (`{text}` → `{translation}`, stored `en` first), `POST /api/feedback`, `GET /api/checklists/{purpose}`, `GET /api/texts`; kebab-case ids; ISO 8601 dates; error envelope `{"error": {"code", "message"}}`; startup checks on content keys and source ids, plus demo answers in demo mode; one JSON log line per request without question or answer text; config from `.env` via `app/config.py`, with `.env.example`, including per-model prices (`PRICE_ANSWER_*`, `PRICE_SMALL_*` for input, output, cache read and cache write); `.env` and `data/` git-ignored.

### UX Design Requirements

No UX design document exists. Page layout and visual design are decided within the chat-page and checklist stories, bound by NFR1 and the stream contract (AD-8).

### FR Coverage Map

FR1: Epic 1 - Ask and answer in Thai, with follow-ups
FR2: Epic 1 - Answers only from the knowledge base, with sources
FR3: Epic 2 - Individual-assessment questions get "the embassy decides"
FR4: Epic 1 - No answer in the knowledge base gives the adviser contact
FR5: Epic 2 - Feedback question at the end of the conversation
FR6: Epic 3 - Checklist with saved ticks
FR7: Epic 4 - English translation
FR8: Epic 1 - Example questions
FR9: Epic 1 - Personal information protection
FR10: Epic 4 - Demo mode
FR11: Epic 1 - Official sources, kept up to date
FR12: Epic 1 - Application steps in order
FR13: Epic 2 - Reach a person
FR14: Epic 2 - Out-of-scope questions

NFRs: NFR1, NFR2, NFR3, NFR5, NFR6 and NFR7 start in Epic 1 and apply to every later epic; NFR2 is completed in Epic 4 (README, demo mode); NFR4 is Epic 5; NFR8 applies to every story that adds fixed Thai text.

## Epic List

### Epic 1: Applicants get answers in Thai from official sources
An applicant opens the chat page, taps an example question or types their own, and gets a Thai answer streamed bit by bit with source links, including the application steps in order. Follow-up questions work. Personal information is removed before anything reaches the AI service, and when the knowledge base has no answer the applicant gets the adviser contact. Includes the project skeleton, CI, the LLM port with fake and real adapters, the knowledge base and ingest script, fixed texts and cost logging.
**FRs covered:** FR1, FR2, FR4, FR8, FR9, FR11, FR12

### Epic 2: Clear limits, a person to contact, and feedback at the end
The chatbot recognises questions about the applicant's own chances, other visa types, requests for a person, and done signals. It answers with fixed texts and the adviser contact, asks the feedback question when the applicant is done, and stores the Yes/No answer.
**FRs covered:** FR3, FR5, FR13, FR14

### Epic 3: Document checklist with saved ticks
An applicant chooses a visit purpose, gets the checklist with source links (including the sponsor's forms), ticks off documents and finds the ticks still there days later. The checklist opens from a permanent button and from answers about documents.
**FRs covered:** FR6

### Epic 4: English translation and demo mode for the examiner
The examiner can run the app without an API key, see the demo-mode label, try the example questions, and show any answer in English. The README explains setup with an own key or in demo mode.
**FRs covered:** FR7, FR10

### Epic 5: Measured quality: test set and evaluation
The adviser and the examiner can see that the chatbot meets its targets: the test set runs against the real models through the full pipeline and produces a report (SM-2), and a statistics script reports the share of "Yes" answers (SM-1).
**FRs covered:** none directly; covers NFR4, SM-1 and SM-2

## Epic 1: Applicants get answers in Thai from official sources

An applicant opens the chat page, taps an example question or types their own, and gets a Thai answer streamed bit by bit with source links, including the application steps in order. Follow-up questions work, personal information is removed before anything reaches the AI service, and when the knowledge base has no answer the applicant gets the adviser contact.

### Story 1.1: Project skeleton with CI

As a developer in the project group,
I want a runnable project skeleton with configuration and automated tests,
So that every later story starts from the same structure and is checked on every push.

**Acceptance Criteria:**

**Given** a fresh clone of the repository
**When** I run `uv sync` and `uv run uvicorn app.main:app`
**Then** the app starts and `GET /api/health` returns `{"status": "ok"}`
**And** the folders `app/{web,pipeline,ports,adapters,static}`, `content/`, `prompts/`, `knowledge-base/`, `scripts/`, `eval/`, `tests/` and `data/` exist as in the architecture spine
**And** dependencies are pinned in `pyproject.toml` and `uv.lock` with the stack versions from the architecture.

**Given** the settings module `app/config.py`
**When** the app starts
**Then** every setting is read from `.env` (`ANTHROPIC_API_KEY`, `MODEL_ANSWER`, `MODEL_SMALL`, `EFFORT_ANSWER`, `EFFORT_SMALL`, `MOCK_LLM`, `ADVISER_CONTACT`, `DATABASE_PATH`, and the `PRICE_ANSWER_*` and `PRICE_SMALL_*` settings for input, output, cache-read and cache-write tokens)
**And** `.env.example` lists all of them with safe example values, and prices taken from Anthropic's pricing page
**And** `.env` and `data/` are git-ignored.

**Given** a push to GitHub
**When** GitHub Actions runs
**Then** `uv run pytest` runs and passes without an API key and without network access to the Claude API (NFR3).

### Story 1.2: Chat page with Thai texts, privacy notice and example questions

As an applicant,
I want the chat page to open in Thai with a privacy notice and example questions I can tap,
So that I can start without typing and know not to share personal information.

**Acceptance Criteria:**

**Given** `content/texts.yaml` with the keys `privacy-notice`, `personal-info-reminder`, `reply-no-answer`, `error` and `demo-label`, each with `th` and `en`, and a list of example questions with `id`, `th` and `en`
**When** the app starts
**Then** `ContentStore` loads them and replaces `{ADVISER_CONTACT}` with the configured value
**And** the app refuses to start if a required key is missing or an example-question `id` is duplicated.

**Given** the app is running
**When** the page calls `GET /api/texts`
**Then** it gets `{demo_mode, texts: {key: text}, example_questions: [{id, text}]}` in Thai.

**Given** an applicant opens the page on a phone
**When** it has loaded
**Then** it shows the privacy notice, which says not to share passport, ID or phone numbers and that questions are sent to an AI service (FR9)
**And** it shows the example questions as large tappable buttons (FR8, NFR1)
**And** it shows a text field and a send button
**And** the page contains no hard-coded Thai; all Thai comes from `/api/texts` (AD-6).

**Given** the Thai texts in `content/texts.yaml`
**When** the story is done
**Then** the adviser has reviewed them, and this is noted in the pull request (NFR8).

### Story 1.3: Knowledge base of official sources

As the adviser,
I want the chatbot's knowledge base to contain only official pages that I have reviewed,
So that answers are based on correct and current information.

**Acceptance Criteria:**

**Given** `knowledge-base/sources.yaml` with 10–20 entries from UDI, VFS Global, the Royal Norwegian Embassy in Bangkok and the EU Schengen pages
**When** I read an entry
**Then** it has a kebab-case `id`, `title`, `url`, `publisher`, `retrieved` date and `file` (FR11, AD-9)
**And** together the sources cover the application steps, document requirements per visit purpose, the sponsorship form and invitation letter, relationship proof and the visa fee.

**Given** I run `uv run python scripts/ingest.py`
**When** a source is an HTML page or a PDF
**Then** the script writes a Markdown snapshot to `knowledge-base/` and updates its `retrieved` date
**And** it prints which snapshots changed, so the adviser can review the git diff before committing
**And** a source that cannot be fetched is reported and its old snapshot is kept.

**Given** the app starts
**When** `KnowledgeBase` loads the committed snapshots
**Then** every source in `sources.yaml` has a snapshot, or the app refuses to start
**And** the app never fetches web pages while running.

### Story 1.4: Personal information filter

As an applicant,
I want passport, ID and phone numbers removed from what I write before it is sent anywhere,
So that my personal information never reaches the AI service or any log.

**Acceptance Criteria:**

**Given** a text containing a Thai ID number, a passport number or a phone number (Thai or Norwegian format)
**When** the filter in `app/pipeline/` runs on it
**Then** each match is removed and replaced with a neutral marker
**And** the filter reports that something was removed (FR9, AD-4).

**Given** a text with no personal information, including Thai text, dates, prices such as "90 euro" and mixed Thai/English
**When** the filter runs
**Then** the text is returned unchanged and nothing is reported as removed.

**Given** the filter module
**When** its tests run
**Then** there are pytest cases for each pattern and for common false positives
**And** the filter is pure logic with no FastAPI or SDK imports.

### Story 1.5: Claude connection with a test version

As a developer,
I want one interface to Claude with a real implementation and a scripted test fake,
So that answers can be built and tested without calling the real API.

**Acceptance Criteria:**

**Given** the `LLMClient` port in `app/ports/`
**When** I read it
**Then** it defines `answer(question, history)`, returning a stream of `{text, source_ids}` chunks followed by `Usage` (input, output including thinking, cache-read and cache-write tokens) (AD-14)
**And** `classify` and `translate` are declared for later epics.

**Given** the scripted fake in `tests/fakes/`
**When** a test configures it
**Then** it can return chunks with and without source IDs, an error or a refusal, without network access (AD-13).

**Given** the Anthropic adapter `app/adapters/anthropic_llm.py`, the only module that imports `anthropic`
**When** `answer` is called
**Then** the request is built in the fixed order: the system prompt from `prompts/answer-system.md`, then all knowledge-base documents sorted by `id` with Citations on and a cache breakpoint after the last document, then history as plain text, then the question (AD-7)
**And** it uses `MODEL_ANSWER` with adaptive thinking and `EFFORT_ANSWER`, and sends no sampling parameters
**And** citations are turned into source IDs, and no SDK types leave the adapter
**And** `stop_reason: "refusal"` is raised as an error.

**Given** `prompts/answer-system.md`
**When** I read it
**Then** it starts with a `version:` line (AD-12, NFR7)
**And** it tells the model to answer in Thai, only from the documents, and to give the application steps in order with the website for each step when asked how to start (FR12).

### Story 1.6: Streamed answer with sources

As an applicant,
I want my question answered in Thai, appearing bit by bit, with links to the official sources,
So that I can see what to do and check where the information comes from.

**Acceptance Criteria:**

**Given** the page sends `POST /api/chat` with `{question, history: []}`
**When** the server handles it
**Then** the pipeline runs the filter before anything is sent to the LLM (AD-1)
**And** the classify step is not part of this story: every question is treated as `general`
**And** the response is JSON Lines with the events `meta` (`category`, `personal_info_removed`, `clean_question`), `text` (`delta`), `sources` (`[{id, title, url}]`, `checklist: false`, `checklist_purposes: []`) and `done`, in that order (AD-8)
**And** the answer is in Thai, also when the question has typos or mixes Thai and English (FR1).

**Given** the LLM returns chunks with citations
**When** the answer streams
**Then** text is held back until the first chunk with a source ID arrives, and then the held text and the rest are sent as `text` events (AD-7)
**And** the `sources` event lists exactly the cited sources, with title and URL from `sources.yaml` (FR2).

**Given** the LLM returns an answer with zero citations
**When** the answer ends
**Then** no model text has been sent, and the fixed `reply-no-answer` text with the adviser contact is sent as one `text` event with an empty `sources` list (FR4).

**Given** the LLM fails or refuses
**When** the error happens
**Then** an `error` event is sent, the stream ends, and the page shows the fixed `error` text.

**Given** the page receives the stream
**When** events arrive
**Then** it reads them with `fetch` + `getReader()` and a streaming `TextDecoder`, appends `text` deltas as they come, and shows the source links under the answer when `sources` arrives
**And** a "typing" indicator shows until the first `text` event.

**Given** a real Android or iPhone phone
**When** the chat page is opened from a link in Facebook's in-app browser
**Then** the answer streams bit by bit as in a normal browser, and the result is noted in the pull request (NFR1, spine Deferred).

**Given** the tests
**When** they run with the scripted fake
**Then** they cover the cited path, the zero-citation path and the error path.

### Story 1.7: Follow-up questions

As an applicant,
I want to ask follow-up questions such as "and how much is the fee?",
So that I don't have to repeat my situation in every question (FR1).

**Acceptance Criteria:**

**Given** a conversation in progress
**When** a `done` event arrives
**Then** the page stores the exchange `{question: clean_question, answer: shown text}` in `sessionStorage`, including fixed replies (AD-3)
**And** an exchange that ended with `error` is not stored.

**Given** stored exchanges
**When** the applicant sends a new question
**Then** the page sends `{question, history}` with at most the last 10 exchanges
**And** the server filters personal information from every history turn before use (AD-4)
**And** the pipeline turns the history into alternating user/assistant plain-text messages.

**Given** the page is reloaded in the same tab
**When** it opens again
**Then** the earlier conversation is shown and continues; closing the tab removes it.

**Given** `meta.personal_info_removed` is `true` for the new question
**When** the reply is shown
**Then** the fixed `personal-info-reminder` appears above the reply, and the rest of the question is answered as normal (FR9).

**Given** the server
**When** it handles any request
**Then** it keeps nothing between requests and writes no question or answer text to disk, database or logs (NFR5).

### Story 1.8: Cost and request log

As the adviser,
I want to see what each question costs,
So that I can report the running cost and keep it under control.

**Acceptance Criteria:**

**Given** a chat request has finished
**When** `app/web` logs it
**Then** one JSON line is written with timestamp, category, prompt versions, model, input, output (including thinking), cache-read and cache-write tokens, and cost in USD (NFR6, AD-12)
**And** the line contains no question text, answer text or personal information (NFR5).

**Given** the `PRICE_ANSWER_*` and `PRICE_SMALL_*` settings from Story 1.1
**When** cost is calculated
**Then** each call is priced with the settings for its model, and cache reads and cache writes are priced separately from normal input tokens.

**Given** several requests using the same knowledge base
**When** I look at the log
**Then** I can see whether the cache was used (cache-read tokens above zero), and the README explains how to read the log.

## Epic 2: Clear limits, a person to contact, and feedback at the end

The chatbot recognises questions about the applicant's own chances, other visa types, requests for a person, and done signals. It answers with fixed texts and the adviser contact, asks the feedback question when the applicant is done, and stores the Yes/No answer.

### Story 2.1: "The embassy decides" for questions about the applicant's own chances

As an applicant,
I want a clear answer when I ask whether I will get the visa,
So that I understand that only the embassy can decide, instead of getting a guess.

**Acceptance Criteria:**

**Given** the `classify(question, recent_history)` method on the `LLMClient` port
**When** the Anthropic adapter implements it
**Then** it calls `MODEL_SMALL` (Claude Haiku 5.5) with `EFFORT_SMALL`, using structured output (`output_config.format`) and no forced tool use (AD-5, AD-14)
**And** it returns `(Category, Usage)`, where the category is `general` or `individual_assessment`
**And** the classifier prompt is `prompts/classifier-system.md` with a `version:` line (AD-12).

**Given** a cleaned question and the last 2 exchanges of history
**When** the pipeline runs
**Then** the classify step runs after the filter and before any answer call (AD-1)
**And** only `general` continues to the answer step.

**Given** a question such as "Will I get the visa?" or "I was refused last year, will I get it this time?"
**When** it is classified as `individual_assessment`
**Then** the reply is the fixed `reply-embassy-decides` text from `content/texts.yaml`, sent as one `text` event with an empty `sources` list (FR3, AD-6)
**And** the `meta` event has `category: "individual_assessment"`
**And** no answer call is made, so the chatbot never estimates the applicant's chances.

**Given** a follow-up such as "and how much is the fee?" after a general question
**When** it is classified with the recent history
**Then** it is `general`.

**Given** the scripted fake
**When** a test sets the category
**Then** tests cover both categories without calling the real API
**And** the classifier's token usage is added to the request log from Story 1.8.

**Given** the new Thai text `reply-embassy-decides`
**When** the story is done
**Then** the adviser has reviewed it (NFR8).

### Story 2.2: Other visa types and requests for a person

As an applicant,
I want to be told when the chatbot can't help with my topic, and how to reach the adviser,
So that I know where to turn instead of being left without an answer.

**Acceptance Criteria:**

**Given** the classifier from Story 2.1
**When** this story is done
**Then** it can also return `out_of_scope` and `reach_person`, and the classifier prompt version is increased.

**Given** a question about anything other than short-stay tourist and visitor visas to Norway, such as a work visa
**When** it is classified as `out_of_scope`
**Then** the reply is the fixed `reply-out-of-scope` text, which says the chatbot only covers short-stay tourist and visitor visas to Norway and gives the adviser contact (FR14).

**Given** the applicant asks to talk to a person, or asks for help with the whole process
**When** the question is classified as `reach_person`
**Then** the reply is the fixed `reply-reach-person` text with the adviser contact (FR13).

**Given** either fixed reply
**When** it is sent
**Then** it is one `text` event with an empty `sources` list, and `{ADVISER_CONTACT}` is filled from configuration.

**Given** the scripted fake
**When** the tests run
**Then** both categories are covered.

**Given** the new Thai texts
**When** the story is done
**Then** the adviser has reviewed them (NFR8).

### Story 2.3: Feedback question at the end of the conversation

As the adviser,
I want applicants to be asked whether they got all the information they needed when they finish,
So that I can measure whether the chatbot helps (SM-1).

**Acceptance Criteria:**

**Given** the classifier from Story 2.2
**When** this story is done
**Then** it can also return `done` for messages such as "thank you", "okay" and their Thai variants, and the classifier prompt version is increased (AD-5).

**Given** the applicant sends a done signal
**When** it is classified as `done`
**Then** the reply is the fixed `feedback-question` text ("Have you received all the information you need?") (FR5)
**And** the page shows Yes and No buttons under that reply.

**Given** the page has no `conversation_id` in `sessionStorage`
**When** the applicant sends the first question
**Then** the page creates a UUID v4 `conversation_id` and keeps it in `sessionStorage` (AD-10).

**Given** the applicant taps Yes or No
**When** the page sends `POST /api/feedback {conversation_id, answer: "yes" | "no"}`
**Then** the server stores `(conversation_id, answer, created_at)` in the SQLite table `feedback`, creating `data/` and the table if missing, and returns 204
**And** an invalid body returns the error envelope `{"error": {"code", "message"}}` with status 422.

**Given** the applicant tapped No
**When** the answer is stored
**Then** the page shows the fixed `feedback-follow-up` text ("What would you still like to know?") and the conversation continues
**And** the feedback question is asked again at the next done signal.

**Given** the applicant tapped Yes
**When** the answer is stored
**Then** the conversation ends: the page clears the history and `conversation_id`, and the next question starts a new conversation.

**Given** the feedback table
**When** I inspect it
**Then** it holds only `conversation_id`, `answer` and `created_at`, and no question or answer text (NFR5).

**Given** the new Thai texts
**When** the story is done
**Then** the adviser has reviewed them (NFR8).

## Epic 3: Document checklist with saved ticks

An applicant chooses a visit purpose, gets the checklist with source links (including the sponsor's forms), ticks off documents and finds the ticks still there days later. The checklist opens from a permanent button and from answers about documents.

### Story 3.1: Checklists per visit purpose

As the adviser,
I want each visit purpose to have a fixed checklist that I have reviewed, with a source for every item,
So that applicants get the same correct list every time instead of a list generated by the AI.

**Acceptance Criteria:**

**Given** `content/checklists.yaml`
**When** I read it
**Then** it has one checklist for each visit purpose, `tourism`, `family` and `friends` (FR6, AD-11)
**And** every item has a stable kebab-case `id`, `th` and `en` text, and a source `id` from `knowledge-base/sources.yaml` (AD-9).

**Given** the `family` checklist
**When** I read it
**Then** it includes the sponsorship form and the invitation letter, says that the sponsor in Norway fills them in, and links to where the sponsor finds them (FR6, UJ-1).

**Given** the app starts
**When** `ContentStore` loads the checklists
**Then** the app refuses to start if an item refers to an unknown source `id` or two items in one checklist share an `id`.

**Given** the app is running
**When** a client calls `GET /api/checklists/family`
**Then** it gets the items in Thai, each with its `id`, text and source resolved to `{title, url}`, without any LLM call
**And** an unknown purpose returns 404 with the error envelope.

**Given** the checklist texts
**When** the story is done
**Then** the adviser has reviewed them against UDI's official checklist, which remains the authority (NFR8).

### Story 3.2: Tick off documents, and the ticks are kept

As an applicant,
I want to tick off the documents I already have and find my ticks again when I come back,
So that I can see which documents are still missing without asking the adviser to check.

**Acceptance Criteria:**

**Given** the chat page
**When** it has loaded
**Then** a "Checklist" button is always visible (AD-11, NFR1).

**Given** the applicant taps the button
**When** the checklist view opens
**Then** they choose a visit purpose (tourism, visiting family or visiting friends), and the page shows that checklist from `GET /api/checklists/{purpose}`, each item with a large checkbox and its source link (FR6).

**Given** the applicant ticks or unticks an item
**When** the checkbox changes
**Then** the page stores the ticked item IDs in `localStorage` under `checklist:{purpose}`
**And** nothing about the ticks is sent to the server (NFR5).

**Given** the applicant closes the browser and opens the page again days later on the same phone
**When** they open the same checklist
**Then** their ticks are still there (UJ-1).

**Given** the adviser has changed the checklist since the ticks were saved
**When** the page loads it
**Then** ticks on unchanged items are kept, ticks for removed item IDs are ignored, and new items start unticked.

**Given** the applicant is in the checklist view
**When** they want to go back
**Then** they return to the chat, and the conversation is unchanged.

### Story 3.3: Open the checklist from the chat

As an applicant,
I want a button to my checklist when the chatbot answers a question about documents,
So that I can go straight from the answer to ticking off what I have.

**Acceptance Criteria:**

**Given** an answer whose cited sources include a source linked to at least one checklist item
**When** the `sources` event is sent
**Then** it has `checklist: true` and `checklist_purposes` lists every visit purpose whose checklist has an item linked to a cited source; otherwise `checklist: false` and `checklist_purposes: []` (AD-8, AD-11).

**Given** a `sources` event with `checklist: true`
**When** the page shows the answer
**Then** an "Open checklist" button appears under it.

**Given** the applicant taps "Open checklist"
**When** `checklist_purposes` has one purpose
**Then** that checklist opens directly
**And** if it has more than one, the visit-purpose choice from Story 3.2 opens first.

**Given** the scripted fake
**When** the tests run
**Then** they cover answers with and without checklist-linked sources.

## Epic 4: English translation and demo mode for the examiner

The examiner can run the app without an API key, see the demo-mode label, try the example questions, and show any answer in English. The README explains setup with an own key or in demo mode.

### Story 4.1: Show the English translation

As the examiner, who does not read Thai,
I want to show an English translation of any reply,
So that I can follow what the chatbot tells applicants.

**Acceptance Criteria:**

**Given** a reply shown in the chat
**When** it has finished (`done` received)
**Then** a "Show English" button appears under it.

**Given** the reply is a fixed text or an example question
**When** the applicant or examiner taps the button
**Then** the page sends `POST /api/translate {text}` and the server returns `{translation}` using the stored `en` text, without calling the LLM (FR7).

**Given** the reply was written by the model
**When** the button is tapped
**Then** the server runs the personal-information filter on the text (AD-4) and calls `LLMClient.translate`, which uses `MODEL_SMALL` (Claude Haiku 5.5) with `EFFORT_SMALL` and the versioned prompt `prompts/translate-system.md` (AD-12, AD-14)
**And** the token usage is written to the request log.

**Given** a translation is returned
**When** the page shows it
**Then** the English text appears under the Thai reply, and the Thai reply is unchanged
**And** a failed translation shows the fixed `error` text.

**Given** the scripted fake
**When** the tests run
**Then** they cover the stored-text path and the model path.

### Story 4.2: Demo mode without an API key

As the examiner,
I want to run the app without an API key and try the example questions,
So that I can see how the chatbot works without paying for or setting up Claude.

**Acceptance Criteria:**

**Given** `MOCK_LLM=true` and no `ANTHROPIC_API_KEY`
**When** I run `uv run uvicorn app.main:app`
**Then** the app starts with the `mock_llm` adapter (AD-2, FR10)
**And** `GET /api/texts` returns `demo_mode: true`, and the page shows the fixed `demo-label` text where it is always visible.

**Given** `content/demo-answers.yaml`, keyed by example-question `id`
**When** I read it
**Then** every example question has a category, a Thai answer, source IDs and an English translation
**And** there is a `done_phrases` list (AD-15)
**And** the app refuses to start in demo mode if an example question has no demo answer, or a demo answer refers to an unknown source.

**Given** demo mode
**When** I tap an example question, or type the same text with different spacing or Unicode form
**Then** the mock matches it after NFC normalisation and trimming, and the stored answer streams with the same events as a real answer, including sources.

**Given** demo mode
**When** I type one of the `done_phrases`
**Then** the feedback question appears as in Story 2.3.

**Given** demo mode
**When** I type any other question
**Then** the reply is the fixed `reply-demo-only` text ("demo mode only answers the example questions"), not `reply-no-answer`.

**Given** demo mode
**When** I tap "Show English"
**Then** the translation comes from the stored `en` of the demo answer or fixed text, without any API call.

**Given** the demo answers and new texts
**When** the story is done
**Then** the adviser has reviewed the Thai (NFR8).

### Story 4.3: README for running and following the app

As the examiner,
I want clear instructions for running and trying the app,
So that I can assess it without help from the group.

**Acceptance Criteria:**

**Given** the repository README
**When** I follow it on a computer with Python 3.12 and uv
**Then** I can start the app in demo mode without an API key, and with my own key using `.env.example` (NFR2)
**And** it explains how to open the page from a phone on the same Wi-Fi (`--host 0.0.0.0`).

**Given** the README
**When** I read it
**Then** it lists every setting in `.env.example` with what it does
**And** it lists the example questions with English and Norwegian translations
**And** it explains how to run the tests (`uv run pytest`) and how to read the cost log.

**Given** a member of the group follows the README on a clean machine
**When** they are done
**Then** both demo mode and own-key mode work, and any missing step is fixed in the README.

## Epic 5: Measured quality: test set and evaluation

The adviser and the examiner can see that the chatbot meets its targets: the test set runs against the real models through the full pipeline and produces a report (SM-2), and a statistics script reports the share of "Yes" answers (SM-1).

### Story 5.1: Test set of Thai questions

As the adviser,
I want a fixed set of Thai test questions with the answers I expect,
So that the chatbot's quality can be measured the same way every time.

**Acceptance Criteria:**

**Given** `eval/testset.yaml`
**When** I read it
**Then** it has 20–30 questions, each with a kebab-case `id`, the Thai question, an English gloss, the expected category, the key facts the answer must contain, and the expected source IDs (NFR4).

**Given** the test set as a whole
**When** I check its coverage
**Then** it includes questions on the application steps, checklists, the sponsorship form and invitation letter, relationship proof and the visa fee
**And** it includes individual-assessment questions, out-of-scope questions, requests for a person, questions containing personal information, questions with typos and questions mixing Thai and English
**And** some questions are follow-ups that come with a short history.

**Given** the expected facts and categories
**When** the story is done
**Then** the adviser has written or reviewed every expected answer (NFR8)
**And** the test set contains no real applicant enquiries or real personal information; personal-information cases use made-up numbers (NFR5).

**Given** a pytest test
**When** it loads the test set
**Then** it checks that every entry has the required fields and refers only to known source IDs and valid categories.

### Story 5.2: Evaluation script and report

As the adviser and the examiner,
I want to run the test set against the real models and get a report,
So that I can see whether the chatbot meets the quality targets after each change (SM-2).

**Acceptance Criteria:**

**Given** a valid `ANTHROPIC_API_KEY` and `MOCK_LLM=false`
**When** I run `uv run python scripts/run_eval.py`
**Then** every question in the test set goes through the same pipeline entry point as `/api/chat`, including the filter and classifier (AD-1)
**And** the script refuses to run in demo mode or without a key, with a clear message.

**Given** each question has run
**When** the script checks the result
**Then** it records automatically whether the category matches, whether the expected sources were cited, and whether personal information was removed
**And** it records the answer text and the expected facts side by side, with an empty column for the adviser's judgement of whether the facts are correct.

**Given** the run has finished
**When** the report is written to `eval/reports/<date>-<prompt versions>.md`
**Then** it shows, per question, the automatic checks and the adviser column
**And** it shows the totals against the targets: at least 90% of general questions correct with the correct source, and 100% of individual-assessment questions answered with "the embassy decides" (NFR4)
**And** it records the models, prompt versions, total tokens and total cost (AD-12, NFR6).

**Given** the adviser has filled in the judgement column
**When** I run `uv run python scripts/run_eval.py --score <report>`
**Then** the totals are recalculated from the adviser's judgements.

**Given** the API has no sampling settings, so answers can vary between runs
**When** the report is read
**Then** each run is judged on its own, and the README says so.

**Given** the README
**When** this story is done
**Then** it explains how to run the evaluation, fill in the judgement column and read the report, and says to rerun it after every change to prompts or sources.

### Story 5.3: Feedback statistics

As the adviser,
I want to see how many applicants got all the information they needed,
So that I can follow the main success metric after launch (SM-1).

**Acceptance Criteria:**

**Given** the SQLite `feedback` table
**When** I run `uv run python scripts/feedback_stats.py`
**Then** it prints the number of conversations with feedback, and the share whose first answer was "yes", counting only the first answer per `conversation_id` (AD-10)
**And** it compares the share with the 80% target.

**Given** I pass `--from` and `--to` dates
**When** the script runs
**Then** it only counts feedback created in that period.

**Given** an empty or missing database
**When** the script runs
**Then** it reports that there is no feedback yet instead of failing.

**Given** pytest
**When** the tests run
**Then** they cover a conversation with "no" followed by "yes", which counts as "no", and the date filter.
