# Eval-no-answer-reason

## 2026-11-18 kl. 23:38 — WannapaS

### Oppgave
Make the evaluation report say why a case got the fixed no-answer text (no source cited, only unknown source ids, or the no-answer sentence guard), since `application-steps` got it in `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-4.md` with no way to tell the cause.

### Plan
- `bmad-build`, short route (one-shot): spec [spec-eval-no-answer-reason.md](../../docs/implementation/spec-eval-no-answer-reason.md); one reviewer subagent (allowed by the user).

### Resultat
- Commit `0452452` (Norwegian message): `Sources.no_answer_reason` in `app/pipeline/answer.py` (`no_citation`, `unknown_ids_only`, `not_available_opening`; with no known citation one of the first two); `scripts/run_eval.py` prints "- No-answer reason: …" for every `no_answer` case; README sentence; tests. Request log, stream and `--score` totals unchanged.
- Review: 3 small patches (label-completeness test, precedence test, docstrings), 5 findings rejected with evidence (triage log in the spec).
- `uv run pytest`: 1513 passed, exit code 0; ruff clean. Pushed to `origin/main` at the user's request (`c6c2ceb..bc9d485`).
- Closed in issues.md: the decision about the no-answer reason.

### Åpne punkter
- The reason shows only in new reports; `application-steps` in the `-citing-3-4` report stays unexplained until a case like it shows up again in a new run.
