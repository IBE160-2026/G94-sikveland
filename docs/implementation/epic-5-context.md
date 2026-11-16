# Epic 5 Context: Measured quality: test set and evaluation

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

The adviser and the course examiner need evidence that the chatbot meets its quality targets, not just that it runs. This epic adds a fixed Thai test set with expected answers, an evaluation script that runs it against the real models through the same pipeline as the chat page and writes a report (SM-2, the during-course success metric), and a statistics script that reports the share of conversations whose first feedback answer was "Yes" (SM-1, the after-launch metric). It covers no new applicant-facing feature. 5.1 and 5.2 are "next" priority, and 5.3 is "if time allows". 5.1, 5.2 and 5.3 are built and in review. `eval/testset.yaml` holds the test set (5.1).

## Stories

- Story 5.1: Test set of Thai questions
- Story 5.2: Evaluation script and report
- Story 5.3: Feedback statistics

## Requirements & Constraints

- **Test set contents (`eval/testset.yaml`).** It has 20–30 questions. Each has a kebab-case `id`, the Thai question, an English gloss, the expected category, the key facts the answer must contain and the expected source IDs. Coverage:
  - application steps, checklists, the sponsorship form and invitation letter, relationship proof and the visa fee
  - individual-assessment and out-of-scope questions
  - questions with typos and questions that mix Thai and English
  - at least 4 in-scope questions that no source answers
  - at least 3 different phrasings of asking for a person or for help with the whole process
  - personal-information cases (at least one Thai ID, one passport number and one phone number)
  - some follow-ups that come with a short history
- **Privacy and review.** Only made-up numbers and no real applicant enquiries. The adviser writes or reviews every expected answer.
- **Quality targets (judged per run).**
  - At least 90% of general questions correct with the correct source. "Correct" means it contains the expected facts and source, as judged by the adviser.
  - 100% of individual-assessment questions get "the embassy decides".
  - 100% of questions the sources do not cover get the no-answer message with no invented facts.
  - 100% of requests for a person get the adviser contact.
  - Answers are in Thai, also for typos and mixed-language questions.
- **When to rerun.** Rerun the evaluation by hand after every change to prompts or sources, and keep the results. It is separate from CI.
- **Evaluation run.** The script refuses demo mode (`MOCK_LLM=true`) or a missing key, with a clear message.
  - Automatic checks: category match, expected sources cited and personal information removed.
  - The report puts the answer text and the expected facts side by side and leaves an empty adviser-judgement column.
  - It shows totals against each target, plus the models, prompt versions, total tokens and total cost.
  - `--score <report>` recalculates the totals from the adviser's judgements.
  - The README explains how to run the evaluation, fill in the judgements and read the report. It says to rerun after changes and that runs vary, so each run is judged on its own.
- **Feedback stats.** `scripts/feedback_stats.py` prints the number of conversations with feedback and the share whose first answer was "yes", compared with the 80% target.
  - Only the first answer per `conversation_id` counts, so "no" followed by "yes" counts as "no".
  - `--from`/`--to` limit the count to feedback created in that period.
  - An empty or missing database reports "no feedback yet" instead of failing.
- **Safe tests.** pytest never calls the real API.
  - 5.1: a test checks that every test-set entry has the required fields and uses only known source IDs and valid categories.
  - 5.3: tests cover the no-then-yes case and the date filter.

## Technical Decisions

- **Same pipeline as the chat page.** `scripts/run_eval.py` must call the same pipeline entry point as `POST /api/chat`: filter personal information → classify → route → answer or fixed reply. It never calls the model directly, so the filter and classifier are evaluated too.
- **Categories (closed set):** `general`, `individual_assessment`, `out_of_scope`, `reach_person`, `done`. The classifier sees the cleaned question plus the last 2 exchanges. History has the shape `[{question, answer}]`, with at most 10 exchanges.
- **No-answer is not a category.** It happens when a `general` answer ends with zero known citations, and the pipeline then sends the fixed `reply-no-answer`. The test set and report have to recognise this outcome separately from the category.
- **Fixed replies by category.** Fixed replies come from `content/texts.yaml` with `{ADVISER_CONTACT}` filled in:
  - `individual_assessment` → `reply-embassy-decides`
  - `out_of_scope` → `reply-out-of-scope`
  - `reach_person` → `reply-reach-person`
  - `done` → `feedback-question`
- **Sources.** A cited ID that is not in `knowledge-base/sources.yaml` is dropped. Source IDs are kebab-case. A source's version is its `retrieved` date.
- **Models and cost.** Answers use `MODEL_ANSWER` (Claude Opus 5.5). Classify uses `MODEL_SMALL` (Claude Haiku 5.5). The adapters return `Usage` (input, output including thinking, cache read, cache write). Cost uses the per-model `PRICE_ANSWER_*` / `PRICE_SMALL_*` settings from `app/config.py`.
- **Prompt versions.** Prompts in `prompts/` start with a `version:` line. The report filename is `eval/reports/<date>-<prompt versions>.md` and records the versions. Under Ollama, the extra prompt `answer-citing-markers.md` is recorded as `citing`.
- **No repeatable sampling.** The API has no sampling settings, so the same run can give different answers next time.
- **Feedback data.** SQLite has one table, `feedback(conversation_id, answer, created_at)`.
  - `conversation_id` is a lower-case UUID v4. `answer` is `yes` or `no`. `created_at` is a UTC ISO 8601 time with milliseconds and `Z`.
  - `DATABASE_PATH` is resolved against the project root, and `data/` is git-ignored.
  - Only `POST /api/feedback` writes to the table. The stats script only reads it.
- **Conventions.** Run scripts with `uv run python scripts/...`. Dates are ISO 8601. Code, identifiers and docs are in English. The README is in Norwegian and is updated story by story.

## Cross-Story Dependencies

- **5.1 → 5.2.** 5.2 runs the test set from 5.1, so the field names in `testset.yaml` set the report's automatic checks. 5.2 reads the cases through `load_testset(path, knowledge_base)` in `scripts/testset.py`, which returns frozen `TestCase`s with the fields `id`, `question`, `en`, `category`, `outcome`, `facts`, `sources`, `tags`, `history` (`Exchange`s) and `personal_info` (`thai_id`, `passport`, `phone`), and raises `TestsetError`. `outcome` is the expected request-log outcome: `answered`, `no_answer` or `fixed_reply`. `sources` lists the snapshots that state the facts; citing any of them counts as a correct source.
- **Earlier epics.** 5.2 depends on the full pipeline from Epics 1–2 (filter, classifier categories, fixed replies, citations, cost logging). 5.3 depends on the feedback table from Story 2.3.
- **Phone numbers are kept.** The user decided on 2026-11-13 that the filter removes only Thai ID and passport numbers; phone numbers are kept, which narrows FR9 (the PRD and epics still say they are removed). The test set follows the decision: a phone-only case (`personal_info: [phone]`) expects the question unchanged, so `personal_info_removed` = false.
- **Known filter gaps.** Known filter misses and false positives are listed in `deferred-work.md` under "check against the evaluation test set before changing".
- **Ollama.** The script's refusal rule only names demo mode and a missing Anthropic key. The planning docs do not say whether the evaluation should also run with `LLM_PROVIDER=ollama`, which needs no key and costs 0.
