# Implementation Plan: Norway Visa Guide For Thai

This plan builds on `product-brief.md` and the feedback in `tilbakemelding-product-brief.md`. It is a working plan; the BMAD documents (PRD, architecture, epics and stories) will replace the details here as they are written.

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Stack | Python, FastAPI, pytest, simple mobile-first HTML/JS chat page, SQLite for feedback | Few moving parts; ingesting HTML and PDF sources is straightforward in Python. |
| Language model | Claude Opus 5.5 (`claude-opus-5-5`, $4 / $20 per million input/output tokens), set via environment variable | Handles Thai well. The model can be changed in `.env` without code changes. |
| Retrieval | Whole knowledge base sent as document blocks with prompt caching and the Citations feature; no vector database | 10–20 documents fit easily in the context window. Citations return the exact quoted text from each source. Thai has no spaces between words, which makes keyword search hard; this avoids it. Revisit if the knowledge base grows a lot. |
| Referral | A small classification call before answering: general / individual assessment / out of scope / contains personal data | Makes "always refer individual cases" a separate, testable step. |
| Demo mode | `MOCK_LLM=true` returns stored answers for the example questions | The examiner can run the app without an API key, and automated tests never call the real API. |
| Examiner support | "Show English translation" button, example questions with English/Norwegian translations in the README | The examiner probably does not read Thai. |
| Extension | Document checklist by visit type (tourism / visiting family or friends), built from structured data | Fully testable without the language model; no login needed, unlike an admin page. |

## Planned repository structure

```
app/                 FastAPI app, chat logic, LLM client, mock client
app/static/          Chat page (HTML/CSS/JS)
prompts/             Versioned system and classifier prompts
knowledge-base/      sources.yaml + Markdown snapshots of each source
scripts/             ingest.py (fetch sources), run_eval.py (test set against real model)
eval/                testset.yaml + evaluation reports
tests/               pytest tests (mock LLM only)
docs/planning/       Brief, feedback, PRD, architecture, epics and stories
```

## Phases

### Phase 0: Revise the product brief
- Move planning documents to `docs/planning/`.
- Add knowledge base, testable success criteria, example conversation, alternatives, concrete v1 scope, technology and cost, and privacy.
- First draft of source list and test questions.

### Phase 1: BMAD planning
PRD → architecture → epics and stories, stored in `docs/planning/`.

### Phase 2: Implementation (epics in build order)
1. **Foundation:** project structure, config, `.env.example`, mock LLM client, GitHub Actions running pytest.
2. **Knowledge base:** `sources.yaml`, `scripts/ingest.py` to convert sources to Markdown once (not at runtime), loader.
3. **Core flow:** chat endpoint → classifier → cited answer → streamed Thai answer with clickable sources. Must be stable before the next epics.
4. **Limits and referral:** referral messages with contact details, "not in my sources" reply, privacy banner.
5. **Feedback:** "Did you receive all the information you needed?" yes/no stored in SQLite, simple stats script.
6. **Extension:** document checklist by visit type.
7. **Quality assurance:** 20–30 test questions in `eval/testset.yaml`; `scripts/run_eval.py` runs them against the real model and writes a report. Rerun after every prompt or source change.
8. **Design and README:** large touch targets, mobile layout, setup with own key and demo mode, example questions with translations.

## Timeline

No deadline is set yet. Work proceeds in the order above; the core flow (epics 1–3) comes first, so there is a working app to show as early as possible. Add dates when the submission deadline is known.

## Open tasks for the domain expert
- Select and verify the 10–20 source pages.
- Write the expected key facts and sources for each test question.
- Check that the Thai in prompts, UI text and answers reads naturally.
