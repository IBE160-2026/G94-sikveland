---
title: 'Adversarial review — Architecture Spine, Norway Visa Guide For Thai'
target: docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md
lens: adversarial (build two units that each obey every AD and still do not fit together)
context: PRD (prd-G94-sikveland-2026-10-19/prd.md + addendum.md), spine .memlog.md
date: '2026-11-02'
---

# Adversarial review — Architecture Spine

## Verdict

**Sound invariants, under-specified contracts. Tighten before writing epics.**

AD-1 to AD-13 get the hard decisions right: filter first, closed categories, stateless server, fixed texts from content files, citations, mock behind a port, two test layers. An attacker cannot easily break those *invariants*. What the spine leaves open is almost every **shape that crosses a story boundary**: the `/api/chat` request body, the LLM port's return type, the content keys, the `/api/texts` payload, the demo-answers lookup key, the translate request and response, who shows the feedback question, and how streaming fits with the zero-citation fallback. For a small course team, where the page, the web layer, the pipeline and the adapters are likely built by different people or in different sessions, each gap below will very probably lead to a mismatch. Each one is cheap to close now with one rule. Each one costs a rework story if it is found in integration.

Two findings are **internal contradictions** in the spine, not just gaps:

- **AD-7 vs AD-8.** You cannot stream an answer bit by bit and also replace it afterwards when it has zero citations (F1).
- **AD-2 vs the layering table.** Adapters are told to emit AD-8 events, but those events carry `category` and source `title`/`url`, which adapters do not own (F3).

There is also one **document conflict**: the addendum puts demo answers in `eval/demo-answers.yaml`, while the spine puts them in `content/demo-answers.yaml` (F6).

## How to read the findings

Each finding names two units one level down (epics or stories). Both units follow every AD to the letter, yet they cannot work together. The **proposed rule** is written so it can be pasted into the spine as a new AD, as a tightened AD, or as a row in Consistency Conventions. Findings are ranked by **how likely the divergence is in practice** for a 2–4 person course team building in parallel or in separate AI sessions.

| Rank | ID | Clash | Likelihood | Where the fix goes |
| --- | --- | --- | --- | --- |
| 1 | F1 | Streaming vs zero-citation replacement | Near-certain | Tighten AD-7 + AD-8 |
| 2 | F2 | `/api/chat` request body and history turn format | Near-certain | Tighten AD-3 + new convention |
| 3 | F3 | LLM port return types (real vs mock adapter) | Very high | New AD-14, reword AD-2 |
| 4 | F4 | Feedback question: two owners; `conversation_id` lifecycle | Very high | Tighten AD-5 + AD-10 |
| 5 | F5 | Content keys, category→text mapping, `/api/texts` payload | Very high | Tighten AD-6 + convention |
| 6 | F6 | Demo mode: lookup key, demo-only message, file location | High | New AD-15 (or tighten AD-2) |
| 7 | F7 | Translate request/response, which replies get the button | High | Convention + tighten AD-4 |
| 8 | F8 | Personal-info flag scope; reminder has two owners; raw PI in history | High | Tighten AD-4 |
| 9 | F9 | Source object shape; `title` missing from `sources.yaml`; checklist payload | Medium-high | Tighten AD-8, AD-9, AD-11 |
| 10 | F10 | Logging vs eval: line granularity, cost owner, prompt version format | Medium-high | Tighten AD-12, AD-13 + convention |
| 11 | F11 | Error semantics: terminal or not, message language, FastAPI 422 shape | Medium | Tighten Errors convention |
| 12 | F12 | Classifier input: with or without history | Medium | Tighten AD-5 |
| 13 | F13 | How a chat question leads to a checklist (UJ-1 step 3) | Medium | Tighten AD-11 |
| 14 | F14 | Startup cross-reference validation of IDs | Low-medium | Convention |

---

## F1 — Streaming vs zero-citation replacement (AD-7 × AD-8)

**Units:** *Story "cited answer streamed to the browser"* (pipeline/answer + web) vs *Story "no-answer fallback"* (pipeline/route + content).

