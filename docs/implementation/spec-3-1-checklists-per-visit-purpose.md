---
title: 'Story 3.1: Checklists per visit purpose'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: 'e63068fa49ff582711752a1cfae5f3f0ce7aa92d'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Applicants ask the adviser to check their documents because there is no fixed, reviewed list per visit purpose; a list written by the AI could differ each time (FR6).

**Approach:** Add `content/checklists.yaml` with one fixed checklist per visit purpose (`tourism`, `family`, `friends`), every item with a stable id, Thai and English text, and a knowledge-base source; load and check it at startup through `ContentStore`; serve it at `GET /api/checklists/{purpose}` with each source resolved to `{title, url}`. No page UI yet (Story 3.2).

**Decisions (from the sources and the PRD):**
- Items come from the embassy's checklist (`embassy-visitor-visa-checklist`): the general requirements in every checklist; the "Tourism" section for `tourism`; the "Visiting family or friends" section for `family` and `friends`. The "Business" section is left out (not a PRD visit purpose). Conditional items keep their condition in the text ("if employed: …", "if under 18 and travelling without a guardian: …").
- `family` also has the sponsorship form and the invitation letter, each saying the sponsor in Norway fills it in, linked to the UDI pages where the sponsor finds them (`udi-sponsorship-form`, `udi-invitation-for-visitor-visa`); `friends` gets them too when the UDI sources say they apply to friends.
- Where sources disagree, the embassy checklist wins (e.g. photo not older than six months); UDI's checklist stays the authority and the texts never add requirements the sources do not state.
- Thai texts are drafts for the user's review (NFR8), marked in the file.

## Boundaries & Constraints

**Always:** item `id` lowercase kebab-case, unique within its checklist, never reused for other content (ticks depend on it, AD-11); every source id exists in `knowledge-base/sources.yaml`; startup fails (`ContentError` or a checklist error) on an unknown source id, a duplicate item id, a missing or extra purpose, a missing `th`/`en`, or an extra field; the endpoint never calls the LLM; response `{"purpose", "items": [{"id", "text", "source": {"title", "url"}}]}` with Thai `text`, items in file order; unknown purpose → 404 with `{"error": {"code": "unknown_purpose", "message"}}`, the requested value not echoed; layering rules hold (`tests/test_layering.py`); ruff clean.

**Never:** no LLM call; no ticks or any applicant data on the server; no page changes (3.2); no new knowledge-base source in this story; no new dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Family | `GET /api/checklists/family` | 200, Thai items with id and resolved source; includes sponsorship form and invitation letter saying the sponsor fills them in | N/A |
| Tourism / friends | `GET /api/checklists/tourism`, `/friends` | 200, their items | N/A |
| Unknown purpose | `GET /api/checklists/business` | 404 envelope | N/A |
| Unknown source | an item cites `no-such-source` | app refuses to start | error names the checklist and item id |
| Duplicate id | two items `passport` in one checklist | refuses to start | names the id |
| Same id in two checklists | `passport` in tourism and family | allowed | N/A |
| Bad id | `Passport_Copy` | refuses to start | N/A |
| Missing purpose / extra field / empty text | file content | refuses to start | N/A |
| Demo mode | `MOCK_LLM=true` | endpoint works the same | N/A |

</frozen-after-approval>

## Code Map

