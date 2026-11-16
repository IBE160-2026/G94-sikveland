---
title: 'Story 5.1: Test set of Thai questions'
type: 'feature'
created: '2026-11-16'
status: 'done'
route: 'dispatch'
baseline_commit: '970615d9746011989e8337d700a940c568c59dc7'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Answer quality is not measured (NFR4, SM-2). `eval/` is empty, and Story 5.2's `run_eval.py` needs a fixed set of Thai questions with expected categories, facts and sources to run against.

**Approach:** Write `eval/testset.yaml` with 20–30 made-up Thai cases that cover every case NFR4 names, plus a small loader that 5.2 reuses and a pytest that checks the schema, the coverage and the filter expectations without any model call. The Thai is a DRAFT until the user approves it as adviser review (NFR8).

**Decisions (derived from earlier user decisions):**
- **Phone numbers:** the filter keeps them (user decision 2026-11-13, Story 1.4). A phone case expects the number kept, not removed.
- **Review:** as for every earlier Thai text, the Thai is marked DRAFT and becomes approved only on the user's explicit approval.

## Boundaries & Constraints

**Always:**
- One case per entry under `cases:`: `id` (kebab-case, unique), `question` (Thai, may mix in English), `en` (English gloss, no Thai), `category` (one of the five in `app/ports/llm.py`), `outcome` (`answered` | `no_answer` | `fixed_reply`, the request-log values), `facts` (English strings), `sources` (ids), `tags`, and optional `history` (1–2 `{question, answer}` exchanges, Thai) and `personal_info` (list of `thai_id` | `passport` | `phone`).
- Consistency: `general` → `answered` or `no_answer`; any other category → `fixed_reply`. `answered` needs ≥1 fact and ≥1 source; `no_answer` and `fixed_reply` have neither.
- Every source id exists in `knowledge-base/sources.yaml`, and every fact of an `answered` case is stated in a cited snapshot. A `no_answer` question is in scope (visitor/tourist visa to Norway) and no snapshot answers it.
- Coverage, checked by tags: `steps`, `checklist`, `sponsorship-form`, `invitation-letter`, `relationship-proof`, `fee`, `typo`, `mixed-language`, `follow-up` (each ≥1); ≥2 `individual_assessment`, ≥2 `out_of_scope`, ≥4 `no_answer`, ≥3 `reach_person` worded differently (asking for a person and for help with the whole process); `personal_info` covers `thai_id`, `passport` and `phone`.
- Only made-up data: Thai ID numbers with a wrong check digit, passport numbers like `AA1234567`, phone numbers like `081-234-5678`; no real enquiry or person.
- The file header says DRAFT, awaiting the user's review (NFR8); expected facts avoid points the adviser has not settled (photo age 3 vs 6 months).

**Never:** no model or network call in tests; no change to `app/`, the filter, prompts or the knowledge base; no `run_eval.py` (Story 5.2); no reuse of the four example questions word for word.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Committed file | `eval/testset.yaml` | loads; 20–30 cases; every coverage rule holds | N/A |
| Thai ID / passport case | `personal_info` has `thai_id` or `passport` | `remove_personal_info(question)` contains `[removed]` and none of the number | N/A |
| Phone-only case | `personal_info: [phone]` | the filter leaves the question unchanged | N/A |
| Any other case | no `personal_info` | the filter leaves question and history unchanged | N/A |
| Unknown source / category / outcome | bad value in a written test file | `TestsetError` naming the case id | loader raises |
| Missing or extra field, duplicate id, bad id | written test file | `TestsetError` naming the case id | loader raises |
| Inconsistent case | `fixed_reply` with sources, `answered` without facts, `general` + `fixed_reply` | `TestsetError` | loader raises |

</frozen-after-approval>

## Code Map

