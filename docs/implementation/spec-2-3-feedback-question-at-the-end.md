---
title: 'Story 2.3: Feedback question at the end of the conversation'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '002c54aba86183da1b9d4f7b0660a8062cf29b7f'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The adviser cannot tell whether the chatbot helps (SM-1): nothing asks the applicant at the end, and "thank you" is answered like a visa question (FR5).

**Approach:** The classifier gains `done` (AD-5). A done signal gets the fixed `feedback-question` text with Yes/No buttons under it. A tap sends `POST /api/feedback {conversation_id, answer}`; the server stores only `(conversation_id, answer, created_at)` in SQLite (AD-10). "No" shows `feedback-follow-up` and the chat goes on; "Yes" ends the conversation.

**Decisions (from the PRD and earlier specs):**
- A conversation is one visit (PRD glossary): the page creates a UUID v4 `conversation_id` at the first question of a chat and keeps it in `sessionStorage`; "new chat", reopening a saved chat, or ending with "Yes" drops it, so the next question starts a new one. It is sent only with feedback, never stored in the saved chats.
- Done-phrase matching (demo mock and classifier tests) ignores surrounding punctuation and emoji (`Thanks!`, `ok.`, `ขอบคุณค่ะ 🙏`) (deferred from Story 4.2). `DATABASE_PATH` is resolved against the project root (deferred from Story 1.1). Demo mode stores feedback too.

**Decision (user, 2026-11-15):** "Yes" keeps the chat: it stays on screen and in the saved chats, a fixed `feedback-thanks` line appears under the buttons, the `conversation_id` is dropped, and the next question starts a new chat (empty screen, new saved chat) automatically.

## Boundaries & Constraints

