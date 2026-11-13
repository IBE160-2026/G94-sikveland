# Epic 1 Context: Applicants get answers in Thai from official sources

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A Thai applicant opens the mobile chat page, taps an example question or types their own, and gets a Thai answer streamed bit by bit with links to the official sources it is based on, including the application steps in order when they ask how to start. Follow-up questions work, personal information is removed before anything reaches the AI service, and when the knowledge base has no answer the applicant gets the adviser contact instead of a guess. The epic also lays the foundation every later epic builds on: project skeleton, CI, the LLM port with a scripted test fake and a real Anthropic adapter, the knowledge base, fixed texts and cost logging. It is the top of the build priority: the core must work end to end before checklist, feedback or translation work starts.

## Stories

- Story 1.1: Project skeleton with CI (done)
- Story 1.2: Chat page with Thai texts, privacy notice and example questions (done)
- Story 1.3: Knowledge base of official sources
- Story 1.4: Personal information filter
- Story 1.5: Claude connection with a test version
- Story 1.6: Streamed answer with sources
- Story 1.7: Follow-up questions
- Story 1.8: Cost and request log

## Requirements & Constraints

- **Thai in, Thai out.** The page opens in Thai; answers are in Thai also for questions with typos or mixed Thai/English. Follow-ups use earlier exchanges from the same conversation.
- **Grounded answers only.** Every model answer is based only on the knowledge base and shows at least one source link; it contains no facts not in its sources. Fixed replies need no source link.
- **No-answer handling.** An in-scope question that no source answers (the answer would cite nothing) gets the fixed no-answer message with the adviser contact and no claims about requirements, fees or deadlines. This must hold for 100% of such questions in the test set (at least four).
- **Application steps.** "How do I start?" gets the steps in this order, each naming and linking its website: prepare documents (embassy checklist) → register at UDI → pay the visa fee → book an appointment at VFS.
- **Example questions.** 3–5 example questions shown as large buttons; tapping one sends it immediately without typing.
- **Privacy.** The page states, in Thai, not to share personal information, that questions go to an AI service, and that names and addresses are not removed automatically. Removed before any AI call and never stored: 13-digit Thai ID (with or without dashes/spaces), passport numbers, Thai phone numbers (08x-xxx-xxxx, +66) and Norwegian phone numbers. Amounts ("90 euro") and dates must survive. When something is removed, the applicant sees a reminder and the rest of the question is still answered.
- **Knowledge base.** 10–20 official sources only (UDI, VFS Global, Royal Norwegian Embassy in Bangkok, EU Schengen pages), each with URL, publisher and retrieval date; covers application steps, document requirements per visit purpose, sponsorship form and invitation letter, relationship proof and the visa fee. The adviser reviews changes before use; every answer is traceable to a source version (its retrieval date).
- **Mobile first.** Works from 360 px width with no horizontal scroll down to 320 px; touch targets at least 44×44 px; simple language. Streaming must be verified on a real phone in Facebook's in-app browser and noted in the PR.
- **Safe tests.** pytest runs in GitHub Actions and never calls the real API.
- **Nothing stored.** No conversation text on disk, in a database or in logs; no secrets or real applicant enquiries in the repo.
- **Cost.** Cost per question is measured and logged; cache use must be visible.
- **Adviser review.** Every fixed Thai text (example questions, privacy notice, no-answer, reminder, error) is reviewed by the adviser before release and noted in the PR.

## Technical Decisions

