# Eval-dropped-source-ids

## 2026-11-21 kl. 22:25 — WannapaS

### Oppgave
Show the dropped unknown source ids in the evaluation report, so a near-miss below the 0.85 closest-id cutoff can be told apart from a made-up id (follow-up to `relationship-proof-unmarried-partner`, which lost all three ids in the 2026-11-21 Ollama run).

### Plan
- `bmad-build`, one-shot route: spec [spec-eval-dropped-source-ids.md](../../docs/implementation/spec-eval-dropped-source-ids.md); one reviewer subagent (allowed).
- Builder's choices: show each id with the closest known id and the similarity, scored as the Ollama adapter does; ids go to the report only, while the request log keeps the count.

### Resultat
- Commit `9cce6bc` (Norwegian message, not pushed). `Sources.unknown_ids` in `app/pipeline/answer.py` (the count is now a property); `normalise_source_id` and `closest_known_ids` factored out in `app/adapters/ollama_llm.py`; `scripts/run_eval.py` line, for example: ``- Dropped unknown source ids: 1 — `udi-waiting-time` (closest `udi-waiting-time-visitor-visa`, 0.71)``. Ties are shown with `or`, and the score is rounded down. README updated.
- Found in review: only Ollama can drop ids; Claude raises an error on an unknown citation index.
- Review: 5 patches, 1 deferred (mapped ids are still not visible in the report; deferred-work.md), the rest rejected with evidence (triage log in the spec).
- `uv run pytest`: 1540 passed, exit code 0; ruff clean.
- Closed in issues.md: the decision to show the dropped ids.
- Pushed at the user's request (`origin/main` = `3a4973e`). A new Ollama run wrote `eval/reports/2026-11-21-answer-1-classifier-4-citing-3-2.md` (committed and pushed at the user's request; the cutoff stays at 0.85 for now, by the user's choice). Results: general 12 of 14 automatic, no-answer 4 of 4, 1 of 29 cases dropped ids. `relationship-proof-unmarried-partner` passed this time. The one dropped id was a near-miss: `embassy-visa-checklist` (closest `embassy-visitor-visa-checklist`, 0.846; runner-up `embassy-visa-faq`, 0.68) in `thanks-and-insurance-question`, which still passed. General misses: `processing-time-typo` (the model opened with the not-available sentence) and `when-to-apply-mixed-language` (no source cited); both passed in the earlier runs.
- Another Ollama run, at the user's request: `eval/reports/2026-11-21-answer-1-classifier-4-citing-3-3.md` (committed and pushed at the user's request). For the first time, every case passes the automatic checks: general 14 of 14, individual assessment 3/3, no-answer 4/4, reach person 4/4. No cases dropped ids, so no new evidence on the cutoff (one near-miss over three runs today).
- Fourth Ollama run, at the user's request: `eval/reports/2026-11-21-answer-1-classifier-4-citing-3-4.md` (not committed). Results: general 13 of 14 automatic, no-answer 4/4, IA 3/3, reach person 4/4. The miss is `own-chances-and-employment-proof` again (classified `individual_assessment`; 2 of the 4 runs today). One dropped id, in `no-answer-pregnancy`: `id:` (closest `udi-fees`, 0.18). That is no misspelling but marker syntax with no id, and the case still got the no-answer text. Near-misses so far: 1 in 4 runs.

### Åpne punkter
- Decide whether to lower the closest-id cutoff from 0.85 to 0.80: the one near-miss seen scored 0.846, and no two real ids are more than 0.73 similar.
