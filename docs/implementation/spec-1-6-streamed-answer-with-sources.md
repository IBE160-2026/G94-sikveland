---
title: 'Story 1.6: Streamed answer with sources'
type: 'feature'
created: '2026-11-14'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'f47b0b2ca1a5a1a14e0631f2a42ee014408d51c3'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The page can show texts and example questions, but a question cannot be sent or answered yet.

**Approach:** Add `POST /api/chat`: filter → (every question is `general`) → answer through the `LLMClient` with the grounding rule (AD-7), streamed as JSON Lines (AD-8). The page sends the question, shows a typing indicator, appends text as it arrives, then the source links; example questions send at once.

## Boundaries & Constraints

**Always:** the filter runs on the question and every history turn before the LLM is called (AD-1, AD-4); `personal_info_removed` describes the new question only. Answer text is held until the first chunk with a source id, then released; zero citations at the end → held text discarded, one `text` event with `reply-no-answer`. Text already sent is never replaced. `sources` lists exactly the cited sources, first-cited first, each once, title and URL from the knowledge base. Only `app/web` builds the JSON events; `app/pipeline` stays free of FastAPI/SDK. The page holds no Thai and only appends text. No question or answer text in logs.

**Never:** no classifier (Story 2.x), no history storage in `sessionStorage` (Story 1.7: the page sends `history: []`), no cost/request log (Story 1.8), no demo adapter (Story 4.2), no checklist (`checklist: false`, `checklist_purposes: []`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cited answer | fake yields text `A`, then source `s1` with text `B`, text `C` | `meta` → `text` `A` (released at `s1`) → `text` `B` → `text` `C` → `sources [s1]` → `done` | N/A |
| Zero citations | fake yields text, no source ids | `meta` → one `text` = `reply-no-answer` (adviser contact filled) → `sources []` → `done`; no model text sent | N/A |
| Personal info | question `passport AA1234567 ...` | LLM receives `passport [removed] ...`; `meta.personal_info_removed: true`, `meta.clean_question` cleaned | N/A |
| History filtered | history turn holds an ID number | LLM receives the turn with `[removed]`; `personal_info_removed` false if the new question is clean | N/A |
| Error before text | fake raises `LLMError` / refusal before any cited chunk | `meta` → `error` (`key: "error"`), stream ends | no `done` |
| Error after text | fake raises after text was sent | `meta` → `text`… → `error`, stream ends | sent text stays |
| Unknown cited id | fake cites an id not in the knowledge base | `error` event, stream ends | no `done` |
| Bad request | empty/whitespace question, question > 1000 chars, history > 10 items, wrong types | HTTP 422 `{"error": {"code": "invalid_request", "message": ...}}`, LLM not called | N/A |

</frozen-after-approval>

## Code Map

- `app/main.py` -- `create_app(settings)`; add an optional `llm: LLMClient | None` (tests pass `ScriptedLLM`); default builds `AnthropicLLM(settings, app.state.knowledge_base, load_prompt(ROOT / "prompts" / "answer-system.md"))` (no key → each answer fails as `LLMError` → `error` event). Include the new router before the static mount.
- `app/pipeline/filter.py` -- `remove_personal_info(text) -> FilterResult(text, removed)`. Reuse.
- `app/ports/llm.py` -- `LLMClient.answer(question, history) -> Iterator[AnswerChunk | Usage]`, `Exchange`, `LLMError`. Reuse; no change.
- `app/ports/knowledge_base.py` -- `source(id)` raises `KeyError` for unknown ids. Reuse.
- `app/ports/content.py` / `app.state.content.texts()` -- `reply-no-answer`, `error`, `personal-info-reminder` (`.th`, contact already filled). No new keys.
- `app/web/texts.py` -- router style to copy.
- `tests/fakes/fake_llm.py` -- `ScriptedLLM(chunks, usage, error, refusal)`, `.calls`. Reuse.
- `app/static/app.js`, `index.html`, `style.css` -- the submit handler is a stub; example buttons only fill the field. `#messages` exists. Keep `load()`/retry as is.
- `tests/test_static.py` -- no Thai, no external URLs in static files; must keep passing.

## Tasks & Acceptance

**Execution:**
- [x] `app/pipeline/answer.py` -- domain events (frozen dataclasses): `Meta(category, personal_info_removed, clean_question)`, `TextDelta(text)`, `Sources(items: tuple[SourceRef, ...])` with `SourceRef(id, title, url)`, `Done`, `Failed`; `answer_question(question, history, llm, knowledge_base, no_answer_text) -> Iterator[event]` implementing filter, grounding rule and error handling per the matrix (catches `LLMError` and unknown ids; yields `Failed` last). `Usage` is consumed and ignored (Story 1.8).
- [x] `app/web/chat.py` -- `POST /api/chat`; pydantic request model (`question` 1–1000 chars after strip, `history` ≤ 10 of `{question, answer}` strings, extra fields forbidden); `StreamingResponse` of JSON Lines (`application/jsonl`, `ensure_ascii=False`, one object per line, `Cache-Control: no-store`, `X-Accel-Buffering: no`); maps events to `meta`/`text` (`delta`)/`sources` (`sources`, `checklist: false`, `checklist_purposes: []`)/`done`/`error` (`key: "error"`); any unexpected exception mid-stream → `error` event, logged by class name only.
- [x] `app/main.py` -- `llm` parameter, adapter wiring, prompt loaded at startup (bad prompt file → app does not start), router included; validation errors on `/api/chat` → 422 with the error shape.
- [x] `app/static/app.js`, `index.html`, `style.css` -- send on submit and on example tap (sends at once); disable the form while answering; show the question bubble, a typing indicator (CSS only, no text) until the first `text`; read with `fetch` + `getReader()` + `TextDecoder` with `{stream: true}`, split on `\n`, parse each line; `meta.personal_info_removed` → `personal-info-reminder` above the reply; append `text` deltas; `sources` → links (`target="_blank" rel="noopener"`) under the answer; `error` or a failed request → the fixed `error` text appended; re-enable the form after `done`/`error`. Touch targets ≥ 48 px; no horizontal scroll at 320 px.
- [x] `tests/test_answer_pipeline.py`, `tests/test_chat_api.py` -- every matrix row (pipeline unit tests with `ScriptedLLM` and a stand-in knowledge base; API tests with `TestClient(create_app(settings, llm=ScriptedLLM(...)))` checking exact event lines and order); `tests/test_static.py` -- `app.js` uses `getReader`, `TextDecoder` and `stream: true`, posts to `/api/chat`.

**Acceptance Criteria:**
- Given `uv run pytest`, when it runs, then all tests pass without network or key.
- Given the app running with a real key, when I tap an example question on a phone-sized window, then a Thai answer appears bit by bit with source links under it.
- Given a real Android or iPhone, when the page is opened from a link in Facebook's in-app browser, then the answer streams bit by bit; the result is noted in the PR (manual, by the user).

## Design Notes

Grounding in the pipeline (golden path):
```
held = []; cited = []   # ordered, unique
for item in llm.answer(clean_q, clean_history):
    Usage -> stop; chunk.source_ids -> resolve each via kb.source (KeyError -> Failed), add to cited
    if not cited: held.append(chunk.text); continue
    if held: yield TextDelta("".join(held + [chunk.text])); held = []  else yield TextDelta(chunk.text) if text
end: cited empty -> TextDelta(no_answer_text); Sources(cited refs); Done
```
Empty text deltas are never sent. The browser-level JS test deferred from Story 1.2 stays deferred (Playwright needs browsers in CI; after part 1); the page is checked by hand.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass.

**Manual checks:**
- `uv run uvicorn app.main:app` with a real key; DevTools at 360 px and 320 px: tap an example, see the typing dots, Thai text arriving in parts, source links, no horizontal scroll. Without a key: the fixed error text appears.

## Implementation Notes

- `Failed` carries a `reason` (exception class name, or `unknown source id`) so `app/web` can log why an answer failed without any question or answer text. *(Since 2026-11-15 `Failed("unknown source id")` is no longer emitted; see the Spec Change Log.)*
- Grounding test fixtures send citations as separate empty-text chunks (`AnswerChunk("", ("s1",))`), the shape the Anthropic adapter yields; a chunk with text and a citation together releases the held text and its own text as one delta.
- History turns are stripped and must be non-empty: question up to 1000 characters, answer up to 10000 (`MAX_ANSWER_CHARS`), so an empty turn cannot break the model request.
- The 422 handler is app-wide (only `/api/chat` takes a body today); the message lists field paths and pydantic messages, never the input; for an unknown field the location (the client's own key) is left out.
- `create_app` always loads `prompts/answer-system.md` (also when a fake `llm` is passed) and keeps it on `app.state.answer_prompt` for the request log in Story 1.8.
- Checked live with uvicorn and a slow fake model: `meta` arrives at once and each `text` line arrives as the model yields it (no buffering).

## Spec Change Log

- 2026-11-15, [spec-ollama-provider.md](spec-ollama-provider.md) (user's decision): the matrix row "Unknown cited id → `error` event, stream ends" no longer holds. An unknown cited id is now dropped (no link), the rest of the answer streams and ends with `sources` and `done`, and `Sources` carries the count of dropped ids for the request log (`unknown_source_ids`). If only unknown ids were cited, the answer counts as uncited and `reply-no-answer` is sent. `Failed("unknown source id")` is no longer emitted. Applies to every provider. The frozen matrix above is left as approved.

## Review Triage Log

Pass 1 (2026-11-14):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | verif (other), blind, edge | 422 message echoes an extra key name (`passport AA1234567: Extra inputs are not permitted`) | low | verified by request; echoed only to the sender, but breaks the "never echoed" rule. patched |
| 2 | blind, edge | History items have no length limits (empty turn → API 400; huge turns billed) | medium | `HistoryItem` fields are plain `str`. patched (strip, 1–1000 question, 1–10000 answer) |
| 3 | blind | Deferred timeout/retries item (target 1.6) neither done nor moved | medium | real; values need the real-phone test. deferred again with the page timeout (#4) and heartbeat (#5) |
| 4 | blind, edge | Page has no client timeout; dots and locked form until the SDK gives up | medium | `fetch` has no `AbortController`. deferred (see #3) |
| 5 | edge | No bytes between `meta` and the first released text; idle proxies may cut | maybe-false | depends on proxy/in-app browser idle limits; settled by the real-phone test. deferred (see #3) |
| 6 | blind | Partial answer after a failure loses its sources | false | AD-8: `error` replaces any later event; the matrix row "error after text" is `meta → text… → error`. rejected |
| 7 | blind | Long unbroken strings overflow at 320 px | false | `body` has `overflow-wrap: anywhere` (style.css:25), which is inherited by the bubbles and links. rejected |
| 8 | blind | Live region announces every fragment; focus lost while answering | low | `#messages` is `aria-live`. patched (`aria-busy` while answering); refocusing the field would reopen the phone keyboard after every answer. focus part rejected |
| 9 | blind, edge | Example tap wipes a typed draft; failed request loses the question | low | `ask()` always clears the field. patched |
| 10 | blind, edge | Reader not cancelled when parsing/handling throws | low | no `reader.cancel()` on that path. patched |
| 11 | blind, edge | Client disconnect may not close the sync generator, so the model stream keeps running | maybe-false | Starlette stops iterating; CPython closes the generator when the response is dropped, which ends the SDK `with` block. Would be settled by a disconnect test against a slow fake; if true, medium (billing). deferred |
| 12 | verif, blind | Page streaming logic only checked by string matching | medium | pre-verified; the browser test stays deferred (spec Design Notes). deferred (new entry with target) |
| 13 | blind | Sprint status and spec say in-progress | false | the workflow moves both at the present step. rejected |
| 14 | edge | LLM stream ending without `Usage` reported as complete | low | the adapter always ends with `Usage` or raises; the fake too (port contract). rejected |
| 15 | edge | More than 40 concurrent streams starve the threadpool | low | far above expected use for one adviser's applicants. rejected |
