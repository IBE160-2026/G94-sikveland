---
title: 'Story 4.2: Demo mode without an API key'
type: 'feature'
created: '2026-11-14'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '44478eb3f7b06241725f666b1fbaa0b6bd77464f'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The examiner cannot try the app without an Anthropic API key: with `MOCK_LLM=true` the app still wires the real adapter and every answer fails.

**Approach:** With `MOCK_LLM=true` the app wires a `mock_llm` adapter (AD-2, AD-15) that answers the example questions from `content/demo-answers.yaml` through the same pipeline and stream as a real answer, sources included. Any other question gets the fixed `reply-demo-only` text. The page always shows the `demo-label`.

**Decisions (user, 2026-11-14):** (1) The data is built now and the UI comes later. `demo-answers.yaml` holds the English translations and a `done_phrases` list, and the mock implements `classify` (done phrase → `done`) and `translate` (stored `en`). The feedback question (Story 2.3) and the "Show English" button (Story 4.1) use them when those stories are built; until then they have no visible effect. (2) Claude drafts the Thai demo answers and `reply-demo-only` only from the knowledge-base snapshots. The commit waits until the user confirms that the adviser has approved the Thai (NFR8).

## Boundaries & Constraints

**Always:** the mock matches after Unicode NFC normalisation, trimming and collapsing whitespace runs to one space, against each example question's `th` (and `en`). A match streams the stored Thai answer in several chunks; the first chunk carries every stored source id. The answer ends with `Usage(0, 0, 0, 0)`. In demo mode, startup fails if an example question has no demo answer, a demo answer cites an unknown source id or has an invalid category, or `done_phrases` is missing or empty. The demo answers state only facts found in their cited snapshots. In demo mode the request log records `model: "mock_llm"` and `cost_usd: 0.0`. The mock never imports `anthropic` and makes no network call.

**Never:** no feedback question or "Show English" UI (Stories 2.3 and 4.1); no demo answers read outside `mock_llm`; no change to the real-mode behaviour; no Thai committed before the adviser's approval.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Example tapped | demo mode, question = example `th` | `meta` → several `text` → `sources` (the stored ids, titles and URLs) → `done`; text equals the stored `th` | N/A |
| Spacing / Unicode form | example `th` with extra spaces, NFD form, or its `en` | same answer as the example | N/A |
| Other question | demo mode, any other text | `meta` → one `text` = `reply-demo-only` → `sources []` → `done` | N/A |
| Personal info | example text plus a passport number | the filter runs first; the clean text no longer matches → `reply-demo-only`; reminder flag true | N/A |
| Done phrase | `classify("ขอบคุณค่ะ", [])` | `("done", Usage(0,0,0,0))` | N/A |
| Translate | `translate(<stored th answer>)` or a fixed text's `th` | the stored `en`; unknown text → `en` of `reply-demo-only` | N/A |
| Texts API | demo mode | `demo_mode: true`; the page shows `demo-label` always visible | N/A |
| Missing demo answer | example id without an entry | app does not start (`DemoContentError`) | message names the id |
| Unknown source | demo answer cites an id not in `sources.yaml` | app does not start | message names both ids |
| Real mode | `MOCK_LLM=false` | unchanged; `demo-answers.yaml` not read | N/A |

</frozen-after-approval>

## Code Map

- `app/main.py` -- `create_app(settings, llm)`; today `llm or AnthropicLLM(...)`. In demo mode (and no `llm` passed) build the mock from `content/demo-answers.yaml`; the request log's model name and the no-answer text depend on the mode.
- `app/web/chat.py` -- passes `content.texts()["reply-no-answer"].th` as `no_answer_text`; in demo mode pass `reply-demo-only`. `log_request` uses `settings.model_answer` and `answer_prices(settings)`.
- `app/ports/llm.py` -- `LLMClient`, `AnswerChunk`, `Usage`, `Category`. Reuse.
- `app/ports/content.py` -- `REQUIRED_TEXT_KEYS`; add `reply-demo-only`. `ExampleQuestion(id, th, en)`.
- `app/adapters/file_content.py` -- YAML loading style to copy (duplicate-key loader, unknown fields rejected, `th` must contain Thai).
- `content/texts.yaml` -- add `reply-demo-only` (`th`/`en`; may use `{ADVISER_CONTACT}`).
- `knowledge-base/*.md` -- snapshots the demo answers must be drawn from; `sources.yaml` ids.
- `app/static/index.html`, `app.js`, `style.css` -- `render(data)` gets `demo_mode`; no Thai in static files.
- `tests/fakes/fake_llm.py`, `tests/test_chat_api.py` -- patterns for API tests.

