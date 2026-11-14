---
title: 'Story 1.5: Claude connection with a test version'
type: 'feature'
created: '2026-11-14'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'df5beda0d38b962a72a165baf8ff1afd7a5130d6'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing can produce an answer yet: there is no interface to Claude, no adapter, no answer prompt, and no way to test answer logic without calling the paid API.

**Approach:** Add the `LLMClient` port (AD-14), a scripted fake in `tests/fakes/`, the Anthropic adapter that builds the fixed, cache-friendly answer request (AD-7) and turns citations into source IDs, and a versioned answer prompt. Wiring into `/api/chat` and the grounding rule are Story 1.6.

**Decision (user, 2026-11-14):** no refusal fallback. A refusal raises `LLMRefusalError`; the request uses the plain `client.messages.stream` (no beta), so every answer comes from `MODEL_ANSWER`.

## Boundaries & Constraints

**Always:** only `app/adapters/anthropic_llm.py` imports `anthropic`; no SDK type or SDK exception leaves it. Request order: system prompt → every KB document (sorted by id, Citations on, one cache breakpoint on the last document) → history as plain-text alternating turns → question. `MODEL_ANSWER`, adaptive thinking, `EFFORT_ANSWER`, no `temperature`/`top_p`/`top_k`. Tests never touch the network or need a key.

**Never:** no `/api/chat` route, pipeline answer logic or startup wiring of the adapter (Story 1.6); no `classify`/`translate` implementation (later epics); no logging of question or answer text; no mock/demo adapter (Story 4.2).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cited answer | stream with text deltas and a citation of document index 2 | chunks with the text in order; a chunk carries the id of `documents()[2]`; then one `Usage` | N/A |
| Uncited answer | text deltas, no citations | text chunks, all with empty `source_ids`, then `Usage` | N/A |
| History | 2 earlier exchanges | messages alternate user/assistant as plain text, documents in the first user turn, question last | N/A |
| Refusal | final `stop_reason: "refusal"` | — | raises `LLMRefusalError` |
| Cut off | final `stop_reason: "max_tokens"` | — | raises `LLMError` |
| API failure | SDK raises (connection, 4xx, 5xx) | — | raises `LLMError` chained to the cause |
| Fake | test scripts chunks / error / refusal | yields the script, then `Usage`, or raises | no network |

</frozen-after-approval>

## Code Map

- `app/ports/knowledge_base.py` -- `KnowledgeBase.documents()` already sorted by id; `Source(id, title, url, text, ...)`. Reuse; no change.
- `app/ports/content.py` -- port style to copy (frozen dataclasses + `Protocol`).
- `app/config.py` -- `Settings.anthropic_api_key` (SecretStr | None), `model_answer`, `effort_answer`. Reuse; no change.
- `app/main.py` -- no change (wiring is Story 1.6).
- `tests/conftest.py` -- pops every `Settings` env var; add `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL` and `ANTHROPIC_PROFILE` (deferred-work, Story 1.1).
- `prompts/.gitkeep` -- folder exists; the answer prompt goes here.
- SDK `anthropic` 2.4.0 (installed): stream events `content_block_delta` with `delta.type` `text_delta` / `citations_delta` (`delta.citation.document_index`); plain-text document source `{"type": "text", "media_type": "text/plain", "data": ...}`; final usage `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` (may be `None`).

## Tasks & Acceptance

**Execution:**
- [x] `app/ports/llm.py` -- `Exchange(question, answer)`, `AnswerChunk(text: str, source_ids: tuple[str, ...])`, `Usage(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens)` frozen dataclasses; `Category` = Literal of the five AD-5 values; `LLMError`, `LLMRefusalError(LLMError)`; `LLMClient` Protocol: `answer(question, history) -> Iterator[AnswerChunk | Usage]` (Usage last), `classify(question, recent_history) -> tuple[Category, Usage]`, `translate(text) -> tuple[str, Usage]` -- the contract 1.6, 4.2 and the eval build on.
- [x] `app/adapters/file_prompts.py` -- `load_prompt(path) -> Prompt(version, text)`: first line must be `version: <non-empty>`; text is the rest, stripped; raises `PromptError` otherwise.
- [x] `prompts/answer-system.md` -- `version: 1`; English instructions: answer in Thai (also for mixed Thai/English or typo questions), only from the documents, say so when they do not answer; when asked how to start, give the steps in order — prepare documents (embassy checklist) → register at UDI → pay the visa fee → book at VFS — naming the website of each step; plain, short language.
- [x] `app/adapters/anthropic_llm.py` -- `AnthropicLLM(settings, knowledge_base, prompt, client=None)`; a pure `build_answer_request(...) -> dict` (kwargs for `messages.stream`); `answer` streams, maps events to chunks, ends with `Usage`, maps stop reasons and SDK errors per the matrix; `classify`/`translate` raise `NotImplementedError`. Client built lazily from the key so construction needs no network.
- [x] `tests/fakes/__init__.py`, `tests/fakes/fake_llm.py` -- `ScriptedLLM(chunks=..., usage=..., error=None, refusal=False)`; records calls.
- [x] `tests/test_llm_port.py`, `tests/test_anthropic_llm.py`, `tests/test_prompts.py` -- matrix rows: request shape (order, sorting, one breakpoint, citations on every document, model, thinking, effort, no sampling keys), event mapping with stand-in event objects and a stand-in client (no network), error mapping, fake behaviour, prompt file (`version:` first, Thai and the four steps mentioned), loader errors.
- [x] `tests/test_layering.py` -- AST scan: only `app/adapters/anthropic_llm.py` imports `anthropic`; nothing in `app/pipeline/` or `app/ports/` imports `fastapi`, `starlette` or `anthropic`.
- [x] `tests/conftest.py` -- also clear the SDK credential env vars listed in the Code Map.

