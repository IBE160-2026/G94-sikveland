---
title: 'Prompt fixes from the first Ollama evaluation'
type: 'bugfix'
created: '2026-11-16'
status: 'done'
route: 'dispatch'
baseline_commit: '2caa42d0c06c7f3147f761a04806ca242c2a8d01'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The first evaluation run with Ollama (`eval/reports/2026-11-16-answer-1-classifier-3-citing-2.md`, scored by the user) missed two NFR4 targets. (A) Three of four questions that no source answers (pregnancy, vaccination certificate, interpreter at VFS) got "the sources do not say this" followed by general requirements with citations, so the pipeline counted them as answers and the fixed no-answer text never showed (no-answer 1 of 4); two replies also told the applicant "the documents you gave me" (เอกสารที่คุณให้มา). (B) The classifier sent "I changed jobs two months ago: will the embassy approve me, and what proof of employment do I need?" to `individual_assessment`, against its own rule that own chances plus a general question is `general`, so the applicant got "only the embassy decides" and no document answer.

**Approach:** Two prompt edits, each a new prompt version. (A) In the Ollama-only citing addendum `prompts/answer-citing-markers.md` (version 2 → 3): when the documents answer none of what was asked, write only a short Thai sentence that this information is not available and cite nothing, with no related general requirements or advice; when they answer part of it, answer that part with citations and say briefly that the rest is not covered; never mention "the documents", "the documents you were given" or anything about how the answer is made. (B) In `prompts/classifier-system.md` (version 3 → 4): make the "own chances plus a general question → general" rule hard to miss, for example as a check made before `individual_assessment`, with at least one new Thai example of the pattern. Then run the evaluation with Ollama again and compare.

**Decisions (user, 2026-11-16):** both fixes in one change; subagents allowed.

## Boundaries & Constraints

**Always:**
- Only the two prompt files change their behaviour; `prompts/answer-system.md` (shared with Claude) is unchanged. The classifier prompt is also used by Claude: its other rules and examples stay, and the tests for them still pass.
- New or reworded examples share no phrase with any question in `eval/testset.yaml` (the evaluation must not be taught its own answers) and keep the prompt's Thai-and-English mix.
- Prompt version lines go up (`version: 3` in the citing addendum, `version: 4` in the classifier); tests that pin the versions and rules are updated, and new tests pin the new rules.
- README: the example report name and `prompt_versions` examples use the new versions.

**Never:** no change to `app/` code, the pipeline, the test set or the knowledge base; no change to how citations become the no-answer text (AD-7).

## Code Map

- `prompts/answer-citing-markers.md` -- Ollama-only addendum appended to the answer prompt (`app/adapters/ollama_llm.py`); its last rule today: "If the documents do not answer the question, say so briefly in Thai and cite nothing."
- `prompts/answer-system.md` -- shared answer prompt; says "Answer only from the documents you are given" (source of the "documents you gave me" wording); not to be edited.
- `prompts/classifier-system.md` -- categories, rules (the own-chances rule is the second rule), examples per category; `general` examples already include "จะได้วีซ่าไหม แล้วต้องใช้เอกสารอะไรบ้าง".
- `app/pipeline/answer.py` `answer_question` -- zero known citations → `no_answer_text` (why cited general advice defeats the no-answer text).
- `tests/test_prompts.py` -- `test_citing_prompt_asks_for_thai_script_only`, `test_classifier_prompt_loads_with_version_3` and the rule/example tests; extend, do not weaken.
- `eval/testset.yaml` -- the 30 questions new examples must not copy; `scripts/run_eval.py` -- the run.
- `README.md` -- `2026-11-16-answer-1-classifier-3.md` and the `prompt_versions` examples.

## Tasks & Acceptance

**Execution:**
- [x] `prompts/answer-citing-markers.md` -- version 3, the no-answer and partial-answer rules, no mention of the documents -- NFR4, AD-7
- [x] `prompts/classifier-system.md` -- version 4, the own-chances-plus-general rule made prominent, new example(s) -- NFR4, AD-5
- [x] `tests/test_prompts.py` -- versions and the new rules pinned -- NFR3
- [x] `README.md` -- version examples -- examiner

**Acceptance Criteria:**
- Given the test suite, when it runs, then it passes and pins both new prompt versions and rules.
- Given a new Ollama evaluation run, when it is compared with the first report, then the no-answer and `own-chances-and-employment-proof` results are shown side by side with the other targets, and any target that got worse is reported, not hidden.

## Implementation Notes