## Tasks & Acceptance

**Execution:**
- [x] `content/demo-answers.yaml` -- `answers:` keyed by example id (`category`, `th`, `en`, `sources`) and `done_phrases:` (Thai and English thank-you/OK variants). The Thai drafts use only facts from the cited snapshots; `how-to-start` gives the four steps in order with websites.
- [x] `content/texts.yaml`, `app/ports/content.py` -- `reply-demo-only` ("demo mode only answers the example questions"), Thai draft and English.
- [x] `app/adapters/file_demo_answers.py` -- load and validate per the matrix (`DemoContentError`); immutable result.
- [x] `app/adapters/mock_llm.py` -- `MockLLM` implementing `answer`, `classify`, `translate` per the Boundaries and the matrix.
- [x] `app/main.py`, `app/web/chat.py` -- demo wiring, `reply-demo-only` as the no-answer text, log model `mock_llm` with zero cost.
- [x] `app/static/index.html`, `app.js`, `style.css` -- demo label shown at the top when `demo_mode` is true, always visible (sticky), no Thai in the files.
- [x] `tests/test_demo_answers.py`, `tests/test_mock_llm.py`, `tests/test_demo_mode.py` -- every matrix row; the committed `demo-answers.yaml` loads against the real example questions and knowledge base; each Thai answer contains Thai.

**Acceptance Criteria:**
- Given `MOCK_LLM=true` and no key, when I run `uv run uvicorn app.main:app` and tap each example question, then a Thai answer streams with source links, and the demo label stays visible while scrolling.
- Given `uv run pytest`, when it runs, then all tests pass.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass.

**Manual checks:**
- Start with `MOCK_LLM=true`, open the page at 360 px, tap all four examples, type another question (→ demo-only text).

## Implementation Notes

- **Wiring (`app/main.py`).** In demo mode `demo-answers.yaml` is loaded and checked even when a test passes its own `llm`, like the answer prompt, so a broken file always stops startup; the mock is built only without `llm`. `app.state.no_answer_key`, `answer_model` and `answer_prices` carry the mode to `app/web/chat.py`: demo mode uses `reply-demo-only`, model `mock_llm`, zero prices and zero usage when none arrived (`fallback_usage`), so `cost_usd` is `0.0` on every demo line: also when a test LLM reports tokens, the answer fails or the client leaves early.
- **No-answer path.** For any other question the mock yields only `Usage(0, 0, 0, 0)`; the pipeline's zero-citation rule then sends `reply-demo-only`. No change to `app/pipeline/answer.py`.
- **Streaming.** A stored answer is cut into chunks of three space-separated words (Thai separates phrases with spaces, so no word or combining mark is split), all source ids on the first chunk. `DEMO_CHUNK_PAUSE_SECONDS = 0.05` in `app/main.py` waits between chunks so the page shows the answer arriving bit by bit; tests set it to 0.
- **Matching.** NFC, trim, whitespace collapse (`str.split()`, so NBSP and tabs count) and case folding, against each example's `th` and `en` and the done phrases alike (`OK`, `thank you`, a lower-case English example). `classify` returns the stored category for an example question and `general` otherwise.
- **Translate.** Covers the demo answers, every fixed text and the example questions; anything else gets the English `reply-demo-only`.
- **Loader checks beyond the matrix.** `category` must be a string and not `done` (it ends a conversation, it is not an answer category). Answers for ids that are not example questions, unknown fields, empty or duplicate `sources`, `th` without Thai and blank done phrases are also rejected.
- **Page.** `#demo-label` sits above `<main>`, `position: sticky; top: 0`, hidden unless `demo_mode` is `true`; text from `texts["demo-label"]`.
- **Thai drafts (not adviser-approved).** `content/demo-answers.yaml` (four answers, Thai done phrases) and `reply-demo-only` in `content/texts.yaml` are drafts from the cited snapshots only: tourist documents from `embassy-visitor-visa-checklist` and `embassy-hand-in-documents`; steps from `embassy-necessary-documents`, `udi-how-to-apply-visitor-visa` and `embassy-online-registration`; fee from `embassy-online-registration` and `udi-fees`; processing time from `embassy-processing-time` and `udi-waiting-time-visitor-visa`. Do not commit until the adviser has approved the Thai (NFR8).