**Acceptance Criteria:**
- Given `uv run pytest` with no network and no key, when it runs, then all tests pass.
- Given `ANTHROPIC_API_KEY` in `.env`, when the manual check below runs, then a Thai answer with at least one source id and a `Usage` comes back (costs a few cents).

## Design Notes

Chunk mapping: each `text_delta` → `AnswerChunk(delta, ())`; each `citations_delta` → `AnswerChunk("", (source_id,))`, the id taken from `documents()[document_index]` (an index out of range raises `LLMError`). Thinking deltas are ignored. Story 1.6 holds text until the first chunk with a source id.

Request messages: `[{"role": "user", "content": [doc_1, …, doc_n (cache_control ephemeral), {"type": "text", "text": <first question>}]}, {"role": "assistant", "content": <answer>}, …, {"role": "user", "content": <question>}]` — documents go in the first user turn; with no history that turn also holds the question. Document block: `{"type": "document", "source": <plain text>, "title": source.title, "citations": {"enabled": True}}`. `max_tokens` 32000.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network.

**Manual checks:**
- With a real key, from a REPL, call `AnthropicLLM(...).answer("ต้องเตรียมเอกสารอะไรบ้าง", [])` twice: Thai text, at least one source id, `cache_write_tokens > 0` on the first call and `cache_read_tokens > 0` on the second.

## Implementation Notes

- Stop reasons other than `end_turn`/`stop_sequence` (e.g. `pause_turn`, `model_context_window_exceeded`) raise `LLMError` like `max_tokens`: the answer would be incomplete.
- Any exception from the SDK call or stream becomes `LLMError` chained to the cause, because the SDK lets transport errors (`httpx2`) through unwrapped mid-stream.
- The SDK client is built in `__init__` when a key is set (no connection until a call); `answer` without `ANTHROPIC_API_KEY` raises `LLMError` on first read.
- `answer` sorts `documents()` by id itself and uses that one tuple for the request and the citation mapping.
- `load_prompt` also rejects a file with no text after the version line, and accepts a UTF-8 BOM.
- Besides stand-in events, `tests/test_anthropic_llm.py` runs the real SDK over an `httpx2.MockTransport` to check event mapping, request body, refusal and status/connection errors without network.
- `ScriptedLLM` raises `error`/refusal after the scripted chunks, so Story 1.6 can test a failure after text has started.
- Manual check with a real key not run (no `.env` in the workspace).

## Spec Change Log

## Review Triage Log

Pass 1 (2026-11-14):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | verif | Real-key path of `_sdk_client` (plain secret, reuse) untested | medium | pre-verified gap. patched (test) |
| 2 | verif | `cache_creation_input_tokens=None` untested | low | pre-verified gap. patched (test) |
| 3 | verif, blind | Fake and adapter not checked against the port signatures (no type checker) | medium | pre-verified; `test_fake_satisfies_the_port` only checks `callable`. patched (signature test) |
| 4 | blind, edge (claim) | Sorting by id neither enforced nor tested | medium | `answer` uses `documents()` as given; tests feed sorted input. patched (sort in `answer`, test with unsorted KB) |
| 5 | blind, edge | Layering test does not stop `app/pipeline`/`app/ports` importing `app.adapters`/`app.web` | low | `_top_level_imports` keeps only `app`. patched |
| 6 | blind, edge | Lazy SDK client built without a lock | low | two concurrent first calls can each build a client. patched (build in `__init__`) |
| 7 | blind | `file_prompts` docstring says the version is logged; nothing logs it yet | low | real; logging is Story 1.8 and the loaded `Prompt` is available at wiring. patched (docstring); exposing it on the port rejected for now |
| 8 | blind | Prompt does not explain `[removed]` or say documents are data | low | real. patched (two prompt lines) |
| 9 | edge (claim) | Step 3 names no website | low | real. patched (udi.no) |
| 10 | blind | Prompt hard-codes websites and a fee claim not in the documents | false | the spec and FR12 require naming each step's website; "pay the fee online during registration" is in `udi-how-to-apply-visitor-visa.md` line 15. rejected |
| 11 | blind, edge | Empty question or history turn gives an API 400 | low | the page stores only shown text and the clean question, never empty; the failure is a loud `LLMError`. Story 1.6 validates the request. rejected |
| 12 | blind | SDK default timeout (10 min) and retries; `LLMError` drops the status | medium | real, but the right timeout depends on the stream UX in Story 1.6. deferred (deferred-work.md) |
| 13 | edge | `Usage` lost on refusal or `max_tokens` | low | rare outcomes; the fix adds public surface to the error. rejected (note for Story 1.8) |
| 14 | blind, edge | Fake: one script for every call; `error` + `refusal` together not rejected | low | Story 1.7 can extend it when needed; a guard adds complexity. rejected |
| 15 | blind | AC 2 (real-key check) not run; no smoke script | low | manual check is listed in Verification; needs the user's key. Shown at present |
| 16 | blind | Prompt tests read `utf-8` not `utf-8-sig`, loose asserts | low | file has no BOM; cosmetic. rejected |
