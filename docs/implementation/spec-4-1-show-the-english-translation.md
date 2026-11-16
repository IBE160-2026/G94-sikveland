---
title: 'Story 4.1: Show the English translation'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '781bf10e41bda3e858df08038b638df69d618ede'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The examiner does not read Thai, so they cannot follow what the chatbot tells applicants (FR7). `LLMClient.translate` exists in the port but every adapter raises `NotImplementedError`, and there is no `/api/translate`.

**Approach:** Every finished reply gets a "Show English" button. Tapping it sends the reply text to `POST /api/translate`. The server filters it (AD-4), returns the stored `en` when the text is a stored Thai text, and otherwise calls `LLMClient.translate` on `MODEL_SMALL` with `prompts/translate-system.md` and logs the token usage. The English appears under the Thai reply.

**Decisions (user, 2026-11-15):**
- **Checklist English:** `GET /api/checklists/{purpose}` also serves each item's stored `en`. The checklist view gets the same button, which shows the stored English under every item, with no server call and no model call. The English stays until the view closes or the purpose changes.
- **Ollama:** `OllamaLLM.translate` is built: a non-streamed `/api/chat` call on `OLLAMA_MODEL` with `think: false`, `num_ctx`, and the same prompt; a done reason other than `stop`, an `error` field or an empty reply → `LLMError`; usage as in `classify`.
- **Label:** the Thai of `translate-button` includes the Latin word "English", e.g. `แปลเป็นภาษาอังกฤษ (English)`.
- **Size:** the spec is kept as one (about 2,600 tokens).

## Boundaries & Constraints

**Always:**
- Request `{text}` (stripped, 1–10,000 chars, extra fields → 422 envelope); response `200 {translation}`. A body without `Content-Type: application/json` gets the 415 envelope, as `/api/feedback` does.
- The personal-information filter runs first. The stored lookup then matches the filtered text against the Thai of every fixed text and example question after NFC, whitespace collapse and trimming. A hit returns the stored `en` with no LLM call and no log line.
- Otherwise `llm.translate(filtered)` runs. Any failure (`LLMError`, `NotImplementedError`, anything else) gets a 502 envelope `translation_failed`. The text is never logged.
- Each model-path call writes one request-log line: `endpoint: "translate"`, outcome `translated` or `error`, `category: null`, `prompt_versions: {"translate": v}`, the translate model, and its usage priced with `PRICE_SMALL_*` (0 in demo mode and with Ollama). Chat lines gain `endpoint: "chat"`; nothing else changes for them.
- Anthropic: `messages.create`, `MODEL_SMALL`, `EFFORT_SMALL`, no `thinking`, `MAX_TOKENS_TRANSLATE = 8192`. `refusal` → `LLMRefusalError`. Any stop other than `end_turn`/`stop_sequence` → `LLMError`. Empty text → `LLMError`. The joined text blocks are stripped.
- `prompts/translate-system.md` starts with `version: 1`. It is loaded at startup in every mode (a `PromptError` stops startup). It says: translate Thai (or mixed) chatbot text to plain English, keep URLs, numbers, amounts and `[removed]` unchanged, add or leave out nothing, and output only the translation.
- Demo mode: the same lookup, then `MockLLM.translate`, which is unchanged (demo-answer `en`, else the `en` of `reply-demo-only`). It is logged as `mock_llm` at no cost.
- Page: the button appears under every reply that ends with `done`: model answers, fixed replies and the feedback question, live and replayed. It does not appear under error replies. The button sits after the reply's sources or checklist button and before the feedback buttons. It sends only the reply text (`record.answer` / `entry.answer`), not the reminder. It is disabled while the request is in flight. On success the button is replaced by an English paragraph (`lang="en"`), and the Thai text, sources and other buttons stay. On failure the fixed `error` text is shown under the reply and the button comes back to try again. A result that arrives after the reply left the screen is ignored. The translation is kept in page memory only, never stored with the chat. The button is at least 48 px and 320 px wide screens need no sideways scrolling. The new text key is `translate-button`, with Thai marked DRAFT for the user's review (NFR8).

