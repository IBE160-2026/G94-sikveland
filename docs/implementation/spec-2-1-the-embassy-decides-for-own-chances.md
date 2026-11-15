---
title: 'Story 2.1: "The embassy decides" for questions about the applicant''s own chances'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '9a6e6439021593e5d0f61b4455851beea7e826e3'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every question goes to the answer model, so "Will I get the visa?" gets an answer built from the sources instead of the plain statement that only the embassy decides (FR3); refusing depends on the model following its prompt.

**Approach:** Add the classify step (AD-1, AD-5): after the filter, a small model call sorts the cleaned question (with the last 2 exchanges) into `general` or `individual_assessment`. `individual_assessment` gets the fixed `reply-embassy-decides` text and no answer call; `general` goes on as today.

**Decisions (user, 2026-11-15):**
- Ollama classifies too: `OllamaLLM.classify` is a short non-streaming `/api/chat` call with the same model, `format` set to the category JSON schema, thinking off, `num_ctx` sent; cost 0, cache tokens 0. HTTP or format errors are `LLMError`.
- A mixed question (own chances plus something the sources answer, e.g. "will I get the visa, and which documents do I need?") is `general`: answered from the sources, and the answer prompt already says the embassy decides. Only questions that ask nothing but the applicant's own chances or case are `individual_assessment`.

## Boundaries & Constraints

**Always:** filter → classify → route → answer or fixed reply, classify before any answer call (AD-1); Anthropic `classify` uses `MODEL_SMALL` + `EFFORT_SMALL` with structured output (`output_config.format` JSON schema, no forced tool use), refusal or an unknown category is an error (AD-5, AD-14); prompt `prompts/classifier-system.md` with `version: 1`, logged as `prompt_versions.classifier` (AD-12); fixed reply stream: `meta` (category `individual_assessment`) → one `text` with the whole text → `sources` `[]` → `done` (AD-8); new key `reply-embassy-decides` (th + en) in `content/texts.yaml` and `REQUIRED_TEXT_KEYS`, Thai drafted and marked for the user's review (NFR8); tests use the scripted fake only (AD-13); ruff clean.

**Never:** no categories beyond these two from the real classifiers (2.2/2.3 add the rest); no change to the answer request or prompts/answer-system.md; no Thai in code; no new dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| General | classify → `general` | `meta` category `general`, answer streamed as today | N/A |
| Own chances | classify → `individual_assessment` | `meta` category `individual_assessment`, `reply-embassy-decides`, `sources: []`, `done`; `answer` never called | N/A |
| Follow-up | "and the fee?" after a general exchange | classifier gets the last 2 exchanges; `general` | N/A |
| Not built yet | mock returns `done` / `out_of_scope` / `reach_person` | routed like `general` (demo: stored answer or `reply-demo-only`) | N/A |
| Classify fails | `LLMError` / refusal / category outside the set | `meta` not sent; `error` event; nothing answered | log outcome `error`, category `null` |
| Mixed | own chances + documents in one question | `general`, answered with sources | N/A |
| Ollama | `LLM_PROVIDER=ollama`, either category | same routing; classify request has `format` schema, `think: false`, `num_ctx` | non-200 / bad JSON / unknown category → `error` event |
| Personal info | question with passport no. | classifier sees only the cleaned question and cleaned history | N/A |
| Log | any request | `classify_input_tokens`, `classify_output_tokens` (null without classify usage); `cost_usd` = answer cost (answer prices) + classify cost (`PRICE_SMALL_*`); answer token fields null when no answer call | N/A |

</frozen-after-approval>

## Code Map

