---
title: 'Story 5.2: Evaluation script and report'
type: 'feature'
created: '2026-11-16'
status: 'done'
route: 'dispatch'
baseline_commit: 'ac4c5979a01fb3ce315d5947c43aa490ed316fa4'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The test set from Story 5.1 exists, but nothing runs it, so nobody can see whether the chatbot meets the NFR4 targets after a prompt or source change (SM-2).

**Approach:** `uv run python scripts/run_eval.py` builds the app exactly as the server does (`create_app`), sends every test case through `answer_question` (the entry point of `/api/chat`, AD-1), checks the result automatically, and writes a Markdown report with an empty adviser column. `--score <report>` recalculates the totals from the adviser's judgements.

**Decisions (user, 2026-11-16):**
- **Ollama:** the provider in `.env` is used, Claude or Ollama. Ollama needs no key and costs 0; its report records `OLLAMA_MODEL` as both models and the `citing` prompt version.
- **Size:** the spec is kept as one (about 1,850 tokens).

## Boundaries & Constraints

**Always:**
- Settings come from `.env` (`get_settings()`). Demo mode (`MOCK_LLM=true`) is refused with a clear message and exit code 2; so is Claude without `ANTHROPIC_API_KEY`. Nothing is called before these checks.
- Each case runs through `answer_question` with the case's `history`, the app's `llm`, knowledge base, `no_answer_key` text and the same fixed replies as `app/web/chat.py`. Cases run one at a time; one failing case (`Failed` or an exception) is recorded as `error` and the run goes on.
- Automatic checks per case: category (from `Meta`), outcome (`answered` / `no_answer` / `fixed_reply` as in `_lines`, or `error`), expected source (`answered`: at least one expected source cited; otherwise none cited), personal information (`Meta.personal_info_removed` is true exactly when `personal_info` has `thai_id` or `passport`), and Thai (the reply contains Thai script).
- Report `eval/reports/<YYYY-MM-DD>-<prompt versions>.md` (e.g. `2026-11-16-answer-1-classifier-2.md`, with `-citing-2` under Ollama); never overwritten: a second run gets `-2`, `-3`. Header: date, provider, answer and classify models, prompt versions, case count, total tokens per field and total cost (`cost_usd` with the app's prices; 0 under Ollama). Then the totals against the four NFR4 targets, then one section per case: id, Thai question, English gloss, expected vs actual category and outcome, each automatic check as pass/fail, cited source ids, the reply text, the expected facts, and an `Adviser: ` line left empty.
- Targets: general correct ≥ 90% (category `general`, outcome `answered`, expected source cited, and the adviser's `yes`); individual assessment, no-answer and reach-person 100% by their automatic checks. Before scoring, the general total is shown as "awaiting adviser" with the automatic part counted.
- `--score <report>` reads each case's `Adviser:` line (`yes` / `no` / empty), rewrites only the totals block in the same file, and reports any case still empty. No model call, no settings check.
- The request log is not written by evaluation runs. Question and reply text appear only in the report.
- README (Norwegian): how to run, cost per run, how to fill in the adviser lines and score, that answers vary between runs so each run is judged on its own, and to rerun after every prompt or source change.

**Never:** no change to `app/` behaviour; no network in pytest (tests inject `ScriptedLLM`); no new dependency; no editing of an existing report except the totals block by `--score`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Demo mode | `MOCK_LLM=true` | message, exit 2, no call, no report | N/A |
| Claude without key | provider `anthropic`, no key | message, exit 2, no call | N/A |
| Ollama | `LLM_PROVIDER=ollama`, no Anthropic key | runs; report records `OLLAMA_MODEL`, `citing` version, cost 0 | N/A |
| All match | scripted categories, citations and usage | every check pass; tokens and cost summed | N/A |
| No citation | `general`, model cites nothing | outcome `no_answer`; passes for a `no_answer` case, fails for an `answered` one | N/A |
| Wrong source | cites only an unexpected known source | source check fails | N/A |
| Case fails | `LLMError` on classify or answer | outcome `error`, all checks fail, run continues | N/A |
| Same day twice | report name taken | `-2` suffix, first report unchanged | N/A |
| Score | adviser lines filled `yes`/`no`/empty | totals rewritten; empty ones listed; other text unchanged | missing file or no cases → message, exit 2 |

</frozen-after-approval>

## Code Map

- `app/pipeline/answer.py` `answer_question`, events `Meta`, `TextDelta`, `Sources`, `Spent`, `Done`, `Failed` -- the entry point; reuse, do not change.
- `app/web/chat.py` `FIXED_REPLY_KEYS`, `_lines` -- fixed-reply keys and the outcome rule to mirror (import the mapping; do not duplicate it).
- `app/main.py` `create_app(settings, llm=None)` -- builds the wired app; state: `llm`, `knowledge_base`, `content`, `no_answer_key`, `prompt_versions`, `answer_model`, `answer_prices`, `classify_prices`. Classify model is `settings.model_small` (Claude) or `settings.ollama_model`.
- `app/pipeline/cost.py` `cost_usd`, `Prices` -- per-call cost.
- `scripts/testset.py` `load_testset`, `TestCase`, `TESTSET_FILE` -- the cases; `sources` means "citing any one counts".
- `tests/fakes/fake_llm.py` `ScriptedLLM` -- scripted categories, citations, usage and errors for tests; pass it as `llm=` to `create_app`.
- `scripts/ingest.py` -- script style: `main(argv) -> int`, `if __name__ == "__main__": sys.exit(main())`.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/run_eval.py` -- settings checks, run, checks, report writing, `--score` -- SM-2
- [x] `eval/reports/.gitkeep` -- the report folder is committed (reports are kept)
- [x] `tests/test_run_eval.py` -- every matrix row with `ScriptedLLM` and `tmp_path` reports -- NFR3
- [x] `README.md` -- "Evaluering" section and the `scripts/` and `eval/` rows -- examiner

**Acceptance Criteria:**
- Given a report written by a run, when the adviser fills in every `Adviser:` line and runs `--score`, then the general total uses those judgements and the report still opens as readable Markdown.
- Given the test suite, when it runs, then no network call is made.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Route | Evidence |
|---|-------|---------|---------|-------|----------|
| 1 | blind, edge-case | A run where every case fails (wrong key, Ollama down) writes a normal-looking report and exits 0 | medium | patch | `run` has no check on all-`error` results; a bad key fails every classify call at once, and the README says reports are kept in git. |
| 2 | blind, verification-gap | The outcome rule is copied from `app/web/chat.py` `_lines`, and nothing ties the two together | medium | patch | Only `FIXED_REPLY_KEYS` is imported; a change to `_lines` would make the evaluation measure something else than the request log. A parity test is the smallest fix. |
| 3 | blind | `Adviser: no – <reason>` is counted as unreadable and treated as empty | medium | patch | `score_text` accepts only an exact `yes`/`no`; an adviser will naturally add why. Accept `yes`/`no` as the first word. |
| 4 | blind | The report does not record which knowledge base was used | low | patch | The README says to rerun after source changes, but reports before and after a change cannot be told apart. `Source.retrieved` is the source version (AD-9). |
| 5 | blind | Follow-up cases show only the earlier questions, not the earlier answers | low | patch | `_case_section` writes `Earlier question N` only; the adviser cannot judge whether the reply fits. |
| 6 | blind | Cited ids not in the knowledge base are invisible in the report | low | patch | `Sources.unknown_source_ids` is ignored; with Ollama's `[[id]]` markers a made-up id is possible. Show the count. |
| 7 | verification-gap | Non-zero cache-read and cache-write sums are never tested | low | patch | Pre-verified: every scripted usage has zero cache tokens, so swapping or dropping the fields stays green. |
| 8 | verification-gap | The `thai_id` half of the personal-information expectation is never tested | low | patch | Pre-verified: `test_personal_info_check` covers passport and phone only. |
| 9 | blind | The all-match test's `"| 1 of 1 (100%) | yes |"` matches any of three rows | low | patch | One target row could break and the test still pass; assert each row. |
| 10 | blind | Error reasons are class names only | low | reject | The pipeline reports `Failed.reason` as a class name by design (no text); changing it is an `app/` change. |
| 11 | blind, edge-case | Ctrl+C or a crash mid-run loses all results | low | reject | A rerun recovers; a partial-report mode adds a new mechanism. |
| 12 | blind | Every case asks for an adviser line, but only `general` uses it | low | reject | The frozen spec gives every case an `Adviser:` line and lists every empty one; the other targets are fixed texts checked automatically. |
| 13 | blind | The Thai check passes on fixed replies and on one Thai character | low | reject | Fixed replies are approved Thai; a script-ratio check adds new logic for a supporting line with no target. |
| 14 | blind | The personal-information check does not prove the number never reached the model | low | reject | Covered deterministically by `tests/test_answer_pipeline.py` and `tests/test_chat_api.py`; the evaluation measures the models. |
| 15 | blind | General row says "awaiting adviser" when 90% is already out of reach | low | reject | Cosmetic; the counts are shown. |
| 16 | blind, edge-case | Spec says `in-review`, sprint status `in-progress`; spec example name `classifier-2` vs README `classifier-3` | false | reject | Step 5 sets `review`; `prompts/classifier-system.md` is version 3, so the README is right and the spec's name is only an example. |
| 17 | blind | Untested paths: invalid case-marker JSON, duplicate totals markers, a stream ending without `Done` | low | reject | Each fails loudly or is covered by the same branch as tested errors; adding tests is optional. |
| 18 | blind | No way to run only some cases | low | reject | New feature; not in the intent. |
| 19 | edge-case | Writing the report can fail with `OSError` and lose the results | low | reject | `eval/reports/` is created by the run itself; unlikely, and a guard adds a fallback path. |
| 20 | edge-case | A prompt version with filename-illegal characters breaks the report name | low | reject | Versions are short numbers in `prompts/*.md`; no such value exists. |
| 21 | edge-case | Bad `.env` or broken content gives a traceback and exit 1, not exit 2 | low | reject | The same startup errors stop the server; the message is readable. |
| 22 | edge-case | Tokens of an answer call that failed mid-stream are not counted | low | reject | The pipeline yields no `Spent` on failure; same as the request log, whose README says sums are lower bounds. |
| 23 | blind, edge-case | `--score` overwrites in place; a crash or locked file can lose judgements | low | reject | The file is small and written at once; a temp-file swap adds a mechanism. |
| 24 | edge-case | Duplicated or deleted case sections, or a second `Adviser:` line, skew scoring | low | reject | Needs manual damage to the report; a guard per case adds checks. |
| 25 | edge-case | A reply with `<!--` hides sections when the report is rendered | low | reject | Thai model replies; `--score` is unaffected because reply lines start with `> `. |
| 26 | edge-case | A general row with no automatic pass shows a verdict instead of "awaiting adviser" | false | reject | Correct: with no case passing the automatic checks no adviser `yes` can count, so the result is final. |

## Verification

**Commands:**
- `uv run pytest` -- expected: exit code 0
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean

**Manual checks (if no CLI):**
- With a real key: `uv run python scripts/run_eval.py` writes a report; fill two `Adviser:` lines, run `--score`, and see the totals change.
