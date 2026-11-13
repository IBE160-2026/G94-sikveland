# Story 1.4: Personal information filter

## 2026-11-13 kl. 22:15 — WannapaS

### Task
Implement Story 1.4 from its spec (dispatched as a subagent): a pure, pattern-based filter that replaces Thai ID numbers, passport numbers and Thai/Norwegian phone numbers with `[removed]`, plus a privacy notice that says names and addresses are not removed.

### Plan
- Spec: [spec-1-4-personal-information-filter.md](../../docs/implementation/spec-1-4-personal-information-filter.md); context: [epic-1-context.md](../../docs/implementation/epic-1-context.md).
- One precompiled regex per pattern, applied in order Thai ID → passport → Norwegian with country code → Thai phone → bare Norwegian mobile; digit boundaries by lookaround instead of `\b`; Thai digits accepted everywhere.
- Parametrized tests for every matrix input, exact output for glued/multiple matches, false positives unchanged, AST check for standard-library-only imports.

### Result
- New `app/pipeline/filter.py` (`REMOVED_MARKER`, frozen `FilterResult`, `remove_personal_info`); ASCII-only source (Thai digit range built with `chr()`, AD-6).
- New `tests/test_filter.py`; `content/texts.yaml` `privacy-notice` th/en replaced with the spec's draft.
- Spec tasks ticked and Implementation Notes added (extra patterns beyond the matrix, known false positive).
- `uv run pytest`: 212 passed. Spec verification command prints the phone replaced, `90 euro` kept, `removed=True`.
- Uncommitted: the Thai notice needs adviser review before commit (NFR8, already an open item from 2026-11-12).

### Open items
- Any bare 8-digit number starting with 4 or 9 (e.g. `90000000`) is removed as a Norwegian mobile number (privacy first); check against the evaluation test set.
- Manual check of the longer privacy notice at 360 px in a browser was not done (`body` already has `overflow-wrap: anywhere`).
