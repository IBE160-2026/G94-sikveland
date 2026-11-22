# Deferred Work

- source_spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md`
  summary: Resolve `DATABASE_PATH` against the project root, not the working directory, when Story 2.3 creates the SQLite file.
  evidence: `database_path` is the relative string `data/feedback.sqlite3`; started from another folder, the feedback file would be created in the wrong place. Nothing uses it before Story 2.3.
- source_spec: `docs/implementation/spec-1-2-chat-page-with-thai-texts.md`
  summary: Add a browser-level test (e.g. Playwright via pytest) for the chat page's JavaScript in Story 1.6: rendering from `/api/texts`, tap-to-fill, the retry button on load failure, and the streamed answer.
  evidence: No test runs `app/static/app.js`; changing `example.text` to `example.th`, dropping the tap handler, or removing `loadFailed.hidden = false` all pass CI. Story 1.6 adds much more page logic (stream reading), so the gap grows there.
- source_spec: `docs/implementation/spec-1-3-knowledge-base-of-official-sources.md`
  summary: Add a VFS Global source (the Thailand–Norway booking/info page) to the knowledge base, so the "book an appointment at VFS" step can link to VFS (FR12).
  evidence: VFS (Cloudflare) answers the ingest client with HTTP 403, the old VFS PDF stated an outdated fee (EUR 80), and the current VFS page is a JavaScript app that could not be saved from the browser; the user dropped VFS for now on 2026-11-13. `PUBLISHER_DOMAINS` still allows `vfsglobal.com`.
- source_spec: `docs/implementation/spec-1-4-personal-information-filter.md`
  summary: Some real Thai ID spellings get through the filter: `1 234567890123`, `1-2345-67890-123`, `1 2345 67890 123`, `12-3456-78901-2-3`, IDs after a 5-digit group (`10110 1234 5678 90123` → `[removed] 90123`), separators outside `SEP` (en space, soft hyphen, word joiner, full-width dot), and passports written `AA: 1234567`.
  evidence: Review pass 4, confirmed by probe on 2026-11-14 (triage #8, #9, #11, #12). The user chose to accept the loop 3 rules because of the 2026-11-15 deadline. A possible fix: accept a 1-digit first group with any 3+ grouping after it, prefer windows that end at a run boundary, widen `SEP`, allow `:` as a passport separator.
- source_spec: `docs/implementation/spec-1-4-personal-information-filter.md`
  summary: The filter removes some phone numbers and amounts it should keep: 13-digit phone spellings starting with `0066`, numbers in 3+ digit groups that add up to 13 (`room 123 0812345678`, `500000-1500000 baht`, `2569 2026 12345`, `021234567 2569`), and glued lowercase amounts (`kr1500000`, `Rs1500000`, `No1234567`).
  evidence: Review pass 4, confirmed by probe on 2026-11-14 (triage #6, #7, #10). This contradicts the Decision that phone numbers are not removed. A possible fix: Thai IDs start with 1–8, so a group starting with 0 cannot open an ID; the glued passport form should need uppercase letters. Check against the evaluation test set before changing.
- source_spec: `docs/implementation/spec-1-5-claude-connection-with-a-test-version.md`
  summary: Set an explicit timeout and `max_retries` on the Anthropic client, and let Story 1.6 tell overload (429/529) from configuration errors (400/401) without user text.
  evidence: The adapter uses the SDK defaults (10-minute timeout, 2 silent retries) and `LLMError` keeps only the exception class name. The right values depend on the stream UX in Story 1.6 (adaptive thinking can pause before the first text).
- source_spec: `docs/implementation/spec-1-6-streamed-answer-with-sources.md`
  summary: Timeouts for a stalled answer: explicit timeout and `max_retries` on the Anthropic client, a page-side `AbortController` deadline that shows the fixed error text, and, if the real-phone test shows idle cuts, a heartbeat line while text is held back. Also check that a client disconnect closes the model stream.
  evidence: Review pass 1 of Story 1.6 (#3, #4, #5, #11). Today a stalled call keeps the typing dots and a locked form until the SDK default (10 minutes, 2 retries). The values need the real-phone test in Facebook's in-app browser; replaces the Story 1.5 entry's target.
- source_spec: `docs/implementation/spec-1-6-streamed-answer-with-sources.md`
  summary: Browser-level tests for the chat page's JavaScript (stream parsing across chunks, append-only text, reminder, sources, error text, form re-enabled), after part 1.
  evidence: Review pass 1 of Story 1.6 (#12): `tests/test_static.py` only matches strings in `app.js`; breaking line buffering or `setAnswering(false)` passes CI. Replaces the Story 1.2 entry's Story 1.6 target.
- source_spec: `docs/implementation/spec-1-7-follow-up-questions.md`
  summary: Extend the deferred browser-level page tests to Story 1.7: exchange stored in sessionStorage only after `done`, follow-up sends the last 10, reload replays the conversation with reminder and sources, closing the tab drops it, malformed stored entries ignored.
  evidence: Review of Story 1.7 (#7, #8): `tests/test_static.py` only matches strings in `app.js`; e.g. `slice(MAX_HISTORY)` instead of `slice(-MAX_HISTORY)` would pass CI.
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: Saved chats changed the Story 1.7 entry above: closing the tab no longer drops the conversation (a new tab opens an empty new chat; past chats stay in `localStorage`). The storage logic in `app/static/history.js` is tested in Node (`tests/test_history_js.py`); the UI wiring in `app.js` (top bar, history panel, reopen, delete with confirm, controls disabled while answering) still needs the deferred browser-level tests.
  evidence: No browser test runner (Playwright deferred); `tests/test_static.py` only matches strings in `app.js`. A one-off headless-browser run passed on 2026-11-15 but is not in CI.
- source_spec: `docs/implementation/spec-4-2-demo-mode-without-an-api-key.md`
  summary: In Story 2.3, make done-phrase matching ignore surrounding punctuation and emoji (`Thanks!`, `ok.`, `ขอบคุณค่ะ 🙏`), in the mock and in the real classifier's tests, and test a stored demo category other than `general`.
  evidence: Review of Story 4.2 (#17, #22): the mock matches done phrases exactly after trimming and casefolding; nothing consumes `classify` yet.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Check the Ollama context budget in a long conversation (system ~24,700 tokens + up to 10 history turns + thinking + answer within `OLLAMA_NUM_CTX` 32768), and detect a full context at runtime (e.g. `prompt_eval_count` reaching `num_ctx`) instead of letting Ollama truncate silently.
  evidence: Review of the Ollama build (#3), medium, unverified: 32768 − ~24,700 leaves ~8k tokens; the probe's documents question used ~2,700 thinking tokens; never run with 10 long turns. Settle with a 10-turn manual run against Ollama.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Cap an Ollama answer (`num_predict` and/or an overall deadline), so a model stuck thinking cannot hold a request open; the read timeout restarts on every thinking line.
  evidence: Review of the Ollama build (#5), medium, unverified: no cap is sent and thinking lines are not shown, so the applicant would see only typing dots. Settle by forcing a long thinking run.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: On slow or CPU-only machines, the first (uncached) ~24,700-token prompt may take longer than the 300 s read timeout before Ollama sends anything; make the timeout a setting or separate the first-byte wait.
  evidence: Review of the Ollama build (#6), medium, unverified: 7 s on the user's GPU; no measurement on CPU. Settle by timing a cold request on a CPU-only machine.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Check that Ollama follow-up questions still cite: earlier answers go back as history without `[[id]]` markers, which may teach a small model to stop citing (then every follow-up becomes `reply-no-answer`).
  evidence: Review of the Ollama build (#8), medium, unverified: the manual run was single-turn only. Settle with a follow-up question against Ollama; if it fails, re-insert markers in history or add a reminder after it.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Browser check of the example questions with `LLM_PROVIDER=ollama` (AC 4): run MT-10 in `manual-test-plan.md` and record the result.
  evidence: Review of the Ollama build (#11): AC 4 was checked through the app by script, not tapped in a browser. The docs part of this entry (README, manual test plan, spine, PRD addendum, spec-1-6 and spec-1-8 change logs) was done on 2026-11-15.
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: Settle how Story 2.3's feedback flow fits saved chats: AD-10 and epics Story 2.3 say "Yes" ends the conversation and "the page clears the history", and `conversation_id` lives in `sessionStorage`; with saved chats it is undefined whether "Yes" deletes, closes or keeps the saved chat, and what `conversation_id` does on "new chat" or when an older chat is reopened.
  evidence: Review of the saved-chats build (blind #10): the spine only says "Story 2.3 decides how they relate"; nothing else tracks it, so it would be missed when Story 2.3 is built.
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: Delete uses `window.confirm`; check that it works in Facebook's and LINE's in-app browsers and after a user ticks "prevent this page from creating additional dialogs" (then `confirm` returns false at once and delete silently does nothing). If it fails, use an in-page confirm built from the existing text keys.
  evidence: Review of the saved-chats build (blind #6), medium, unverified: the decision to use `window.confirm` is in the approved spec; whether in-app webviews suppress it needs a real-phone test (MT-09 setup).
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: If `history.js` is missing when `app.js` runs (a stale cached `index.html` without the new script tag after the update), `window.ChatHistory` is undefined, `startOpenChat` throws before `load()`, and the page stays blank with no retry button; guard it or send `Cache-Control: no-cache` for the static files.
  evidence: Review of the saved-chats build (edge #1), medium, unverified: FastAPI's StaticFiles sends ETag/Last-Modified but no Cache-Control, so browsers may serve a stale `index.html` heuristically; settle by loading the old page in a browser, updating, and reloading once.
- source_spec: `docs/implementation/spec-2-1-the-embassy-decides-for-own-chances.md`
  summary: Show "the embassy decides" in demo mode (the examiner path): today every stored demo answer is `category: general`, so `MOCK_LLM=true` never shows FR3. Add an example question with a stored `individual_assessment` category (new Thai example text for the user to approve, NFR8), a `MockLLM` routing test and a demo step in MT-12.
  evidence: Review of Story 2.1 (blind #7): the epic context asks to test a stored demo category other than `general`; the Story 2.1 intent covers the real classifiers only, and a new example question is a visible product change for the user to decide.
- source_spec: `docs/implementation/spec-2-1-the-embassy-decides-for-own-chances.md`
  summary: Check the Claude classify call against the real API: `MAX_TOKENS_CLASSIFY = 4096` must cover Haiku's thinking at `EFFORT_SMALL` (and at higher values a user may set in `.env`); a `max_tokens` stop makes every question show the error text.
  evidence: Review of Story 2.1 (blind #15), medium, unverified: no real call has been made; settle with MT-12 using a real key, trying `EFFORT_SMALL=low` and `high`.
- source_spec: `docs/implementation/spec-2-1-the-embassy-decides-for-own-chances.md`
  summary: Check whether Ollama keeps the knowledge base cached now that a short classify call runs on the same model before every answer; with one slot the answer call could re-read ~24,700 tokens each time (minutes on a CPU-only machine). If so, document `OLLAMA_NUM_PARALLEL` ≥ 2 or use a separate small classify model.
  evidence: Review of Story 2.1 (edge #4), medium, unverified: a live run on the user's GPU on 2026-11-15 showed answers at ~9 s and `prompt_eval_count` ~24,790 both before and after the classifier, so no change is visible there, but `prompt_eval_count` does not show cache reuse; settle with Ollama's debug log or on a CPU-only machine.
- source_spec: `docs/implementation/spec-2-2-other-visa-types-and-requests-for-a-person.md`
  summary: Show `out_of_scope` and `reach_person` in demo mode too: `MockLLM.classify` returns `general` for anything but an example question, so in `MOCK_LLM=true` "can I talk to a staff member?" gets `reply-demo-only` without the adviser contact. Add a few demo phrases mapped to these categories (like `done_phrases`) and a demo step in MT-13; decide together with the Story 2.1 demo entry.
  evidence: Review of Story 2.2 (blind #8): `content/demo-answers.yaml` holds only `general` entries; the examiner path cannot show FR13 or FR14.
- source_spec: `docs/implementation/spec-2-3-feedback-question-at-the-end.md`
  summary: Extend the deferred browser-level page tests to Story 2.3: the Yes/No flow in `app.js` (follow-up or thanks text after a 204, `endChat` after Yes and a new chat at the next question, buttons back with the error text after a failed POST, controls blocked while a feedback POST is in flight). The pure parts in `history.js` are tested in Node; the DOM wiring is pinned only by source-text checks.
  evidence: Review of Story 2.3 (verification gap #1): swapping `element.append(group, note)` to `(note, group)` makes `group.nextElementSibling` null, so no text shows and Yes never ends the chat, and every test stays green. A one-off headless run passed on 2026-11-15 but is not in CI; MT-14 covers it by hand.
- source_spec: `docs/implementation/spec-3-1-checklists-per-visit-purpose.md`
  summary: Story 3.2: decide how conditional checklist items ("if employed", "if under 18", "if relevant") are shown, so an applicant they do not apply to can still reach a fully ticked list (e.g. a `condition` flag or field per item, or a "not relevant" state on the page).
  evidence: Review of Story 3.1 (blind #5): about half the items are conditional and `ChecklistItem` has no marker for it; cheaper to add before ticks exist in real use.
- source_spec: `docs/implementation/spec-3-1-checklists-per-visit-purpose.md`
  summary: Story 4.1 ("Show English"): checklist items store `en` but `GET /api/checklists/{purpose}` serves only Thai; decide how the English reaches the page (serve `en`, or let `/api/translate` look up stored checklist English).
  evidence: Review of Story 3.1 (blind #10): nothing in the spec, README or epic context says how 4.1 reaches checklist English. Settled by Story 4.1 (user decision, 2026-11-15): `GET /api/checklists/{purpose}` serves each item's stored `en`, and the checklist view's "Show English" shows it with no request and no model call.
- source_spec: `docs/implementation/spec-3-2-tick-off-documents-and-the-ticks-are-kept.md`
  summary: Extend the deferred browser-level page tests to the checklist view: refresh after a change (progress, all-done, dimmed rows, `data-state`), the stale-response guard after change purpose or close, retry and focus, and the purpose buttons from `/api/texts`. The pure logic in `checklist.js` is tested in Node; the DOM wiring in `app.js` only by source text.
  evidence: Review of Story 3.2 (verification gap #1): removing `refreshChecklist()` from `changeChecklist` keeps ticks saved but never updates the progress line, and every test stays green. A one-off headless run passed on 2026-11-15; MT-15 covers it by hand. The Story 3.1 entry on conditional items is settled by this story (`conditional` + "doesn't apply to me").
- source_spec: `docs/implementation/spec-3-2-tick-off-documents-and-the-ticks-are-kept.md`
  summary: `eu-eea-family-member` is a pointer ("the embassy's separate checklist applies"), not a document, yet it is a tickable item that counts towards "ready"; decide whether checklists get non-tickable notes (shown as a banner, outside the progress count).
  evidence: Review of Story 3.2 (blind #13): if it applies, most of the family list is the wrong list, but the applicant can still reach all-done on it.
- source_spec: `docs/implementation/spec-3-2-tick-off-documents-and-the-ticks-are-kept.md`
  summary: Let the applicant clear a checklist's ticks (a new application, or another traveller on the same phone), and decide whether "delete all chats" should also clear `checklist:*` and `checklist-na:*`.
  evidence: Review of Story 3.2 (blind #8): no reset exists; on a shared phone the ticks stay after "delete all chats". Ticks hold only item ids, no personal text.
- source_spec: `docs/implementation/spec-3-3-open-the-checklist-from-the-chat.md`
  summary: Extend the deferred browser-level page tests to the "Open checklist" button: shown under a live answer only for a `checklist: true` event, back on reload and reopen from the stored `checklistPurposes`, one purpose opening that checklist directly and several the purpose choice, focus back on the button after Back or Escape, and opening while another answer streams. The pure parts (`validPurposes`, `openTarget`) are tested in Node and the server flags in pytest; the DOM wiring in `app.js` only by source text.
  evidence: Story 3.3 build: no browser test runner exists (Playwright deferred); MT-16 covers it by hand.
- source_spec: `docs/implementation/spec-3-3-open-the-checklist-from-the-chat.md`
  summary: A general answer can open the family checklist directly: "how to start" cites `embassy-necessary-documents`, which only the `eu-eea-family-member` pointer item uses, so `checklist_purposes` is `["family"]` and a tourist lands in the family list. Settle together with the Story 3.2 entry on non-tickable notes (exclude notes from the source → purpose map), or show the purpose choice when the only link comes from a conditional item.
  evidence: Review of Story 3.3 (blind #2): verified in the demo run and in MT-16 step 3; the mapping rule follows the story's AC, the odd result comes from a pointer item citing a general source.
- source_spec: `docs/implementation/spec-4-1-show-the-english-translation.md`
  summary: Extend the deferred browser-level page tests to "Show English": the button only under a `done` reply (live and replayed) and before the feedback buttons, disabled while in flight, replaced by the `lang="en"` paragraph on success, the error text and the button back on failure, a late result ignored after a new chat, and the checklist view's English kept across ticks and cleared on a purpose change. The pure parts (`translateBody`, `translationText`, `validItems` with `en`) are tested in Node and the endpoint in pytest; the DOM wiring in `app.js` only by source text.
  evidence: Story 4.1 build: no browser test runner exists (Playwright deferred); MT-17 covers it by hand.
- source_spec: `docs/implementation/spec-4-1-show-the-english-translation.md`
  summary: Check the translate call against the real API and a real Ollama model: that `MAX_TOKENS_TRANSLATE = 8192` covers the English of the longest answers at `EFFORT_SMALL`, that the translation keeps URLs, amounts and `[removed]`, and that it adds nothing.
  evidence: Story 4.1 build: no real call has been made; settle with MT-17 part B.
- source_spec: `docs/implementation/spec-4-1-show-the-english-translation.md`
  summary: Add to the browser-level tests for "Show English": the checklist button becomes visible after the items load (`checklistTranslate.hidden = checklistEnglish` in `renderChecklist`), `closeChecklist` resets the English and hides the button, and an earlier `.translate-error` is removed on retry.
  evidence: Review of Story 4.1 (verification gap #2, blind #13): deleting `checklistTranslate.hidden = checklistEnglish;` keeps the button hidden forever and every test stays green; the page tests only match source text. MT-17 step 7 covers it by hand.
- source_spec: `docs/implementation/spec-4-1-show-the-english-translation.md`
  summary: Check whether a non-streamed Ollama translation of a long answer can pass the 300 s read timeout on a slow machine; if so, stream the translate reply or give it a longer timeout.
  evidence: Review of Story 4.1 (edge case #5), unverified (would be medium): `_post` uses the shared 300 s timeout with `stream: false`, so nothing arrives until the whole English is written. Settle with MT-17 part B on the user's 16 GB GPU and a long answer.
- source_spec: `docs/implementation/spec-eval-prompt-fixes.md`
  summary: Run the evaluation with Claude after classifier prompt version 4, and check that the own-chances cases (`own-chances-salary`, `own-chances-earlier-overstay`, `follow-up-own-chances`) still get `individual_assessment` and `own-chances-and-employment-proof` gets `general`.
  evidence: Review of the eval prompt fixes (blind): the classifier prompt is shared with Claude, but only an Ollama run could be made (no Claude key on this machine).

- source_spec: `docs/implementation/spec-eval-dropped-source-ids.md`
  summary: Show in the evaluation report which marker ids the Ollama adapter mapped to a known id, and at what similarity, so both sides of the 0.85 cutoff are visible.
  evidence: The report now lists dropped ids (below the cutoff or tied) but mapped ids only reach an INFO log line with the known id; the pipeline never sees the model's original text, so this needs the adapter to pass mapping details through the port.

- source_spec: `docs/implementation/spec-ollama-chinese-word-repair.md`
  summary: The Ollama repair call (and the classify call) may evict the cached knowledge-base prompt, so the next answer re-reads ~24,600 tokens.
  evidence: Review of the Chinese-word repair (E6), medium, unverified. Settle with Ollama's debug log, or by timing an answer right after a repaired answer against one after an ordinary answer.
