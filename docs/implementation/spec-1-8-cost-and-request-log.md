---
title: 'Story 1.8: Cost and request log'
type: 'feature'
created: '2026-11-14'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'cec76044eb3c12ec7868d2f3df05c47323ce51ba'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The adviser cannot see what a question costs or whether the prompt cache works: the pipeline drops the `Usage` the adapter returns, and nothing is logged.

**Approach:** Pass `Usage` through the pipeline, price it with the settings for the model that was called (cache reads and writes priced separately), and have `app/web` write one JSON line per finished chat request with no question or answer text (NFR5, NFR6, AD-12). Explain in the README how to read the log.

**Decision (user, 2026-11-14):** the log is the file `data/requests.jsonl`, set by the new setting `REQUEST_LOG_PATH` (default `data/requests.jsonl`, a relative path is resolved against the project root). `data/` is already git-ignored.

## Boundaries & Constraints

**Always:** one line per `/api/chat` request whose stream started, written when the stream ends (also on error or client disconnect). Fields: `timestamp` (UTC, ISO 8601, `Z`), `outcome` (`answered` = cited sources, `no_answer` = fixed no-answer reply, `error`, `incomplete` = client went away), `category`, `prompt_versions` (`{"answer": <version>}`), `model`, `input_tokens`, `output_tokens` (includes thinking), `cache_read_tokens`, `cache_write_tokens`, `cost_usd` (6 decimals). Token fields and `cost_usd` are `null` when no `Usage` arrived. Cost = (input × `PRICE_*_INPUT` + output × `PRICE_*_OUTPUT` + cache_read × `PRICE_*_CACHE_READ` + cache_write × `PRICE_*_CACHE_WRITE`) / 1 000 000, with the `ANSWER` prices for the answer call. A failure to write the log never breaks the answer.

**Never:** no question text, answer text, clean question, history, source titles or personal-information flags of the content in the line; no logging of 422 requests (the model is not called); no database; no change to the stream events the page receives.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Cited answer | fake yields cited text, `Usage(1000, 200, 50000, 0)` | one line: `outcome: "answered"`, tokens as given, `cost_usd` = (1000×4 + 200×20 + 50000×0.2 + 0×5)/1e6 = 0.018 with default prices | N/A |
| No answer | zero citations, `Usage` | `outcome: "no_answer"`, tokens and cost set | N/A |
| Error | fake raises before `Usage` | `outcome: "error"`, tokens and `cost_usd` `null` | stream still ends with `error` |
| Client gone | stream closed by the client mid-answer | `outcome: "incomplete"` | N/A |
| Privacy | question with a passport number, cited answer | the line contains neither the question, the answer text nor the passport number | N/A |
| Log not writable | log path points to a folder that cannot be created/written | answer streams normally; the problem is reported once to the app logger by class name | N/A |
| Bad request | 422 | no line written | N/A |

</frozen-after-approval>

## Code Map

- `app/pipeline/answer.py` -- `answer_question` breaks on `Usage` and drops it; events `Meta/TextDelta/Sources/Done/Failed`. Add a `Spent(usage)` event yielded after `Sources` and before `Done` when `Usage` arrived (the page never sees it).
- `app/web/chat.py` -- `_lines(events)` builds the JSONL stream; the only place that knows when the stream ends. Collect category, outcome and usage here and write the line in a `finally`.
- `app/main.py` -- `app.state.answer_prompt.version`, `app.state.settings.model_answer`; create the request log here.
- `app/config.py` -- `price_answer_*`, `price_small_*` already exist; `.env.example` must list every setting (`tests/test_config.py::test_env_example_lists_every_setting`).
- `tests/test_answer_pipeline.py`, `tests/test_chat_api.py` -- compare exact event lists; update for `Spent`.
- `README.md` -- Norwegian group README (headings `Medlemmer`, `Dokumentasjon`); add a short section in the same language.

## Tasks & Acceptance

**Execution:**
- [x] `app/pipeline/cost.py` -- `Prices(input, output, cache_read, cache_write)` frozen dataclass and `cost_usd(usage, prices) -> float` (pure).
- [x] `app/pipeline/answer.py` -- `Spent(usage: Usage)` event as in the Code Map.
- [x] `app/web/request_log.py` -- `RequestLog` that appends one JSON line (`ensure_ascii=False`) under a lock, creates the folder if needed, and swallows write errors after one warning; `answer_prices(settings) -> Prices`.
- [x] `app/web/chat.py` -- build and write the line per the Boundaries and matrix.
- [x] `app/main.py`, `app/config.py`, `.env.example` -- wire the log to `REQUEST_LOG_PATH` (Decision); tests can point it to `tmp_path`.
- [x] `tests/test_cost.py`, `tests/test_request_log.py`, updates in `tests/test_answer_pipeline.py` and `tests/test_chat_api.py` -- every matrix row; the exact cost from the matrix; field set of the line is exactly the list in Boundaries.
- [x] `README.md` -- short section: where the log is, one line per question, what the fields mean, how to see cache use (`cache_read_tokens` > 0 from the second question within 5 minutes) and total cost (a one-line `uv run python -c ...` summing `cost_usd`).