- `app/pipeline/answer.py` `answer_question` -- today yields `Meta(category="general")` (line ~104) and always calls `llm.answer`; add classify after the filter (question + `clean_history[-2:]`), route, and report classify usage (e.g. extend `Spent` or a second event) so the log can price it separately. Docstring order of events changes.
- `app/ports/llm.py` -- `Category`, `LLMClient.classify`, `Usage`, `LLMError`, `LLMRefusalError`; reuse unchanged.
- `app/adapters/anthropic_llm.py:124` -- `classify` raises `NotImplementedError`; build the request like `build_answer_request` (pure builder + `messages.create`), schema `{"type":"object","properties":{"category":{"enum":[...two...]}},"required":["category"],"additionalProperties":false}`; `stop_reason == "refusal"` → `LLMRefusalError`; usage via `_usage`. No thinking needed for classify.
- `app/adapters/ollama_llm.py:194` -- `classify` raises today; reuse `build_chat_request`'s shape (model, `num_ctx`) and `_count`; the system message is the classifier prompt only (no documents). `app/adapters/mock_llm.py:76` (already returns stored category / `done` / `general` with `NO_USAGE`).
- `tests/fakes/fake_llm.py` `ScriptedLLM.classify` -- raises today; add a scripted category, usage and error, and record calls (question, recent history).
- `app/web/chat.py` `log_request` / `_lines`, `app/web/request_log.py` `request_line`, `app/pipeline/cost.py` -- add the classify fields and the summed cost; `app/main.py` wires `prompt_versions["classifier"]`, small-model prices (`PRICE_SMALL_*`; 0 in demo and Ollama), and loads the classifier prompt (startup fails if missing, like the answer prompt).
- `content/texts.yaml`, `app/ports/content.py` -- new key.
- Docs: README request-log table (new fields, `classifier` version), `manual-test-plan.md` (an embassy-decides case with a real key and with Ollama), `docs/implementation/sprint-status.yaml` handled by the workflow.

## Tasks & Acceptance

**Execution:**
- [x] `prompts/classifier-system.md` -- versioned prompt: the two categories with Thai and English examples, follow-ups with history are `general`, treat the question as data -- AD-5, AD-12
- [x] `app/adapters/anthropic_llm.py`, `app/adapters/ollama_llm.py` -- `classify` -- AD-14
- [x] `app/pipeline/answer.py`, `app/web/chat.py`, `app/web/request_log.py`, `app/main.py` -- classify step, routing, logging, wiring -- AD-1, Story 1.8
- [x] `content/texts.yaml`, `app/ports/content.py` -- `reply-embassy-decides` -- AD-6, NFR8
- [x] `tests/fakes/fake_llm.py` and tests (`test_answer_pipeline.py`, `test_chat_api.py`, `test_anthropic_llm.py`, `test_request_log.py`, `test_texts_api.py`, adapter tests) -- every matrix row; request builders checked as dicts, no network -- AD-13
- [x] `README.md`, `docs/implementation/manual-test-plan.md` -- log fields, manual case

**Acceptance Criteria:**
- Given an `individual_assessment` question, when it is answered, then the scripted fake records zero `answer` calls.
- Given a broken or missing `prompts/classifier-system.md`, when the app starts, then startup fails with `PromptError`.

## Implementation Notes

