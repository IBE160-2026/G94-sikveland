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

### Åpne punkter
- The next Ollama evaluation run shows which ids `relationship-proof-unmarried-partner` drops; then decide between lowering the cutoff and changing the citing prompt.
