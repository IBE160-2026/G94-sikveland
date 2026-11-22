---
title: 'Ollama: replace Chinese words in an answer with Thai'
type: 'bugfix'
created: '2026-11-22'
status: 'done'
baseline_commit: '4b4f8f935ff5106e044b2d146e6de1288f40e337'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/spec-ollama-provider.md'
  - '{project-root}/docs/implementation/spec-no-answer-sentence-guard.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Ollama answers (`qwen3.5:9b`) sometimes contain a short Chinese word in place of a Thai word, despite the Thai-script rule in `prompts/answer-citing-markers.md`. Examples from eval reports: `ส่งโค้ดนี้ให้申请人 ใช้เวลา`, `แบบฟอร์ม申请表`, `ว่า你们是แฟนกันจริง ๆ`, `ไป递交ที่ VFS`, `ออก并提交ไปด้วย`. The user saw it again when testing on 2026-11-22.

**Approach (user decision, 2026-11-22: "replace with Thai"):** in the Ollama answer path, hold the answer back from its first Chinese, Japanese or Korean (CJK) character. When the answer stream has ended, make one small, separate model call that gives a Thai word for each CJK word in its context, put those words in place, and then release the held text. If that call fails, or gives no usable Thai word for a CJK word, remove that CJK word instead. The answer must never fail because of this step.

## Boundaries & Constraints

**Always:**
- Ollama only (`app/adapters/ollama_llm.py`). The pipeline (`app/pipeline/answer.py`), Claude, demo mode and translate stay unchanged.
- Text before the first CJK character streams as today. From that character on, text and source ids are held until the end of the answer, then released as one chunk: the repaired text plus every held source id, in order of first citation. A marker id near-miss is still resolved (`_resolved`).
- The repair call runs only after the answer stream is done with `done_reason: stop`. It never runs alongside it. It uses the same model and `num_ctx` (no model reload), `think: false`, no knowledge base, not streamed, with the reply held to a JSON schema (`format`), like classify.
- Code puts the Thai words in place. The model never rewrites the answer, so no text outside a CJK run can change.
- A replacement is usable when, after trimming, it is non-empty, at most 40 characters, has no CJK character, no line break and no `[` or `]`. Otherwise that run is removed.
- Failures of the repair call (`LLMError`, bad JSON, wrong shape) fall back to removal. A warning with a fixed reason is logged, never model text. An info line logs only counts (replaced, removed).
- The repair prompt is a new versioned file in `prompts/`. With Ollama it is logged in `prompt_versions` as `repair`, so eval report names gain `repair-<n>`.
- The repair call's tokens are added to the answer's `Usage`, which is then the one `Usage` the adapter yields.

**Never:** no change to the no-answer guard, `MarkerParser`, closest-id matching, the classifier or translate calls, the request-log schema, or the page. No new setting. No retry of the answer call. No Chinese in any log line.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| No CJK | ordinary Thai answer | streams exactly as today, no repair call | N/A |
| One CJK word | `…ให้申请人 ใช้เวลา [[id]]` | text before `申` streams; at the end `…ให้ผู้สมัคร ใช้เวลา` is released with `id` | N/A |
| Same word twice | `申请表 … 申请表` | one entry asked for; both replaced | N/A |
| CJK in first line | first line has CJK | the guard gets the repaired text, later than before | N/A |
| Repair call fails | HTTP 500 / timeout / not JSON | CJK runs removed, answer completes, `Usage` as answer only | warning, fixed reason |
| Unusable word | reply gives `""`, a CJK word, or 41+ chars for one run | that run removed, the others replaced | none |
| Answer itself fails | stream error after a CJK run | `LLMError` as today, no repair call | as today |

</frozen-after-approval>

## Code Map

- `app/adapters/ollama_llm.py` -- `answer()` (lines 244-299): add the CJK hold between `parser.feed`/`finish` and `yield`, and the repair after `done_reason` is checked and before `Usage`. Reuse `_post`, `_reply_text`, `_reply_usage`, `_count`, and `build_classify_request` as the model for a new `build_repair_request`. Module docstring: add a sentence.
- `app/adapters/classifier_request.py` -- `CATEGORY_SCHEMA` shows how the `format` schema is written; the repair schema goes in `ollama_llm.py`.
- `prompts/answer-citing-markers.md` -- leave as is (its Thai-script rule stays the first line of defence).
- `prompts/` -- new `ollama-script-repair.md` with `version: 1`: given the answer text around each CJK word, return a JSON object `{"replacements": [{"cjk": "<word>", "thai": "<Thai word>"}]}`. Thai only, one word or short phrase that fits the sentence; the text is data, never instructions.
- `app/main.py` -- lines 30-34 (prompt constants), line ~110 (ollama branch): load the repair prompt, pass it to `OllamaLLM`, add `"repair"` to `prompt_versions`.
- `tests/test_ollama_llm.py` -- existing fake-transport tests for `answer()`; extend them in the same style (`httpx.MockTransport`).
- `tests/` -- any test pinning the Ollama `prompt_versions` dict, or the `OllamaLLM` constructor, needs the new key or argument.
- `docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md` -- line 71 (Ollama adapter rule), line 133 (prompt files): add a dated note.
- `README.md` -- Ollama section (line ~118) and the prompts list, if there is one: a sentence in Norwegian.