- `content/checklists.yaml` (new) -- the three checklists; header comment on the item-id rule and the draft status.
- `app/ports/content.py` -- `ContentStore` gains `checklists()` (purpose → items); frozen dataclasses like `FixedText`/`ExampleQuestion`; a `VISIT_PURPOSES` closed tuple.
- `app/adapters/file_content.py` -- reuse `_UniqueKeyLoader`, `_reject_extra_fields`, `_language`, `ContentError`; `load_content` currently reads only `texts.yaml` (`CONTENT_FILE` in `app/main.py`); either a second path argument or a separate loader for `checklists.yaml`. Source ids are checked against the knowledge base, so loading needs the `KnowledgeBase` (already loaded first in `create_app`).
- `app/ports/knowledge_base.py` `KnowledgeBase.source(id)` -- raises `KeyError` for unknown ids; use it to check and to resolve `{title, url}`.
- `app/web/` (new `checklists.py` router) + `app/main.py` (include it before the static mount) -- pattern: `app/web/texts.py`.
- Tests: new `tests/test_checklists.py` (loader rules on temp files, the real file's shape incl. the family sponsor items, endpoint per matrix row, no LLM call via a fake that fails on any call, demo mode); `tests/test_layering.py` if new modules need rules.
- Docs: README (checklist endpoint, where the checklists live and that the adviser reviews them), `ARCHITECTURE-SPINE.md` only if something differs from AD-11.

## Tasks & Acceptance

**Execution:**
- [x] `content/checklists.yaml` -- three checklists from the sources -- FR6, AD-11
- [x] `app/ports/content.py`, `app/adapters/file_content.py`, `app/main.py` -- load and validate at startup -- AD-11
- [x] `app/web/checklists.py` -- the endpoint -- AD-11
- [x] `tests/test_checklists.py` (+ layering) -- every matrix row -- AD-13
- [x] `README.md` -- short section

**Acceptance Criteria:**
- Given the real `content/checklists.yaml`, when every item's source is resolved, then each resolves and every checklist has at least the passport, photo, application form and travel insurance items.
- Given any purpose, when the endpoint runs with an LLM fake that raises on every call, then it still returns 200.

## Implementation Notes

- `load_checklists(path, knowledge_base, adviser_contact)` in `app/adapters/file_content.py` validates the file; its result is passed to `load_content(..., checklists)` (required), so `FileContentStore.checklists()` serves it; the store raises `ContentError` unless the keys are exactly `VISIT_PURPOSES`. Texts-only test readers pass `tests/fakes/content.py::committed_checklists()`. `create_app` now loads the knowledge base before the content. The route is `{purpose:path}`, so `/api/checklists/`, `/api/checklists/tourism/` and deeper paths get the `unknown_purpose` envelope instead of the static 404.
- Item field for the source is `source` (one id per item). Errors are `ContentError`.
- Shared items are written once in the YAML and repeated with aliases (`&passport` / `*passport`); `friends` repeats the whole `family` section, since UDI's invitation and sponsor pages name friends as well as family.
- Left out on purpose: the embassy checklist's "Business" section and its "OPTIONAL" items (power of attorney, previous visas), which the spec's decisions do not include.
- Added after review: `signed-embassy-checklist` (print, tick, sign and hand in the embassy's checklist at VFS) and an unconditional `proof-of-occupation` in every list; `eu-eea-family-member` (source `embassy-necessary-documents`) in `family` only. The family/friends ties item has its own id `social-and-financial-ties`, since its text differs from tourism's `ties-to-thailand`; a test now checks that an id shared by checklists has identical content.

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-15; interrupted once by the usage limit and resumed). B = blind, E = edge case, V = verification gap.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| V0 | No verification gaps | — | every loader rule, the startup wiring and the endpoint are exercised by tests |
| V1 | Dead no-echo assertion in the 404 test | low | asserted a string that could never be in that response. patched |
| B1 | General "Proof of occupation" left out | medium | the embassy checklist lists it as a general requirement. patched (`proof-of-occupation` in all three) |
| B2 | No item for signing and handing in the embassy checklist | low | the source says to print, tick, sign and submit it. patched (`signed-embassy-checklist`) |
| B3 | No pointer to the authoritative checklist; README wording vs cited sources | low | patched via B2; README and file header say UDI's requirements are the authority (FR6), reached through the embassy's official checklist (first patch wording named the embassy checklist as the authority; corrected to the PRD) |
| B4 | Family list never mentions the separate EU/EEA family-member checklist | medium | `embassy-necessary-documents` links it. patched (`eu-eea-family-member` in `family`) |
| B5 | Conditional items have no structured marker | low | design input for Story 3.2. deferred |
| B6 | `ties-to-thailand` holds different texts in different lists | low | no ticks exist yet. patched (`social-and-financial-ties` for family/friends; test that a shared id has identical content) |
| B7 | Nothing pins id → text (snapshot) | low | would fail on every approved rewording; the shared-id test covers the cross-list case. rejected |
| B8 | `checklists` optional, so a missed wiring gives valid purposes a 404 | low | patched (required; store rejects keys other than `VISIT_PURPOSES`) |
| B9 | Tests pin exact draft phrases; awkward English sponsor copy | low | patched (checked by id and source; English rewritten) |
| B10 | `en` is stored but not reachable for Story 4.1 | low | deferred (Story 4.1) |
| B11 | Spec in review while sprint status says in-progress | false | the workflow moves sprint status to `review` at the end |
| B12 | Stale build-order sentence in `epic-3-context.md` | low | patched |
| B13 | Malformed paths fall through to the static 404 | low | same as E1. patched |
| B14 | Core source path contains `xx-old-unused` | low | already an open adviser item in `issues.md` (confirm the embassy checklist is current); not caused by this story. rejected as tracked |
| E1 | `/api/checklists/`, trailing slash, extra segment → `{detail}` not the envelope | low | verified for the trailing slash. patched (`{purpose:path}` route + tests) |
| E2 | Store without checklists breaks the protocol | low | same as B8. patched |
| E3 | Claim "all general requirements" misses proof of occupation | medium | same as B1. patched |

## Verification

**Commands:**
- `uv run pytest` -- all pass
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks (if no CLI):**
- `uv run uvicorn app.main:app`, open `/api/checklists/family`: Thai items, source titles and https links; the sponsor items say the sponsor in Norway fills them in.