- `scripts/ingest.py`, `tests/test_ingest.py` -- scripts have no `__init__.py`; tests import them as `scripts.<name>`. New `scripts/testset.py` follows that.
- `app/adapters/file_knowledge_base.py` `load_knowledge_base(KNOWLEDGE_BASE_DIR).source(id)` -- raises `KeyError` for unknown ids; `app/main.py` has `KNOWLEDGE_BASE_DIR`. Snapshots are `knowledge-base/<id>.md` (15 sources).
- `app/ports/llm.py` `Category`, `Exchange(question, answer)` -- reuse; `app/web/request_log.py` `Outcome` holds the outcome values.
- `app/pipeline/filter.py` `remove_personal_info(text).text`, `REMOVED_MARKER` -- removes Thai IDs and passports only; `docs/implementation/deferred-work.md` lists known misses and false positives ("check against the evaluation test set") -- pick numbers the filter handles today.
- `tests/test_demo_answers.py` -- pattern for loading YAML against the real knowledge base; `tests/test_checklists.py:355` -- header check for "NFR8" + "approved"/"DRAFT".
- `content/texts.yaml` `example-questions` -- the four questions not to copy.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/testset.py` -- `load_testset(path, knowledge_base) -> list[TestCase]` (frozen dataclasses, `history` as `Exchange`s), `TestsetError`, all schema and consistency rules -- Story 5.2 reads cases through it
- [x] `eval/testset.yaml` -- 24–28 cases, DRAFT header, facts taken from the snapshots -- NFR4
- [x] `tests/test_testset.py` -- the committed file and every matrix row, using `tmp_path` files for the error rows -- NFR4
- [x] `README.md` -- `eval/` row and a short "Testsett" section (Norwegian): what is in it, the fields, that 5.2 runs it -- examiner

**Acceptance Criteria:**
- Given the committed test set, when pytest runs, then it passes with no network access and reports a failure naming the case for any broken rule.
- Given an `answered` case, when the adviser reads it, then each fact can be found in a cited snapshot.

## Implementation Notes

- 30 cases: 15 `answered`, 4 `no_answer`, 3 `individual_assessment`, 3 `out_of_scope`, 4 `reach_person`, 1 `done`. This goes past the task's 24–28 (still within the frozen 20–30): review added three cases for the classifier prompt's boundary rules (thanks plus a question → `general`; own chances plus a document question → `general`; a follow-up that turns to a study permit → `out_of_scope`). No-answer topics (document translation, pregnancy, vaccination certificate, interpreter at VFS) were checked by grep to appear in no snapshot; VFS opening hours was dropped because a snapshot gives the VFS address and contact details.
- The reach-person questions share no phrase with the classifier prompt's few-shot examples.
- `sources` means "the snapshots that state the facts; citing any of them is a correct source" (written in the file header) -- Story 5.2 should check "at least one expected source cited", not all.
- The loader also requires `history` exactly on cases tagged `follow-up`, at most 2 history exchanges, Thai in every history turn, no Thai in `en`/facts, unique tags/sources/personal_info kinds. Coverage counts are checked only in the test, so small written files load.
- `TestCase` and `TestsetError` set `__test__ = False` so pytest does not try to collect them.
- Extra checks beyond the matrix: Thai ID numbers have a wrong check digit, every number in an expected fact appears in a cited snapshot, no question equals one of the four example questions, history passes the filter unchanged.

- The user approved the Thai of `eval/testset.yaml` (30 questions, 3 history exchanges) and the expected facts as adviser review on 2026-11-16 (NFR8).

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Route | Evidence |
|---|-------|---------|---------|-------|----------|
| 1 | blind | `no-answer-vfs-opening-hours` may be answered: a correct answer can point to VFS's phone and website and cite a source | medium | patch | `knowledge-base/embassy-hand-in-documents.md` lines 17–24 give the VFS Rama 9 address, phone, email and website; a cited answer ends `answered`, so the 100% no-answer target would count a good answer as a miss. |
| 2 | blind | No boundary cases for the rules in `prompts/classifier-system.md` (thanks plus a question is `general`, own chances plus a document question is `general`, a follow-up that turns out of scope) | medium | patch | Lines 14, 20 and 22 of the prompt state these rules; every non-general case today has one easy intent, so a prompt change that breaks them would go unseen. Adding three cases (30 total) stays within the frozen 20–30. |
| 3 | blind | `reach-person-whole-process` and `reach-person-thai-adviser-mixed-language` are close paraphrases of the classifier prompt's few-shot examples | low | patch | Prompt lines 29–30: "อยากติดต่อที่ปรึกษาค่ะ", "ช่วยดูเรื่องยื่นวีซ่าให้ทั้งหมดได้ไหม"; close copies inflate the reach-person score. Rewording two Thai strings is a direct correction. |
| 4 | verification-gap | The duplicate-tag rule in `_tags` is never tested | low | patch | Pre-verified: `lists tag` appears only in the raise. One table row. |
| 5 | verification-gap | The Thai check on a history `question` is never tested | low | patch | Pre-verified: only the history `answer` row exists. One table row. |
| 6 | verification-gap, edge-case | `test_thai_id_numbers_are_made_up_with_a_wrong_check_digit` passes with zero matches | low | patch | No `assert` that `_THAI_ID.findall` found anything; a one-line assertion. |
| 7 | blind, edge-case | The number check skips numbers written as words, yet the README says every number in a fact is in a source | low | patch | `_NUMBER` matches digits only; facts say "three months", "two blank pages", "five years". README wording only. |
| 8 | blind | `epic-5-context.md` says `eval/` is empty, all stories are in backlog and the phone conflict is open | low | patch | Each contradicts this change or the spec's decisions; Story 5.2 starts from this file. Direct correction. |
| 9 | blind | The NFR8 header test passes whether the file says DRAFT or approved | low | reject | Same check as `tests/test_checklists.py:356`, the project's convention; it only guards that the review note exists. |
| 10 | blind | "Citing any listed source is correct" accepts a source that states only some facts (`passport-validity`) | low | reject | The adviser judges the facts per answer; per-fact sources would change the schema 5.2 builds on. |
| 11 | blind | No case has personal information in the history | low | reject | History filtering is deterministic and tested in `tests/test_answer_pipeline.py:161` and `tests/test_chat_api.py:147`; the evaluation measures the models. |
| 12 | blind | The known filter misses in `deferred-work.md` are not in the set | low | reject | The spec chose numbers the filter handles today; xfail cases would add a new mechanism. The phone case already checks one false-positive class. |
| 13 | blind | `done-thanks` has no history and is the only `done` case | low | reject | The prompt says a thank-you is `done` also with no history; a second case adds little. |
| 14 | blind | The "worded differently" reach-person check only counts distinct strings | low | reject | Cosmetic; the cases and tags carry the real check. |
| 15 | blind | `scripts/testset.py` has no `__main__` entry | low | reject | The README does not tell anyone to run it; pytest is the check. |
| 16 | blind, edge-case | Spec says `in-review` while sprint status says `in-progress` | false | reject | Mid-workflow: step 5 sets `review`. |
| 17 | blind | `_choice` returns `str` into `Literal` fields | false | reject | No type checker is configured (`pyproject.toml`, CI); no tool or caller is affected. |
| 18 | blind | Duplicate questions are not rejected | low | reject | None exist; a check adds a guard. |
| 19 | edge-case | A case without `personal_info` could hold a phone number unnoticed | low | reject | None does today (only `reach-person-call-back` has a phone number); a detector adds a guard. |
| 20 | edge-case | Declared `personal_info` kinds are not compared with the kinds in the text | low | reject | All four cases declare exactly their one kind; a detector adds a guard. |
| 21 | edge-case | A phone number in a case that also has an ID is never checked to be kept | false | reject | No case mixes kinds. |
| 22 | edge-case | Near-copies of example questions (spacing, punctuation) pass the copy guard | low | reject | Checked by reading: no question is close to the four example questions. |
| 23 | edge-case | A `mixed-language` tag is accepted on a question without Latin letters | low | reject | All three such cases contain Latin words; a check adds a guard. |
| 24 | edge-case | An empty `tags` list loads | low | reject | No case has one; a guard. |
| 25 | edge-case | `load_testset` given a `str` path raises `AttributeError` | low | reject | No caller yet; Story 5.2 owns its argument parsing. |
| 26 | edge-case | A duplicate key inside a case is reported by line, not case id | low | reject | The line number locates it; cosmetic. |

## Verification

**Commands:**
- `uv run pytest` -- expected: exit code 0
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean
