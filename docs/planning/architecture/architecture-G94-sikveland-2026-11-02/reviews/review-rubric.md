---
reviewed: docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md
against: good-spine checklist (divergence coverage, enforceable rules, safe deferrals, verified tech, PRD coverage, dimension coverage incl. operational envelope)
inputs: ARCHITECTURE-SPINE.md, .memlog.md, prd-G94-sikveland-2026-10-19/prd.md, addendum.md, implementation-plan.md
calibration: IBE160 course prototype; runs locally and in demo mode; hosting out of scope (PRD 8.2)
date: 2026-11-02
---

# Architecture Spine Review: Norway Visa Guide For Thai

## Verdict

**Revise before epics.** The spine is strong. The paradigm is clear, the dependency rules work, and 13 ADs cover most real divergence points. It traces every FR in the PRD, and the hosting deferral is justified. Two issues should be fixed before stories are cut. First, AD-7 and AD-8 contradict each other: an answer can't be replaced after it has already been streamed. Second, demo mode, which is the examiner's main path, has no rules for how stored answers are matched or what the mock returns. The remaining findings are contract gaps of medium size and small tidy-ups.

| Severity | Count |
| --- | --- |
| Critical | 0 |
| High | 2 |
| Medium | 9 |
| Low | 10 |

## Checklist summary

| Check | Result |
| --- | --- |
| Fixes the real divergence points, misses none | Mostly. Gaps: demo-mode matching (H2), the request and event wire shape (M3), the feedback client/server split (M4), classifier input (M5), how the checklist is reached from chat (M1) |
| Every AD Rule is enforceable and prevents its divergence | Mostly. AD-7 is not implementable together with AD-8 (H1). AD-7's caching rule doesn't fix document placement, so it doesn't prevent the cache misses it names (M6). AD-4's flag misfires on resent history (M2) |
| Nothing under Deferred lets two units diverge | Pass. All five deferrals are either inside one unit or out of scope |
| Named tech verified-current | Pass for the core packages (PyPI check 2026-11-02 in memlog: anthropic 2.4.0, fastapi 0.162.0, uvicorn 0.54.0, pytest 9.2.0; Citations+caching and Citations-vs-structured-output checked against the Claude docs). Supporting libraries are missing (M9) |
| Covers the PRD's capabilities | Pass at map level (FR1–FR14 all mapped). Behavioural gaps in FR6/UJ-1 (M1), FR10 (H2), FR11 traceability (L2) |
| Every owned dimension decided / deferred / open | Mostly. Environments and hosting are handled. Local operations is thin: entrypoint, run command, dependency/lock file, gitignore, DB init, phone access (M8) |

## Findings

### High

#### H1. AD-7 "replace zero-citation answers" contradicts AD-8 streaming

- **Location:** AD-7 Rule ("An answer that comes back with zero citations is replaced by the fixed no-answer reply"); AD-8 Rule (`text` deltas streamed, `sources` at the end).
- **Problem:** Once the answer is streaming, the text deltas reach the page before anyone knows whether the answer has any citations. By the time the stream ends with zero citations, the uncited answer is already on screen. The two ADs can't both be met as written. One developer will buffer the whole answer, which loses streaming. Another will stream and then append the no-answer reply, which shows an uncited answer and breaks FR2/FR4. The page story and the answer story will diverge.
- **Fix:** Add a rule to AD-7/AD-8: "The answer step holds back `text` events until the first citation arrives in the model stream (`citations_delta`). From then on it flushes the held-back text and streams normally. If the model stream ends with no citation, the held-back text is discarded and the fixed no-answer reply is sent as one `text` event. Text the page has received is never withdrawn." The mock adapter must reproduce both paths so pytest covers them. (The alternative is a `replace` event the page must honour. That is weaker, because the uncited text is still shown briefly.)

#### H2. Demo mode (FR10) has no matching or mock-behaviour rules

- **Location:** AD-2 (only "the mock produces the same stream events"); AD-5 (closed category set); AD-6 (fixed-text list); Source tree (`content/demo-answers.yaml`); Environments table.
- **Problem:** Demo mode is how the examiner runs the app (no API key), and pytest also depends on the mock. Several things are undecided, and each one splits stories:
  - How a question is matched to a stored answer: exact Thai text, or an example-question ID sent by the page?
  - What the mock classifier returns. If it always returns `general`, FR3/FR14 can't be demonstrated. If it uses keywords, that contradicts the memlog's "no keyword list".
  - Where the FR10 "demo mode only answers the example questions" Thai message comes from. It isn't in AD-6's list, and AD-5 has no category or `meta` value for it.
  - How the mock translation finds its stored translation.
  - How the page learns that it is in demo mode so it can show the "Demo mode" label.
  - Whether pytest uses the same demo-answers mock or a scripted fake that can force each category.

  The example-questions content story, the mock adapter story, the page story and the test story will each make their own choice.
- **Fix:** Add an AD "Demo mode contract":
  1. Each example question in content has a kebab-case `id`. `demo-answers.yaml` is keyed by the same `id` and holds the Thai answer, `sources` (source IDs) and the English translation.
  2. The mock matches the cleaned question by exact normalised text to an example question (or the page sends `example_id`; pick one).
  3. On a match, the mock classifier returns the stored category, so the example set can include one embassy-decides and one out-of-scope example. On no match, the pipeline sends the fixed `demo-only` content text with `meta.category = "demo_only"`. Add that value to AD-5's closed set, or add a separate `meta.mode` field.
  4. The mock translation returns the stored translation by answer ID.
  5. `GET /api/texts` (or `meta`) carries `demo_mode: true` for the label.
  6. pytest uses an injectable scripted `LLMClient` fake for category and citation paths, and the demo mock for end-to-end demo tests.

  Also add the demo-only message to AD-6's list of content texts.

### Medium

#### M1. No path from a chat question to the checklist (FR6, UJ-1 step 3)

- **Location:** Capability map row FR6 (content, web, static only); AD-5; AD-11.
- **Problem:** In UJ-1, Fah *asks* which documents she needs and *gets* the family checklist. In the spine, the checklist is reachable only through `GET /api/checklists/{purpose}`. No category, event or answer convention connects a chat question to it. A general answer about documents would be model-written prose, which competes with the fixed, adviser-reviewed checklist (NFR8). The chat story and the checklist story will pick different entry points.
- **Fix:** Decide one entry point and write it into AD-11. Option (a): the checklist is opened only from page controls (purpose picker), and the answer prompt points to it. Option (b): add a `checklist` category (AD-5) whose fixed reply is a content text plus a `meta.checklist_purpose`, and the page opens that checklist. Option (b) matches UJ-1 more closely. Purpose detection then needs to be either in the classifier's structured output or a purpose picker in the reply.

#### M2. `personal_info_removed` fires on every turn after the first leak

- **Location:** AD-4 Rule ("runs on every text … every history turn … If anything was removed, the stream's `meta` event carries `personal_info_removed: true`"); AD-3 (history lives in `sessionStorage`).
- **Problem:** The page stores the raw text the applicant typed and sends it back as history every turn. Once one message contains a passport number, every later request finds personal info in the history, so the flag is true and the reminder is shown again on every answer. The raw personal information also stays in `sessionStorage` and is shown in the chat, even though FR9 says it is "deleted".
- **Fix:** In AD-4, set `personal_info_removed` from the *new question only*. Also add a `cleaned_question` field to `meta` (or a dedicated event). The page then replaces the stored and shown user turn with that text, so `sessionStorage` never keeps the raw value. Keep filtering history on the server as defence in depth.

#### M3. The wire contract is only half-fixed (request bodies, event shape, other endpoints)

- **Location:** AD-8; Consistency Conventions (Endpoints, Errors).
- **Problem:** AD-8 fixes the event *names*, but several parts of the contract are left open, and the page story and the web story can each pick their own:
  - The discriminator key (`type`, `event`?).
  - The fields of the `error` event and of `done`.
  - The `/api/chat` request body: the shape of `question` and `history`, roles, whether fixed replies are included in history, and any limit on turns.
  - The `/api/translate` request and response.
  - The `/api/texts` and `/api/checklists/{purpose}` response shapes. For example, does a checklist item include the source `url`/`title`, or only its `id`?
- **Fix:** Add a small "Wire shapes" table:
  - Each NDJSON line is `{"type": "...", ...}`.
  - `error` = `{"type":"error","code":"...","text_key":"..."}`.
  - Chat request = `{"question": str, "history": [{"role": "user"|"assistant", "text": str}], "example_id"?: str}`, with history capped at N turns.
  - Translate = `{"text": str}` → `{"text": str}`.
  - Texts = `{"demo_mode": bool, "texts": {key: str}, "examples": [{id, text}]}`.
  - Checklist items carry `source: {id, title, url}`.

  Pydantic models in `app/web/` are the single definition, and `app/static/` follows them.

#### M4. Feedback loop: client/server split and the `conversation_id` lifecycle are undecided

- **Location:** AD-5 (`done` triggers the feedback question); AD-6 (feedback question and follow-up are content); AD-10 (`conversation_id` "a random ID the page creates").
- **Problem:** Several points are open:
  - Does tapping **No** send a chat message, call `/api/feedback`, or both?
  - Is "What would you still like to know?" shown by the page from `/api/texts`, or sent by the server?
  - Do the Yes/No taps enter the history?
  - What does "Yes ends the conversation" do on the page?
  - When is a new `conversation_id` made: per page load, per `sessionStorage` life, or after **Yes**?

  SM-1 counts the *first* answer per `conversation_id`. If the ID outlives a **Yes**, later conversations are miscounted, and if it is regenerated on every reload, one conversation is counted twice.
- **Fix:** Extend AD-10 as follows:
  - On `meta.category = done`, the page shows Yes/No buttons.
  - A tap calls only `POST /api/feedback`, with `{conversation_id, answer}`.
  - **No** makes the page show the `feedback-follow-up` text from `/api/texts`. It is not a chat request, and the taps never enter the history.
  - **Yes** makes the page show a closing text, clear the conversation in `sessionStorage` and create a new `conversation_id`.
  - The `conversation_id` lives in `sessionStorage` next to the conversation.

#### M5. Classifier input is undefined (history or not)

- **Location:** AD-1, AD-5.
- **Problem:** Follow-ups (FR1) such as "and for my aunt?" can't be classified without context. Short messages such as "okay" are `done` at the end of a conversation, but may be an acknowledgement in the middle. Messages that mix a done signal with a new question are also common (the UJ-2 dialogue: "Thank you very much. If I cannot manage…"). The classifier-prompt story and the pipeline story will choose different inputs, and eval results will move with that choice.
- **Fix:** State in AD-5 that the classifier receives the cleaned new question plus the last N cleaned turns. Also give a precedence rule for mixed messages: any request for information outranks `done`, and `individual_assessment` outranks `general`.

#### M6. AD-7's caching rule doesn't fix document placement, so it doesn't prevent the cache misses it names

- **Location:** AD-7 Rule ("prompt caching on the documents"); Prevents: "cache misses from changing request shape".
- **Problem:** Citations need the documents as `document` blocks inside a user message. If one implementation attaches them to the *latest* user turn, the cached prefix changes on every follow-up and caching never hits. NFR6 cost is then badly overstated, and nothing in the rule stops this. Document order and the system prompt position also affect the cache key.
- **Fix:** Add to AD-7:
  - Request layout is system prompt → first user message holding all knowledge-base documents in `sources.yaml` order (each `title` = source `id`), with `cache_control` on the last document → history turns → new question.
  - The documents and their order are built once at startup and reused byte for byte.
  - The document index maps back to source `id` through that order.

#### M7. The evaluation may bypass the pipeline it is meant to measure

