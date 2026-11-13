---
title: 'Story 1.3: Knowledge base of official sources'
type: 'feature'
created: '2026-11-13'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'd758ccd60f5d5af1b4dfa215ab630c136fee56ec'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Answers must come only from official pages the adviser has reviewed, but the knowledge base is empty and nothing loads or checks it.

**Approach:** Add `knowledge-base/sources.yaml` (15 official sources) with committed Markdown snapshots, `scripts/ingest.py` to fetch HTML, PDF and DOCX sources into snapshots offline, and a `KnowledgeBase` port with a file adapter that validates everything at startup so the app refuses to start on a missing or bad snapshot.

## Boundaries & Constraints

**Always:** sources come only from the four official publishers, each tied to its domains (UDI → `udi.no`, VFS Global → `vfsglobal.com`, Royal Norwegian Embassy in Bangkok → `norway.no`, European Commission → `europa.eu`); every source has an `https` URL and snapshot `<id>.md`; `documents()` is sorted by `id` (AD-7 cache order); the user (with the adviser) reviews the snapshot diff before it is committed; ingest prints UTF-8 safely on Windows.

**Never:** no module under `app/` fetches over the network or imports `httpx`; no runtime re-ingest; no answer, prompt or LLM work (Story 1.5); no comments in `sources.yaml` (ingest rewrites it).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid KB | sources + all snapshots | loads; documents sorted by id | N/A |
| Missing / empty snapshot | `<id>.md` absent or blank | app refuses to start | `KnowledgeBaseError` naming the id |
| Bad entry | missing/extra field, non-kebab or duplicate id, duplicate YAML key, non-https URL, unknown publisher, URL host not that publisher's domain, `file` ≠ `<id>.md`, `retrieved` not a date | refuses to start | `KnowledgeBaseError` naming the entry |
| Ingest, changed | fetched text differs from snapshot | snapshot rewritten, `retrieved` = today, printed `changed` (or `new`) | N/A |
| Ingest, unchanged | same text | nothing written, `retrieved` kept, printed `unchanged` | N/A |
| Ingest, fetch fails | HTTP error, timeout, unsupported type, empty text | old snapshot and `retrieved` kept, printed `FAILED <reason>` | exit code 1 after all sources run |

**Decisions (user, 2026-11-13, during review):** no VFS Global source for now: VFS blocks the ingest client (HTTP 403) and its PDF stated an outdated fee (EUR 80 vs EUR 90), and the current VFS page could not be captured from the browser. UDI's fees page replaces it as source 15. VFS Global stays an allowed publisher so a VFS source can be added later.

</frozen-after-approval>

## Code Map

- `app/adapters/file_content.py` -- pattern to copy: error class, `_UniqueKeyLoader` (duplicate keys), `_KEBAB_CASE`, `MappingProxyType`/tuple immutability. Do not change its behaviour.
- `app/ports/content.py` -- port style (frozen dataclasses + `Protocol`).
- `app/main.py` -- `create_app`: add `app.state.knowledge_base = load_knowledge_base(ROOT / "knowledge-base")` next to content loading; update docstring.
- `tests/conftest.py`, `tests/test_content.py` -- fixture and `tmp_path` loader-test patterns.
- `tests/test_layout.py` -- checks folders only; `knowledge-base/.gitkeep` and `scripts/.gitkeep` can go.
- `pyproject.toml` -- httpx, markdownify, pypdf already direct deps; `beautifulsoup4` (4.15) only transitive via markdownify → add `beautifulsoup4~=4.15.0` as direct dep, `uv lock`.
- `pytest` `pythonpath = ["."]` → tests can `import scripts.ingest`; the script itself must put `ROOT` on `sys.path` before importing `app.*` (run as `uv run python scripts/ingest.py`).

## Tasks & Acceptance

