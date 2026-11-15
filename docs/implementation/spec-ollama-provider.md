---
title: 'Ollama as an alternative model provider'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '2ee521a3718c61da3a243eebe8e8249c86fbf5bb'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Answers can only come from Claude, so the app depends on one paid AI service and cannot run real answers without an Anthropic key.

**Approach:** Add an Ollama adapter behind the existing `LLMClient` port, chosen by a new `LLM_PROVIDER` setting (`anthropic` default, `ollama`). Without Claude's Citations, the Ollama model marks sources as `[[source-id]]`; the adapter turns markers into `source_ids` and strips them from the text.

**Decisions (user, 2026-11-15):**
- Option, not replacement: Claude stays the default and its request is unchanged; demo mode (`MOCK_LLM=true`) wins over `LLM_PROVIDER` and is unchanged.
- Thinking on for Ollama (`"think": true`); thinking text is never shown, stored or logged.
- An unknown cited source id is dropped (no link for it) and the rest of the answer is shown, for every provider; the request log records how many were dropped.
- Docs (README, manual test plan, architecture spine, PRD addendum) are split off to `deferred-work.md` and done before the branch is merged; this spec is code and tests only.

## Boundaries & Constraints

**Always:** the pipeline order, stream contract and zero-citation → `reply-no-answer` rule stay as they are (AD-1, AD-7, AD-8); sources are sent sorted by `id` in a fixed layout so Ollama can reuse the cached prompt; every Ollama request sends `options.num_ctx` (default 32768; Ollama's own default of 4096 silently cuts the ~24,600-token knowledge base); no SDK or `httpx` type leaves the adapter, failures are `LLMError`; tests never call a real Ollama (AD-13); ruff clean.

**Never:** no new dependency (use `httpx`); no change to Thai texts in `content/` (NFR8); no change to `prompts/answer-system.md` (Claude's prompt); no change to `anthropic_llm.py` request building; no classifier/translate for Ollama (raise `NotImplementedError` like the Anthropic adapter).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cited answer | stream `"90 ยูโร [[udi-fees]]."` | chunk text `"90 ยูโร."`, `source_ids ("udi-fees",)` | N/A |
| Split marker | `"ข้อมูล [["`, `"udi-"`, `"fees]] ต่อ"` | markers never shown; id arrives once complete | N/A |
| Adjacent markers | `"x [[a]][[b]]"` | text `"x"`, ids `a`, `b` | N/A |
| Not a marker | `"[1]"`, `"[["` left open at end | shown as written (open `[[` flushed at end) | N/A |
| Thinking | `message.thinking` pieces | ignored | N/A |
| No citations | text only | pipeline sends `reply-no-answer` | N/A |
| Unknown id | id not in `sources.yaml` | id dropped, answer continues; log `unknown_source_ids: 1` | no `Failed` |
| Only unknown ids | all cited ids unknown | `reply-no-answer` | N/A |
| Ollama down / HTTP ≠ 200 / bad JSON line / `error` field | — | `LLMError` → page shows fixed error text | N/A |
| Cut off | `done_reason` other than `stop` | `LLMError` (incomplete) | N/A |
| Usage | final line | `Usage(prompt_eval_count, eval_count, 0, 0)`, cost 0.0 | missing counts → 0 |

</frozen-after-approval>

## Code Map

- `app/ports/llm.py` -- `LLMClient`, `AnswerChunk`, `Usage`, `LLMError`; reuse unchanged.
- `app/adapters/anthropic_llm.py` -- pattern to mirror (constructor with injectable client, sorted documents, `stop_reason` check); do not change.
- `app/pipeline/answer.py:107-113` -- `except KeyError: yield Failed("unknown source id")` becomes drop-and-count; `Sources` gains a count of dropped ids.
- `app/web/chat.py` `_lines`/`log_request` -- read the dropped count from `Sources`, pass to the log line.
- `app/web/request_log.py` `request_line` -- new field `unknown_source_ids` (int, 0 when none, `null` if the stream ended before `Sources`); `prompt_versions` may hold more keys.
- `app/main.py:60-77` -- wiring: `mock_llm` → demo; else by `settings.llm_provider`; Ollama: `answer_model = ollama_model`, prices all 0, `fallback_usage = None`.
- `app/config.py` -- add `llm_provider: Literal["anthropic","ollama"]="anthropic"`, `ollama_base_url="http://localhost:11434"`, `ollama_model="qwen3.5:9b"`, `ollama_num_ctx` (int ≥ 4096, default 32768).
- `app/adapters/file_prompts.py` `load_prompt` -- reuse for the new prompt file.
- `tests/test_config.py:78-93` -- `.env.example` must list every setting with a valid value.
- `tests/test_answer_pipeline.py:184` -- expects `Failed("unknown source id")`; update.
- `tests/test_layering.py` -- keep passing; `anthropic` only in its adapter.
- Probe that proved the format: `<document id="…" title="…">text</document>` blocks after the prompt, `/api/chat` JSON lines with `message.content`, `message.thinking`, `done`, `done_reason`, `prompt_eval_count`, `eval_count`.

## Tasks & Acceptance

**Execution:**
- [x] `prompts/answer-citing-markers.md` -- new versioned prompt part: after each sentence or list item write `[[id]]` for every document it rests on, only ids from the documents, cite nothing when the documents do not answer -- the marker contract.
- [x] `app/config.py`, `.env.example` -- the four settings, with comments -- provider choice.
- [x] `app/adapters/ollama_llm.py` -- `OllamaLLM(settings, knowledge_base, prompt, citing_prompt, client=None)`: system = answer prompt + citing prompt + document blocks; history as alternating plain messages; stream `/api/chat` with `think: true`, `options.num_ctx`; incremental marker parser (strip marker and whitespace before it); `Usage` last; timeouts (connect short, read ≥ 120 s) -- the adapter.
- [x] `app/pipeline/answer.py`, `app/web/chat.py`, `app/web/request_log.py` -- drop unknown ids, count, log -- decision 3.
- [x] `app/main.py` -- wiring; log `prompt_versions` `{"answer", "citing"}` for Ollama -- provider switch.
- [x] `tests/test_ollama_llm.py` (httpx `MockTransport`), `tests/test_answer_pipeline.py`, `tests/test_request_log.py`, `tests/test_chat_api.py`, `tests/test_config.py` -- matrix rows, wiring by setting, log field.

**Acceptance Criteria:**
- Given no `LLM_PROVIDER`, when the app starts, then Claude is used exactly as before (all existing tests pass unchanged except the unknown-id test).
- Given `LLM_PROVIDER=ollama` and `MOCK_LLM=true`, when the app starts, then demo mode is used.
- Given `LLM_PROVIDER=ollama`, when a question is answered, then the log line has `model` = `OLLAMA_MODEL`, `cost_usd` 0.0, cache tokens 0, and no question or answer text.
- Given a local Ollama with the model and `LLM_PROVIDER=ollama`, when an example question is tapped, then a Thai answer streams with working source links.

## Implementation Notes

- Implemented by a subagent from this spec; 661 tests pass (584 before), ruff clean. Manual run through the real app against local Ollama `qwen3.5:9b`: fee question streamed a Thai answer without brackets, sources `embassy-online-registration` and `udi-fees` (19.7 s); weather question gave exactly `reply-no-answer` (4.9 s); log lines had `model: qwen3.5:9b`, `cost_usd: 0.0`, cache tokens 0, `prompt_versions {"answer":"1","citing":"1"}`, `unknown_source_ids: 0`. Not yet tapped in a browser.
- `httpx` was forbidden everywhere in `app/` by `tests/test_knowledge_base.py::test_app_never_fetches_over_the_network`; only `app/adapters/ollama_llm.py` is exempted, and `tests/test_layering.py` now checks that it is the only `httpx` importer and that pipeline/ports import none.
- AC 1 holds for behaviour (Claude's request and answers are unchanged), but more existing tests changed than "the unknown-id test": the new log field and the `prompt_versions` mapping in `request_line` touched field lists and expected log dicts, and the unknown-source case left the error-log test because it is no longer an error.
- Read timeout 300 s (spec: at least 120 s): the first, uncached prompt is ~24,700 tokens and can be slow on weaker machines.
- Known limits: Ollama reports `prompt_eval_count` ~24,700 also when it reused its cached prompt, so `input_tokens` overstates the work (cost is 0 either way); document text is not escaped inside `<document>` blocks (only `id` and `title` attributes), so a snapshot containing `</document>` would break a block; none does today.

- Review pass 1: 8 patches applied by the implementing subagent (wiring test, `OLLAMA_NUM_CTX` minimum 32768, thinking-model note, operator warnings for HTTP status and error lines, keep line breaks before markers, network guard narrowed to `httpx`, neutral citing-prompt examples, websites named in text); 5 findings deferred to `deferred-work.md`; 7 rejected. 668 tests pass, ruff clean.
- Live re-run after the patches, through the app against `qwen3.5:9b`: fee and how-to-start questions answered with sources and no brackets (7.5–27.6 s); the weather question got `reply-no-answer`; one answer cited an unknown id, which was dropped and logged as `unknown_source_ids: 1` while the answer still came through. The fee answer contained Chinese words inside the Thai (探亲, 递交): a model quality issue, not handled by this spec.

## Spec Change Log

- 2026-11-15: `prompts/answer-citing-markers.md` version 2 adds a Thai-script rule ("write the answer in Thai script, never Chinese, Japanese or Korean characters or punctuation; Latin only for names and ids"), because a live run had Chinese words in the Thai. Live check through the app (`qwen3.5:9b`, `num_ctx` 32768, 6 questions × 6 runs per version, single-turn): version 1 had 5/36 answers with non-Thai script (Chinese words 行程, 结婚证 in 2; only the Chinese full stop 。 in 2; an Arabic word in 1), version 2 had 2/36 (探亲 in a fee answer; 。 in 1). No errors; 2/36 answers without sources in both. Fewer, not zero, and too few answers to prove the rule works: a native Thai reader still judges Ollama's Thai (NFR8). Claude's prompt is unchanged.

## Review Triage Log

Review pass 1 (2026-11-15): blind hunter (B), edge-case hunter (E), verification gap (V).

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | V | `create_app` wiring of `OllamaLLM` checked only by type; swapped or wrong prompts would pass | medium | pre-verified: no test sends a question through the default-built adapter; streaming tests build their own | patch (test that the default-built adapter's system message holds both prompts and a document block) |
| 2 | B, E | `OLLAMA_NUM_CTX` accepts 4096, the value that cuts the ~24,600-token knowledge base | medium | `Field(ge=4096)`; the probe showed Ollama loads with the requested context and the prompt is ~24,600 tokens | patch (minimum 32768, comments and tests) |
| 3 | B, E | No context budget for history + thinking + answer; overflow can truncate or end with `length` | maybe-false | 32768 − ~24,700 leaves ~8k; probe thinking used up to ~2,700 tokens; not run with 10 long turns | defer (medium, unverified; settle with a 10-turn manual run) |
| 4 | B, E | `think: true` always sent; models without thinking get HTTP 400 | low | Ollama rejects `think` for non-thinking models; the user chose thinking on, so only the setting's comment is missing | patch (`.env.example`: the model must support thinking) |
| 5 | B, E | No cap on generation or overall deadline; a thinking loop keeps the request open | maybe-false | read timeout restarts on every thinking line; no `num_predict`; never observed | defer (medium, unverified; settle by forcing a long thinking run) |
| 6 | E | First byte after > 300 s on slow (CPU-only) hardware fails every cold request | maybe-false | 7 s on the user's GPU; CPU prefill of ~24,700 tokens can take minutes; no data | defer (medium, unverified; settle on a CPU-only machine) |
| 7 | B | Operator cannot tell "model not pulled" from "Ollama down": status and error category never logged | low | adapter has no logger; `chat.py:138` logs only the class name `LLMError`; setup mistakes are likely | patch (log HTTP status and a fixed reason in the adapter, never the body) |
| 8 | B | History shows the model its own answers without markers, so follow-ups may stop citing | maybe-false | manual run was single-turn only | defer (medium, unverified; settle with a follow-up question against Ollama) |
| 9 | B, E | `\s*` before a marker also strips line breaks; paragraphs and list items merge | medium | verified: a paragraph break, then `[[a]] 2`, after `1.` becomes `"1. 2"` | patch (strip only spaces and tabs, in `_MARKER` and `_OPEN_TAIL`; test the case) |
| 10 | B, E | Network-guard test exempts the whole adapter, so `requests`/`urllib` there would go unnoticed | low | `test_knowledge_base.py` skips the file entirely; direct fix | patch (exempt only `httpx` for that file) |
| 11 | B | Deferred docs entry misses stale items (README log table and cache check, test plan cache check, spec 1-8 log contract, spec 1-6 `Failed` reason) and the browser check | low | each named place still describes the old behaviour | defer (new deferred-work entry) |
| 12 | B | Citing prompt example states a real fact (`90 ยูโร [[udi-fees]]`) the model could repeat | low | `prompts/answer-citing-markers.md` line 5; direct edit | patch (neutral placeholder) |
| 13 | B | "never cite a website address" can read as conflicting with "name the website of each step" | low | `answer-system.md` asks for website names; direct edit | patch (websites are named in the text; only ids go inside `[[ ]]`) |
| 14 | B | `httpx.Client` never closed | low | one client per app lifetime, freed at exit; a lifespan hook adds code for no observed harm | reject |
| 15 | B | Same unknown id cited twice not tested; operator guidance missing | false | `test_unknown_id_before_a_known_one…` cites `nope` twice and expects 2 distinct; guidance belongs to the deferred docs | reject |
| 16 | E | Blank or schemeless `OLLAMA_BASE_URL`/`OLLAMA_MODEL` pass validation | low | an operator typo; every answer fails loudly with the error text | reject |
| 17 | E | `HTTP_PROXY` without `NO_PROXY` would route local calls through a proxy | low | no proxy set on the user's machine (Ollama log shows empty proxy vars) | reject |
| 18 | E | Snapshot text with `</document>` breaks a block | low | no snapshot contains document tags today; escaping all text would change what the model reads | reject |
| 19 | E | Ids with other case or trailing punctuation are dropped as unknown | maybe-false | not seen in 6 probe answers; the new `unknown_source_ids` count would show it | reject (only low if real) |
| 20 | E | AC 1 says existing tests are unchanged except one, but more changed and Claude log lines gain a field | low | true and already recorded in Implementation Notes; the fix would be editing this spec | reject |

## Design Notes

Marker parsing holds back any tail that could still become a marker (trailing whitespace, `[`, `[[`, `[[partial-id`, `[[id]`), so a split marker is never shown. A marker body is any run of non-bracket, non-newline characters up to 80 long; non-kebab bodies pass through as ids and are dropped by the pipeline as unknown. Ollama's prompt prefix cache needs the system message to be byte-identical between requests, hence sorted documents and no per-request data in it.

## Verification

**Commands:**
- `uv run pytest` -- all pass
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks:**
- `LLM_PROVIDER=ollama`, Ollama running with `qwen3.5:9b`: fee question gives Thai answer with source links; weather question gives `reply-no-answer`; `data/requests.jsonl` line as in the ACs.