- **Stack:** Python 3.12 with uv, FastAPI, uvicorn, anthropic SDK, pydantic-settings, PyYAML, pytest, plain HTML/CSS/JS page (no framework). Ingest uses httpx, markdownify and pypdf. Models: `MODEL_ANSWER` = Claude Opus 5.5 for answers; `MODEL_SMALL` = Claude Haiku 5.5 for classify/translate (later epics).
- **Layers:** `app/web` (routes, stream events, logging), `app/pipeline` (pure logic, no FastAPI/SDK imports), `app/ports` (`LLMClient`, `KnowledgeBase`, `ContentStore`, `FeedbackStore`), `app/adapters`, `app/static`. `app/main.py` wires adapters and runs startup checks.
- **Fixed pipeline order:** filter personal info → classify → route → answer or fixed reply. Nothing reaches the LLM before the filter. In this epic there is no classifier yet: every question is treated as `general`.
- **LLM port:** `answer(question, history)` yields `{text, source_ids}` chunks then `Usage` (input, output incl. thinking, cache-read, cache-write). `classify` and `translate` are declared but implemented in later epics. Adapters return no SDK types; only `app/adapters/anthropic_llm.py` imports `anthropic`. A refusal stop reason is raised as an error. Adaptive thinking with effort from config; no sampling parameters.
- **Answer request shape (fixed, for caching):** system prompt → all KB documents sorted by source `id`, Citations on, cache breakpoint after the last document → history as plain-text alternating user/assistant turns → question. Citations become source IDs.
- **Grounding rule in the pipeline:** hold back answer text until the first cited chunk arrives, then stream held text and the rest. Zero citations at the end → discard held text and send `reply-no-answer`. A reply that has started streaming is never replaced. Shown sources are exactly the cited ones.
- **Stream contract:** `POST /api/chat` with `{question, history: [{question, answer}]}` returns JSON Lines. Events: one `meta` (`category`, `personal_info_removed`, `clean_question`) → zero or more `text` (`delta`) → one `sources` (`[{id, title, url}]`, `checklist`, `checklist_purposes`; in this epic always `false` / `[]`) → `done`. `error` can replace any later event and ends the stream. A fixed reply is one `text` event. Only `app/web` builds events. The page reads with `fetch` + `getReader()` + streaming `TextDecoder`, only appends text, and shows a typing indicator until the first `text`.
- **Stateless server:** the conversation lives in the page's `sessionStorage`; at most the last 10 exchanges are sent. The page stores an exchange only after `done` (never after `error`), using `clean_question` and the exact shown text, fixed replies included. Reload in the same tab keeps it; closing the tab drops it.
- **Personal-info filter:** pattern-based, pure logic, runs on the new question and every history turn (and later translate input). `personal_info_removed` describes the new question only. Matches are replaced with a neutral marker. Exact patterns are an implementation detail but must pass the tests and test set.
- **Fixed texts:** `content/texts.yaml`, closed key list, each with `th` and `en`; `{ADVISER_CONTACT}` filled at load. Keys used here: `privacy-notice`, `personal-info-reminder`, `reply-no-answer`, `error`, `demo-label`. `GET /api/texts` returns `{demo_mode, texts, example_questions: [{id, text}]}`. No hard-coded Thai in the page.
- **Knowledge base:** `knowledge-base/sources.yaml` (kebab-case `id`, `title`, `url`, `publisher`, `retrieved`, `file`) plus committed Markdown snapshots. `scripts/ingest.py` runs offline, writes snapshots, updates `retrieved`, reports changed and failed sources (keeping old snapshots). The app never fetches at runtime and refuses to start if a source lacks a snapshot. Every link shown must be a source in this file.
- **Prompts:** `prompts/answer-system.md` starts with a `version:` line; it instructs Thai answers, documents only, and the ordered application steps with websites.
- **Logging and cost:** `app/web` writes one JSON line per request: timestamp, category, prompt versions, model, input/output/cache-read/cache-write tokens, cost in USD. Never question or answer text. Each call is priced with its model's `PRICE_ANSWER_*` / `PRICE_SMALL_*` settings (USD per million tokens), with cache reads and writes priced separately.
- **Conventions:** config only via `app/config.py` from `.env` (`.env.example` lists all settings); `.env` and `data/` git-ignored; kebab-case IDs; ISO 8601 dates, UTC timestamps; non-streaming errors use `{"error": {"code", "message"}}`; the applicant always sees the fixed `error` text. Code, identifiers, logs and docs in English; user-facing text in Thai with stored English.
- **Tests:** a scripted fake `LLMClient` in `tests/fakes/` can return chunks with or without source IDs, errors or refusals; tests cover the cited, zero-citation and error paths, filter patterns and false positives.

## UX & Interaction Patterns

- No UX design document; layout is decided in the stories, bound by the mobile-first constraints and the stream contract.
- Page shows: privacy notice, example-question buttons, text field and send button, streamed answer with source links underneath, typing indicator until text arrives.
- When personal info was removed, the fixed reminder appears above the reply.
- On error, the fixed `error` text is shown and the exchange is not kept in history.

## Cross-Story Dependencies

- Build order: 1.3–1.8 finish the core, then 2.1 ("the embassy decides"), 4.2 (demo mode) and 4.3 (README) so the examiner can run the app early. If time is short, Story 1.3 can start with hand-made snapshots and add the ingest script last.
- 1.5 needs the knowledge base (1.3) for the answer request; 1.6 needs the filter (1.4), the LLM port and fake (1.5) and texts from 1.2; 1.7 builds on 1.6's stream and `meta.clean_question`; 1.8 needs `Usage` from 1.5 and price settings from 1.1.
- Later epics extend this epic's pieces: Epic 2 adds the classifier and new fixed-reply categories into the same pipeline and logs its usage; Epic 3 fills `checklist`/`checklist_purposes` in the `sources` event; Epic 4 adds `translate`, the `mock_llm` demo adapter and README; Epic 5 runs the test set through the same pipeline entry point. Keep the port, stream contract and pipeline entry stable for them.