- **Location:** AD-13 ("runs `eval/testset.yaml` against the real model"); AD-12 (eval reports record prompt versions).
- **Problem:** NFR4 measures embassy-decides (100%), out-of-scope and personal-information handling. These are produced by the filter, the classifier and the routing, not by the answer call. If `run_eval.py` calls the LLM directly, as "against the real model" allows, those targets are untested. The report contents (sources cited, cost, source versions) aren't fixed either, so SM-2 and NFR6 reporting can drift.
- **Fix:** In AD-13, require that `run_eval.py` drives the same pipeline entry that `/api/chat` uses, in process, with the real adapter. Each report row records: question id, category, `personal_info_removed`, answer text, cited source ids + `retrieved` dates, tokens and cost, and prompt versions. The report header records the model and the git commit. Correctness is judged afterwards by the adviser (NFR4), in a column in the report.

#### M8. The local operations envelope is thin

- **Location:** Structural Seed (Environments, Source tree, Runtime view); Conventions (Config); Deferred (hosting).
- **Problem:** Hosting is correctly deferred, but *running locally* is in scope (NFR2), and several of its pieces are left silent:
  - There is no app entrypoint in the source tree (no `app/main.py` or app factory), even though "web wires adapters at startup".
  - There is no run command (`uvicorn app.main:app …`).
  - There is no dependency manifest or lock decision (`requirements.txt` vs `pyproject.toml` + lock).
  - The CI Python version isn't stated.
  - There is no rule that `.env` and the SQLite file are git-ignored (NFR5: "no secrets … in the repository").
  - There is no rule for how the feedback table is created (create on startup?).
  - There is no startup check (e.g. `MOCK_LLM=false` with no key → fail fast with a clear message).
  - The Runtime view shows a *phone* browser calling a *local* uvicorn, but doesn't say how the phone reaches it (bind `0.0.0.0` on the LAN, or a tunnel). That matters for testing NFR1 on a real phone, and LAN binding exposes a paid-API endpoint without any limit.
- **Fix:** Add an "Operations (local)" block:
  - The entrypoint is `app/main.py:create_app()`, and the run command is `uvicorn app.main:app`.
  - Dependencies go in `pyproject.toml` with pinned versions, and CI uses Python 3.12.
  - `.gitignore` covers `.env` and `data/*.db`.
  - The feedback table is created on startup with `CREATE TABLE IF NOT EXISTS`.
  - Startup validates the settings and fails fast.
  - Phone testing: `--host 0.0.0.0` on a trusted LAN only, preferably in demo mode. Facebook in-app browser testing is deferred with hosting.

#### M9. The stack table leaves out libraries that several stories will need