**Always:** classifier prompt version 3 with `done` (thank you, okay and Thai variants; a done signal that also asks something is that other category); `done` routes through the existing fixed-reply path (outcome `fixed_reply`); both real classifiers and the mock; `feedback` table with exactly `conversation_id TEXT, answer TEXT CHECK (answer IN ('yes','no')), created_at TEXT` (UTC ISO 8601 `Z`, set by the server), created with `data/` if missing, written only by `/api/feedback` through a `FeedbackStore` port and a SQLite adapter (AD-2 layering); 204 on success; invalid body → 422 envelope `{"error": {"code", "message"}}` (the app-wide handler); a storage failure → 500 envelope, never the body echoed; new text keys `feedback-question`, `feedback-follow-up`, `feedback-thanks`, `feedback-yes`, `feedback-no` (th + en, Thai drafted for the user's review, NFR8); buttons ≥ 48 px, 320 px without sideways scroll; no Thai in `app/static/`; page JavaScript logic that can be pure goes in `history.js` (tested in Node).

**Never:** no question or answer text in the database or in `/api/feedback`; no other server-side storage; no change to the stream contract beyond the existing fixed-reply events; no new dependency (`sqlite3` from the standard library).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Done signal | "ขอบคุณค่ะ" → `done` | `feedback-question`, `sources: []`; page shows Yes/No under it | N/A |
| Done + question | "thanks, and the fee?" | not `done` (classified by the question) | N/A |
| Yes | tap Yes | `POST {conversation_id, "yes"}` → 204; `feedback-thanks` shown; chat stays on screen and saved; id dropped | network/5xx → buttons back, fixed error text |
| After Yes | next question typed or tapped | `feedback-thanks` shown under the buttons; the next question opens an empty new chat (new saved chat, new id) and is asked there | N/A |
| No | tap No | stored; `feedback-follow-up` shown below; chat goes on; next done signal asks again with buttons | same |
| Twice | tap after an answer | buttons disabled after the first tap; one row per tap | N/A |
| First question | no `conversation_id` | page creates UUID v4 in `sessionStorage` | storage blocked → id kept in memory |
| New chat / reopen | tap new chat or a saved chat | `conversation_id` dropped; next question makes a new one | N/A |
| Reload | buttons shown, not answered | stored reply shows the question text without buttons; asking "thanks" again shows them | N/A |
| Bad body | missing field, `answer: "maybe"`, id not a UUID, extra field | 422 envelope, nothing stored | N/A |
| No data dir | `data/` missing | created with the table on first write | N/A |
| Demo | done phrase with punctuation/emoji | `done` → feedback question; feedback stored | N/A |

</frozen-after-approval>

## Code Map

- `app/adapters/classifier_request.py` `CLASSIFIER_CATEGORIES` + `app/web/chat.py` `FIXED_REPLY_KEYS` -- add `done` → `feedback-question`; the rule-agreement test in `tests/test_classifier_request.py` then covers it. Remove the "not built yet" tests for `done` (`tests/test_answer_pipeline.py`, `tests/test_chat_api.py`).
- `prompts/classifier-system.md` -- v2 has "Greetings, thanks and questions about how to use this chat are general" (until 2.3): thanks/okay become `done`; greetings and how-to-use stay `general`.
- `app/adapters/mock_llm.py` `normalise` / `classify` -- done-phrase matching ignoring surrounding punctuation and emoji; `content/demo-answers.yaml` `done_phrases` (+ `ok`, `okay`, `thank you`, Thai variants already there).
- New `app/ports/feedback.py` (`FeedbackStore.add(conversation_id, answer, created_at)`), `app/adapters/sqlite_feedback.py`, `app/web/feedback.py` (route), wiring in `app/main.py` (`DATABASE_PATH` via the existing `_from_root`, like `REQUEST_LOG_PATH`); `tests/test_layering.py` rules for the new modules.
- `app/static/history.js` (pure: conversation id lifecycle, feedback state), `app/static/app.js` (buttons under a `done` reply — `meta.category` is already in the stream; POST; follow-up text; end on Yes), `style.css`; `tests/test_history_js.py`, `tests/test_static.py`.
- `content/texts.yaml`, `app/ports/content.py` -- five keys.
- Docs: `ARCHITECTURE-SPINE.md` AD-10 (where `conversation_id` lives with saved chats), epics Story 2.3 note, README (feedback, `data/feedback.sqlite3`, how to count SM-1), manual test plan (new case), `deferred-work.md` entries for the two items done here are left as history.

## Tasks & Acceptance

**Execution:**
- [x] Classifier: `classifier_request.py`, `chat.py`, `prompts/classifier-system.md` v3, `mock_llm.py`, `demo-answers.yaml` -- `done` everywhere -- AD-5
- [x] Feedback store and endpoint: `ports/feedback.py`, `adapters/sqlite_feedback.py`, `web/feedback.py`, `main.py` -- AD-10
- [x] Page: `history.js`, `app.js`, `index.html`, `style.css` -- buttons, id, Yes/No flow -- FR5
- [x] Texts: `content/texts.yaml`, `app/ports/content.py` -- five keys -- AD-6, NFR8
- [x] Tests for every matrix row (pytest; Node for `history.js`), layering, 422/500 envelopes, table columns -- AD-13
- [x] Docs listed in the Code Map

**Acceptance Criteria:**
- Given a stored feedback row, when the table is read, then it has only `conversation_id`, `answer` and `created_at` (NFR5).
- Given `DATABASE_PATH` relative and the app started from another folder, when feedback is posted, then the file is under the project root.

## Implementation Notes

- Classifier: `done` is added to `CLASSIFIER_CATEGORIES` (both real classifiers' JSON schema grow) and to `FIXED_REPLY_KEYS` → `feedback-question`, so it takes the Story 2.1 fixed-reply path unchanged (`meta` with `category: "done"`, one `text`, empty `sources`, `done`; outcome `fixed_reply`). `prompts/classifier-system.md` version 3: a `done` category, rules (thanks/okay that only close the conversation are `done`, also right after an answer, with punctuation, emoji and polite particles around them; a done signal that also asks something is sorted by what it asks; greetings and how-to-use stay `general`), Thai and English examples, and two mixed examples under `general`.
- Demo: `mock_llm.done_key` strips whitespace, punctuation (P\*), symbols and emoji (S\*), format characters and the emoji marks (variation selectors, ZWJ, keycap) from both ends after `normalise`; Thai letters and marks are never trimmed (`ได้` ends in a tone mark). Example-question matching is unchanged. `done_phrases` gained `ขอบคุณนะคะ/ครับ`, `ขอบคุณมากๆ` (+ `ค่ะ`/`ครับ`) and `thank you very much` (`ๆ` is a letter, not punctuation). The deferred "stored demo category other than `general`" is tested with a constructed `DemoAnswers` (all four stored answers are `general`).
- Feedback: `app/ports/feedback.py` (`FeedbackStore.add(conversation_id, answer, created_at: datetime)`, `FeedbackStoreError`), `app/adapters/sqlite_feedback.py` (one connection per write under a lock, `CREATE TABLE IF NOT EXISTS` with exactly the spec's column text, `data/` created on the first write, `created_at` as UTC `...sssZ`), `app/web/feedback.py` (`extra="forbid"`; `conversation_id` must match a UUID v4 pattern, any letter case, stored in lower case; `answer` `Literal["yes","no"]`; 204; any store failure → 500 `{"error": {"code": "feedback_not_stored", ...}}`, logged by class name only). Wired in `app/main.py` with `_from_root(settings.database_path)`. `tests/conftest.py` points `database_path` to `tmp_path`, so no test writes into `data/`.
- Page: `history.js` holds the pure parts (`uuid4` with `randomUUID` or a `getRandomValues` fallback, since `randomUUID` needs a secure page and a phone in the LAN uses plain http; `conversationId`/`dropConversationId` with a memory fallback when `sessionStorage` is blocked; `showsFeedback`, `feedbackBody`, `afterFeedback`). `app.js` reads `meta.category` into a per-request `info` object (never stored with the exchange), adds the buttons after a finished `done` reply, disables both on the first tap, and on failure re-enables them with the fixed `error` text. `showChat` (new chat, reopen, deleting the open chat) drops the id. "Yes" also clears the open-chat id, so a reload after "Yes" opens an empty new chat as the next question would; it closes any other unanswered button group in that chat, so a later tap cannot make a new id for an ended chat. `index.html` needed no change (the buttons are built per reply).
- Thai drafts for the user's review (NFR8): `feedback-question` คุณได้รับข้อมูลที่ต้องการครบถ้วนแล้วหรือไม่, `feedback-follow-up` คุณยังอยากทราบเรื่องอะไรอีก พิมพ์คำถามได้เลย, `feedback-thanks` ขอบคุณสำหรับคำตอบ หากมีคำถามใหม่ พิมพ์ได้เลย คำถามถัดไปจะเริ่มเป็นแชทใหม่, `feedback-yes` ใช่, `feedback-no` ไม่.
- Docs: spine AD-10 (saved chats and `conversation_id`, validation, first-write creation), AD-3 cross-reference and the deployment line on when the SQLite file is created; epics Story 2.3 note; README (status, flow, `DATABASE_PATH`, the feedback section with an SQL count of SM-1 until `feedback_stats.py`); manual test plan MT-14 and MT-13's classifier version; `.env.example` comment. `deferred-work.md` is left as history.
- Verification: `uv run pytest` 961 passed (853 before); `uv run ruff check` and `ruff format --check` clean. A one-off headless Edge run over CDP (demo mode, 320 px, not in CI) passed 29 checks covering matrix rows Done signal, No, Yes, After Yes, Twice, First question, New chat / reopen, Reload and a network failure; the database then held exactly two rows (`no`, `yes`) with one `conversation_id`, as the manual check expects.

- Review fixes (2026-11-15):
  - While a feedback POST is in flight, the page blocks new questions, new chat, reopen and delete (`busy()` = answering or sending), and a group closed meanwhile ignores the late result. `endChat` closes every group that is not closed, and new buttons close earlier ones, so only the latest feedback question can be answered.
  - `startOpen` drops a leftover `conversation_id` when it opens an empty chat (stale open id, chat deleted elsewhere, unsaved chat), and `appendExchange` drops it (and the page's memory copy) when a follow-up to a deleted chat starts a new one.
  - `/api/feedback` stores only `Content-Type: application/json` (415 `unsupported_media_type` for other types such as `+json`). FastAPI 0.162 already answers 422 to a body without a content type (strict content type is its default).
  - The chosen button gets the class `feedback-chosen` and `aria-current="true"` instead of `aria-pressed`; the note after an answer has `role="status"`.
  - The privacy notice gained a DRAFT sentence (th + en) saying the server keeps only the Yes/No answer with an anonymous number and the time.
  - The README SM-1 count has a `uv run python -c` form, and both forms are tested on a database with No then Yes in one conversation and Yes in another.
  - MT-14 gained part B for the real classifiers.

- The user approved all Thai texts of this story on 2026-11-15 (the five feedback keys, with the buttons kept as ใช่ / ไม่, and the privacy-notice sentence) (NFR8).

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-15). B = blind, E = edge case, V = verification gap.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| V1 | The Yes/No DOM flow in `app.js` is pinned only by source-text checks | medium | pre-verified gap; no browser runner (deferred since Story 1.2). deferred (browser tests); pure parts are Node-tested, MT-14 by hand |
| V2 | Emoji-only done phrase removal (`- {""}`) untested | low | patched (test) |
| B1 | AD-10's Rule line still says "Yes" clears the history | low | contradicted the addendum. patched (marked replaced) |
| B2 | AD-6 key list lacks three new keys | low | patched |
| B3 | Sprint status `in-progress` while the spec is in review | false | the workflow moves it to `review` at the end of the build |
| B4 | NFR8 owner unclear; classifier examples and `done_phrases` also Thai | low | the user approves fixed texts (as for 2.1/2.2); prompt examples and match phrases are not shown to applicants. rejected; the Thai texts are put to the user |
| B5 | Bare `ใช่` / `ไม่` buttons may read curt | low | wording for the user's Thai review; raised with the user, not patched |
| B6 | A typed yes/no after a replayed feedback question is not handled | low | the matrix's reload row covers it: a typed thanks is `done` and shows the buttons again. rejected |
| B7 | A question can be sent while a Yes POST is in flight | medium | `ask()` checked only `answering`. patched (busy guard; with E1–E4) |
| B8 | `aria-pressed` announces one-shot buttons as toggles | low | patched (class + `aria-current`, result note `role="status"`) |
| B9 | "Chat never writes feedback" test runs the `general` path | low | patched (`category="done"`) |
| B10 | No manual check of the real classifiers on `done` | medium | patched (MT-14 part B); live Ollama run 2026-11-15: 12/12 as intended |
| B11 | README SM-1 query untested; `sqlite3` CLI often missing on Windows | low | patched (test runs the exact query; `uv run python -c` form first) |
| B12 | Privacy notice does not mention the stored Yes/No answer | medium | NFR5 transparency. patched (DRAFT sentence for the user) |
| B13 | UUID-case comments wrong; Thai range written as literal characters | low | patched |
| E1 | Yes in flight, then new chat/reopen/delete: `endChat` hits the new chat | medium | same root as B7. patched |
| E2 | A `sending` group reopens after another group's Yes ended the chat | low | `endChat` closed only `open` groups. patched |
| E3 | Late-result guard was dead code | low | same as E2. patched |
| E4 | Question asked during an in-flight Yes ends up in the ended chat | medium | same as B7. patched |
| E5 | Earlier unanswered button groups stay tappable | low | patched (only the latest feedback question can be answered) |
| E6 | Stale open id after reload keeps the old `conversation_id` | low | patched (`startOpen` drops it) |
| E7 | `appendExchange` restart keeps the old `conversation_id` | low | patched (dropped from session and memory) |
| E8 | "Duplicate tab" copies `sessionStorage`, so two tabs share an id | low | rare on phones; the saved-chats open id has the same trait. rejected |
| E9 | A typeless no-cors Blob lets any site insert rows | false | FastAPI 0.162 already rejects a body without Content-Type with 422; an explicit `application/json` check (415) was added as a guard anyway |
| E10 | No rate limit on `/api/feedback` | low | the prototype runs locally; hosting is out of scope (PRD). rejected |
| E11 | Naive datetime shifts `created_at` | false | the only caller passes `datetime.now(UTC)` |
| E12 | Empty or directory `DATABASE_PATH` fails only at runtime | low | misconfiguration; each tap gets the 500 envelope and is logged. rejected |
| E13 | Typed yes/no after the feedback question | low | same as B6. rejected |
| E14 | Claim "Yes ends the conversation" broken by a `sending` group | medium | same as E2. patched |
| E15 | Claim "new id per chat" broken by stale/restarted chats | low | same as E6/E7. patched |
| E16 | Matrix rows Twice/Reload/Yes-failure/After-Yes only source-checked | medium | same as V1. deferred |

## Verification

**Commands:**
- `uv run pytest` -- all pass
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks (if no CLI):**
- Demo mode, 360/320 px: ask an example, send "ขอบคุณค่ะ 🙏", tap No (follow-up text, chat goes on), send "ok." again, tap Yes; `sqlite3 data/feedback.sqlite3 "select * from feedback"` shows two rows with one `conversation_id`.
