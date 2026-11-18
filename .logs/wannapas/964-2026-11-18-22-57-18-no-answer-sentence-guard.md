# No-answer-sentence-guard

## 2026-11-18 kl. 22:57 — WannapaS

### Oppgave
Add a pipeline guard so that a reply that opens with the "this information is not available" sentence gets the fixed no-answer text even when the model goes on to cite sources (the remaining Ollama miss `no-answer-interpreter-at-vfs`). The user chose this over more prompt work, knowing it changes `app/` and amends AD-7.

### Plan
- `bmad-build`, spec [spec-no-answer-sentence-guard.md](../../docs/implementation/spec-no-answer-sentence-guard.md).
- User decisions: narrow pattern (first line only; แต่ / อย่างไรก็ตาม on that line means it is an answer, so `application-steps` stays answered); spec kept whole; subagents allowed.
- Review pass 1 found an intent gap (the check ran on an incomplete first line: Claude's empty citation chunk disarmed it, a แต่ after an Ollama mid-line citation was missed). Code reverted; the user chose to hold the text only while it could still become a not-available opening; re-derived.

### Resultat
- Commit `258f5b3` (Norwegian message): `app/pipeline/answer.py` (guard, patterns, holding rule), `tests/test_answer_pipeline.py` (a test per matrix row, both adapters' chunk shapes, tests tying the pattern to the prompt's example sentence and `reply-no-answer`), AD-7 amended in `ARCHITECTURE-SPINE.md`, one README sentence, the spec, and the report `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-2.md`.
- Review pass 2: 3 patches (hold only while it can still match, the pattern-source tests, docstrings), 11 findings rejected with evidence (known, accepted limits of the narrow rule: the apology alone on the first line, a แต่ that starts the second line, a partial answer that puts "not covered" first).
- `uv run pytest`: 1509 passed, exit code 0; ruff clean.
- Ollama run: no false positive; `no-answer-interpreter-at-vfs` now gets the no-answer text; no-answer 3 of 4 because `no-answer-pregnancy` came back as a partial answer ("you can apply as usual" with sources, then "no information about special conditions"), which the guard leaves by design; the classifier sent `own-chances-and-employment-proof` to individual assessment this run (variance). A 20-case run with the first implementation gave no-answer 4 of 4. An earlier full run was aborted by Ollama errors (cases 11-30) and was not kept.
- Closed in issues.md: the interpreter no-answer item.

### Åpne punkter
- `no-answer-pregnancy`: the model now gives a partial answer (you can apply as usual + no special conditions in the sources). Decide with the adviser whether that is acceptable (change the test case's expected outcome) or should be a no-answer.
- The adviser judges the general answers in `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-2.md` too, then `--score`.
