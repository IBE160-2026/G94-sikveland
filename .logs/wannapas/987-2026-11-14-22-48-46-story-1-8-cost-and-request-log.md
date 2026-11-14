# Story 1.8: Cost and request log

## 2026-11-14 kl. 22:48 — WannapaS

### Task
Push Story 1.7 and implement Story 1.8: the adviser can see what each question costs and whether the prompt cache works, from one JSON line per chat request without any question or answer text.

### Plan
- `bmad-build` dispatch route. Spec: [spec-1-8-cost-and-request-log.md](../../docs/implementation/spec-1-8-cost-and-request-log.md). Decision (user): the log is the file `data/requests.jsonl` (`REQUEST_LOG_PATH`).
- Implementation by a subagent, then review with three reviewers (blind, edge case, verification gap) and patches.

### Result
- Pushed Story 1.7 (`cec7604` on origin/main).
- New `app/pipeline/cost.py` (prices and pure `cost_usd`), `app/web/request_log.py` (`RequestLog` with a reentrant lock, line builder, `answer_prices`). The pipeline passes `Usage` on as an internal `Spent` event (before `Sources`); `app/web/chat.py` writes one line when the stream ends (answered / no_answer / error / incomplete) and closes the model stream. New setting `REQUEST_LOG_PATH` (default `data/requests.jsonl`, relative to the project root); tests write to `tmp_path`.
- README: Norwegian section on the request log (fields, cache check, total-cost one-liner as a lower bound).
- Review: 17 findings, 9 patched (reentrant lock against a GC deadlock, warning reset after success, `Spent` before `Sources`, explicit close of the model stream, README fixes, import order, test comment), 1 carried on the Story 1.6 deferral (route-level disconnect test), 7 rejected.
- `uv run pytest`: 491 passed. Committed to main as `4de13f1`. Spec `done`, sprint status `review`. Not pushed.
- All Epic 1 stories are now in `review`.

### Open items
- Manual cache check with a real key: two questions within 5 minutes; the second line has `cache_read_tokens` > 0 and lower `cost_usd`.
- Refusals and cut-off answers are billed but logged with `cost_usd: null` (rejected for now; the README calls the total a lower bound).
