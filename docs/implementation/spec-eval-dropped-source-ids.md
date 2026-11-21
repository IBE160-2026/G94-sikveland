---
title: 'Dropped source ids in the evaluation report'
type: 'feature'
created: '2026-11-21'
status: 'done'
route: 'oneshot'
baseline_commit: '3fe2a70947e9fb12b481bca99b438c5f23697b4a'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The evaluation report only counts the cited ids the pipeline dropped as unknown ("Dropped unknown source ids: 3"). In `eval/reports/2026-11-21-answer-1-classifier-4-citing-3.md`, `relationship-proof-unmarried-partner` lost all three of its ids, and nobody can tell whether they were near-misses just below the closest-id cutoff (0.85, `app/adapters/ollama_llm.py`) or ids the model made up. Without that you can't decide between lowering the cutoff and changing the prompt.

**Approach:** The pipeline's `Sources` event also carries the dropped ids, in order of first citation (evaluation only, like `no_answer_reason`). `scripts/run_eval.py` lists them on the case's dropped-ids line. Each id is shown as the model wrote it, with the closest known id and its similarity score, worked out with the same normalisation and difflib ratio the Ollama adapter uses. Example: `` - Dropped unknown source ids: 2 — `embasy-visa-checklst` (closest `embassy-visitor-visa-checklist`, 0.78), `visa-guide` (closest `udi-visit-visa`, 0.42) ``. The request log, the stream, `app/web/chat.py`, the `eval-case` JSON and the `--score` totals do not change.

**Decisions (user, 2026-11-21):** the user asked for the dropped ids in the report; subagents allowed. Builder's choices: show the closest id and score as well (that is what tells a near-miss apart); the ids go only to the report, which is generated from the fictional test set, never to the request log (it keeps the count only).

</frozen-after-approval>

## Implementation Notes

- `app/pipeline/answer.py`: `Sources.unknown_ids` (tuple, order of first citation) replaces the `unknown_source_ids` field; `unknown_source_ids` is now a property (its length), so `app/web/chat.py`, the request log and `scripts/run_eval.py` read the count unchanged. The pipeline keeps the unknown ids in an insertion-ordered dict instead of a set.
- `app/adapters/ollama_llm.py`: `normalise_source_id` and `closest_known_ids` factored out of `resolve_source_id` (behaviour unchanged), so the report scores ids exactly as the adapter does.
- `scripts/run_eval.py`: `DroppedId` (id, closest known ids, similarity), `CaseResult.dropped_ids`, `_dropped_id` and `_dropped_text`. The dropped-ids line gets ` — ` plus each id as the model wrote it (one line, backticks turned into `'`, cut at 80 characters with `…`), then `(closest `x`, 0.78)`. A tie names every closest id joined by ` or ` (the adapter maps nothing on a tie). The similarity is rounded down to two decimals, so 0.8499 shows as 0.84, not as the 0.85 cutoff. The `eval-case` JSON still holds only the count, so `--score` is unchanged.
- Tests: pipeline event lists name the ids, plus an order-and-count test; `tests/test_run_eval.py` checks the full line in a run and `_dropped_text` for a near-miss with normalisation, a tie, an empty knowledge base, rounding down, and an id with a backtick, a line break and too many characters. README: two sentences in the report description.
- `uv run pytest`: 1540 passed, exit code 0; ruff check and format clean.
- Review fixes: the README example is now an id below the cutoff (`udi-waiting-time`, 0.71) and says that only Ollama drops ids (Claude raises `LLMError` on an unknown citation index, `app/adapters/anthropic_llm.py` `_chunk`); tied ids are sorted ascending; the length limit is `MAX_MARKER_BODY` imported from the adapter rather than a copy; tests use a real below-cutoff id and a tie above the cutoff, both checked against `resolve_source_id`. 1540 passed, exit code 0; ruff clean.

## Review Triage Log

One reviewer (blind hunter).

- medium, patched: the README example `udi-fee` (0.93) can never be dropped, because the adapter maps it; Claude never drops ids at all.
- low, not patched (frozen block): the spec's example `udi-visit-visa` is not a real source id; it is only an illustration in the intent.
- defer: mapped ids are still invisible, so the report shows only one side of the cutoff (deferred-work.md).
- low, rejected: the script imports the Ollama adapter for the scoring helper. Scripts and tests already import adapters, no layering rule covers `scripts/`, and the scoring has to match the adapter's.
- low, patched: `MAX_DROPPED_ID_CHARS` duplicated `MAX_MARKER_BODY`.
- low, patched: tied closest ids were listed in reverse order.
- low, patched: the tests didn't cover a realistic dropped near-miss or a tie at 0.85 or more.
- false: "a formatting failure turns the case into an error". `knowledge_base.documents()` is the same call the report header makes on the same object, and `_dropped_id`/`_dropped_text` only use difflib and string operations; no reachable exception was shown.
- low, patched: the README didn't say that only Ollama drops ids, or describe the tie form.
- false: "the spec isn't finished". It was mid-workflow; it is finalized now. Rerunning the Ollama evaluation was a separate step the user had not asked for.
- false: "builder's choices sit in the frozen block". They are labelled as the builder's, as in earlier specs, and the user sees them before the commit.