## Spec Change Log

## Review Triage Log

Pass 1 (2026-11-14; plus one finding from the orchestrator's source check):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | blind | `tourist-visa-documents` presents a partial checklist as complete | medium | the cited checklist also has a name-change certificate, a section for minors and more. patched (main documents + pointer to the full checklist) |
| 2 | blind | Item 10 makes bank statements mandatory; the source allows "other proof of sufficient means" | medium | `embassy-visitor-visa-checklist.md:47`. patched |
| 3 | blind, orchestrator | Fee exemption worded loosely ("apply as a family member") and presented as the only one | medium | `udi-fees.md:34` says travel with or visit a close family member who is an EU/EEA national; other groups listed. patched |
| 4 | blind | "45 days" drops "calendar" | low | `embassy-processing-time.md:3`. patched |
| 5 | edge | Non-string `category` raises an unhashable `TypeError`, not `DemoContentError` | low | `frozenset` membership on a list. patched |
| 6 | blind | Loader accepts `category: done` for a stored answer | low | `done` would turn an example into the feedback trigger. patched (rejected) |
| 7 | blind, edge | English examples match case-sensitively; done phrases are casefolded | low | patched (casefold both) |
| 8 | edge (claim) | Demo request left by the client logs `cost_usd: null`, spec says 0.0 | low | no `Usage` before the end. patched |
| 9 | verif | The chunk pause is never exercised | medium | pre-verified; all tests run with pause 0. patched (sleep recorder test, wiring check) |
| 10 | blind | Demo wiring with a passed-in `llm` untested | low | patched |
| 11 | blind | Test id `newline-nbsp` has no NBSP | low | patched |
| 12 | blind | `reply-demo-only` key written twice | low | patched (import `DEMO_ONLY_KEY`) |
| 13 | blind | `role="status"` makes the banner a live region | low | patched |
| 14 | blind | `safe-area-inset-top` has no effect without `viewport-fit=cover` | low | patched (dropped) |
| 15 | blind | Comment says the label explains "example questions only"; label is not shown on the load-failed screen | low | comment patched; the load-failed screen cannot know the mode (texts did not load). rest rejected |
| 16 | verif, blind | Demo label show/hide and static tests checked only by source text | medium | known; browser-level tests deferred (Story 1.6 entry). deferred (carried) |
| 17 | edge | Done phrases with punctuation or emoji (`Thanks!`, `ขอบคุณค่ะ 🙏`) classify as `general` | low | no consumer until Story 2.3. deferred |
| 18 | edge, blind | Lookup collisions (two examples with the same key, a done phrase equal to an example) | low | the four examples and phrases are distinct; a check adds code for a state not shown. rejected |
| 19 | edge | `{ADVISER_CONTACT}` in a demo answer is not filled in | low | no demo answer uses it. rejected |
| 20 | edge | A stored answer of three words or fewer streams as one chunk | low | all stored answers are long. rejected |
| 21 | blind | No DRAFT marker on the unapproved Thai | low | the commit is gated on the user's adviser confirmation (Decision 2). rejected |
| 22 | verif (other) | `classify`/`translate` have no consumer; stored categories all `general` | low | by Decision 1; Stories 2.3 and 4.1 should test a non-`general` category. note |
