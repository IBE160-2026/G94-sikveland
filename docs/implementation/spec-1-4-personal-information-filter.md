---
title: 'Story 1.4: Personal information filter'
type: 'feature'
created: '2026-11-13'
status: 'done'
route: 'dispatch'
review_loop_iteration: 3
baseline_commit: '4915efee4ceef7b23fff8b5426ce7df6fe2b32df'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Applicants may write their Thai ID or passport number in a question, and nothing stops it from reaching the AI service or a log. The privacy notice also does not say what is and is not removed.

**Approach:** Add a pure, pattern-based filter in `app/pipeline/filter.py` that replaces Thai ID numbers and passport numbers with a neutral marker and reports whether anything was removed. Update the privacy notice and the reminder (Thai + English) to match: ID and passport numbers are removed; phone numbers, names, addresses and emails are not, so the applicant should not write them. Wiring the filter into the chat request is Story 1.6.

**Decision (user, 2026-11-13, review loop 2):** phone numbers are not removed. Review rounds kept finding new ways to write a phone number, and each fix removed more dates and amounts. Thai ID and passport numbers have fixed shapes and stay in scope. This narrows FR9 and the Story 1.4 acceptance criteria; the PRD and epics are updated separately.

## Boundaries & Constraints

**Always:** no checksum on Thai ID numbers, so made-up test numbers are removed too; matches use digit/letter boundaries, not `\b`, so numbers glued to Thai text are caught; any Unicode decimal digit counts (Latin, Thai ๐–๙, full-width); the marker is the plain string `[removed]` (no Thai in code, AD-6); the adviser reviews the changed Thai texts before commit (NFR8).

**Never:** no removal of phone numbers, names, addresses or emails; no FastAPI, SDK, I/O or logging in the filter; no wiring into routes (Story 1.6); no change to text keys other than `privacy-notice` and `personal-info-reminder`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Thai ID | `1234567890123`, `1-2345-67890-12-3`, `1 2345 67890 12 3`, `1234 5678 90123`, `๑๒๓๔๕๖๗๘๙๐๑๒๓` | replaced with `[removed]`, removed = true | N/A |
| Passport | `AA1234567`, `A1234567`, `aa1234567`, `AA 1234567`, `AA-1234567` | replaced, removed = true | N/A |
| Glued | `เลขบัตร1234567890123ครับ`, `passportAA1234567` | `เลขบัตร[removed]ครับ`, `passport[removed]`, removed = true | N/A |
| Several matches | ID and passport in one sentence | each replaced, rest of text kept | N/A |
| Phone numbers | `081-234-5678`, `+66 81 234 5678`, `+47 412 34 567`, `98765432` | text returned exactly as given, removed = false | N/A |
| Dates, times, amounts | `05-11-2026 10:00`, `2026-12-01 - 2026-12-20`, `15.11.2026`, `ปี 2569`, `THB 1500000`, `costs 1500000 baht`, `COVID-1234567`, `100000-200000 บาท`, `30,000 euro`, `90 euro` | text returned exactly as given, removed = false | N/A |
| No personal info | Thai text, mixed Thai/English, empty string | text returned exactly as given, removed = false | N/A |

</frozen-after-approval>

## Code Map

- `app/pipeline/__init__.py` -- empty package; first module goes here. Pipeline must stay free of FastAPI/SDK imports (layer rule; Story 1.5 adds the import test).
- `content/texts.yaml` -- change `privacy-notice` and `personal-info-reminder` (th/en); keep the `>-` folded style and the header comment.
- `app/adapters/file_content.py` -- validates the file at startup (every `th` must contain Thai; no stray braces); no change needed.
- `tests/test_content.py`, `tests/test_texts_api.py` -- committed-file tests; must still pass after the text change.
- `app/static/` -- renders the texts from `/api/texts`; no code change.

## Tasks & Acceptance

