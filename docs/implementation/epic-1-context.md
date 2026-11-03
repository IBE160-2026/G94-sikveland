# Epic 1 Context: Applicants get answers in Thai from official sources

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

An applicant opens a mobile chat page, taps an example question or types their own, and gets a Thai answer streamed bit by bit, grounded only in official sources and linking to them, including the application steps in order. Follow-up questions work, personal information is removed before anything reaches the AI service, and when the knowledge base has no answer the applicant gets the adviser contact. The epic also lays the foundation every later epic builds on: project skeleton, CI, the LLM port with fake and real adapters, the knowledge base and ingest script, fixed texts and cost logging.

## Stories

- Story 1.1: Project skeleton with CI
- Story 1.2: Chat page with Thai texts, privacy notice and example questions
- Story 1.3: Knowledge base of official sources
- Story 1.4: Personal information filter
- Story 1.5: Claude connection with a test version
- Story 1.6: Streamed answer with sources
- Story 1.7: Follow-up questions
- Story 1.8: Cost and request log

## Requirements & Constraints

- Answers in Thai, also for typos and mixed Thai/English; the page opens in Thai; follow-ups use earlier questions in the same conversation.
- Every model answer is based only on the knowledge base and shows at least one source link; no facts outside its sources. Zero citations means the fixed no-answer text with the adviser contact.
- When asked how to start, the steps come in order: documents → register at UDI → pay the visa fee → book at VFS, each with its website.
- Privacy: the page warns against sharing passport, ID or phone numbers and says questions go to an AI service. Those numbers are removed before any AI call and never stored; the rest of the question is still answered, with a reminder.
- Knowledge base: 10–20 official sources (UDI, VFS Global, Royal Norwegian Embassy in Bangkok, EU Schengen pages), each with URL, publisher and retrieval date; updated by a script; the adviser reviews diffs before commit.
- Mobile first, including Facebook's in-app browser; large touch targets, simple language.
- Runnable locally from the README with an own API key; demo mode (no key) arrives in Epic 4.
- Automated tests never call the real API and run in GitHub Actions.
- No conversation text stored anywhere on the server (disk, database, logs); no secrets or real enquiries in the repo.
- Cost per question is measured and reported; prompts are versioned files.
- All fixed Thai texts are reviewed by the adviser before release; note it in the pull request.

## Technical Decisions

- **Stack:** Python 3.12, uv (`pyproject.toml` + `uv.lock`), FastAPI 0.162, uvicorn 0.54, anthropic 2.4.0, pydantic-settings 2.16, PyYAML 6.0, httpx 0.28, markdownify 1.2, pypdf 6.21, pytest 9.2, SQLite from the standard library. Plain HTML/CSS/JS page, no framework. Start with `uv run uvicorn app.main:app`.
- **Layout:** `app/{web,pipeline,ports,adapters,static}`, `app/main.py` (wiring + startup checks), `app/config.py`; plus `content/`, `prompts/`, `knowledge-base/`, `scripts/`, `eval/`, `tests/` (with `tests/fakes/`), `data/`.
- **Dependency direction:** page → `app/web` over HTTP only; web → pipeline and config; pipeline → ports only (pure logic, no FastAPI or SDK imports); adapters → ports and config; `main.py` wires adapters.
- **SDK isolation:** only `app/adapters/anthropic_llm.py` imports `anthropic`; no SDK types leave it. `MOCK_LLM=true` wires the demo adapter. pytest always uses the scripted fake in `tests/fakes/`.
- **Pipeline order:** filter personal info → classify → route → answer or fixed reply. Nothing reaches the LLM before the filter. In this epic, classify is not yet built: every question is `general`.
- **LLM port:** `answer(question, history)` streams `{text, source_ids}` chunks then `Usage` (input, output incl. thinking, cache-read, cache-write). `classify` and `translate` are declared for later epics. Answers use `MODEL_ANSWER` (Claude Opus 5.5) with adaptive thinking and `EFFORT_ANSWER`, no sampling parameters; `stop_reason: "refusal"` is an error.
- **Answer request shape:** system prompt → every KB document sorted by source id, Citations on, cache breakpoint after the last document → history as plain text → question. Text is held back until the first citation; a started reply is never replaced.
- **Stream contract:** `POST /api/chat` returns JSON Lines; events `meta` (`category`, `personal_info_removed`, `clean_question`) → `text` (`delta`)* → `sources` (`[{id, title, url}]`, `checklist`, `checklist_purposes`) → `done`, or `error` ending the stream. Only `app/web` builds events. The page reads with `fetch` + `getReader()` + streaming `TextDecoder` and only appends text.
- **Stateless server:** history lives in the page's `sessionStorage`, sent as `{question, history: [{question, answer}]}`, max 10 exchanges, stored only after `done` using `clean_question`. The filter also runs on every history turn.
- **Fixed texts:** `content/texts.yaml`, closed key list with `th` and `en`; `{ADVISER_CONTACT}` filled at load; `GET /api/texts` returns `{demo_mode, texts, example_questions}`; no hard-coded Thai in the page.
- **Knowledge base:** `knowledge-base/sources.yaml` (`id`, `title`, `url`, `publisher`, `retrieved`, `file`) + Markdown snapshots from `scripts/ingest.py`; the app never fetches at runtime; startup fails if a snapshot is missing.
- **Config:** everything from `.env` via `app/config.py` (pydantic-settings): `ANTHROPIC_API_KEY`, `MODEL_ANSWER`, `MODEL_SMALL`, `EFFORT_ANSWER`, `EFFORT_SMALL`, `MOCK_LLM`, `ADVISER_CONTACT`, `DATABASE_PATH`, and `PRICE_ANSWER_*` / `PRICE_SMALL_*` (input, output, cache read, cache write; USD per million tokens). `.env.example` lists all; `.env` and `data/` are git-ignored.
- **Conventions:** kebab-case ids for sources, content keys and example questions; ISO 8601 dates, UTC timestamps; non-streaming errors use `{"error": {"code", "message"}}`; one JSON log line per request (category, prompt versions, usage, cost) with no question or answer text; prompts in `prompts/` start with a `version:` line. Code, identifiers, logs and docs in English; user-facing text in Thai with stored English.

## UX & Interaction Patterns

- No UX document; layout is decided in the chat-page stories, bound by mobile-first and the stream contract.
- The page shows the privacy notice, example questions as large tappable buttons, a text field and send button, a typing indicator until the first text, and source links under each answer.
- A real-phone check that streaming works in Facebook's in-app browser belongs to the streamed-answer story.

## Cross-Story Dependencies

- 1.1 is the base for everything (layout, config, CI). 1.2 and 1.3 provide `ContentStore` and `KnowledgeBase`; 1.4 the filter; 1.5 the LLM port, fake and real adapter; 1.6 combines them into `/api/chat` and the page; 1.7 adds history; 1.8 adds the request log on top of `Usage` from 1.5.
- Epic 2 adds `classify` and more fixed-text keys; Epic 3 the checklist flag in `sources`; Epic 4 `translate` and the demo adapter.