**Acceptance Criteria:**
- Given `uv run pytest`, when it runs, then all tests pass without network or key.
- Given two questions within 5 minutes with a real key, when I read the log, then the second line has `cache_read_tokens` > 0 and a lower `cost_usd` than the first (manual).

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass.

## Implementation Notes

- `Spent` is yielded before `Sources` (the Code Map said after), so a client that leaves at `Sources` still has its billed tokens and cost logged.
- `Spent` is consumed in `app/web/chat.py::_lines` and never becomes a stream event; the page's events are unchanged.
- The line is written in `_lines`' `finally`. `incomplete` relies on the server closing the stream generator when the client goes away: Starlette 1.10 does not close it explicitly, so CPython closes it when the abandoned generator is collected (checked by hand under uvicorn with a raw socket that disconnects mid-answer: one `incomplete` line). A stream that never started writes nothing.
- `outcome` is `answered`/`no_answer` only once `done` is reached; it is `error` on `Failed` or any exception.
- The test `settings` fixture (`tests/conftest.py`) points `REQUEST_LOG_PATH` to `tmp_path`, so tests never write to `data/`.
- Timestamps have millisecond precision (`2026-11-14T09:30:05.123Z`).

## Spec Change Log

- 2026-11-15, [spec-ollama-provider.md](spec-ollama-provider.md): the log line has one more field, `unknown_source_ids` (number of cited ids not in `sources.yaml` that were dropped; 0 when none; `null` if the stream ended before the sources). `prompt_versions` may hold more keys than `answer`: with `LLM_PROVIDER=ollama` it also holds `citing` (`prompts/answer-citing-markers.md`). With Ollama, `model` is `OLLAMA_MODEL`, all prices are 0 so `cost_usd` is 0, and both cache fields are 0 because Ollama does not report them, so the cache check in this spec and the README applies to Claude only. The frozen field list above is left as approved.

## Review Triage Log

Pass 1 (2026-11-14):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | blind, verif (other), edge | Refusal and `max_tokens` calls are billed but logged with null cost | low | the adapter raises before yielding `Usage` (Story 1.5 triage #13); both outcomes are rare and the fix adds usage to the error contract. rejected; README says null-cost lines are not counted (#2) |
| 2 | blind | `error`/`incomplete` lines have null cost, so the README total runs low without saying so | low | real. patched (README: the total is a lower bound) |
| 3 | edge | GC finalizer can re-enter `RequestLog.write` in a thread already holding the non-reentrant lock and deadlock it | medium | `_lines`' `finally` runs on GC, which can happen inside the locked section. patched (`RLock`) |
| 4 | edge | Client leaving at the `Sources` yield after `Usage` arrived logs a billed call as incomplete with null cost | low | `Spent` came after `Sources`. patched (`Spent` before `Sources`) |
| 5 | blind, verif, edge | Upstream generator not closed in `_lines`; disconnect depends on GC; no route-level disconnect test | maybe-false | GC closes it in CPython; covered by the Story 1.6 deferred entry (timeouts and disconnect check). patched the explicit `events.close()`; the route-level test stays deferred (carried) |
| 6 | verif (other) | Test comment says the server closes the generator; GC does | low | real. patched |
| 7 | blind, edge | Only the first write failure is ever reported | low | `_warned` never reset. patched (reset after a successful write) |
| 8 | blind, edge | README total-cost one-liner crashes on a blank or half-written line | low | `json.loads` on every line. patched (skip blank lines) |
| 9 | edge | `category` is null when a request fails before `Meta`; README says always `general` | low | real. patched (README) |
| 10 | blind | Import out of order in `app/web/chat.py` | low | real. patched |
| 11 | blind, edge | `threading.Lock` is per process; several uvicorn workers could interleave lines | low | the app runs as one uvicorn process. rejected |
| 12 | blind | No rotation or retention of the log | low | a few hundred bytes per question; small app. rejected |
| 13 | edge | Stream closed before its first event writes no line | false | the spec logs requests "whose stream started". rejected |
| 14 | edge | Empty, directory, `~` or root-relative `REQUEST_LOG_PATH` | low | empty values fall back to the default (`env_ignore_empty`); a bad path warns and the answer still works. rejected |
| 15 | edge | Cost below 1e-4 serialized as `4e-06` | low | an answer call is never that cheap (the knowledge-base prefix alone costs more). rejected |
| 16 | blind | Second safety net in `_lines` untested; config default test reads oddly | low | cosmetic. rejected |
| 17 | blind | Spec and sprint status still in progress | false | the workflow moves both at the present step. rejected |