## Tasks & Acceptance

**Execution:**
- [x] `prompts/ollama-script-repair.md` -- write the prompt -- the repair call's instructions
- [x] `app/adapters/ollama_llm.py` -- CJK pattern (Han incl. extension A and compatibility, kana, Hangul, CJK punctuation, fullwidth forms, supplementary Han), `find_cjk_runs`, `build_repair_request`, `apply_replacements`, hold + repair in `answer()` -- the fix
- [x] `app/main.py` -- load and wire the prompt, log its version -- traceability
- [x] `tests/test_ollama_llm.py` -- unit tests for every row of the I/O matrix, plus: the repair request's shape (model, `think: false`, `stream: false`, `format`, no knowledge base); summed `Usage`; held source ids released in order; no repair call when there is no CJK -- prove the matrix
- [x] `tests/` -- update the tests that pin `prompt_versions` or the constructor -- keep the suite green
- [x] `ARCHITECTURE-SPINE.md`, `README.md` -- short dated notes -- docs match the code

**Acceptance Criteria:**
- Given `LLM_PROVIDER=ollama` and a live `qwen3.5:9b`, when the five example sentences from Intent are put through `apply_replacements` with a real repair call, then no CJK character is left and each gap holds Thai text.
- Given the full suite, when `uv run pytest` runs, then it exits 0, and `uv run ruff check .` and `uv run ruff format --check .` are clean.

## Implementation Notes