**Never:** no translation in `/api/chat` or in stored history; no question or answer text in any log; no Thai in `app/static/`; no new dependency; no change to `/api/chat` events.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fixed reply | text = `reply-embassy-decides` th (any spacing) | stored `en`, LLM not called, no log line | N/A |
| Example question / filled contact | th of an example question; `reply-reach-person` with the contact filled in | stored `en` | N/A |
| Model answer | other Thai text | `llm.translate` result; one log line `translated` with small-model usage | N/A |
| Personal info | text with a passport number | the LLM gets `[removed]` in its place | N/A |
| Model fails / refuses / Ollama not built | `LLMError`, refusal, `NotImplementedError` | 502 `translation_failed`; log line `error`, usage null | page shows `error`, button back |
| Bad body | empty, whitespace-only, >10,000 chars, extra field, not JSON | 422 envelope; no LLM call, no log | N/A |
| Wrong media type | `text/plain` body | 415 envelope; no LLM call | N/A |
| Demo | demo answer th; any other text | its `en`; `reply-demo-only` `en`; logged `mock_llm`, cost 0 | N/A |
| Checklist | view open, button tapped | stored `en` under every item; no request | N/A |
| Ollama | model answer | `OllamaLLM.translate` result; logged with `OLLAMA_MODEL`, cost 0 | `LLMError` → 502 |
| Replayed chat | reopened from history | each saved reply gets the button | N/A |
| New chat mid-request | translation returns after the chat changed | ignored | N/A |

</frozen-after-approval>

## Code Map

- `app/ports/llm.py` `LLMClient.translate(text) -> (str, Usage)` -- the contract exists; keep it.
- `app/adapters/anthropic_llm.py` -- add `build_translate_request` next to `build_classify_request` and implement `translate` with the same error handling as `classify`. The constructor gains the translate `Prompt`.
- `app/adapters/mock_llm.py` `translate` -- already done; reuse its `normalise` idea (NFC + whitespace), but the pipeline must not import adapters.
- `app/adapters/ollama_llm.py` `build_classify_request`/`classify` -- the pattern for `build_translate_request`/`translate`; the constructor gains the translate `Prompt`.
- `app/web/checklists.py` -- add `"en": item.en` per item; `app/static/app.js` `renderChecklist` -- the button in the checklist view and the English under each item.
- `app/pipeline/filter.py` `remove_personal_info` -- apply before the lookup.
- New `app/pipeline/translate.py` -- pure: filter, stored lookup (a `Mapping[str, str]` keyed by the normalised Thai), else `llm.translate`; returns the translation, `usage | None`, and whether it was stored.
- New `app/web/translate.py` -- the route, envelopes, 415 check (copy the pattern in `app/web/feedback.py`), log line. Uses ports and pipeline only (`tests/test_layering.py`).
- `app/main.py` -- load the translate prompt and build the stored map once from `content.texts()` and `example_questions()`. Set `state.translate_model`/`translate_prices` per mode: Claude = `model_small` + `small_prices`, Ollama = `ollama_model` + `NO_PRICES`, demo = `mock_llm` + `NO_PRICES`. Add `prompt_versions["translate"]` and include the router.
- `app/web/request_log.py` `request_line`, `Outcome` -- add `endpoint` and outcome `translated`. `app/web/chat.py` passes `endpoint="chat"`.
- `app/static/app.js` `createReply`, `handle`/`ask` (after `done`), `showConversation` -- the button. Pure helpers, if any, go in `history.js` and get Node tests. Also `style.css`.
- `content/texts.yaml`, `REQUIRED_TEXT_KEYS` -- `translate-button`.
- Tests: `tests/fakes/fake_llm.py` `ScriptedLLM` gains `translation`/`translate_usage`/`translate_error` and records `translate_calls`; new `tests/test_translate_api.py`; `tests/test_anthropic_llm.py`, `test_prompts.py`, `test_request_log.py`, `test_demo_mode.py`, `test_static.py`, `test_layering.py` (only if a rule needs the new modules).