**Execution:**
- [x] `app/pipeline/filter.py` -- `REMOVED_MARKER = "[removed]"`; `FilterResult(text: str, removed: bool)` frozen dataclass; `remove_personal_info(text: str) -> FilterResult` implementing the Thai ID group search and the passport pattern in Design Notes -- the single entry point Story 1.6 and the evaluation call.
- [x] `tests/test_filter.py` -- one parametrized case per matrix input and per extra case in Design Notes (alone and inside a sentence); exact output for glued and several-matches cases; kept cases return the input unchanged with removed false; `REMOVED_MARKER.isascii()`; an AST check that the module imports only what it uses from `re`, `unicodedata`, `dataclasses` and calls none of `open`, `print`, `__import__`, `eval`, `exec`; a committed-content test that `privacy-notice` and `personal-info-reminder` load and that both `privacy-notice` texts mention phone numbers (`เบอร์โทรศัพท์` / `phone`).
- [x] `content/texts.yaml` -- new `privacy-notice` and `personal-info-reminder` th/en from Design Notes.

**Acceptance Criteria:**
- Given the app runs, when I open `/`, then the privacy notice says ID and passport numbers are removed and phone numbers, names, addresses and emails are not, and asks me not to write them.
- Given `uv run pytest`, when it runs, then all filter cases and the existing content tests pass.

## Design Notes

Applied in this order on the original text (never normalise the whole text: NFKC changes Thai vowels). `D` = any Unicode decimal digit (`\d`). `SEP` = one of: space, tab, NBSP U+00A0, U+2009, U+202F, U+3000, zero-width U+200B–U+200D and U+FEFF, `-`, dashes U+2010–U+2015, U+2212, U+FE63, U+FF0D, `.`, `/`. Amended in loop 3 (see Spec Change Log).

1. **Thai ID (group search):** find digit runs: digit groups joined by 1–3 `SEP` chars, not preceded or followed by a digit. Scan each run's groups from the left and remove the first consecutive groups whose digits total exactly 13 and whose shape is one of: one group of 13; the official 1-4-5-2-1 grouping; every group 3+ digits. Continue after the removed groups. Separators outside removed groups and all other groups stay. So `ID 1234567890123 2 people` → `ID [removed] 2 people`; `1234567890123 1234567890123` → both removed; `12345678901234` (one 14-digit group), `1 2 3 4 5 6 7 8 9 10 11` and `0066 81 234 5678` stay.
2. **Passport:** letters `L` = `A–Z`, `a–z`, full-width `Ａ–Ｚ`, `ａ–ｚ`; then 7 digits not followed by a digit (a following ` 2` does not block it).
   - Glued (`L{1,2}` + 7 digits): the letters start a word (not preceded by a letter), any case; or they are uppercase and preceded by a lowercase letter (`passportAA1234567`, `passportA1234567` → `passport[removed]`). `COVID1234567` and `ref1234567` stay.
   - With separators (1–3 `SEP` chars between letters and digits): 1–2 uppercase letters that start a word. `AA 1234567`, `AA - 1234567` are removed; `is 1500000`, `kr 1500000`, `up to 1500000`, `No 1234567`, `THB 1500000`, `COVID-1234567` stay.

Extra test cases beyond the matrix. Removed: ID with NBSP, en dash, tab, U+200B, ` - ` and dots in the 1-4-5-2-1 shape; full-width-digit ID `１２３４５６７８９０１２３`; `ID 1234567890123 2 people` (exact output); `1234567890123 1234567890123` (both); `ＡＡ1234567`; `AA - 1234567`; `AA 1234567 2` (exact output `[removed] 2`); `passportA1234567` (exact output). Kept: `12345678901234`, `x 12345678901234`, `AA12345678`, `COVID1234567`, `ref1234567`, `is 1500000`, `kr 1500000`, `up to 1500000 baht`, `No 1234567`, `1 2 3 4 5 6 7 8 9 10 11`, `0066 81 234 5678`. Known and accepted (test so the trade-off is visible): `081 234 5678 123` is removed (groups of 3+ totalling 13); `A 1234567` is removed.