**Execution:**
- [x] `app/ports/knowledge_base.py` -- `Source(id, title, url, publisher, retrieved: date, text)` frozen dataclass; `KnowledgeBase` Protocol: `documents() -> Sequence[Source]` (sorted by id), `source(id) -> Source` (KeyError if unknown) -- port Story 1.5/1.6 build on.
- [x] `app/adapters/file_knowledge_base.py` -- `KnowledgeBaseError`; `PUBLISHER_DOMAINS`; `SourceEntry`; `load_sources(path) -> list[SourceEntry]` (YAML checks only, shared with ingest); `load_knowledge_base(dir) -> FileKnowledgeBase` (sources + snapshots, UTF-8) -- startup gate.
- [x] `app/main.py` -- wire loader.
- [x] `scripts/ingest.py` -- `run(kb_dir, client, today, out) -> int` + `main()`; httpx client (follow redirects, 30 s timeout, UA `Mozilla/5.0 (compatible; norway-visa-guide-ingest)`); type from Content-Type, fallback URL suffix; HTML: bs4, `<main>` else `<body>`, drop script/style/nav/header/footer/form/noscript/svg, relative links made absolute, markdownify ATX headings; PDF: pypdf text per page; DOCX: stdlib `zipfile` + `ElementTree` paragraphs, drop checkbox-only paragraphs; collapse 3+ blank lines; per-source status line with snapshot size, then total characters; rewrite `sources.yaml` with `safe_dump(sort_keys=False, allow_unicode=True)` only if a date changed.
- [x] `knowledge-base/sources.yaml` + 15 snapshots -- generated by running ingest on the list in Design Notes.
- [x] `tests/test_knowledge_base.py` -- every loader matrix row; committed KB loads with 10–20 sources, every publisher except VFS Global present, required topics mentioned; no `.py` under `app/` imports `httpx`, `requests` or `urllib.request`.
- [x] `tests/test_ingest.py` -- `httpx.MockTransport`: HTML main extraction + absolute links, DOCX (built in test with `zipfile`), PDF dispatch (pypdf may be monkeypatched), changed/new/unchanged/failed rows, exit code.

**Acceptance Criteria:**
- Given the committed `sources.yaml`, when I read it, then together the sources cover application steps, documents per visit purpose, sponsorship form, invitation letter, relationship proof and the visa fee.
- Given `uv run python scripts/ingest.py`, when it finishes, then it lists each source as new/changed/unchanged/FAILED so the diff can be reviewed before commit.
- Given `uv run uvicorn app.main:app`, when it starts, then the knowledge base is loaded from disk with no network access.

## Design Notes

Ingest is built now, not deferred: all 15 sources fetched with a plain client in planning (2026-11-13), so it is faster than hand-made snapshots. `retrieved` changes only when the text changes, so a source's version is the date its content was captured and the diff shows only real changes.

All URLs `https://`; `…` = `www.norway.no/en/thailand/services-info/visitors-visa-res-permit`. Titles: each page's own English title.

| id | URL (shortened) | covers |
|---|---|---|
| embassy-necessary-documents | …/visitors-visa/necessary-doc | checklists |
| embassy-visitor-visa-checklist | www.norway.no/contentassets/f0130372be264373abd19a30d9709485/xx-old-unused/thailand_document-checklist-schengen-visa_m24.docx (the live link on the page above) | documents per purpose, sponsorship, relationship proof |
| embassy-online-registration | …/visitors-visa/online-reg | steps, fee EUR 90 |
| embassy-hand-in-documents | …/visitors-visa/hand-in-doc | VFS appointment |
| embassy-processing-time | …/visitors-visa/processing-time | waiting time |
| embassy-visa-faq | …/frequently-asked-questions/ | FAQ |
| udi-how-to-apply-visitor-visa | www.udi.no/en/answer-pages/frequently-asked-questions-about-visitor-visa/how-do-i-apply-for-a-visitor-visa/ | steps |
| udi-visit-family-how-to-apply | www.udi.no/en/want-to-apply/visit-and-holiday/visitors-visa-to-norway/visit-family/how-to-apply-for-a-visitors-visa/ | family visit |
| udi-sponsor-for-visitors | www.udi.no/en/word-definitions/sponsor-for-visitors/ | sponsorship |
| udi-what-it-means-to-be-a-sponsor | www.udi.no/en/answer-pages/frequently-asked-questions-about-visitor-visa/what-does-it-mean-to-be-a-sponsor/ | sponsorship |
| udi-invitation-for-visitor-visa | www.udi.no/en/word-definitions/invitation-for-a-visitors-visa-/ | invitation letter |
| udi-sponsorship-form | www.udi.no/globalassets/global/skjemaer/sponsorskjema-bm-og-eng.pdf | the form |
| udi-waiting-time-visitor-visa | www.udi.no/en/waiting-time/visitor-visa/ | waiting time |
| udi-fees | www.udi.no/en/word-definitions/fees/ | visa fee EUR 90 / 45, exemptions |
| eu-applying-for-schengen-visa | home-affairs.ec.europa.eu/policies/schengen/visa-policy/applying-schengen-visa_en | Schengen rules |