- Implemented by a subagent from this spec. `uv run pytest`: 1467 passed, exit code 0; ruff check and format clean. The new Ollama evaluation run is not done yet (left to the orchestrator).
- Citing addendum version 3: the old last rule became a section "When the documents do not answer the question" with three rules: none answered → one short Thai sentence (example "ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ"), no citations, nothing else; part answered → answer that part with citations plus one sentence that the rest is not covered; never mention the documents below or how the answer is made (English and Thai wordings listed), while naming the documents the applicant must hand in stays fine (เอกสาร means both).
- Classifier version 4: the `individual_assessment` line now ends "Make the check below before you choose it.", and a section "Check before you choose individual_assessment" sits between the categories and the rules (general part present → general, also when the own-chances part comes first or is longer; a request for a person and own chances for out-of-scope things keep their rules). The old rule and its example stay. New `general` examples: two Thai (bank balance + statement months, mixed Thai-English; age 65 travelling alone + insurance) and one English (freelancer + bank statements). They avoid the employment-proof topic of the test case.
- Test-set overlap is pinned: a test checks that the three new examples share no run of 10 characters with any test-set question or history question. The older examples were not changed and share common words (e.g. ค่าธรรมเนียม, ต้องใช้เอกสาร) with the test set, so the check covers only the new ones.
- Also changed beyond the code map: `tests/test_chat_api.py` `test_classifier_prompt_is_loaded_and_versioned` pinned classifier `"3"`; now `"4"`. Not changed: `docs/implementation/manual-test-plan.md` still expects `prompt_versions.classifier` `"3"` in the Story 2.2 and 2.3 checks.
- Review patches (applied by the orchestrator; the implementer could not be resumed): the citing addendum now says a not-available sentence never gets `[[id]]` (an intermediate run cited it in two no-answer cases), and that a left-over own-chances part gets "the embassy decides each application" instead of "not covered" (FR3); two tests pin these rules; `manual-test-plan.md` now expects classifier `"4"`. `uv run pytest`: 1469 passed, exit code 0; ruff clean.
- Final Ollama run `eval/reports/2026-11-18-answer-1-classifier-4-citing-3.md` compared with `2026-11-16-answer-1-classifier-3-citing-2.md`: general 15 of 15 pass the automatic checks (was 14 of 15 automatic, 13 of 15 after the adviser; the new run awaits the adviser); individual assessment 3 of 3 (unchanged); no-answer 3 of 4 (was 1 of 4); reach person 4 of 4 (unchanged); `own-chances-and-employment-proof` now `general` + answered, with "the embassy decides" for the chances part; "documents you gave me" wording in 1 reply (was 3). No target got worse. Still missed: `no-answer-interpreter-at-vfs` wrote the not-available sentence, then went on with cited advice and "เอกสารที่ให้มา" (the same case passed in the intermediate run, so the 9B model follows the rule only most of the time).

## Spec Change Log

## Review Triage Log

Evidence from an intermediate Ollama run made before the patches below (report not kept, since its prompt version label matches the final one): classifier fixed, individual assessment 3 of 3, no-answer 2 of 4, `sponsorship-form-validity` fell to `no_answer` after a dropped unknown id.

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | edge-case | The model cites the not-available sentence because "after each sentence write `[[id]]`" wins over "cite nothing" | high | `no-answer-pregnancy` and `no-answer-vaccination-certificate` replied "ขออภัย ไม่มีข้อมูล…" with 4 and 2 cited sources, so they counted as answered and the no-answer text never showed | patch |
| 2 | blind, edge-case | In an own-chances-plus-general question, the partial-answer rule makes the own-chances part "not covered" instead of "the embassy decides" | medium | `own-chances-and-employment-proof` replied "…ความน่าจะเป็นในการอนุมัติ… ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ"; manual test plan Story 2.1 step 4 expects "says the embassy decides" (FR3) | patch |
| 3 | blind, edge-case | `manual-test-plan.md` still expects `prompt_versions.classifier` `"3"` (Story 2.2 step 10, Story 2.3 Part B step 6) | low | lines 173 and 199; a manual tester would record a false failure | patch |
| 4 | blind | Classifier version 4 also changes Claude's sorting, and only an Ollama run is planned | medium | the classifier prompt is shared; no `.env` key on this machine, so a Claude run cannot be made here | defer |
| 5 | blind, edge-case | Banning "the documents" may make the model stop listing documents to hand in | false | `relationship-proof-unmarried-partner` and `own-chances-and-employment-proof` still list the documents to hand in | reject |
| 6 | blind, edge-case | The check may count the history's general part, so a pure own-chances follow-up becomes general | false | `follow-up-own-chances` still got `individual_assessment` / `fixed_reply` | reject |
| 7 | blind, edge-case | Three money/income `general` examples and no counterweight may flip pure own-chances questions to general | false | `own-chances-salary`, `own-chances-earlier-overstay` and `follow-up-own-chances` all got `fixed_reply`; individual assessment 3 of 3 | reject |
| 8 | edge-case | Examples share words with the test set (กี่เดือน, แบบไหน, ประกัน) | false | those are single common words, not phrases; the test pins no shared 10-character run, which is the spec's bar | reject |
| 9 | blind | The forbidden list misses wording about "sources" | false | the app shows source links to the applicant, so naming official sources is not misleading; "the documents you gave me" wording fell from 3 replies to 0 | reject |
| 10 | blind | The overlap test checks only exact 10-character runs, not `en`, case or paraphrase | low | true, but the spec's bar (no shared phrase) is met and a fuzzy check adds complexity | reject |
| 11 | blind | Tests pin wording, not behaviour | low | prompt behaviour is measured by the evaluation; uncited → no-answer text is already tested (`tests/test_answer_pipeline.py:127`, `tests/test_chat_api.py:121`) | reject |
| 12 | blind | The check repeats Rule 2 and the out-of-scope rule | low | the spec requires the old rule and its example to stay | reject |
| 13 | blind | `prompts/answer-system.md` still says "the documents you are given" | low | the intent forbids editing the shared answer prompt | reject (out of scope by intent) |
| 14 | edge-case | Own chances plus a rule question about an out-of-scope permit may become general | low | unlikely; the check's third bullet keeps the out-of-scope rule | reject |
| 15 | blind | The README example report name does not exist | false | the README gives it as an example of the naming pattern, as before | reject |
| 16 | blind | The second acceptance criterion (new run, side-by-side comparison) is not met | false | the run is done and the comparison is presented at the end of the build | reject |
| 17 | blind | The example not-available sentence never reaches the applicant | low | by design (AD-7) the pipeline replaces it; a note in the prompt would go to the model | reject |

## Verification

**Commands:**
- `uv run pytest` -- expected: exit code 0
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean

**Manual checks (if no CLI):**
- `LLM_PROVIDER=ollama MOCK_LLM=false uv run python scripts/run_eval.py` (local, no cost) after the change; the orchestrator runs it and compares with the first report.
