---
title: 'Closest known source id for misspelled Ollama markers'
type: 'feature'
created: '2026-11-18'
status: 'done'
route: 'oneshot'
baseline_commit: '210e13b525544e53412ef42bb7213c06b2b3c03e'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Ollama marks its sources as `[[id]]` and sometimes misspells the id (seen: `udi-sponsor-for-visators` for `udi-sponsor-for-visitors`). The pipeline drops unknown ids (AD-7), so a correct answer loses its source link or, when it cited only misspelled ids, becomes the no-answer text. In `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-5.md` this caused two of the three general misses.

**Approach:** In `OllamaLLM.answer` (`app/adapters/ollama_llm.py`), each marker id that is not a known document id is first normalised (trimmed, lower case, spaces and underscores to hyphens); if that is still not known, it is mapped to the closest known document id when their similarity (`difflib.SequenceMatcher` ratio) is at least 0.85, the best match wins and a tie maps nothing. Any other id is passed on unchanged, so the pipeline still drops and counts it. No two known ids today are more than 0.8 similar to each other, so a match cannot land between two real sources. `MarkerParser` stays as it is; the Claude adapter is not touched (its citations point at documents by index). AD-7 and the README say so in one sentence each.

**Decisions (user, 2026-11-18):** the user asked for the matching in the Ollama adapter; subagents allowed. The threshold and the normalisation are the builder's choice, recorded here.

</frozen-after-approval>

## Implementation Notes

- `app/adapters/ollama_llm.py`: `CLOSEST_ID_CUTOFF = 0.85`, `resolve_source_id(source_id, known_ids)` (exact → normalised → closest by `difflib.SequenceMatcher` ratio, a tie maps nothing), `_resolved` applied to every chunk `answer` yields (also the `finish` chunk); module docstring. `MarkerParser` unchanged.
- Short ids are stricter by nature: `b-feez` vs `b-fees` is 0.83, not mapped; the real ids are 8-31 characters, so one wrong letter in them stays above 0.85 (`udi-feez` 0.875). `embassy-faq` (0.815 to `embassy-visa-faq`) and `udi-invitation-letter` (0.65) are not mapped.
- Tests in `tests/test_ollama_llm.py`: near-miss ids mapped (incl. the one seen in an evaluation), other ids passed on, a tie, no known ids, and the mapping through `answer`. AD-7 and README (Ollama section) amended.
- `uv run pytest`: 1528 passed, exit code 0; ruff clean.
- Review patches: the tie test now ties above the cutoff; the tests use the real ids from `sources.yaml`; a test that no two real ids are 0.8 or more similar (today 0.73 at most); a mapping logs the known id it chose (never the model's text) and README/AD-7 say mapped ids no longer count as unknown; the AD-7 amendment note moved after the earlier ones; the README sentence names trimming, the tie rule and difflib's ratio. `uv run pytest`: 1530 passed, exit code 0; ruff clean.

## Review Triage Log

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | The tie test never reaches the tie rule | low | "ab-cd" vs "ab-ce"/"ab-cf" is 0.8, below the cutoff | patch |
| 2 | The `embassy-faq` case passes trivially | low | the hand-copied id list left out `embassy-visa-faq` | patch (real ids) |
| 3 | Nothing protects "no two known ids are near-misses" | medium | a new source close to an existing one would let a misspelling land on the wrong one | patch (test) |
| 4 | A mapping is silent; mapped ids vanish from `unknown_source_ids` | medium | the request-log count was how the problem was found | patch (log line with the known id only; docs) |
| 5 | Generic ids map to a possibly wrong source; no gap to the runner-up | false | on the real ids every example has a wide gap (0.857 vs 0.667, 0.889 vs 0.75, 0.863 vs 0.431, 0.923 vs 0.78) and lands on a plausible source | reject |
| 6 | No pipeline test and no re-run of the misses | low | a mapped id is a known id, which the pipeline already handles and tests; a re-run is offered to the user | reject |
| 7 | Spec front matter out of date, spec untracked | false | set when the spec is finalised and committed with the change | reject |
| 8 | AD-7 amendment notes out of date order | low | the new note sat before the 2026-11-15 one | patch |
| 9 | README leaves out trimming, ties, difflib | low | direct wording fix | patch |
| 10 | Dots, slashes, quotes are not normalised | low | not seen in any run; the fuzzy match already rescues long ids | reject |