- **Unit A** follows AD-8 and memlog ("answers stream bit by bit"). It forwards each model `text` delta as soon as it arrives.
- **Unit B** follows AD-7. When the finished answer has zero citations, it "replaces" it with the fixed no-answer reply, which AD-8 says is "one `text` event with the whole text".
- **Clash:** Whether the answer has zero citations is only known at the end of the model stream, and by then A has already sent the uncited text to the phone. B's "replacement" then reaches the page as a *second* `text` event, which the page appends. The applicant sees an invented answer followed by "we have no answer". This breaks FR2/FR4 in exactly the case AD-7 is meant to protect. A third developer might fix it by turning streaming off for all answers. That quietly drops the streaming decision.
- **Why likely:** Each story is correct when tested alone. The mock always returns cited answers, so CI never exercises the clash.

**Proposed rule (append to AD-7):**

> The answer step holds back model text until the first cited text block arrives, then sends everything held back plus all further text as `text` events. If the model response ends with zero citations, the held-back text is discarded and the fixed no-answer reply is sent as one `text` event. Once any model-written `text` event has been sent for a reply, that reply is never replaced, retracted or followed by a fixed reply. A test with a mock answer that has zero citations must assert that no model text reaches the stream.

**Proposed rule (append to AD-8):** "The page renders `text` events by appending only. There is no replace or retract event."

---

## F2 — `/api/chat` request body and history turn format (AD-3)

**Units:** *Story "chat page keeps conversation in sessionStorage"* (static) vs *Story "/api/chat endpoint + answer with follow-ups"* (web + pipeline), plus the **real vs mock adapter**.

- **Unit A (page)** sends `{"message": "...", "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`. It stores the user turn when the user taps Send. It skips fixed replies such as "embassy decides" in history because they are "not answers", and if the stream fails it keeps the user turn.
- **Unit B (web)** expects `{"question": "...", "history": [{"question": "...", "answer": "..."}]}`, which is equally consistent with AD-3 ("sends prior turns").
- **Clash 1:** The field names differ, so FastAPI returns 422 on the first integration run. This is obvious and gets fixed quickly, but one side has to be rewritten.
- **Clash 2 (subtle):** A's "user turn kept after error" and "fixed replies skipped" produce two **user turns in a row**. The real Messages API rejects non-alternating turns (400). The mock accepts anything. CI is green and the demo works, but the first real follow-up after an out-of-scope reply fails.
- **Clash 3:** Neither side says whether the feedback question, the Yes/No taps, the "What would you still like to know?" text or the personal-info reminder are turns. Each choice changes what the classifier and the answer model see.
- **Clash 4:** There is no cap on history size. Long conversations grow the request with no limit, and the server has no rule for rejecting it.

**Proposed rule (new convention row "Chat request" + append to AD-3):**

> `POST /api/chat` body is `{"question": str, "history": [{"question": str, "answer": str}]}`, oldest exchange first. The page stores an exchange only after its `done` event, never after `error`. `answer` is exactly the text the page showed for that reply: the concatenated `text` deltas, including fixed replies and the feedback question. Source lists, the personal-information reminder, Yes/No taps and the feedback follow-up text are not part of history. The page sends at most the last 10 exchanges. The server rejects more than 20 exchanges, or any field over 2,000 characters, with error code `request_too_large`. Only the pipeline turns exchanges into model messages, and it always produces strictly alternating user/assistant turns.

---

## F3 — LLM port return types: real vs mock adapter (AD-2, AD-8, layering)

**Units:** *Story "Anthropic adapter with citations and caching"* (adapters/anthropic_llm) vs *Story "mock LLM adapter"* (adapters/mock_llm), and the *pipeline answer step* that consumes both.

- AD-2 says "The mock produces the same stream events (AD-8) as the real adapter". But AD-8 events are `meta{category, personal_info_removed}`, `sources{id,title,url}`, `done`. An adapter knows neither the category (pipeline) nor source titles and URLs (KnowledgeBase). Taken literally, the rule forces adapters to reach across layers. Ignoring it leaves the port's real shape undefined.
- **Unit A (real)** passes through SDK-shaped data: text blocks with `citations[].document_index` (an index into the documents array), plus `usage` on the final message.
- **Unit B (mock)** yields AD-8-shaped dicts, `{"type": "text", "delta": ...}` and then `{"type": "sources", "sources": [{"id": ...}]}`, because AD-2 told it to.
- **Clash:** The pipeline answer step is written against whichever adapter its author saw first. Tests pass with the mock and the real run fails, or the reverse. Citation identity is a separate trap: the real adapter yields `document_index`, the mock yields source `id`, and the zero-citation check (AD-7) or the sources list (AD-8) is computed differently per adapter. Cost logging (NFR6) also needs token usage, and the mock has no reason to provide it.