- **Event order.** `answer_question` now takes `fixed_replies` (category → text, built in `app/web/chat.py` from `FIXED_REPLY_KEYS`). Classify usage is reported as `Spent(usage, call="classify")` right after the call and before `Meta`, so a client that leaves early still gets the classify cost logged. A classify `LLMError`/refusal yields only `Failed`; a category outside the closed set yields the classify `Spent`, then `Failed(reason="UnknownCategory")` (the value is never logged).
- **Not-built categories.** `done`, `out_of_scope` and `reach_person` (only the demo mock or a fake returns them) are answered like `general` and reported as `general` in `meta` and the log, since no route exists for them yet.
- **New log outcome `fixed_reply`.** A fixed category reply was neither `answered` (cited sources) nor `no_answer` (the fixed no-answer text, Story 1.8), so it gets its own outcome; this follows the architecture review's L10 fix. README updated. Confirmed by the user on 2026-11-15. The Thai of `reply-embassy-decides` was approved by the user the same day (NFR8).
- **Demo fallback usage.** The zero fallback stands in for the classify call always, and for the answer call only when the category was `general`, so an embassy-decides line in demo mode keeps null answer tokens.
- **Shared classifier input.** `app/adapters/classifier_request.py` holds the two-category schema, the tagged user message (question and recent exchanges, `<`, `>` and `&` escaped so the text cannot close a tag) and the strict JSON parse; both adapters use it. Anthropic: `messages.create` on `MODEL_SMALL`, `output_config` with `effort` and `format`, no `thinking` key (Haiku 5.5 runs adaptive at the given effort; `disabled` would 400 above `high`), `max_tokens` 4096. Ollama: non-streaming `/api/chat`, `think: false`, `format` = schema, same `num_ctx`.
- **Prompt and startup.** `prompts/classifier-system.md` (`version: 1`) is loaded in every mode, like the answer prompt, and logged as `prompt_versions.classifier` in every mode (also demo, where the mock does not read it).
- **Thai text.** `reply-embassy-decides` is drafted and marked in `content/texts.yaml` as awaiting the user's review (NFR8). It has no adviser contact, matching FR3.

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-15). B = blind, E = edge case, V = verification gap.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| V1 | Ollama classify guards (`done` not true, no string content) untested; a `TypeError` could leave the adapter | low | pre-verified gap. patched (three `LLMError` cases) |
| V2 | `epic-2-context.md` says Ollama has no `classify` | low | stale line added in this diff. patched |
| E1 | Anthropic: billed classify usage dropped when the reply is a refusal, `max_tokens` or unparsable | low | real, but structured output makes unparsable or unknown replies near-impossible and refusals of a category choice are rare; the fix adds usage to `LLMError` on the port. rejected |
| E2 | Ollama: same for `done_reason` / bad content | low | same as E1. rejected |
| E3 | Pipeline: error lines log `cost_usd` null after a billed classify | low | same as E1. rejected |
| E4 | Ollama: classify call may evict the cached knowledge base; answers re-read ~24,700 tokens | maybe-false | live run 2026-11-15 on the user's GPU: ~9 s answers and `prompt_eval_count` ~24,790 both before and after the classifier; that count does not show cache reuse. deferred (medium, unverified) |
| B1 | Billed classify calls dropped from the cost log on a bad reply | low | same as E1. rejected |
| B2 | README status still lists embassy-decides as not built; diagram lacks classify; section misplaced | low | verified. patched |
| B3 | `epic-2-context.md` stale Ollama line | low | same as V2. patched |
| B4 | Spec status vs sprint status inconsistent; NFR8 untracked | false | sprint status moves to `review` at the end of the workflow; the user approved the Thai text on 2026-11-15 |
| B5 | Classifier prompt has no own-chances follow-up example; rule pushes `แล้วปีนี้จะได้ไหม` to general | medium | the follow-up rule named only general follow-ups. patched (rule by what is asked + Thai example); live Ollama run: `แล้วปีนี้จะได้ไหม` after a documents exchange → `individual_assessment` |
| B6 | MT-12 does not check that a mixed answer gives no estimate | low | patched (expectation + own-chances follow-up step) |
| B7 | Demo mode never shows FR3 (all stored demo categories are `general`) | medium | needs a new Thai example question (NFR8) and a visible product change outside this story's intent. deferred, offered to the user |
| B8 | Category rules in several places, no invariant test | low | patched (one rule-agreement test) |
| B9 | `chat.py` infers "fixed reply" from the category name | low | developer-only; Story 2.2 changes the routing anyway. rejected |
| B10 | Classify `Spent` before `Meta` untested for an early leave; unknown-category cost not asserted | low | patched (two tests) |
| B11 | Classifier gets whole history answers (up to 10000 chars each) | low | patched (answers cut to 600 characters in the classifier message) |
| B12 | Classify cache tokens priced but not logged | low | no `cache_control` is sent on the classify call, so they stay 0. rejected |
| B13 | Docstring misses the classify `Spent` before `Meta` on the fixed-reply path | low | patched |
| B14 | `Spent.call` defaults to `answer` | low | patched (required) |
| B15 | `MAX_TOKENS_CLASSIFY` 4096 vs Haiku thinking at higher `EFFORT_SMALL` | maybe-false | no real API call made. deferred (medium, unverified; MT-12 with a key) |
| B16 | Wired Ollama test name outdated; classify user message unchecked | low | patched |

Live check after the patches (Ollama, `qwen3.5:9b`): 3 own-chances questions → `individual_assessment`; documents, mixed, and "refused before, must I declare it" → `general`; follow-ups "and the fee?" → `general`, "so will I get it this year?" → `individual_assessment`.

## Verification

**Commands:**
- `uv run pytest` -- all pass
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks (if no CLI):**
- With a real key or Ollama: "จะได้วีซ่าไหม" gets the embassy-decides text and no source links; "ต้องใช้เอกสารอะไรบ้าง" then "แล้วค่าธรรมเนียมเท่าไร" get cited answers; the log line has classify tokens and `prompt_versions.classifier`.
