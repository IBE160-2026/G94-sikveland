# Ollama-closest-source-id

## 2026-11-18 kl. 23:55 — WannapaS

### Oppgave
Map a misspelled `[[id]]` marker from Ollama to the closest known knowledge-base id instead of letting the pipeline drop it; misspelled ids caused two of three general misses in `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-5.md`.

### Plan
- `bmad-build`, short route: spec [spec-ollama-closest-source-id.md](../../docs/implementation/spec-ollama-closest-source-id.md); one reviewer subagent (allowed).
- Builder's choices: normalise (trim, lower case, spaces/underscores to hyphens), then difflib ratio at least 0.85, a tie maps nothing; only in the Ollama adapter (Claude cites by document index).

### Resultat
- Commit `938c4c5` (Norwegian message): `resolve_source_id` and `CLOSEST_ID_CUTOFF` in `app/adapters/ollama_llm.py`, applied to every chunk of `answer`; a mapping logs the known id only; tests with the real ids incl. a guard that no two real ids are 0.8 or more similar (today 0.73); AD-7 and README amended.
- Review: 6 patches, 4 findings rejected with evidence (triage log in the spec).
- `uv run pytest`: 1530 passed, exit code 0; ruff clean. Pushed to `origin/main` at the user's request.
- Closed in issues.md: the decision about mapping misspelled ids.

### Åpne punkter
- No evaluation run with the matching yet; the next Ollama run shows whether the misses from misspelled ids are gone.

## 2026-11-21 kl. 22:17 — WannapaS

### Oppgave
Continue from last time: run the Ollama evaluation to see whether closest-id matching (`938c4c5`) removed the misses from misspelled source ids; commit and push the report.

### Plan
- No uncommitted report was left from 2026-11-18, so the run was made again: `LLM_PROVIDER=ollama uv run python scripts/run_eval.py` (no `.env` on this machine).
- Compare with `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-5.md`.

### Resultat
- New report `eval/reports/2026-11-21-answer-1-classifier-4-citing-3.md`, committed `314e724` and pushed.
- General: 12 of 14 pass the automatic checks (was 11); individual assessment 3/3; no-answer 3/4; reach person 4/4; Thai 29/29; personal information 29/29. Cases that dropped unknown ids: 2 of 29 (was 4).
- General misses: `relationship-proof-unmarried-partner` (3 unknown ids dropped → no-answer text; the report does not list the dropped ids, so it cannot tell whether they were near-misses below the 0.85 cutoff) and `own-chances-and-employment-proof` (classified `individual_assessment` again; fixed by classifier v4 on 2026-11-18, back now).
- No-answer miss: `no-answer-pregnancy` answered this time (the known flip-flop).
- Closed in issues.md: the run to check the misspelled-id misses.

### Åpne punkter
- `relationship-proof-unmarried-partner` still loses all its citations to unknown ids; decide whether the report (or the request log) should list the dropped ids so near-misses can be told from made-up ids.
- Classifier v4 sent `own-chances-and-employment-proof` to individual assessment again (1 of 3 runs since the fix); watch it or tighten the prompt.
- Adviser judges the 14 general answers in the new report, then `--score` and commit.