**Proposed rule (new AD-14 "LLM port contract"; reword AD-2 to "the mock implements the same port types"):**

> `app/ports/llm.py` defines the only types that cross the LLM port. Adapters return these types and no SDK objects.
> - `classify(question: str, history: list[Exchange]) -> (Category, Usage)`. The adapter validates the result against the AD-5 set.
> - `answer(question: str, history: list[Exchange], documents: list[SourceDoc]) -> Iterator[AnswerChunk | Usage]`, where `AnswerChunk = {text: str, source_ids: list[str]}` (`source_ids` empty for uncited text), and exactly one `Usage` comes last.
> - `translate(text: str) -> (str, Usage)`.
> - `Usage = {step, model, prompt_version, input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens}`. The mock reports zeros.
>
> The adapter maps citation document positions to source `id`s. Building AD-8 events is done only in `app/web`, from pipeline output.

---

## F4 — Feedback question: two owners, `conversation_id` lifecycle (AD-5, AD-6, AD-10)

**Units:** *Story "done signal → feedback question"* (pipeline/classify + route) vs *Story "feedback buttons + POST /api/feedback"* (static + web).

- **Unit A (server)** reads AD-6 ("the feedback question … comes from content files") and AD-8 ("a fixed reply is one `text` event"). On category `done` it sends the feedback question as the reply text.
- **Unit B (page)** reads AD-5 ("`done` triggers the feedback question") and AD-6 ("the page gets its fixed UI texts from `/api/texts`"). On `meta.category == "done"` it renders the feedback question with Yes/No buttons from `/api/texts`.
- **Clash:** The question is shown twice. Or, if A sends nothing for `done`, the stream has no `text` and F2's history gets an empty answer. "What would you still like to know?" has the same problem: the server might send it after a "No" posted to `/api/chat` (the stateless server cannot know it follows a "No"), or the page might show it locally.
- **Second clash, `conversation_id`:** AD-10 says the page "creates" it but not when. If it is created once per page load, a reload mid-conversation produces a new ID, and SM-1 ("first answer per `conversation_id`") counts the same conversation twice. If it is never renewed after "Yes", the next conversation in the same tab is merged with the previous one. The `answer` value is also untyped: page sends `true`, server stores `'yes'`, `feedback_stats.py` counts `'Yes'`. `created_at` could come from the client or the server.

**Proposed rule (append to AD-5 and AD-10):**

> On category `done` the server sends the feedback question (content key `feedback-question`) as the fixed reply, followed by `sources: []` and `done`. When the page sees `meta.category == "done"`, it adds Yes/No buttons under that reply. It never renders the question itself. Yes/No taps never go to `/api/chat`. A tap sends `POST /api/feedback {"conversation_id": "<uuid4>", "answer": "yes" | "no"}`. The server sets `created_at` (UTC ISO 8601), stores `answer` as the lowercase string, and returns 204. After "no" the page shows `feedback-follow-up` from `/api/texts` locally; it is not a history exchange. After "yes" the page shows `conversation-end` and deletes history and `conversation_id` from sessionStorage. The page creates `conversation_id` when it sends the first question of a conversation and keeps it in sessionStorage next to history, so a reload keeps it. The buttons of a feedback question accept one tap.

---

## F5 — Content keys, category→text mapping, `/api/texts` payload (AD-6, IDs convention)

**Units:** *Story "content files written and reviewed by adviser"* (content/) vs *Story "route step sends fixed replies"* (pipeline/route) vs *Story "page loads UI texts"* (static + `/api/texts`).