## Tasks & Acceptance

**Execution:**
- [x] `prompts/translate-system.md` -- versioned prompt -- AD-12
- [x] `app/adapters/anthropic_llm.py`, `app/adapters/ollama_llm.py` -- `translate` -- AD-14
- [x] `app/pipeline/translate.py`, `app/web/translate.py`, `app/web/request_log.py`, `app/web/chat.py`, `app/main.py` -- endpoint, lookup, log -- FR7, AD-4
- [x] `app/web/checklists.py`, `app/static/app.js`, `style.css` -- reply button and English paragraph; checklist `en` and its button -- FR7
- [x] `content/texts.yaml`, `app/ports/content.py` -- `translate-button` DRAFT -- NFR8
- [x] `tests/` -- every matrix row; stored path and model path with `ScriptedLLM` (no network) -- NFR
- [x] `README.md` (endpoint, button, `endpoint` log field, translate cost), `docs/implementation/manual-test-plan.md` (new MT case), `docs/implementation/deferred-work.md` (mark the Story 3.1 checklist-English entry as settled by this story)

**Acceptance Criteria:**
- Given a finished reply, when I tap the button, then the English appears under it and the Thai text and source links are unchanged.
- Given the test suite, when it runs, then it never makes a network call and covers both the stored-text path and the model path.
- Given a model-path translation, when it finishes, then `data/requests.jsonl` gets one line with the small model's tokens and cost and no text.

## Implementation Notes

- The pipeline (`app/pipeline/translate.py`) keys the stored map by `lookup_key` (the personal-information filter, then NFC + whitespace collapse + trim), so a stored Thai text the filter would change still matches its filtered request. Unlike `MockLLM`'s own lookup it does not lowercase. If two stored Thai texts were the same, the first wins (none are today).
- An empty or whitespace-only translation from any adapter is an `LLMError` in the pipeline too, so the route never returns an empty `translation`.
- The route checks the media type before reading the body, so a body with no `Content-Type` gets 415 (not 422 as `/api/feedback` can give). A `GET /api/translate` falls through to the static files (404), as for the other POST routes.
- The Ollama adapter's shared non-streamed POST moved into `_post`/`_reply_text`/`_reply_usage`, used by `classify` and `translate`; classify behaviour is unchanged (its tests are untouched).
- `translate_prompt_versions` is kept apart from `prompt_versions`, so chat lines never gain a `translate` key.
- Not verified by hand in a browser (no browser tool in this run): the button layout at 320 px and the live page flow. MT-17 in the manual test plan covers them; the endpoint was smoke-tested in demo mode with `TestClient`.

