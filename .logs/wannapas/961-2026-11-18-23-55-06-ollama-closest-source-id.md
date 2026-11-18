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
