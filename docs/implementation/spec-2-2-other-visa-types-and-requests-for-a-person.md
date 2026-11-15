---
title: 'Story 2.2: Other visa types and requests for a person'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Questions about other visa types (e.g. a work visa) or about anything else than short-stay visas go to the answer model, and an applicant who asks for a person gets no adviser contact unless the sources happen to give one (FR13, FR14).

**Approach:** Grow the Story 2.1 classifier by two categories (AD-5): `out_of_scope` → fixed `reply-out-of-scope` (the chatbot only covers short-stay tourist and visitor visas to Norway, plus `{ADVISER_CONTACT}`); `reach_person` (asking for a person, or for help with the whole process) → fixed `reply-reach-person` with `{ADVISER_CONTACT}`. Same fixed-reply path, stream shape and log outcome `fixed_reply` as Story 2.1; classifier prompt version 2; both real classifiers (Claude, Ollama) and the scripted fake cover both categories.

Rules taken from the PRD (no user decision needed): out of scope is anything other than short-stay tourist and visitor visas to Norway (glossary, FR14), so non-visa topics such as the weather are `out_of_scope`, and FR4's no-answer reply stays for in-scope questions no source answers; a question that also asks something in scope is `general` (as in Story 2.1); asking for a person wins over the other categories. New Thai texts are drafts for the user's review (NFR8).

</frozen-after-approval>

## Implementation Notes

- Implemented inline (oneshot route). The Story 2.1 fixed-reply path needed no change: `CLASSIFIER_CATEGORIES` (`app/adapters/classifier_request.py`) gains `out_of_scope` and `reach_person`, so both real classifiers' schemas grow; `FIXED_REPLY_KEYS` (`app/web/chat.py`) maps them to `reply-out-of-scope` and `reply-reach-person`; the keys are added to `REQUIRED_TEXT_KEYS` and `content/texts.yaml` (Thai marked DRAFT for the user's review, NFR8). `{ADVISER_CONTACT}` is filled at load as for every text.
- `prompts/classifier-system.md` version 2: the two new categories with Thai and English examples; rules: a request for a person wins over the rest, a question mixing out-of-scope and in-scope parts is `general`, a short visit to family or a partner is in scope (not family immigration).
- Only `done` (Story 2.3) is still "not built yet" and answered like `general`; the unknown-category tests use `done` now instead of `out_of_scope`.
- MT-06 used the weather question as its no-answer example; by the PRD's definition that is now out of scope, so MT-06 uses an in-scope question no source answers (vaccinations before applying; no source mentions vaccines). A first pick, VFS opening hours in Chiang Mai, was dropped in review: the embassy sources give the VFS centre's address and contact. MT-10 step 2 points to it. New MT-13 covers this story.
- Tests: 853 pass (new: both categories through the chat API with the contact filled and no answer call, the fixed-reply key map, both texts served in Thai with the contact, prompt rules and examples; the Claude and Ollama classify tests run all four categories). Ruff clean.
- Live check on Ollama (`qwen3.5:9b`): 14 of 14 questions sorted as intended (5 out of scope incl. study, Germany, permanent move to a spouse, weather; 4 reach_person incl. "talk to a real person about my chances"; 1 own chances; 4 general incl. visiting a partner, VFS hours, and a work-vs-tourist mixed question). About half are the prompt's own examples, so this is a smoke test, not an evaluation.
- Review fixes (see the triage log): classifier prompt rules for Norway with other Schengen countries (general), own chances for something out of scope (out_of_scope), greetings and thanks (general until Story 2.3), "explain the steps" is not a request for a person, and an out-of-scope follow-up example; both Thai drafts end by inviting the applicant to keep asking here; MT-06 example changed to vaccinations; MT-13 gained precedence and follow-up steps; MT-10's pass noted as before Stories 2.1/2.2. Live Ollama recheck: 22 of 22 as intended.
- The user approved the Thai of `reply-out-of-scope` and `reply-reach-person` on 2026-11-15 (NFR8).

## Review Triage Log

Blind review, 2026-11-15.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| 1 | MT-06's VFS example is probably answerable; the spec says there is no VFS source | medium | verified: 8 sources mention VFS, `embassy-hand-in-documents.md` gives the centre's contact. patched (vaccination question; spec note corrected) |
| 2 | MT-10's pass row predates the changed step 2 and prompt v2 | low | patched (note on the row) |
| 3 | Duplicate `done` case and stale test name in `test_classifier_request.py` | low | verified at lines 20, 61-62. patched |
| 4 | Greetings, thanks and "the chatbot itself" now get the out-of-scope apology | medium | prompt listed "the chatbot itself" as out of scope and had no rule for greetings. patched (greetings, thanks, using the chat are general until Story 2.3); live: สวัสดีค่ะ, ขอบคุณค่ะ → general |
| 5 | Norway plus other Schengen countries may be routed out of scope | medium | prompt said "visas for other countries" with a France example. patched (rule + example); live: "French Schengen visa, can I enter Norway?" → general |
| 6 | `reach_person` boundary: "help me with the steps" has no contrast; mixed half dropped silently | low | patched (rule + `ช่วยบอกขั้นตอนการยื่นวีซ่าหน่อย` example; reply text invites further questions) |
| 7 | `reply-out-of-scope` sends even weather questions only to the adviser | low | patched (draft text ends with an invitation to ask about short-stay visas here) |
| 8 | Demo mode cannot show the new categories | medium | `MockLLM.classify` returns `general` for non-examples. deferred (with the Story 2.1 demo entry) |
| 9 | README lists Story 2.2 as done before the Thai review and MT-13 | low | "Ferdig og testet" is used for stories with passing automated tests (Story 2.1 is listed the same way before MT-12). rejected |
| 10 | README's first sorting sentence names two categories | low | patched |
| 11 | MT-13 has no precedence or follow-up steps; live check not recorded | low | patched (steps 6-9); the live check is in the Implementation Notes, not a manual-test result |
| 12 | Follow-up rule has no example for the new categories | low | patched (`แล้ววีซ่าทำงานล่ะ` → out_of_scope) |
| 13 | Precedence between own chances and out of scope undefined | low | patched (own chances for something out of scope is out_of_scope); live: ฝรั่งเศสจะให้วีซ่าฉันไหม → out_of_scope |