- **Unit A (content)** writes one Markdown file per text, `content/embassy-decides.md`, `content/no-answer.md`, … and lists example questions in `content/examples.yaml`. Keys are kebab-case, as the IDs convention requires.
- **Unit B (route)** looks up `content.get(category)` with category `individual_assessment`. AD-5 values are snake_case, so this lookup fails, and there is no content key for `general`'s no-answer case at all.
- **Unit C (page)** expects `GET /api/texts` to return `{"privacyNotice": ..., "examples": [...]}`. Unit D (web) returns the flat map of all content, fixed replies included.
- **Other gaps:** Nothing says who fills `{ADVISER_CONTACT}` in `/api/texts` (ContentStore at load time, or each consumer). Nothing says how the page learns it is in demo mode so it can show the FR10 label: no endpoint carries `MOCK_LLM`, and the endpoint list is closed. Checklist purpose labels (Thai) have no home.

**Proposed rule (append to AD-6; new convention row "Content keys"):**

> All fixed Thai texts except checklists and demo answers live in `content/texts.yaml`: a flat map of kebab-case key → Thai string, plus `example-questions` as a list of `{id, text}`. The key set is closed and listed in the spine: `reply-individual-assessment`, `reply-out-of-scope`, `reply-reach-person`, `reply-no-answer`, `reply-demo-only`, `feedback-question`, `feedback-yes`, `feedback-no`, `feedback-follow-up`, `conversation-end`, `personal-info-reminder`, `privacy-notice`, `demo-label`, `translate-button`, `checklist-button`, `checklist-purpose-tourism`, `checklist-purpose-family`, `checklist-purpose-friends`, `error-generic`, `error-request-too-large`. Adding a key means changing this list.
>
> The route step maps categories through one fixed table:
>
> | Category | Content key |
> | --- | --- |
> | `individual_assessment` | `reply-individual-assessment` |
> | `out_of_scope` | `reply-out-of-scope` |
> | `reach_person` | `reply-reach-person` |
> | `done` | `feedback-question` |
> | `general` with zero citations | `reply-no-answer` |
>
> Categories stay snake_case and content keys stay kebab-case; this table is the only bridge between them.
>
> `ContentStore` fills `{ADVISER_CONTACT}` when it loads. Startup fails if a listed key is missing or a `{…}` placeholder remains.
>
> `GET /api/texts` returns `{"demo_mode": bool, "texts": {key: str}, "example_questions": [{"id", "text"}]}`. The `reply-*` and `feedback-question` texts are included only so the page can render offline states. The page never chooses a reply itself.

---

## F6 — Demo mode: lookup key, demo-only message, file location (AD-2, FR10)

**Units:** *Story "mock adapter with stored demo answers"* (adapters/mock_llm) vs *Story "example questions on the page"* (content + static), plus *pytest fixtures*.

- **Unit A (mock)** keys `content/demo-answers.yaml` by the **Thai question text**, copied from the example list.
- **Unit B (content)** lets the adviser rephrase an example question during NFR8 review. Only `texts.yaml` is edited, and the copied text in demo-answers no longer matches. A tap on that example in demo mode gets "demo mode only answers example questions". A trailing space, a zero-width character, or a different Unicode form of a Thai vowel or tone mark (NFC vs NFD) breaks the match in the same way.
- **Demo-only message has no owner.** It is a fixed Thai text (AD-6, content), but only the mock knows a question is unmatched. The mock cannot return a category outside AD-5, and adapters have no ContentStore. One developer makes the mock return zero citations, so the applicant gets `reply-no-answer` and not the FR10 message. Another hard-codes Thai in the mock, which breaks AD-6 and NFR8.
- **Mock classifier undefined.** If the mock classifies everything as `general`, "ขอบคุณ" in demo mode never triggers `done`, so the examiner cannot see FR5.
- **Two readers of one file.** `ContentStore` ("content files in `content/`") and `mock_llm` might both parse `demo-answers.yaml` with different schemas. Tests need their own scripted categories (for example `individual_assessment`), with no defined way to inject them.
- **Location conflict:** the addendum says `eval/demo-answers.yaml`, the spine says `content/demo-answers.yaml`.

**Proposed rule (new AD-15 "Demo fixtures"):**

