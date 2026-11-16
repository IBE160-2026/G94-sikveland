---
title: 'Story 5.3: Feedback statistics'
type: 'feature'
created: '2026-11-16'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The main success metric (SM-1, at least 80% of conversations whose first feedback answer is "Yes") can only be read today with a long SQL one-liner in the README, which has no date filter and fails with `no such table` before the first answer is stored.

**Approach:** `uv run python scripts/feedback_stats.py [--from YYYY-MM-DD] [--to YYYY-MM-DD]` reads the SQLite file at `DATABASE_PATH` (from `.env`, relative to the project root) read-only and prints the number of conversations with feedback, how many and what share had "yes" as their first answer, and whether the 80% target is met. Only the first answer per `conversation_id` counts (the row stored first), so "no" then "yes" counts as "no" (AD-10). The date filter keeps conversations whose first answer was created on or between the given dates, both inclusive, in UTC as stored. A missing file, a missing table or no rows in the period prints "no feedback yet" and exits 0; an invalid date, or `--from` after `--to`, is a usage error (exit 2). The script never creates or changes the database. Tests use temporary SQLite files; the README section on feedback points to the script instead of the SQL one-liners.

</frozen-after-approval>

## Implementation Notes

- New `scripts/feedback_stats.py`: `first_answers(path)` opens the file with a read-only SQLite URI (`Path.as_uri()` + `?mode=ro`, so it never creates the file) and selects each conversation's row with the lowest `rowid`, as the README's old one-liner did; `count(rows, start, end)` filters by the UTC day of that first answer, so a conversation belongs to the period of its first answer ("no" in October, "yes" in November counts once, in October, as "no"); `report` prints the period, the count, the yes share with one decimal and whether 80% is met (exactly 80% is met). `DATABASE_PATH` is resolved like `app/main.py` `_from_root`. A file that is not a SQLite database exits 2 with the class name and message.
- A row whose `created_at` cannot be parsed is left out when a date filter is given and counted otherwise; only `POST /api/feedback` writes the table, so this does not occur in practice.
- New `tests/test_feedback_stats.py` (15 tests) writes rows through `SqliteFeedbackStore`, so the tests use the real table.
- README: the SQL one-liners in the feedback section are replaced by the script and its options; the `scripts/` row names it.
- `tests/test_feedback_api.py` pinned the two SQL one-liners the README no longer has (`test_readme_sm1_query_counts_the_first_answer_per_conversation`, `test_readme_python_command_gives_the_same_count`); they are removed, and `test_the_readme_command_runs_against_a_database_the_app_wrote` in `tests/test_feedback_stats.py` runs the README's script command as a subprocess against a database the app wrote.

## Review Triage Log

One blind review (edge-case and verification-gap layers are not part of the one-shot route).

| # | Finding | Verdict | Route | Evidence |
|---|---------|---------|-------|----------|
| 1 | With no file or table and a date filter, it says "No feedback yet in this period", as if feedback existed elsewhere | low | patch | `report` only looked at the filters; it now also knows whether there was any feedback at all. Test added. |
| 2 | The README names exit 2 only for date errors, not for a file that is not a database, and no longer shows sample output | low | patch | `StatsError` also returns 2; README wording and a sample output block added. |
| 3 | `_day` says "UTC day" but takes the date in the string's own offset | low | patch | Correct today because the store always writes `Z`; `.astimezone(UTC)` makes it match the docstring. |
| 4 | Missing tests: a single-day period, the `--from is after --to` message | low | patch | Two tests added. |
| 5 | `manual-test-plan.md` MT-14 step 8 has no run of the script; `epic-5-context.md` still says 5.2 and 5.3 are in the backlog | low | patch | Step 8 and its expectation now include `feedback_stats.py`; the context sentence is corrected. |
| 6 | The share is printed rounded (7999 of 10000 shows 80.0%) while "met" uses the exact ratio | low | reject | Needs thousands of conversations just under 80%; the verdict is the correct one. |
| 7 | The spec has only Intent and Implementation Notes | false | reject | The one-shot route keeps only those sections by design. |
| 8 | A database read error shares exit code 2 with usage errors | low | reject | Nothing calls the script automatically; the message says which it is. |
| 9 | Rows with an unparseable `created_at` are dropped from filtered counts without notice | low | reject | Only `POST /api/feedback` writes the table, always with a valid UTC stamp; the rule is in the Implementation Notes. |
| 10 | `database_path()` copies `app/main.py` `_from_root` | low | reject | One line with the same rule; sharing it means changing `app/` for no current harm. |
| 11 | Rows with a NULL `conversation_id` are never counted | low | reject | The API requires a UUID; no such row can be written. |
| 12 | The correlated `MIN(rowid)` query is quadratic without an index | low | reject | Feedback volume is small; the same query was in the README before. |
| 13 | The story is still `in-progress` | false | reject | Finalize sets the spec to `done` and the sprint status to `review`. |