## Verification

**Commands:**
- `uv run python scripts/ingest.py` -- expected: 15 sources, none FAILED; total size printed
- `uv run pytest` -- expected: all pass
- `uv run python -c "from app.main import app; print(len(app.state.knowledge_base.documents()))"` -- expected: 15

**Manual checks:**
- Skim each snapshot: main content, no menus/cookie banners; user and adviser review the diff before commit.

## Implementation Notes

- 2026-11-13: `vfs-thailand-visitor-visa-info` returns HTTP 403 from Cloudflare (`{"code": "403201"}`) to the ingest client on this network, so it has no snapshot and the app refuses to start until it does. Not worked around (no browser-UA spoofing). Its `title` is provisional (from the file name) until the PDF has been read.
- Embassy page URLs use the spec's form without a trailing slash; both forms return 200 with no redirect.
- HTML clean-up also drops `hr`, icon-font ligature elements (`material-symbols*`/`material-icons*`), buttons without `aria-controls` ("To top", "Print") and empty headings. Accordion titles (`button[aria-controls]`) and `aria-hidden` collapsed sections are kept: the embassy FAQ lives in them.
- Known noise: UDI pages include an "Important messages" news item, so they may show `changed` when UDI posts news.
- 2026-11-13: VFS snapshot resolved: plain curl got 200 but httpx still got 403, so the user saved the PDF from their browser and it was converted with `scripts/ingest.py`'s own `pdf_to_text` + `tidy` (same bytes as fetched in planning, 439,789). Title set to the document's heading. Ingest will keep reporting this source as `FAILED HTTP 403` (exit 1) while Cloudflare blocks it; the snapshot is kept.
- Content conflict for adviser review: the VFS PDF says visa fee EUR 80 (EUR 40 for ages 6–11) and processing time 15 days; the embassy pages say EUR 90. Both are in the knowledge base.
- `uv run pytest`: 159 passed; app loads 15 sources.

- Review patches (2026-11-13, by the implementing subagent): invalid calendar date → `KnowledgeBaseError`; unreadable old snapshot fails only that source; `sources.yaml` written in a `finally` so an aborted run keeps dates in step with rewritten snapshots; redirects must land on the publisher's domain (shared `on_domain` helper in the loader); tests for real two-page PDF text, `<base href>`/`<img>`, DOCX tab/break, committed-KB topic coverage. Loader tests no longer import `app.main` at module level.
- 2026-11-13: VFS PDF replaced by `udi-fees` (user decision, see frozen block). The current VFS page is a JavaScript app; browser "HTML only" saves gave an empty shell and a print-to-PDF captured UDI's page as drawings, so no VFS capture was possible. Ingest: 15 sources, 0 failed, 98,374 characters. `uv run pytest`: 171 passed; app loads 15 sources.

## Spec Change Log