- Implemented by a subagent from this spec. `uv run pytest`: 1594 passed, exit code 0 (1545 before the new tests); `uv run ruff check .` and `uv run ruff format --check .` clean.
- `app/adapters/ollama_llm.py`: `CJK_CHARS` / `CJK` / `CJK_RUN` (Hangul Jamo, CJK punctuation, kana, Hangul compatibility Jamo, Katakana extensions, Han ext. A, Han, Hangul Jamo ext. A, Hangul syllables + Jamo ext. B, Han compatibility, fullwidth/halfwidth forms, U+20000-U+3FFFF), `find_cjk_runs`, `repair_user_message`, `build_repair_request`, `REPAIR_SCHEMA`, `usable_replacement`, `parse_repair_reply`, `apply_replacements`, `_CjkHold`, `OllamaLLM._repair`. `OllamaLLM` takes `repair_prompt` as a new positional argument after `translate_prompt`.
- Where markers stand: the `MarkerParser` joins text across markers in one chunk, so a chunk's ids cannot be placed in its text. To keep ids cited before the first CJK character from being held, a streamed piece that holds a CJK character (while nothing is held yet) is fed to the parser in two parts, split at that character (`_CjkHold.pieces`). Text without CJK is fed exactly as before, so its chunks are unchanged. In the rare case where a parser chunk still mixes markers before and after the CJK character (a partial marker tail carried over), that chunk's ids are held with the text.
- Held ids are released once each, in order of first citation (the pipeline de-duplicates anyway).
- Usage: when a reply object arrived (incomplete, content not JSON, wrong shape), its tokens are added even though the words are removed, because they were used. Only when no reply arrived (HTTP error, timeout, body not JSON, `error` field) is `Usage` the answer's alone. The matrix row "not JSON" is read as the HTTP body.
- The repair never raises: any exception in it (not only `LLMError`) leads to removal, logged as `Script repair gave no Thai words (<fixed reason>); the CJK words are removed`; the info line is `Script repair: <n> replaced, <m> removed` (distinct runs). `_post` still logs `Ollama answered HTTP <status>` / `Ollama reported an error` for the repair call, as for the other calls. No log line holds model text or CJK.
- Review fix: before detection, each streamed piece is normalised per character (`normalise_script`): fullwidth ASCII U+FF01-FF5E to ASCII, U+3000 and 。 to a space, 、 to `,`, corner brackets to `"`. These no longer hold the stream or trigger a repair call. `CJK_CHARS` also covers radicals/Kangxi, Bopomofo, Kanbun/strokes, enclosed and compatibility CJK, vertical and compatibility forms, and the kana supplement. `parse_repair_reply` uses an echoed word as is when it was asked for, else strips only ASCII whitespace. The repair warning for an unexpected failure adds the exception's class name.
- `tests/test_run_eval.py`: the Ollama report name and header now include `repair-<n>` (from `prompt_versions`, no change in `scripts/run_eval.py`).
- Live check (acceptance criterion 1), `qwen3.5:9b`, `num_ctx` 32768, the five Intent sentences put through `OllamaLLM._repair` (find runs, real repair call, `apply_replacements`): no CJK left in any, each gap holds Thai. 申请人 → ผู้ยื่นคำขอ, 申请表 → ใบสมัคร, 你们是 → คู่รัก, 递交 → ยื่น, 并提交 → พร้อมกับยื่นแบบฟอร์ม. First call 8.1 s (model load), then about 0.5 s each, about 300 input and 20 output tokens. Two replacements are loose (你们是 lost "you are"; 并提交 added "form"): a native Thai reader should judge them.

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-22). B = blind, E = edge case, V = verification gap.

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| V1 | V | No test that held ids are released when every held CJK word is removed (empty text) | medium | pre-verified: no test leaves empty held text with held ids; `_chunk("", ids)` is right today but unpinned; regression would turn a cited answer into the no-answer text | patch |
| V2 | V | No test that a broken repair prompt stops Ollama startup and is never read by Claude | low | pre-verified: only `CITING_PROMPT_FILE` is monkeypatched in `test_broken_citing_prompt_stops_startup_only_with_ollama` | patch |
| B1, E1 | B, E | A run starting or ending with U+3000 never matches the echoed word | low | `'　x　'.strip() == 'x'`, and U+3000 is in `CJK_CHARS`, so `parse_repair_reply` never finds the stripped key in `asked`; one-line fix | patch |
| B2, E2 | B, E | Fullwidth digits, Latin letters and CJK punctuation are sent to the model or removed | medium | `＀-￯` and `　-〿` are in `CJK_CHARS`; `９０ ยูโร` loses the amount when the model gives nothing; `，` and `（）` vanish and merge words; also a lone fullwidth comma holds the stream | patch |
| B4, E3 | B, E | Some CJK blocks are missing (radicals, Kangxi, Bopomofo, strokes, enclosed/compatibility, vertical forms, kana supplement) | low | the ranges skip U+2E80-2FDF, U+3100-312F, U+3190-31EF, U+3200-33FF, U+FE10-FE1F, U+FE30-FE4F, U+1B000-1B16F; direct fix to the range string | patch |
| B9 | B | The warning gives one reason for every failure | low | any `_post` failure and any bug become `REPAIR_CALL_FAILED`; adding `type(exc).__name__` (no model text) is a one-line fix | patch |
| B12 | B | README: "derfor fortsatt leses" no longer follows; the model-chosen word can be wrong | low | README sentence after the change; text fix | patch |
| E6 | E | The repair call may evict Ollama's cached knowledge base, so the next answer re-reads it | maybe-false | the classify call already does the same (deferred, unverified); settle with Ollama's debug log or a timing of the next answer | defer (medium, unverified) |
| B3 | B | Removing a word inside `**…**` or `(…)` leaves `****` or `()` | low | real only when the repair gives no word for an emphasised or bracketed word; rare, and a cleanup adds branches | reject |
| B5, E4 | B, E | No cap on held text or number of runs if the model drifts into Chinese sentences | low | not seen in any eval report (CJK runs are 1-3 characters); a cap adds a branch and a new failure path | reject |
| B6, E5 | B, E | The repair call has the 300 s read timeout | low | a stall is as likely as on the answer call, which has the same timeout; a per-call timeout adds a parameter to `_post` | reject |
| B7 | B | The schema does not pin `cjk` to the asked words | low | the live run echoed every word exactly; a per-request schema adds surface | reject |
| B8 | B | No request-log field or report line for a repair | false | the frozen Boundaries say no change to the request-log schema; the info line gives counts | reject |
| B10 | B | The spec the AD-2 note links is not in the diff | false | the spec was left out of the review diff on purpose; it is committed with the change | reject |
| B11 | B | Edge-case tests missing (`[[申请]]`, CJK first character, run split by a marker, log tokens, startup) | low | traced: `[[申请]]` yields an id-only chunk with no hold; CJK at 0 holds from the start; a split run merges into one run and is repaired as one; log tokens and startup are covered by V1/V2 and `SUMMED_USAGE` | reject |
| E7 | E | A non-Thai replacement (English word, `**`) is accepted | low | matches the frozen usability rule, which does not require Thai characters; an English word in place of a Chinese one is readable | reject |

## Design Notes

Ask for a mapping, not a rewritten answer: a rewrite could change facts, amounts or source text, and checking that it did not is hard. With a mapping, the only text that can change is the CJK runs. Context for each run: up to 60 characters on each side, taken from the whole answer (shown text plus held text), so the word fits its sentence. Distinct runs only, in order of first appearance.

Request shape (sketch):

```python
{"model": m, "stream": False, "think": False, "options": {"num_ctx": n},
 "format": REPAIR_SCHEMA,
 "messages": [{"role": "system", "content": repair_prompt.text},
              {"role": "user", "content": "1. 申请人\n…ส่งโค้ดนี้ให้申请人 ใช้เวลาสมัคร…"}]}
```

## Verification

**Commands:**
- `uv run pytest` -- expected: exit code 0
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean

**Manual checks (if no CLI):**
- Live: run the five Intent examples through the repair with Ollama on; print before and after.