- The user approved the Thai button text `translate-button` (แปลเป็นภาษาอังกฤษ (English)) on 2026-11-16 (NFR8).

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Route | Evidence |
|---|-------|---------|---------|-------|----------|
| 1 | verification-gap | The translate prompt passed by position to the app-built `AnthropicLLM`/`OllamaLLM` is never checked; swapping it with the classifier prompt keeps every test green | medium | patch | Pre-verified gap: the adapter tests build the adapter by hand, and the only app-built Claude test fails in `_sdk_client()` before any prompt is used. |
| 2 | verification-gap, blind | Page behaviour of "Show English" (`translateReply`, `renderChecklist` visibility line, `closeChecklist` reset, error note removal) is checked only by source text | medium | defer | No browser runner exists (Playwright deferred); `checklistTranslate.hidden = checklistEnglish` appears in no test. MT-17 covers it by hand. |
| 3 | verification-gap, blind, edge-case | A reply over 10,000 characters gets a button that always gets 422 | low | reject | Real in theory (answers are not capped), but the longest demo answer is 1,229 characters and real answers are far below 10,000; the fix adds a length guard. |
| 4 | verification-gap | `test_checklist_view_shows_the_stored_english_without_a_request` says the English is redrawn on a tick, but a tick calls `refreshChecklist`, not `renderChecklist` | low | patch | Verified in `app.js`: `changeChecklist` → `refreshChecklist`; the comment is wrong, the behaviour is right. Direct correction. |
| 5 | blind | `epic-4-context.md` says Ollama has no `translate`, lookup before the filter and over demo answers, 4.1 in backlog, checklist English open, 44 px targets | low | patch | Each statement contradicts the shipped code or the user's decisions; Story 4.3 builds its README from this file. Direct correction. |
| 6 | blind | Spec says `in-review` while sprint status says `in-progress` | false | reject | Mid-workflow: step 5 sets the sprint status to `review` when the story is committed. |
| 7 | blind | README lists 4.1 under "Ferdig og testet" while the Thai label is a draft and MT-17 is not run | false | reject | Project convention: every story in `review` (Epics 2–3, 4.2) is listed there; the Thai label is approved before the commit. |
| 8 | blind | The failure note is Thai only, so the examiner cannot read it | low | reject | The intent fixes the `error` text; failures are rare and the button comes back, which shows a retry is possible. A bilingual note needs new UI. |
| 9 | blind | `/api/translate` is an open paid endpoint with no rate limit | low | reject | Same exposure as `/api/chat` (which calls the larger model); the app runs locally for the examiner. A rate limit adds a new mechanism. |
| 10 | blind | The README says Claude translates "uten tenking", but the request only leaves out `thinking`, so the small model decides | low | patch | `build_translate_request` and `build_classify_request` both say "`thinking` is not sent: the small model decides". README wording only. |
| 11 | blind, edge-case | A cut-off or refused translation drops its billed usage, so the log has null tokens and cost | low | reject | Same as the classify and answer paths; the README already says null-cost lines are left out and the sum is a lower bound. The fix needs usage on exceptions. |
| 12 | blind | Demo mode shows the `reply-demo-only` English as the translation of a non-stored text | false | reject | The frozen intent says `MockLLM.translate` is unchanged: demo-answer `en`, else `reply-demo-only` `en`. |
| 13 | blind | Other Thai (reminder, follow-up after Yes/No, privacy notice, checklist headings) has no English | false | reject | The intent limits the button to replies ending with `done` and excludes the reminder. |
| 14 | blind | Any exception, also one from the filter or lookup, is logged as a failed model call | false | reject | `remove_personal_info` and `dict.get` on a validated `str` have no reachable raise; no path was shown. |
| 15 | blind, edge-case | Focus is read after the await (a disabled button may lose focus) and the English is not announced to screen readers after a tap | maybe-false | reject | Depends on each browser's focus fixup after `disabled`; if true it is low (keyboard focus lands on body, nothing breaks). |
| 16 | edge-case | The JSON body is read in full before the 10,000-character check | low | reject | Same as `/api/feedback` and `/api/chat`; local app; a size guard adds a new check. |
| 17 | edge-case | A long translation with a slow local Ollama model can pass the 300 s read timeout | maybe-false | defer | If true, medium: long answers always fail in Ollama mode. Settle with MT-17 part B on the user's GPU. |
| 18 | edge-case | A demo answer that the filter rewrites would miss `MockLLM`'s lookup | false | reject | Checked: the filter changes none of the four demo answers. |
| 19 | blind | The Story 3.1 deferred entry's summary still reads as open; only its evidence says settled | low | reject | Cosmetic; the spec task asked for the entry to be marked settled, which the evidence line does. |

## Verification

**Commands:**
- `uv run pytest` -- expected: exit code 0
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean

**Manual checks (if no CLI):**
- Demo mode (`MOCK_LLM=true`): tap the button under an example answer and under the embassy-decides reply; English appears; 320 px has no sideways scroll.