> `content/demo-answers.yaml` is the only demo fixture file; the addendum's `eval/` path is superseded. Only `mock_llm` reads it. It has two parts:
> - `answers`: a map from example-question `id` (from `content/texts.yaml`) to `{answer: Thai, source_ids: [...], translation: English}`. It never repeats question text.
> - `done_phrases`: a list of Thai and English phrases the mock classifies as `done`.
>
> `mock_llm` matches the incoming cleaned question to an example `id` by exact equality after Unicode NFC normalisation and trimming of whitespace.
> - A match classifies as `general` and answers with one `AnswerChunk` that cites all its `source_ids`.
> - A `done_phrases` match classifies as `done`.
> - Anything else classifies as `general` and answers with zero citations.
>
> When `MOCK_LLM=true`, the route step sends `reply-demo-only` in place of `reply-no-answer`. The web layer passes `demo_mode` from config into the pipeline. `MockLLM` is built from a fixtures object; demo mode loads this file, and tests pass their own fixtures.

---

## F7 — Translate request/response and which replies get the button (FR7, AD-4)

**Units:** *Story "translate button"* (static) vs *Story "/api/translate"* (web + pipeline/translate) vs *mock translate*.

- **Unit A (page)** posts `{"answer": "<Thai>", "sources": [...]}` and expects a stream, because chat streams.
- **Unit B (web)** expects `{"text": ...}` and returns `{"translation": ...}` as JSON, because the Errors convention implies translate is non-streaming.
- **Which replies?** The page shows the button under every reply, fixed ones included. In demo mode the mock has stored translations only for demo answers, so tapping it under "embassy decides" fails, or hard-coded English is added to the mock.
- **Mock lookup:** If the mock looks up the stored translation by Thai answer text, it must match the text the page built from deltas (same normalisation issue as F6).

**Proposed rule (new convention row "Translate"):**

> `POST /api/translate` body is `{"text": str}` (at most 4,000 characters); the response is `200 {"text": str}` (English) as plain JSON, not streamed. Errors follow the Errors convention. The page shows the translate button only under replies whose `sources` event was non-empty, which means a cited model answer. The translation is held in page memory only and is not part of history. `mock_llm.translate` returns the stored `translation` of the demo answer whose `answer` equals the input after NFC normalisation and trimming, and otherwise the fixed English string "Translation not available in demo mode."

---

## F8 — Personal-info flag scope, reminder has two owners, raw PI kept in history (AD-3, AD-4)

**Units:** *Story "personal-information filter"* (pipeline/filter) vs *Story "privacy reminder on the page"* (static), and the addendum vs AD-4.

- AD-4: "If anything was removed, the stream's `meta` event carries `personal_info_removed: true`." The filter also runs on **every history turn**. The page stores what the user typed (AD-3 gives it no cleaned text), so a passport number typed in turn 1 is re-sent and removed on every later request. `personal_info_removed` is then `true` on every reply for the rest of the conversation, and the reminder repeats under each answer.
- The raw passport number also stays in sessionStorage and crosses the network with every request. This is within AD-3's wording but against the spirit of FR9 ("deleted").
- **Two owners of the reminder:** The addendum says "a reminder … is added to the answer", meaning the server appends it to the text. AD-4 says "the page shows the fixed reminder". A server developer who reads the addendum adds it to the `text` stream, the page adds it again, and the reminder text then also ends up in the history `answer` (F2).

**Proposed rule (replace the last sentence of AD-4):**

> `meta.personal_info_removed` is `true` only when something was removed from the new question. History turns are filtered silently. `meta` also carries `question`: the cleaned question. The page stores that text, not what was typed, in history. Only the page shows the reminder (`personal-info-reminder` from `/api/texts`), outside the reply text. The server never adds it to `text` events. This rule replaces the addendum's "added to the answer".

---

## F9 — Source object shape; `title` missing from `sources.yaml`; checklist payload (AD-8, AD-9, AD-11)

**Units:** *Story "ingest + sources.yaml"* (scripts/knowledge-base) vs *Story "sources under an answer"* (web + static) vs *Story "checklist endpoint + page"*.