- **Location:** Stack.
- **Problem:** The spine uses YAML everywhere (`sources.yaml`, `checklists.yaml`, `demo-answers.yaml`, `testset.yaml`) but names no YAML library. It names no settings library for `app/config.py` and `.env` (pydantic-settings or python-dotenv), no HTTP client for `scripts/ingest.py` (FastAPI's `TestClient` also needs `httpx`), and no HTML→Markdown converter. It also names no PDF text extraction, even though the implementation plan expects "HTML and PDF sources" and the embassy checklists are often PDFs. Each story will pick its own, and none of these versions were checked on PyPI.
- **Fix:** Add rows for PyYAML (or ruamel.yaml), pydantic-settings, httpx, one HTML→Markdown library and one PDF extraction library. Verify the versions with `pip index versions` as was done for the core packages, and record them in the memlog.

### Low

#### L1. Source metadata doesn't match what the stream and checklist need

- **Location:** AD-9 (`sources.yaml`: `id`, `url`, `publisher`, `retrieved`, snapshot); AD-8 (`sources` events carry `{id, title, url}`); AD-11 (items carry a source `id`).
- **Fix:** Add `title` (Thai or original) to the `sources.yaml` fields. State that the checklist endpoint resolves source `id` to `{id, title, url}`.

#### L2. FR11 "every answer traceable to a source version" is not carried anywhere

- **Location:** AD-9 ("A source's version is its `retrieved` date"); AD-8 `sources` event.
- **Fix:** Add `retrieved` to the `sources` event items and to the eval report (M7). Production answers aren't stored (AD-3), so the eval report together with the git history is the trace.

#### L3. The format of the content files is open

- **Location:** AD-6; Source tree (`content/` "fixed Thai texts").
- **Fix:** Name the file and shape, e.g. `content/texts.yaml` as a flat `key: Thai text` map with kebab-case keys. List the required keys (`embassy-decides`, `out-of-scope`, `no-answer`, `reach-person`, `pii-reminder`, `feedback-question`, `feedback-follow-up`, `privacy-notice`, `demo-only`, `error-generic`). Startup fails if one is missing.

#### L4. The `demo-answers.yaml` location differs from the PRD addendum

- **Location:** Source tree (`content/demo-answers.yaml`) vs addendum ("`eval/demo-answers.yaml`").
- **Fix:** `content/` is the better home (NFR8 review set). Record that this is a deliberate change in the spine or memlog, and update the addendum reference so stories don't follow the old path.

#### L5. The prompt version format and the owner of prompt loading are unstated

- **Location:** AD-12; Dependency direction (pipeline → ports only, but prompts are files).
- **Fix:** Fix the format, e.g. YAML front matter `version: 3` in `prompts/<name>.md`. Assign loading to an adapter behind a port (e.g. a `PromptStore`, or `ContentStore` extended) so the pipeline stays free of file I/O. The adapter exposes `(text, version)` for the logging.

#### L6. The source of the cost calculation is undecided

- **Location:** Conventions (Logging: "cost"); NFR6 map row.
- **Fix:** Put the per-model token prices (input, output, cache write, cache read) in config with the current Opus 5.5 values. Cost is computed in one place (the LLM adapter returns usage, and the web layer logs it). The README figure comes from eval reports.

#### L7. Storage in Facebook's in-app browser is an unrecorded risk for FR6/NFR1

- **Location:** AD-11 (`localStorage`); NFR1.
- **Fix:** Add an open question or deferred item. In-app browser storage is separate from Safari/Chrome and may not be kept across visits, so ticks may not survive for a user who arrives sometimes via Facebook and sometimes directly. Verify this when the page is hosted. It can't be tested locally.

#### L8. Python 3.12 is in security-only support; the pin policy is unstated

- **Location:** Stack.
- **Fix:** Keeping 3.12 is reasonable, because it matches the local install (3.12.10, memlog). Note it as a deliberate choice, and state that versions are pinned to the PyPI-verified versions in `pyproject.toml` (M8).

#### L9. Rules AD-2 and AD-3 could be checked by machine

- **Location:** AD-2 ("only `anthropic_llm.py` imports `anthropic`"); AD-3 / Logging ("never question or answer text").
- **Fix:** Add to AD-13 two guard tests. One is an import scan that fails if `anthropic` is imported outside the adapter. The other is a `caplog` test that sends a marked question and asserts the marker never appears in logs.

#### L10. The no-answer and fixed-reply outcomes can't be told apart in logs or on the page

- **Location:** AD-7 (no-answer arrives as category `general` with empty sources); Logging convention; FR7 (translate button).
- **Fix:** Add `outcome` (`answered` | `no_answer` | `fixed`) to the request log line, and optionally to `meta`. The no-answer rate can then be measured, and the page can decide whether to offer translation on fixed replies (or always offer it — decide).

## What is good (keep)

- The pipeline paradigm, with fixed replies separated from model-written answers (AD-1, AD-6), makes FR3/FR4/FR13/FR14 deterministic and testable.
- Classifying with structured output and answering with Citations in separate calls is grounded in a verified API constraint (memlog).
- Keeping the server stateless with the conversation in the browser (AD-3) and feedback as the only server data (AD-10) is clean for NFR5.
- Stable checklist item IDs (AD-11) directly solve "ticks survive content updates".
- The deferrals are well chosen. None of them lets two units diverge, and hosting is deferred with a clear trigger.
