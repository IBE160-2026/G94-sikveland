---
title: 'Story 1.2: Chat page with Thai texts, privacy notice and example questions'
type: 'feature'
created: '2026-11-12'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '4ffae5834ddbcf3123b5651a7c798798ad53fe2e'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There is no page yet. An applicant needs a phone-friendly chat page that opens in Thai, warns against sharing personal information, and offers example questions to tap. All its Thai text must come from one adviser-reviewed content file.

**Approach:** Add `content/texts.yaml` (fixed texts + example questions, `th` and `en`), a `ContentStore` port with a file adapter that validates and fills `{ADVISER_CONTACT}` at startup, `GET /api/texts`, and a plain HTML/CSS/JS page in `app/static/` served at `/` that builds itself from `/api/texts`.

## Boundaries & Constraints

**Always:**
- Required text keys (closed list for now): `privacy-notice`, `personal-info-reminder`, `reply-no-answer`, `error`, `demo-label`, plus the UI keys `send-button` and `question-placeholder` (needed so the page holds no Thai; extends AD-6's list). Every entry has non-empty `th` and `en`.
- Example questions: list of `{id, th, en}`, kebab-case unique ids, at least one.
- `ContentStore` replaces `{ADVISER_CONTACT}` in every text with `settings.adviser_contact` at load.
- `/api/texts` → `{"demo_mode": settings.mock_llm, "texts": {key: th}, "example_questions": [{"id", "text": th}]}`.
- Page: `<html lang="th">`, viewport meta, mobile-first, touch targets ≥ 48 px, readable at 320 px width without horizontal scroll. No Thai literal in `app/static/`.
- Tapping an example question puts its text in the field and focuses it; sending is wired in Story 1.6.
- Decisions: four example questions — `tourist-visa-documents`, `how-to-start`, `visa-fee`, `processing-time`. Claude drafts all Thai (with `en`); the user (adviser) reviews it before commit. The review is recorded as "Thai texts reviewed by the adviser (NFR8)" in the commit message and session log, since work goes straight to `main` without a pull request.

**Never:**
- No `/api/chat`, no LLM, no history, no translate button, no demo-label display (Story 4.2), no checklist.
- No framework or build step for the page; no external CDN.
- `app/pipeline/` untouched.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid content | committed `texts.yaml` | app starts; `/api/texts` returns Thai with contact filled in | N/A |
| Missing key | `error` absent | startup fails | `ContentError` names the key |
| Unknown key | `privcy-notice` | startup fails | `ContentError` names the key |
| Missing language | entry without `en` or with empty `th` | startup fails | `ContentError` names key and language |
| Duplicate id | two example questions `visa-fee` | startup fails | `ContentError` names the id |
| Duplicate YAML key | same text key twice | startup fails | `ContentError` (no silent last-wins) |
| Leftover placeholder | `{SOMETHING}` after filling | startup fails | `ContentError` names the key |
| Texts fail to load | `/api/texts` unreachable | page shows a retry button (↻ symbol, no words) | N/A |

</frozen-after-approval>

## Code Map

- `app/main.py` -- `create_app(settings)`; add content loading (adapter) onto `app.state.content`, include texts router, mount `StaticFiles(directory=app/static, html=True)` at `/` after the API routers so `/api/*` wins.
- `app/config.py` -- `ROOT`, `Settings.adviser_contact`, `mock_llm`; reuse, do not change.
- `app/web/health.py` -- router pattern to copy.
- `app/ports/__init__.py`, `app/adapters/__init__.py` -- empty packages; first port/adapter goes here.
- `tests/conftest.py` -- `settings` fixture (no `.env`); reuse. `tests/test_health.py` -- `TestClient` pattern.
- `tests/test_layout.py` -- checks folders; `content/.gitkeep` and `app/static/.gitkeep` may be removed once real files exist (check the test does not require `.gitkeep`).
- PyYAML 6.0 already locked; `StaticFiles` comes with FastAPI/Starlette, no new dependency.
- Web importing `app.ports` types is accepted (route reads `ContentStore` from `app.state`); pipeline stays SDK/FastAPI-free.

## Tasks & Acceptance

**Execution:**
- [x] `app/ports/content.py` -- `FixedText(th, en)`, `ExampleQuestion(id, th, en)` frozen dataclasses; `ContentStore` Protocol with `texts() -> Mapping[str, FixedText]`, `example_questions() -> Sequence[ExampleQuestion]`; `REQUIRED_TEXT_KEYS` -- port shared by later stories.
- [x] `app/adapters/file_content.py` -- `ContentError`; `load_content(path, adviser_contact) -> FileContentStore`; YAML loader rejecting duplicate keys; all matrix checks -- one validated source of fixed text.
- [x] `content/texts.yaml` -- `texts:` map and `example-questions:` list, Thai + English -- adviser-reviewable content.
- [x] `app/web/texts.py` -- `GET /api/texts` -- page's only Thai source.
- [x] `app/main.py` -- wire loader (path `ROOT/content/texts.yaml`), router, static mount.
- [x] `app/static/index.html`, `app/static/style.css`, `app/static/app.js` -- fetch `/api/texts`, render privacy notice, example buttons, input + send button; retry on load failure.
- [x] `tests/test_content.py`, `tests/test_texts_api.py`, `tests/test_static.py` -- every matrix row; `/api/texts` shape and contact fill; committed file loads; `/` serves the page; no Thai code point (U+0E00–U+0E7F) in `app/static/*`.

**Acceptance Criteria:**
- Given `uv run uvicorn app.main:app`, when I open `/` in a phone-width browser, then I see the Thai privacy notice, the example questions as large buttons, a text field and a send button.
- Given an example button, when I tap it, then its Thai text is in the field.

## Implementation Notes

- Implemented by a subagent from this spec; 68 tests passed before review. Checked in headless Edge with device emulation at 320 and 360 px: no horizontal scroll, buttons ≥ 52 px tall, tap fills and focuses the field, blocked `/api/texts` shows only ↻ and retry recovers. Not yet tried on a real phone.
- Beyond the matrix, the loader also rejects unknown top-level keys, unknown fields in an entry and an unreadable file; example questions get `{ADVISER_CONTACT}` filled in too. Browser tab title is the English product name "Norway Visa Guide" (no title key). `content/.gitkeep` and `app/static/.gitkeep` removed.
- Matrix row "Texts fail to load" is covered by the manual headless check and a test that the retry button exists, not by an automated JS test (no JS runtime in CI); deferred, see triage #1.

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | verif, blind, edge | `app.js` behaviour (render, tap-to-fill, retry on failure) runs in no test | medium | pre-verified: three named regressions pass CI. Fix needs a browser test harness (new tooling). defer to Story 1.6, which adds streaming JS |
| 2 | edge | Non-UTF-8 content file raises `UnicodeDecodeError`, not `ContentError` | low | reproduced by the reviewer; startup still fails but with the wrong error. patch: catch it |
| 3 | blind, edge | Blank/whitespace `ADVISER_CONTACT` accepted → help texts name no contact | medium | `env_ignore_empty` covers only empty, not `"  "`; `Settings(adviser_contact="")` also accepted. patch: non-blank constraint in config |
| 4 | blind, edge | Placeholder typos (`{ADVISER CONTACT}`, unclosed brace) reach users | medium | `_PLACEHOLDER` only matches `{Identifier}`. patch: reject any brace left after removing `{ADVISER_CONTACT}` |
| 5 | blind | Textarea has no accessible name | low | placeholder only. patch: `aria-label` from `question-placeholder` |
| 6 | blind | Retry button has no accessible name | low | real, but its label cannot come from `/api/texts` (it shows when that failed) and Thai may not be hard-coded. rejected |
| 7 | blind, edge | `STATIC_FILES` reads binaries as UTF-8 | low | first favicon would break collection. patch: filter by suffix |
| 8 | blind, edge | External-resource test misses single quotes, CSS `url()`, `fetch()` | low | regex only matches `src="`/`href="`. patch: widen regex |
| 9 | blind | Committed-file test checks Thai in only three keys | low | English pasted into `th` elsewhere would pass. patch: check every `th` |
| 10 | blind | Page blank while loading; no `<noscript>` | low | same-origin small request; Facebook's in-app browser runs JS; fix adds elements. rejected |
| 11 | edge | `/api/texts` that never responds leaves page blank | low | unlikely for a same-origin static read; fix adds AbortController/timeout. rejected |
| 12 | blind | English `<title>` on a Thai page, not in content | low | it is the product name; a title key would change the frozen closed key list. rejected |
| 13 | blind | `CONTENT_FILE`/`STATIC_DIR` in `app.main`; broken YAML fails collection of several modules | low | CI still fails loudly with the `ContentError` message. rejected |
| 14 | blind | `/api/texts` has no Pydantic response model | low | shape pinned by `test_texts_shape_in_thai`. rejected |
| 15 | blind | Structural errors don't name the file | low | there is one content file. rejected |
| 16 | blind | Privacy notice names only passport, ID and phone; says nothing about storage | false | FR9 and the addendum define exactly these three (addresses dropped as undetectable); the text says questions go to an AI service as FR9 requires |
| 17 | blind | Sprint status `in-progress` vs spec `in-review`; spec missing from diff; 1-1 done in same change | false | sprint sync to `review` happens at the present step; the spec is kept out of the diff on purpose; the user asked to mark 1-1 done |
| 18 | edge | Tapping an example overwrites a typed draft | false | frozen intent: tapping "puts its text in the field"; sending on tap arrives with Story 1.6 |

## Design Notes

```yaml
texts:
  privacy-notice: {th: "...", en: "..."}
example-questions:
  - {id: visa-fee, th: "...", en: "..."}
```

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass
- `uv run uvicorn app.main:app` + `curl http://127.0.0.1:8000/api/texts` -- expected: JSON with Thai and the adviser contact

**Manual checks:**
- Page at 360 px width in a browser's device mode: no horizontal scroll, buttons easy to tap.
