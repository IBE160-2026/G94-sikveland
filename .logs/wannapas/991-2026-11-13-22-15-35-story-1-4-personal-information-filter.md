# Story 1.4: Personal information filter

## 2026-11-13 kl. 22:15 — WannapaS

_Note 2026-11-14: this section describes the first implementation (with phone rules), which was later reverted. See the 2026-11-14 section for the final design._

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

## 2026-11-14 kl. 22:05 — WannapaS

### Task
Continue Story 1.4 from yesterday. Review loops 2 and 3 ran after the first log entry. Loop 2: the user decided phone numbers are not removed. Loop 3: group-based Thai ID search and stricter passport rules. Today: review the loop 3 implementation, then finish and commit.

### Plan
- Resumed `bmad-build` at review: three reviewers (blind, edge case, verification gap) on the diff since `4915efe`, every finding checked by probe, triage written to the spec (Pass 4).
- The review found more spec-level problems (would be loop 4 of 5). With the 2026-11-15 deadline in mind, the user chose to **accept the loop 3 rules** and defer the rest instead of looping again.
- Spec: [spec-1-4-personal-information-filter.md](../../docs/implementation/spec-1-4-personal-information-filter.md).

### Result
- Final design: `app/pipeline/filter.py` removes only Thai ID numbers (13 digits in allowed groupings, any Unicode digits) and passport numbers (1–2 Latin letters + 7 digits). Phone numbers, names, addresses and emails are not removed. The notice and reminder in `content/texts.yaml` say so.
- Patches from review: tests for an ID after another number in the same run, passports with Thai/full-width digits, punctuation around matches, `aa 1234567` kept, accepted false positives inside a sentence, stronger wording check for the notice and reminder, `unicodedata` removed from the purity allowlist. English reminder fixed to "before sending it".
- Deferred (2 entries in `docs/implementation/deferred-work.md`): ID spellings that leak (`1 234567890123`, `12-3456-78901-2-3`, `AA: 1234567`, unusual separators, tail after a 5-digit group) and false positives (`0066…` phones, `500000-1500000 baht`, `kr1500000`).
- The adviser approved the Thai texts (NFR8). `uv run pytest`: 294 passed. Spec verification command OK.
- Committed to main as `4da7990` (Story 1.4). Spec `done`, sprint status `review`. Not pushed. `docs/VFS data/` deliberately left out (contains the user's name).
- Closed in issues.md: adviser review of the Thai notice, and the obsolete `90000000` item.

### Open items
- Filter: known ID leaks and false positives (deferred-work.md, 2 entries); check against the evaluation test set and fix if they matter.
- Update the PRD (FR9) and epics to the narrower scope: phone numbers are not removed.
- Manual check of the longer privacy notice at 360 px (already in issues.md).
