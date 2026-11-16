# Epic 4 Context: English translation and demo mode for the examiner

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

The course examiner does not read Thai and may not have an Anthropic API key. This epic lets them run the app locally without a key (demo mode), see a visible demo-mode label, try the example questions with stored Thai answers and sources, show any reply in English, and set everything up from the README alone, with their own key or in demo mode. It finishes the "easy to run" requirement. Demo mode (4.2) and the README (4.3) are core priority so the examiner can run the app early. The English translation (4.1) is lowest priority ("if time allows"). Stories 4.2 and 4.1 are built and in review. 4.3 is in the backlog.

## Stories

- Story 4.1: Show the English translation
- Story 4.2: Demo mode without an API key
- Story 4.3: README for running and following the app

## Requirements & Constraints

- **English translation.** Every finished reply (after `done`) gets a "Show English" button. The English appears under the Thai reply. The Thai text and its source links stay unchanged and visible. A failed translation shows the fixed `error` text.
- **Demo mode.** It runs with no API key. It answers the example questions with stored Thai answers and sources, streamed with the same events as a real answer. Any other question gets the fixed `reply-demo-only` message, never `reply-no-answer`. A "Demo mode" label (`demo-label`) is always visible. Typing a done phrase triggers the feedback question. "Show English" in demo mode never calls an API.
- **Easy to run.** Following the README on a machine with Python 3.12 and uv, you can start the app in demo mode and with your own key (via `.env.example`), and open it from a phone on the same Wi-Fi (`--host 0.0.0.0`). The README lists every `.env.example` setting with what it does, lists the example questions with English and Norwegian translations, explains `uv run pytest`, and explains how to read the cost log. Cost per question is reported in the README. A group member checks both modes on a clean machine and fixes any missing step.
- **Privacy.** Model-written text sent for translation goes through the personal-information filter first. Only token usage, never the text, is logged.
- **Adviser review.** Demo answers and any new fixed Thai texts are reviewed by the adviser before release.
- **Safe tests.** pytest never calls the real API. Tests for 4.1 cover both the stored-text path and the model path with the scripted fake.

## Technical Decisions

- **Endpoint:** `POST /api/translate` takes `{text}` and returns `{translation}`. Errors use the envelope `{"error": {"code", "message"}}`.
- **Translation order:** first filter the text for personal information. If the filtered text (after NFC, whitespace collapse and trimming) matches the Thai of a fixed text (`content/texts.yaml`) or an example question, return its stored `en` with no LLM call and no log line. Otherwise call `LLMClient.translate(text) -> (str, Usage)`. With Claude that uses `MODEL_SMALL` (Claude Haiku 5.5) with `EFFORT_SMALL` and the versioned prompt `prompts/translate-system.md`, which starts with a `version:` line. The request log records the prompt version and Usage. In demo mode `MockLLM.translate` returns the stored `en` of a demo answer, and the `en` of `reply-demo-only` for any other text.
- **Adapter boundary:** only `app/adapters/anthropic_llm.py` imports `anthropic`. Adapters return no SDK types. `stop_reason: "refusal"` is an error. The Ollama adapter (`LLM_PROVIDER=ollama`) has `translate` too (user decision, 2026-11-15): a non-streamed call on `OLLAMA_MODEL` with `think: false` and the same prompt, logged at no cost. `MOCK_LLM=true` takes priority over `LLM_PROVIDER`.
- **Demo mode wiring:** `MOCK_LLM=true` wires `mock_llm`, which is the only reader of `content/demo-answers.yaml`. That file is keyed by example-question `id`. Each entry has a category, a Thai answer, source IDs and an English translation. The file also has a `done_phrases` list. A question matches after Unicode NFC normalisation and trimming. A match returns the stored data. A done phrase returns `done`. Anything else returns `general` with zero citations, and the route step turns that into `reply-demo-only`. `GET /api/texts` returns `demo_mode: true`.
- **Startup checks in demo mode:** the app refuses to start if an example question has no demo answer or a demo answer refers to an unknown source id.
- **Config:** all settings come from `.env` through `app/config.py`. `.env.example` lists them all, including the per-model prices (`PRICE_ANSWER_*`, `PRICE_SMALL_*`) and the Ollama settings. User-facing text is in Thai with stored English. Code, identifiers and logs are in English.

## UX & Interaction Patterns

- The "Show English" button is available under every reply and appears only once the reply is finished. The translation is added below the reply and never replaces any shown text.
- The demo label is visible at all times. The page holds no hard-coded Thai, so every label comes from `GET /api/texts`.
- Mobile-first: works from 360 px wide with no horizontal scrolling down to 320 px, buttons at least 48 px, and it must work in Facebook's in-app browser.

## Cross-Story Dependencies

- 4.2 depends on the streamed answer (1.6), the categories from 2.1 and the feedback flow from 2.3 (for `done_phrases`). All of these are built.
- 4.1 uses the stored `en` from demo answers (4.2, through `MockLLM.translate`), fixed texts and example questions. Checklist English (carried from Epic 3) is settled: `GET /api/checklists/{purpose}` serves each item's stored `en`, and the checklist view's "Show English" shows it with no request.
- Open demo-mode gaps: every stored demo answer is `general`, so demo mode cannot show "the embassy decides", out-of-scope or reach-person replies. Adding demo examples for them needs new Thai text that the user approves.
- 4.3 documents the finished behaviour of every epic, including the Ollama option and the cost log. A README already exists (written in Norwegian) and is updated story by story, so 4.3 completes and verifies it instead of starting from scratch.