Notice and reminder drafts (Claude's Thai; adviser reviews before commit):

```yaml
privacy-notice:
  th: >-
    โปรดอย่าใส่เลขหนังสือเดินทาง เลขบัตรประชาชน เบอร์โทรศัพท์ ชื่อ ที่อยู่ หรืออีเมลในคำถาม
    ระบบจะลบเลขหนังสือเดินทางและเลขบัตรประชาชนให้อัตโนมัติ
    แต่จะไม่ลบเบอร์โทรศัพท์ ชื่อ ที่อยู่ และอีเมล คำถามของคุณจะถูกส่งไปยังบริการ AI เพื่อสร้างคำตอบ
  en: >-
    Please do not include your passport number, ID card number, phone number,
    name, address or email in your question. Passport and ID card numbers are
    removed automatically, but phone numbers, names, addresses and emails are not.
    Your question is sent to an AI service to create the answer.
personal-info-reminder:
  th: >-
    เราได้ลบเลขหนังสือเดินทางหรือเลขบัตรประชาชนออกจากคำถามของคุณก่อนส่ง
    โปรดอย่าใส่ข้อมูลส่วนตัวในคำถาม
  en: >-
    We removed passport or ID card numbers from your question before sending it.
    Please do not include personal information in your questions.
```

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass
- `uv run python -c "from app.pipeline.filter import remove_personal_info as f; print(f('ID 1-2345-67890-12-3 tel 081-234-5678 fee 90 euro'))"` -- expected: ID replaced, phone and `90 euro` kept, removed True

**Manual checks:**
- Page at 360 px: the longer notice wraps without horizontal scroll.

## Implementation Notes

- Pattern order: Thai ID, passport, Norwegian with `+47`/`0047`, Thai phone, bare Norwegian mobile. Prefixed numbers run before the bare 8-digit pattern so the country code is removed with the number.
- Every literal digit in the patterns (leading `0`, `+66`, `+47`, mobile prefixes) also accepts its Thai digit, so `๐๘๑...` is caught. The Thai digit range is built with `chr()` so the module stays ASCII (AD-6).
- Beyond the matrix, also removed (privacy first): Thai provincial landlines `0xx-xxx-xxx`, `08-1234-5678`, `+66 2 123 4567`, `+66 0812345678`, Norwegian `+47 dd dd dd dd`. Known false positive: any bare 8-digit number starting with 4 or 9 (e.g. `90000000`) is removed.
- The new Thai privacy notice is Claude's draft from Design Notes; it has not been reviewed by the adviser yet (NFR8), so the change is left uncommitted.
- Manual 360 px check not done in a browser; `body` already has `overflow-wrap: anywhere`.

- 2026-11-13, review loop 1: the first implementation was reverted (see Spec Change Log). The notes above describe the reverted code.
- 2026-11-13, review loop 2: the second implementation (two-step design with phone rules) was reverted after the user decided phone numbers are not removed (see frozen Decision and Spec Change Log).
- 2026-11-13, loop 2 implementation: two compiled patterns (Thai ID, then passport) applied with `subn` on the original text; NBSP, dashes and full-width letters are written as escape sequences so the module stays ASCII (the test checks `source.isascii()`). Known behaviour of the Design Notes rules, not covered by the matrix: a 13-digit phone spelling such as `0066 81 234 5678` is removed as a Thai ID, and a 7-digit amount after a one- or two-letter word (`up to 1500000 baht` -> `up [removed] baht`) is removed as a passport.
- The new Thai privacy notice and reminder are Claude's drafts from Design Notes and have not been reviewed by the adviser (NFR8), so the change is left uncommitted. Manual 360 px check not done in a browser.
- 2026-11-13, review loop 3: the third implementation (fixed separator guards) was reverted for a group-based Thai ID search and stricter passport rules (see Spec Change Log).

- 2026-11-13, loop 3 implementation: Thai ID is a `sub` over digit runs with a callback that scans groups from the left (`_thai_id_spans`); passport is one compiled pattern with three alternatives (glued word start, glued uppercase after lowercase, uppercase word start with 1-3 `SEP`). Non-ASCII characters are written as escape sequences; `unicodedata` is not needed and not imported. Tests: 108 cases in `tests/test_filter.py` (matrix and extra cases alone and inside a sentence, exact outputs, accepted false positives, ASCII and AST purity checks, committed notice content). The new Thai notice and reminder are Claude's drafts and not yet reviewed by the adviser (NFR8), so nothing is committed. Manual 360 px check not done in a browser.

## Spec Change Log

- 2026-11-13, loop 1. Triggering findings: the filter missed common real-world spellings of IDs and phone numbers (NBSP, en dash, double space, `0066`, `+66 (0)`, `(+66)`, 4-3-3 and other groupings, passport with a separator or after a Latin word, full-width digits, over-long runs) and removed amount ranges such as `4000-5000 บาท` (edge, blind; verified by probe). Amended: Design Notes (fixed pattern shapes replaced by a passport regex plus classified digit runs; extra removed, kept and accepted-false-positive cases), the two Execution tasks to match, and the notice draft (emails are not removed either, consistent with the frozen Never). Known-bad state avoided: personal numbers reaching the AI service because they were not written in one of a few fixed groupings. KEEP: the `REMOVED_MARKER`/`FilterResult`/`remove_personal_info` API and module path; Thai-digit support; digit-boundary matching (no `\b`) so numbers glued to Thai text are caught; ASCII-only source (build non-ASCII ranges with `chr()` or escapes); the test layout (parametrized matrix cases, exact glued and several-matches outputs, unchanged false positives, AST import check); the `>-` style in `texts.yaml`.
- 2026-11-13, loop 2 (intent change by the user). Triggering findings (round 2): date followed by time destroyed (`05-11-2026 10:00` → `[removed]:00`); passport rule cutting words (`THB 1500000` → `T[removed]`, `costs 1500000` → `cos[removed]`); and many more unhandled phone spellings (dots, slashes, ` - `, Unicode spaces and dashes, `412-34-567`, `81 234 5678`, `+ 47`, Norwegian landlines). The user decided phone numbers are not removed. Amended: frozen Intent, Decision, Always/Never and Matrix (phones and the round-2 false positives are now "kept" rows; Thai ID other groupings, Thai digits, passport separators and glued cases moved into the matrix); Design Notes (two patterns: Thai ID and passport only; the 11+ fallback removed because it would remove phone numbers with a country code); tasks; notice and reminder drafts (the reminder no longer says phone numbers are removed). Known-bad state avoided: an endless series of phone-format patches, each adding false positives on dates and amounts. KEEP: the `REMOVED_MARKER`/`FilterResult`/`remove_personal_info` API and module path; Unicode-digit support via `\d` and value-based reading; digit-boundary matching; ASCII-only source with escapes; the test layout (parametrized matrix cases, exact glued and several-matches outputs, unchanged kept cases, AST purity check now as an allowlist).

- 2026-11-13, loop 3. Triggering findings (round 3, verified by probe): an ID or passport followed by another number is kept (`ID 1234567890123 2 people`, `AA 1234567 2`, two IDs in a row) because of the `SEP`+digit guards; IDs with zero-width spaces, ` - `, dots or slashes are kept; the spaced passport form removes amounts after short words (`is 1500000`, `kr 1500000`, `up to 1500000`); the glued form cuts words (`COVID1234567` → `COV[removed]`, `passportA1234567` → `passpor[removed]`); any 13 digits in single-digit groups are removed; `0066 81 234 5678` removed as an ID. Amended: Design Notes (group-based Thai ID search with allowed shapes; wider `SEP`; passport glued/spaced rules with word starts and uppercase; only `(?!\d)` after the 7 digits), extra test cases, test task (content test for the notice), English reminder ("numbers"). Frozen Intent and Matrix unchanged. Known-bad state avoided: IDs leaking next to other numbers, and amounts removed as passports. KEEP: everything from loop 2 KEEP; the ASCII-only source; the matrix tests as written in loop 2.

## Review Triage Log

Pass 1 (loop 0 implementation; routed to bad_spec loopback):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | blind, edge | Separators other than one ASCII space/hyphen (NBSP, en dash, tab, double space) let numbers through | high | probe: `081 234 5678`, `081–234–5678` → removed False. bad_spec: Design Notes fixed single ASCII separators |
| 2 | edge | `0066 81 234 5678`, `+66 (0)81 …`, `+66 0 81 …` not removed | high | probe → removed False. bad_spec (same root: fixed shapes) |
| 3 | verif (other), blind | `(+66) 81 234 5678`, `(+47) 41234567` not (fully) removed | high | probe → removed False. bad_spec |
| 4 | edge | Thai mobile grouped 4-3-3 / 3-3-2-2 not removed | high | probe `0812-345-678` → False. bad_spec |
| 5 | blind, edge | Thai ID in other groupings (`1234 5678 90123`) not removed | high | probe → False. bad_spec |
| 6 | blind, edge, verif (other) | Passport with separator (`AA 1234567`) or after a Latin word (`passportAA1234567`) not removed | high | probe → False. bad_spec |
| 7 | blind, edge | Full-width digits not matched | medium | probe `０８１２３４５６７８` → False. bad_spec |
| 8 | blind, verif (other) | Over-long runs (14/16/20 digits, 11-digit Norwegian ID) remove nothing | medium | probe `12345678901234` → False; contradicts "when in doubt, remove". bad_spec |
| 9 | edge | Amount ranges `4000-5000 บาท` removed as a Norwegian mobile | medium | probe → `[removed] บาท`. bad_spec: new rule keeps hyphenated 8-digit runs |
| 10 | verif, blind | Extra formats and Thai-digit country codes untested | medium | pre-verified gap. folded into the re-derived test task (extra cases listed in Design Notes) |
| 11 | blind | Accepted false positives (`90000000`, reference numbers) untested | low | trade-off is the frozen "when in doubt, remove"; now listed as tested accepted false positives |
| 12 | blind | AST test does not forbid logging/I/O | low | test checked stdlib only. folded into the re-derived test task |
| 13 | blind | `test_marker_is_plain_text` only repeats the constant | low | folded into the re-derived test task (`isascii()`) |
| 14 | blind | Notice says nothing about email | medium | spec Never excludes email detection, so the notice should say it is not removed. Design Notes draft amended |
| 15 | blind | Notice promises removal before Story 1.6 wires the filter | false | no question reaches the AI service before Story 1.6 adds the chat endpoint; both ship before release. rejected |
| 16 | blind | Notice overclaims for foreign phone numbers | false | the amended design removes any `+` number with ≥ 8 digits. rejected |
| 17 | blind | `FilterResult` reports only a bool | low | AD-4 needs only `personal_info_removed`; changing the contract later is cheap while there is no caller. rejected |
| 18 | blind | Sprint status `in-progress` vs spec `in-review` | false | sprint sync to `review` happens at the present step by design. rejected |
| 19 | blind | Unreviewed Thai text could be committed by accident | false | commit is gated on the user's adviser-review confirmation at the present step. rejected |
| 20 | blind | `FILTER_FILE` built from a hard-coded path | low | moving the module fails loudly; cosmetic. rejected |
| 21 | edge | `None`/non-str input raises `TypeError` | false | Story 1.6 passes a validated `str`; a loud failure on unreachable input is correct. rejected |
| 22 | edge | Intent claim: phone removal misses common formats | high | same as #1–#5. bad_spec |

Pass 2 (loop 1 implementation; routed to intent change by the user, loop 2):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | blind | Date followed by time destroyed: `05-11-2026 10:00` → `[removed]:00` | high | verified by the reviewer's probe; the 9–10-digit phone rule joined date and hour. intent change: no phone rules; now a "kept" matrix row |
| 2 | blind, edge | Passport rule cuts words: `THB 1500000`, `costs 1500000`, `COVID-1234567` | medium | verified (`THB 1500000` → `T[removed]` reported by the implementer). bad_spec, folded into the loop 2 design: letters must start a word when a separator is used |
| 3 | blind | 11+ fallback joins years and amount ranges (`2024 2025 2026`, `100000-200000 บาท`) | medium | verified by probe. fallback dropped in loop 2; ranges are now "kept" matrix rows |
| 4 | blind, edge | Dotted / slashed phone numbers get through | medium | real; intent change: phones are not removed |
| 5 | edge | ` - ` separators, Unicode minus/full-width hyphen/ZWSP split phone runs | medium | real; intent change: phones are not removed |
| 6 | edge | Hyphenated Norwegian mobile `412-34-567` kept | medium | real; intent change |
| 7 | edge | Country code without `+` or with `+ ` kept | medium | real; intent change |
| 8 | edge | Thai mobile without trunk 0 (`81 234 5678`) kept | medium | real; intent change |
| 9 | blind, edge | Norwegian landlines kept | medium | real; intent change |
| 10 | edge | Passport regex eats first 7 digits of a longer phone (`Tel 0812345-678`) | medium | real; loop 2 design requires the 7 digits not to be followed by SEP+digit |
| 11 | blind, edge | Leading `(` left behind (`([removed]`) | low | phones are no longer removed, so no runs with brackets are replaced. moot |
| 12 | blind, edge | Full-width passport letters not matched | low | real; folded into the loop 2 design (full-width letters allowed) |
| 13 | verif | `+` other-country branch and `(+` prefix only tested through the fallback | medium | pre-verified gap; moot after the intent change (no phone rules) |
| 14 | verif (other) | `00` branch and 13-digit rule redundant with other rules | low | moot: the loop 2 design has only the Thai ID and passport patterns |
| 15 | blind | Thai-digit cases thin (local phone, ID, passport) | low | Thai-digit ID now a matrix row; passport digits follow the same `\d` |
| 16 | blind | No test for Norwegian national ID `DDMMYY NNNNN` | low | moot: 11-digit fallback dropped; Norwegian IDs are out of scope per FR9 |
| 17 | blind, edge | Purity test misses attribute calls, `__import__`, blocklist incomplete | low | folded into the re-derived test task (allowlist of imports, forbidden names) |
| 18 | blind | `_is_international` docstring hides the rules | low | moot: function removed in loop 2 |
| 19 | blind | Spec stale (notes describe reverted code; `digit` vs `decimal`) | low | notes now marked as reverted per loop; Design Notes no longer name the function. fixed in spec |
| 20 | blind | Sprint status vs spec status; adviser review not visible in diff | false | carried: as pass 1 #18 and #19 |
| 21 | edge | Notice claims phone numbers are removed although many spellings slip | high | real; intent change: notice now says phone numbers are not removed |

Pass 3 (loop 2 implementation; routed to bad_spec loopback, loop 3):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | edge | ID followed by another number kept (`ID 1234567890123 2 people`) | high | probe → removed False. bad_spec: `SEP`+digit guard in Design Notes |
| 2 | edge | Two IDs separated by one space both kept | high | probe → removed False. bad_spec (same guard) |
| 3 | edge | Passport followed by ` 2` kept | high | probe `AA 1234567 2` → removed False. bad_spec (same guard) |
| 4 | blind, edge | ID with ZWSP, ` - `, dots, slashes, Unicode minus/full-width hyphen kept | medium | probe ZWSP and ` - ` → removed False. bad_spec: `SEP` set and one-char limit |
| 5 | blind, edge | Spaced passport form removes amounts after short words (`is`, `kr`, `up to`) | medium | probe `is 1500000` → `[removed]`. bad_spec: uppercase + word start required |
| 6 | blind, edge, verif (other) | Glued passport form cuts words (`COVID1234567`, `passportA1234567`, `ref1234567`) | medium | probe `COVID1234567` → `COV[removed]`. bad_spec: word start or lowercase→uppercase join |
| 7 | edge | Any 13 digits in single-digit groups removed (`1 2 3 … 11`) | low | probe → `[removed]`. folded into loop 3 (allowed shapes) |
| 8 | blind, edge | `0066 81 234 5678` removed as an ID although phones are kept | low | probe → removed. folded into loop 3 (shapes: the `81` group blocks it) |
| 9 | blind | English reminder says "a … number" when several were removed | low | real. draft amended ("numbers") |
| 10 | verif, blind | NBSP/dash/tab and full-width cases untested | medium | pre-verified gap (mutations survive). folded into the extra test cases |
| 11 | verif, blind | Boundary cases (14 digits, `AA12345678`) untested | medium | pre-verified gap. folded into the extra kept cases |
| 12 | blind | Notice content not tested | low | folded into the test task (content test) |
| 13 | blind | Notice says "removed automatically" though some spellings slip | low | after loop 3 the remaining misses are unusual spellings; the user chose the wording scope. rejected |
| 14 | blind | Allowlist includes unused `unicodedata`; forbidden-name check too broad | low | folded into the test task (allow only what is imported) |
| 15 | blind | Docstring says phones never removed but `0066 …` was | low | moot after loop 3 (#8) |
| 16 | blind | Sprint status vs spec; spec untracked | false | carried: as pass 1 #18 |
| 17 | edge | `None` input raises `TypeError` | false | carried: as pass 1 #21 |
| 18 | edge | Intent claims: IDs/passports leak in common phrasings | high | same root as #1–#4. bad_spec |

Pass 4 (loop 3 implementation; verified by probe 2026-11-14):

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | verif | ID after another number in the same run untested (`else: i += 1` mutation survives) | medium | pre-verified gap; probe `born 01.02.1990 1234567890123` → `born 01.02.1990 [removed]`. patched (tests) |
| 2 | verif | Passport with Thai/full-width digits untested (`[0-9]` mutation survives) | medium | pre-verified gap; probe `AA` + Thai digits → removed. patched (tests) |
| 3 | verif (other), blind, edge | Session log and `issues.md` describe the reverted phone design (`90000000` item) | low | real. Fixed in the session log for this session, not in code |
| 4 | blind | `issues.md` misses adviser review of the new texts, PRD/epics update for narrower FR9 | low | real. Fixed in the session log for this session |
| 5 | blind | English reminder "before sending them" refers to the numbers | low | real (`content/texts.yaml:24`). fixed: "before sending it" in texts.yaml and the Design Notes draft |
| 6 | blind, edge | 13 digits in 3+ groups that are not an ID are removed: `room 123 0812345678`, `500000-1500000 baht`, `1500000 / 250000`, `2569 2026 12345`, `021234567 2569`, `98765432 12345` | medium | probe → `[removed]` for each. deferred (user chose accept over loop 4, 2026-11-14): the "every group 3+" shape in Design Notes |
| 7 | edge | 13-digit phone spellings removed: `0066812345678`, `0066 812345678`, `0066-812-345-678` | medium | probe → removed; contradicts the frozen Decision. deferred (user chose accept over loop 4, 2026-11-14): no rule against a leading 0 (Thai IDs start with 1–8) |
| 8 | blind, edge | Real ID spellings leak: `1 234567890123`, `1-2345-67890-123`, `1 2345 67890 123`, `12-3456-78901-2-3` | high | probe → removed False. deferred (user chose accept over loop 4, 2026-11-14): allowed shapes too narrow |
| 9 | edge | Left-first scan leaks the tail of an ID after a 5-digit group: `10110 1234 5678 90123` → `[removed] 90123` | medium | probe confirms. deferred (user chose accept over loop 4, 2026-11-14): scan order in Design Notes |
| 10 | blind, edge | Glued lowercase/mixed words remove amounts: `kr1500000`, `Rs1500000`, `No1234567` | medium | probe → `[removed]`. deferred (user chose accept over loop 4, 2026-11-14): glued any-case rule |
| 11 | edge | Separators outside `SEP` (U+2002–U+2008, soft hyphen, word joiner, full-width dot) let IDs through | low | probe en-space ID → kept. deferred (user chose accept over loop 4, 2026-11-14): same `SEP` definition |
| 12 | edge | `AA: 1234567`, `AA:1234567` leak | medium | probe → kept. deferred (user chose accept over loop 4, 2026-11-14): colon not a passport separator |
| 13 | blind | `NO 1234567`, `US 1234567` removed | low | exact passport shape; indistinguishable without context. rejected |
| 14 | edge | `CovID1234567` → `Cov[removed]` | low | rare spelling; fix adds rules. rejected |
| 15 | blind, edge | Letter pair after a digit: `2AA1234567` → `2[removed]` | low | passport still removed; stray digit harmless. rejected |
| 16 | edge | `ID 1234567 890` → `[removed] 890` | low | rare; fix adds a lookahead branch. rejected |
| 17 | edge | `AA1234567890123`, `AA 1234567 123456` leave orphan `AA` | low | personal digits removed; letters harmless. rejected |
| 18 | blind | Content test does not check the new wording; reminder only checked non-empty | low | real. patched (tests) |
| 19 | blind | Purity test allows unused `unicodedata`; forbidden names only via `ast.Name` | low | `unicodedata` part real (pass 3 #14 not applied), patched; attribute-call part rejected (no realistic caller) |
| 20 | blind | Test coverage gaps: punctuation around matches, `1AA1234567`, `aa 1234567` kept | low | real. patched (tests) |
| 21 | edge | Accepted false positives tested alone only | low | real. patched (tests) |
| 22 | blind | Test file comment says escapes, but Thai is raw | low | real. patched (comment) |
| 23 | verif (other), blind | Implementation Notes' first block describes reverted code | low | fix is to edit this spec. rejected |
| 24 | edge (claim) | "Phone numbers are not removed" fails for some spellings | medium | same root as #6, #7 |
| 25 | edge (claim) | Notice says IDs are removed but some spellings leak | high | same root as #8, #9, #11, #12 |
