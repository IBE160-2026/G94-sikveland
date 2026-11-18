---
title: 'No-answer reason in the evaluation report'
type: 'feature'
created: '2026-11-18'
status: 'done'
route: 'oneshot'
baseline_commit: 'c6c2cebd554d289cf7857dfb9945bd97ac5efe57'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A reply ends in the fixed no-answer text for one of three reasons: the answer cited no source, it cited only ids that are not in the knowledge base, or the no-answer sentence guard declined it (AD-7). The evaluation report shows only the outcome, so a miss such as `application-steps` in `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-4.md` cannot be explained.

**Approach:** The pipeline's `Sources` event carries the reason whenever the no-answer text was sent (`None` otherwise), and `scripts/run_eval.py` prints it in the case section of every case that ends in `no_answer`: "No-answer reason: no source cited", "only unknown source ids cited" or "opened with the not-available sentence". When no known source was cited, the reason is one of the first two, also if the text opened with the not-available sentence. The README's description of the case section gets the new line. The request log, the stream events, `app/web/chat.py` and the `--score` totals do not change.

**Decisions (user, 2026-11-18):** the user asked for the reason in the evaluation report; subagents allowed.

</frozen-after-approval>

## Implementation Notes

- `app/pipeline/answer.py`: `NoAnswerReason` (`no_citation`, `unknown_ids_only`, `not_available_opening`) and `Sources.no_answer_reason` (default `None`), set only when the no-answer text was sent; with no known citation the reason is one of the first two (also when the text opened with the not-available sentence). Fixed replies keep `None`.
- `scripts/run_eval.py`: `CaseResult.no_answer_reason`, `NO_ANSWER_REASON_LABELS`, and the line "- No-answer reason: …" after the dropped-ids line, only for `no_answer` outcomes. Not in the `eval-case` JSON, so `--score` and the totals are unchanged.
- `app/web/chat.py`, the request log and the stream are unchanged (`chat.py` reads only `items` and `unknown_source_ids`).
- Tests: the existing pipeline event lists now name the reason (zero citations, empty answer, only unknown ids, every guard case); `tests/test_run_eval.py` checks the line for each reason and its absence for answered and fixed-reply cases. README: one sentence in the report description.
- `uv run pytest`: 1511 passed, exit code 0; ruff clean.
- Review patches: a test that every reason has a label (a missing label would stop the report after a paid run); a pipeline test that a not-available sentence with no citation gets `no_citation`; module and `answer_question` docstrings name the reason. `uv run pytest`: 1513 passed, exit code 0; ruff clean.

## Review Triage Log

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | A reason without a label raises `KeyError` while the report is written, after every case ran | low | `NO_ANSWER_REASON_LABELS[...]` in `_case_section`; nothing tied the dict to `NoAnswerReason` | patch (test) |
| 2 | No test for a not-available sentence with no ids at all (precedence of `no_citation`) | low | only the unknown-ids variant was tested; the spec states the precedence | patch (test) |
| 3 | Module and `answer_question` docstrings do not mention the reason | low | they described a declined `Sources` as just empty | patch |
| 4 | A `no_answer` case without a reason would hide the line | false | the pipeline sets a reason whenever it sends the no-answer text; a `general` case with empty `items` is always declined | reject |
| 5 | No summary count of reasons | low | an extra feature, not asked; the per-case line answers the question | reject |
| 6 | The test does not check the line order | low | order does not change what the reader learns | reject |
| 7 | Spec status, untracked spec, no open item for a new run | false | status is set when the spec is finalised, the spec is committed with the change, and the session log records the follow-up | reject |
| 8 | The reason repeats the dropped-ids line for `unknown_ids_only` | false | both lines are true and short; no reader is misled | reject |
