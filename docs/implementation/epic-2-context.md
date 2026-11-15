# Epic 2 Context: Clear limits, a person to contact, and feedback at the end

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

The chatbot stops guessing. A classifier step sorts each cleaned question before any answer call: questions about the applicant's own chances get a fixed "the embassy decides" reply, questions outside short-stay tourist/visitor visas to Norway and requests for a person get fixed replies with the adviser contact, and done signals ("thank you", "okay", Thai variants) trigger the feedback question. The Yes/No answer is the only data the server ever stores, and it feeds the adviser's main success measure (share of conversations whose first feedback answer is "Yes", target at least 80%). Story 2.1 is part of the core build priority; 2.3 and 2.2 come after the checklist epic.

## Stories

- Story 2.1: "The embassy decides" for questions about the applicant's own chances
- Story 2.2: Other visa types and requests for a person
- Story 2.3: Feedback question at the end of the conversation

## Requirements & Constraints

- **Never estimate chances.** Individual-assessment questions ("Will I get the visa?", "I was refused last year, will I get it this time?") always get the embassy-decides reply; no answer call is made. Target: 100% on the test set.
- **Out of scope.** Anything other than short-stay tourist and visitor visas to Norway (e.g. work visa) gets a reply saying the chatbot covers only those visas, plus the adviser contact.
- **Reach a person.** Asking for a person, or for help with the whole process, gets the adviser contact. The test set will hold at least three phrasings; all must succeed.
- **Follow-ups stay general.** "and how much is the fee?" after a general question must classify as `general`.
- **Fixed replies need no source link** and make no claims about requirements, fees or deadlines.
- **Feedback loop.** Done signal → feedback question ("Have you received all the information you need?") with Yes/No buttons. "No" → "What would you still like to know?", conversation continues, question asked again at the next done signal. "Yes" ends the conversation. A done signal alone never ends it.
- **Privacy.** Server stores only `conversation_id`, Yes/No answer and its time; never question or answer text.
- **Adviser review.** Every new Thai text (`reply-embassy-decides`, `reply-out-of-scope`, `reply-reach-person`, `feedback-question`, `feedback-follow-up`) is reviewed by the adviser before release and noted in the PR.
- **Safe tests.** All categories are tested with the scripted fake; CI never calls the real API.

## Technical Decisions

- **Pipeline order is fixed:** filter personal info → classify → route → answer or fixed reply. Classify runs after the filter and before any answer call; only `general` reaches the answer step. The eval script uses the same pipeline entry.
- **Classifier:** `LLMClient.classify(question, recent_history) -> (Category, Usage)`; sees the cleaned question plus the last 2 exchanges. Anthropic adapter calls `MODEL_SMALL` (Claude Haiku 5.5) with `EFFORT_SMALL`, using structured output (`output_config.format`), never forced tool use. Returns no SDK types; refusal is an error.
- **Closed category set:** `general`, `individual_assessment`, `out_of_scope`, `reach_person`, `done`. Grown per story (2.1: first two; 2.2: + `out_of_scope`, `reach_person`; 2.3: + `done`). Adding any other category means changing the architecture.
- **Classifier prompt:** `prompts/classifier-system.md` with a `version:` line; bump the version each time categories are added. Request log and eval reports record prompt versions.
- **Category → text key:** `individual_assessment` → `reply-embassy-decides`, `out_of_scope` → `reply-out-of-scope`, `reach_person` → `reply-reach-person`, `done` → `feedback-question`; plus `feedback-follow-up` shown locally by the page after "No". All live in `content/texts.yaml` (closed key list, `th` + `en`); `{ADVISER_CONTACT}` filled from config at load. Startup fails if a key is missing. No Thai hard-coded in the page.
- **Stream shape for fixed replies:** `meta` (with the real `category`) → one `text` event with the whole text → `sources` with empty list (`checklist: false`) → `done`.
- **Request log:** classifier `Usage` is added to the per-request JSON log line and priced with `PRICE_SMALL_*`; the log carries the category, never text.
- **Feedback endpoint:** `POST /api/feedback {conversation_id, answer: "yes" | "no"}` → 204; server sets `created_at` (UTC ISO 8601). Invalid body → 422 with `{"error": {"code", "message"}}`. SQLite table `feedback(conversation_id, answer, created_at)` is the only server-side data and is written only by this endpoint, via the `FeedbackStore` port and a SQLite adapter. Create `data/` and the table if missing; resolve `DATABASE_PATH` against the project root, not the working directory.
- **`conversation_id`:** UUID v4 created by the page at the first question, kept in `sessionStorage`, sent only with feedback. SM-1 counts the first answer per `conversation_id`.
- **Demo mode:** the mock adapter already implements `classify` (example question → stored category, `done_phrases` match → `done`, otherwise `general`). Done-phrase matching should ignore surrounding punctuation and emoji (`Thanks!`, `ok.`, `ขอบคุณค่ะ 🙏`), in the mock and in the real classifier's tests; test a stored demo category other than `general`.
- **Ollama provider:** `OllamaLLM.classify` exists since Story 2.1: a short non-streaming `/api/chat` call with the same model and `num_ctx`, `format` set to the category JSON schema, thinking off, cost 0. Later stories extend its categories the same way as the Claude classifier's (`CLASSIFIER_CATEGORIES` in `app/adapters/classifier_request.py`).

## UX & Interaction Patterns

- Fixed replies render like any reply, without source links.
- After a `feedback-question` reply, the page shows Yes and No buttons under it (touch targets at least 44×44 px, works from 360 px width).
- "No" → page shows `feedback-follow-up` locally; input stays open.
- "Yes" → conversation ends: page clears history and `conversation_id`; the next question starts a new conversation.
- **Open decision for Story 2.3:** the page now saves past chats in `localStorage` (latest 20) with a local list `id` that is *not* the feedback `conversation_id`. Story 2.3 must decide whether "Yes" deletes, closes or keeps the saved chat, and what happens to `conversation_id` on "new chat" or when an older chat is reopened.

## Cross-Story Dependencies

- 2.1 introduces the classify step, prompt file, routing and fixed-reply path; 2.2 and 2.3 extend the same classifier and route table.
- 2.3 depends on 2.2's classifier and on the page's saved-chats storage (open conversation id in `sessionStorage`, chats in `localStorage`).
- Builds on Epic 1: filter, stream contract, `meta.clean_question`, history handling and the request log (Story 1.8).
- Demo mode (Story 4.2) relies on 2.1's categories; its `done_phrases` take effect once 2.3 is built.
- Epic 5 uses this epic's output: the test set checks embassy-decides, out-of-scope and reach-person replies, and the feedback statistics script reads the `feedback` table (first answer per `conversation_id`).