- AD-9 lists the `sources.yaml` fields as `id`, `url`, `publisher`, `retrieved`, snapshot. AD-8 requires `{id, title, url}`. The ingest developer, following AD-9, writes no `title`. The web developer then fills `title` from the Markdown's first heading, from `publisher`, or from the model's `document_title`, and the result differs between real and mock.
- FR11 ("every answer can be traced to a specific version of a source") needs `retrieved` on the page or in the eval report, but it is not in the AD-8 object.
- AD-11 gives checklist items a source `id`, but the page has no way to resolve an id to a link (the endpoint list has no source lookup). One developer embeds the URL in `checklists.yaml`, which creates a second owner of source URLs that goes stale when `sources.yaml` changes. Another sends only the id, and the page shows nothing.
- No response shape is given for `GET /api/checklists/{purpose}`, and no error for an unknown purpose.

**Proposed rule (tighten AD-9, AD-8, AD-11):**

> - **AD-9:** `sources.yaml` entries have `id`, `title` (shown to the applicant), `url`, `publisher`, `retrieved` and `snapshot`. `sources.yaml` is the only place a source's URL or title is written.
> - **AD-8:** a source sent to the page is always `{id, title, url, retrieved}`, resolved on the server by `KnowledgeBase`. The page never resolves IDs. In the `sources` event, sources are listed in order of first citation, without duplicates.
> - **AD-11:** `GET /api/checklists/{purpose}` returns `{"purpose", "title", "items": [{"id", "text", "source": {id, title, url, retrieved}}]}`. An unknown purpose returns 404 with error code `unknown_purpose`.

---

## F10 — Logging vs eval: log line granularity, cost owner, prompt version format (AD-12, AD-13, Logging convention)

**Units:** *Story "cost and request logging"* (web/adapters) vs *Story "run_eval.py + reports"* (scripts/eval) vs *Story "versioned prompt files"* (prompts/).

- **Granularity:** The convention says "one JSON line per request". `/api/chat` makes two model calls (classify + answer). The adapter developer logs per call; the web developer logs per request. This produces two formats in one stream, and `cost per question` (NFR6) is computed differently by each.
- **Cost has two owners:** the logger computes cost from a price table, and `run_eval.py` computes its own (it needs cost per run for the report). The price tables drift. The meaning of "cache tokens" is also open: cache *writes* and cache *reads* are priced very differently, and "input/output/cache tokens" does not say which.
- **Prompt version format:** "a version number in each file" could be a filename `answer.v3.md` or a front-matter `version: 3`. The loader developer and the prompt editor pick differently, and the eval report records `None`.
- **Eval entry point:** `run_eval.py` either calls `/api/chat` over HTTP and parses NDJSON, or calls the pipeline in-process. Neither is specified, and both need the stream or pipeline shape to be fixed (F1–F3).
- **`eval/testset.yaml` schema** is not defined, yet NFR4 needs expected category, facts and source per item.
- **AD-3 vs AD-13:** AD-3 says the server "never writes question or answer text to disk". Eval reports must contain answers so the adviser can judge them. A careful developer leaves answers out of reports, and NFR4 cannot be judged.

**Proposed rule (tighten AD-12, AD-13, Logging):**

> - **AD-12:** each prompt file begins with front matter `version: <integer>`. Filenames carry no version. The prompt loader returns `(text, version)`.
> - **Logging:** `app/web` writes exactly one JSON line to stdout per `/api/chat` or `/api/translate` request: `{ts, endpoint, category, calls: [Usage + cost_usd], cost_usd}`. `Usage` is the F3 type with the Anthropic usage field names. Adapters never log. Cost is computed only by `app/cost.py`, which holds the price table.
> - **AD-13:** `scripts/run_eval.py` calls the pipeline in-process with the real adapter and uses `app/cost.py`. `eval/testset.yaml` items are `{id, question, expected_category, expected_facts: [str], expected_source_ids: [str]}`. Each report records model, prompt versions, each cited source's `retrieved` date, and per item the category, cited source ids, answer text and cost. Answer text in eval reports is allowed: test-set questions are not applicant data, and AD-3 applies to the running server only.

---

## F11 — Error semantics (AD-8, Errors convention)

**Units:** *Story "stream reader on the page"* vs *Story "web error handling"*.