- 2026-11-13, review finding "sources disagree on the visa fee" (blind): the VFS PDF said EUR 80, the embassy EUR 90. Amended: Design Notes source table (VFS PDF → `udi-fees`) and the committed-KB test task (VFS Global no longer required), after the user's decision recorded in the frozen block. Known-bad state avoided: the bot quoting an outdated fee. Handled as a data amendment, not a code loopback: the code does not depend on which sources are listed, so it was not reverted. KEEP: all code and tests as patched in review; only `sources.yaml`, the snapshot set and the publisher assertion changed.

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | blind | Sources disagree on the visa fee (VFS PDF EUR 80 vs EUR 90) | high | confirmed by grep. data amendment after user decision: VFS PDF → `udi-fees` (see change log) |
| 2 | blind | Sources disagree on photo age (6 vs 3 months) | medium | confirmed; the embassy FAQ itself says both. Not a code fix: adviser decides; open item in session log |
| 3 | blind | Checklist URL path "xx-old-unused" may be stale | maybe-false | it is the live link on the embassy's necessary-documents page; adviser confirms it is current. open item |
| 4 | blind | No VFS booking page source for the "book at VFS" step | medium | real; VFS pages block the ingest client and could not be captured. defer: deferred-work entry |
| 5 | blind | Snapshots contain non-source / volatile links (UDI login URL) | false | a second ingest run reported all unchanged, so the URL is stable; only cited sources from `sources.yaml` are ever shown (AD-7/AD-9), never snapshot links. rejected |
| 6 | blind, edge | Ingest does not check where a redirect lands | medium | `follow_redirects=True`, no host check. patch: final host must be on the publisher's domain |
| 7 | blind, edge, verif | Aborted run leaves rewritten snapshots with stale dates | medium | writes happen in the loop, YAML after it. patch: write `sources.yaml` in `finally` |
| 8 | blind | DOCX/PDF converters drop links and heading structure; form PDF has Norwegian text | low | the sponsorship form is its own source, so its link is not lost; cosmetic for the model. rejected |
| 9 | blind | Accordion headings come out as list-item links | low | cosmetic; text and order kept. rejected |
| 10 | blind, verif | Tests miss real PDF text, `<base>`/`<img>`, DOCX tab/br | medium | pre-verified gaps (verif). patch: tests added |
| 11 | blind | No test that the KB covers the required topics | medium | `test_committed_knowledge_base_loads` checked counts only. patch: keyword coverage test |
| 12 | blind | `norway.no` covers every Norwegian embassy | low | real, but sources are reviewed by the adviser and the fix adds path rules. rejected |
| 13 | blind | Epic context Stack line omits beautifulsoup4 | low | cosmetic; `pyproject.toml` is the source of truth. rejected |
| 14 | blind | Ingest-only packages installed with the app | low | the architecture's stack lists them as dependencies; the fix contradicts the approved spec. rejected |
| 15 | blind | No run instructions for ingest outside the docstring | low | README is Story 4.3, next in the build order. rejected |
| 16 | blind | Spec and `docs/VFS data/` untracked; provenance lost | false | the spec is committed with the story; provenance of the (now removed) VFS snapshot is in Implementation Notes; `docs/VFS data/` holds personal metadata and is not committed. rejected |
| 17 | edge | Impossible calendar date escapes as raw `ValueError` | medium | reproduced: `yaml.safe_load('2026-02-30')` → ValueError. patch: caught as `KnowledgeBaseError` |
| 18 | edge | Ingest catches only `KnowledgeBaseError` from `load_sources` | medium | same root cause as #17; fixed by the same patch |
| 19 | edge, verif | Old-snapshot read outside the per-source try aborts the run | medium | `_read_snapshot` ran before `try`, caught only `FileNotFoundError`. patch: read inside per-source handling |
| 20 | edge | DOCX text boxes / AlternateContent could duplicate text | low | no duplicate lines in the committed checklist snapshot; fix adds branches. rejected |
| 21 | edge | `<header>`/`<footer>` inside `<main>` dropped | low | checked: the only case (embassy FAQ) loses just the H1 title and date, and the title is in `sources.yaml`. rejected |
| 22 | edge | Rewriting `sources.yaml` deletes adviser comments | false | frozen Never: no comments in `sources.yaml`. rejected |
| 23 | edge | Network-import guard misses `urllib`, `http.client`, `socket` | low | unlikely in this codebase; fix needs allow-listing `urllib.parse`. rejected |
| 24 | edge | Epic context lost the env-var list | low | names live in `app/config.py` and `.env.example`. rejected |
| 25 | edge | Epic context lost the dependency-direction rule | low | rule is in the architecture spine; Story 1.5 adds the import-rule test (deferred-work). rejected |
| 26 | verif | Nothing reads `app.state.knowledge_base` yet | false | by design: Story 1.5 is the consumer; loading is tested at startup. rejected |