- "`error` at any point": the page cannot tell whether `done` still follows, or whether the partial text already shown stays. One side ends the stream after `error`; the other waits for `done` and hangs the spinner.
- `{"error": {"code", "message"}}`: `code` values are not listed, and `message` could be Thai (user-facing) or English (log). The page shows `message` directly, and the server developer writes English there.
- FastAPI's built-in validation failure is 422 `{"detail": [...]}`, which breaks the convention unless someone installs a handler. A malformed chat body then returns that before any stream starts, and the page's NDJSON reader crashes on it.

**Proposed rule (replace the Errors convention row):**

> Error `code` is one of `bad_request`, `request_too_large`, `unknown_purpose`, `llm_unavailable`, `internal`. `message` is English and only for developers. The page always shows a Thai text from `/api/texts` chosen by code (`error-request-too-large`, otherwise `error-generic`). Request validation errors return HTTP 400 with the error object, not a stream; `app/web` installs a handler that replaces FastAPI's 422 `detail` shape. Inside a stream, `error` is the last event: nothing follows it. The page drops the partial reply and stores no exchange.

---

## F12 — Classifier input: with or without history (AD-5)

**Units:** *Story "classifier"* vs *Story "follow-up questions"* (FR1).

- The classifier developer sends only the new question; AD-5 does not mention history. The follow-up developer tests "แล้วถ้าไปเยี่ยมป้าล่ะ?" ("and if I visit my aunt?") after a general answer. Without context the classifier may label it `out_of_scope` or `individual_assessment`, and the follow-up gets a fixed reply. In the other direction, "โอเค แล้วค่าธรรมเนียมเท่าไหร่" ("okay, and how much is the fee?") has a done-like opening and a real question.

**Proposed rule (append to AD-5):**

> The classifier receives the cleaned question plus the same history as the answer step. A message that contains a question is never `done`, even if it also contains thanks or "okay".

---

## F13 — How a chat question leads to the checklist (UJ-1 step 3, AD-5, AD-11)

**Units:** *Story "checklist page section"* vs *Story "answer prompt"*.

- UJ-1: "She asks which documents she needs and gets a document checklist." The categories are closed (AD-5) and none means "checklist". The answer step is model text from the knowledge base. One developer builds the checklist as a separate page control. Another expects the chat to open it, and either adds a `checklist` category (breaking AD-5) or lets the model write a document list (breaking AD-11's "not generated by the model").

**Proposed rule (append to AD-11):**

> Checklists are reached only through a page control that is always visible (`checklist-button`, then a purpose picker). The chat never returns a checklist. The answer prompt tells the model to point the applicant to that control by its Thai label when asked about documents, and still answers from the knowledge base with citations.

---

## F14 — Startup cross-reference validation

**Units:** *content/checklists.yaml*, *demo-answers.yaml*, *testset.yaml* vs *knowledge-base/sources.yaml*.

- Three files refer to source IDs owned by a fourth. A source renamed during re-ingest breaks checklist links and demo citations silently. The mock does not care, and the page shows a missing link.

**Proposed rule (new convention row "Reference checks"):**

> At startup, and in one pytest test, every source `id` in `checklists.yaml`, `demo-answers.yaml` and `eval/testset.yaml`, and every example-question `id` in `demo-answers.yaml`, must exist. Otherwise startup fails and names the missing ID.

---

## Pairs tried that held

These attacks did **not** produce a mismatch, because the spine already closes them:

- **Two writers to the database.** AD-10 names the single table and the single writer.
- **Checklist ticks server-side vs client-side.** AD-11 fixes the `localStorage` key and value shape.
- **Classifier and answer combined in one call.** AD-7's ban on combining citations with structured output, together with AD-1, prevents it.
- **Knowledge base fetched at runtime by one story and offline by another.** AD-9 is explicit.
- **Tests hitting the real API.** AD-2 + AD-13 + the environment table close it, but the mock's *shape* is still open (F3).

## Suggested order of fixes

F1, F2, F3 and F4 are the contracts every Epic 3 ("core flow") story needs. Add them before stories are written. F5 and F6 are needed before the content and demo stories. F7–F14 can go into the same edit, as they are single sentences or table rows.
