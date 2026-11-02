---
title: 'Reconcile: architecture spine vs. its inputs'
spine: docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md
memlog: docs/planning/architecture/architecture-G94-sikveland-2026-11-02/.memlog.md
inputs:
  - docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md
  - docs/planning/prds/prd-G94-sikveland-2026-10-19/addendum.md
  - docs/planning/implementation-plan.md
  - docs/planning/product-brief.md
date: '2026-11-02'
---

# Reconcile: architecture spine vs. inputs

**Test used:** a requirement belongs in the spine only if two independently built units (for example page and server, mock and real adapter, endpoint and stats script, test set and eval script) could diverge on it. Purely behavioural detail the PRD already states is marked **ok, PRD-owned**.

**Verdict:** The spine covers the PRD's FR/NFR set well. Pipeline order, personal-information filter, closed categories, fixed-content rule, citations, stream contract, knowledge-base versioning, feedback storage, checklist IDs, prompt versioning and test layers all land. There are five real gaps, plus one internal contradiction (AD-7 vs AD-8). Most of the gaps are in **demo mode** (FR10), which the spine treats as only "mock with stored answers".

## Real gaps (fix in spine)

| # | Gap | Units that could diverge | Input |
| --- | --- | --- | --- |
| G1 | **Demo-mode contract is undefined.** The spine does not say how the mock recognises an example question (by content key/ID sent from the page, or by exact Thai text after filtering), what it returns for the classify call, or what a **non-example question** gets. FR10 requires a Thai "demo mode only answers the example questions" message. That text is not in AD-6's list, and no category or `meta` value is defined for it, because AD-5's closed set has no slot. The spine also leaves out what the memlog decided about **English translation in demo mode**: stored translations, looked up by what key, given that `/api/translate` receives answer text. It also does not say whether translating fixed replies (embassy-decides etc.) works in demo mode. Finally, the same mock also serves CI (AD-2/AD-13), and pytest needs every category and zero-citation path, so the spine must say whether the mock is fixture-scriptable in addition to `demo-answers.yaml`. | mock adapter, pipeline, page, `content/demo-answers.yaml`, tests | PRD FR10, FR7; addendum "Demo mode"; memlog line 19 |
| G2 | **The page cannot learn that demo mode is on.** FR10 requires a visible "Demo mode" label. The page holds no config, and no endpoint (`/api/texts` or other) exposes a `demo_mode` flag. | web, page | PRD FR10 |
| G3 | **The no-answer replacement clashes with streaming (internal contradiction AD-7 vs AD-8).** AD-7 replaces an answer with zero citations by the fixed no-answer reply. AD-8 streams `text` deltas as they arrive. Whether an answer has citations is only known once the model is done, so by then the uncited text has already reached the browser. The spine needs one rule: either buffer until the first citation or the end, or add a `replace`/`reset` event that the page and both adapters implement. | answer step, web, page, both LLM adapters | PRD FR2, FR4; spine AD-7, AD-8 |
| G4 | **The `conversation_id` lifecycle is not fixed.** The spine says the browser makes a UUID v4 but not when it is created, where it is kept (sessionStorage like the conversation?), or whether it is replaced after "Yes" ends the conversation (PRD glossary). SM-1 ("first answer per `conversation_id`") is only correct if page and `feedback_stats.py` agree on this. The encoding of `answer` (`yes`/`no` text vs boolean) is also not fixed (the memlog says yes/no; the spine column has no type). | page, `/api/feedback`, `scripts/feedback_stats.py` | PRD FR5, glossary "Conversation", SM-1 |
| G5 | **The checklist response shape and source links are open.** AD-11 gives each item a source `id`, but `GET /api/checklists/{purpose}` does not say whether it returns the source resolved to `{id, title, url}` (as AD-8 does for answers). The page has no other route to `sources.yaml`. FR6 also needs the family checklist to link to "where the sponsor finds" the sponsorship form and invitation letter. If that page is not a knowledge-base source, the item has nothing to point at. Either require it in `sources.yaml` or allow a plain `url` on an item. | content/checklists.yaml, web, page | PRD FR6 bullets 5–6; FR11 coverage list |

## Minor gaps (worth one line each, not blocking)

- **Request bodies for `/api/chat` and `/api/translate`.** AD-8 fixes the response but not the request: the history turn format (roles, whether fixed replies and sources are included, any length cap) and translate input/output (the memlog says the client sends the answer text; JSON, not streamed). Page and server are two units.
- **Source version is not visible downstream (FR11 "traced to a specific version").** The `sources` event carries `{id, title, url}` but not `retrieved`. AD-12 makes eval reports record prompt versions but not knowledge-base version (git commit or `retrieved` dates). NFR4 reruns are triggered by source changes, so reports should record both.
- **Cost (NFR6).** The per-request log line has a `cost` field, but the spine does not say where token prices live (Opus 5.5 $4/$20 per M, cached-read rate), which matters because `MODEL` is configurable. It also does not say how per-request lines are combined into the README figure: by `run_eval.py` or a script. One line naming the price source and the reporter is enough.
- **`eval/testset.yaml` schema.** The adviser writes the test set and `run_eval.py` reads it (implementation-plan "Open tasks"). The fields are not fixed. They should include the Thai question, English translation (brief), expected facts, expected source `id`s from `sources.yaml`, expected category, and a place for the adviser's correct/incorrect judgement (NFR4 "as judged by the adviser").
- **Adviser review of Thai content (NFR8).** AD-6 routes every fixed Thai text to `content/`, and AD-9 has an explicit adviser review gate for knowledge-base snapshots. `content/` (texts, checklists, demo answers, example questions) has no equivalent gate or "reviewed" marker. This is mostly process, so a sentence in AD-6 would do.
- **Facebook in-app browser (NFR1, addendum).** Visual design is correctly deferred to UX. One architecture risk is not noted: in-app browsers may keep `localStorage` separate from Chrome/Safari, or clear it, which weakens FR6 "ticks still there". This is irrelevant until hosting (also deferred) but belongs in the Deferred hosting bullet.
- **README example-question translations.** The addendum and brief want the README to list the example questions in English and Norwegian. The Thai originals live in `content/`, so the two lists can drift. This is low risk.

## Per input

### PRD (prd.md)

| Item | Status |
| --- | --- |
| FR1 Thai Q&A, follow-ups | Covered (AD-1, AD-3, AD-8). Typo/mixed-language handling: ok, PRD-owned (NFR4 eval). Whether the classifier also sees history: ok, pipeline-internal. |
| FR2 sources | Covered (AD-7, AD-8). "No facts not in sources" beyond the zero-citation check: ok, PRD-owned (eval). See G3. |
| FR3 embassy decides | Covered (AD-5, AD-6). |
| FR4 no answer | Covered (AD-7), but see G3. |
| FR5 feedback | Mostly covered (AD-5 `done`, AD-6, AD-10). Gap G4. Whether the "No" follow-up comes from the page via `/api/texts` or from the server: ok, UX/PRD-owned, since AD-6 says the text is a content file either way. |
| FR6 checklist | Covered (AD-11) except G5. "Ticks on unchanged items kept" is covered by stable IDs. "UDI's checklist is the authority": ok, PRD-owned. How the chat leads to the checklist (UJ-1 step 3): ok, UX-owned as long as it is a UI control and not a model output. If the chat answer should open it, that needs a new AD-5 category. |
| FR7 translation | Covered in real mode (AD-2, AD-4, `/api/translate`). Demo-mode translation missing (G1). |
| FR8 example questions | Covered (AD-6, `/api/texts`). Linking them to stored demo answers is in G1. |
| FR9 privacy | Covered (AD-1, AD-4). **Privacy notice saying questions go to an AI service** is covered as a content text (AD-6 lists "the privacy notice"). Its wording: ok, PRD-owned. |
| FR10 demo mode | **Gaps G1, G2.** Non-example message, visible label and demo translations are missing. |
| FR11 knowledge base | Covered (AD-9). Official-publisher restriction: ok, PRD-owned. Version traceability downstream: minor gap. |
| FR12 steps in order | Covered via knowledge base and prompt (AD-7, AD-12). Order: ok, PRD-owned (eval). |
| FR13 / FR14 | Covered (AD-5 `reach_person`, `out_of_scope`; AD-6). |
| NFR1 mobile / Facebook | Deferred to UX, correctly. Storage risk not noted (minor). |
| NFR2 easy to run | `.env.example` covered (Config convention). README: ok, PRD-owned. It is not in the source tree, which is harmless. |
| NFR3 safe tests | Covered (AD-2, AD-13). |
| NFR4 answer quality | Covered (AD-13). Test-set schema and adviser judgement field: minor gap. |
| NFR5 privacy | Covered (AD-3, AD-4, AD-10, Logging convention). "No secrets/real enquiries in repo": ok, PRD-owned (`.env` gitignore is implicit). |
| NFR6 cost | Partly covered (Logging convention, AD-12). Price source and README report: minor gap. |
| NFR7 prompts | Covered (AD-12). |
| NFR8 adviser review | Partly covered (AD-6 intent, AD-9 gate for knowledge base). No gate for `content/` (minor). |
| SM-1 | Covered (AD-10, `feedback_stats.py`), but its correctness depends on G4. |
| SM-2 | Covered (AD-13). |
| SM-C1 | Ok, PRD-owned. The adviser counts emails by hand, so nothing is built. |

### Addendum (addendum.md)

| Item | Status |
| --- | --- |
| Checklist stable IDs, localStorage, no server storage | Covered (AD-11). |
| Facebook in-app browser | Deferred (see minor gap). |
| Stack, model in config | Covered (Stack, Config). |
| Whole knowledge base + caching + Citations, no vector DB | Covered (AD-7). |
| Classifier with 3 categories | Spine has 5. This is a deliberate extension explained in memlog lines 18 and 25 (`done`, `reach_person`), so not a contradiction. |
| Pattern filter before AI; reminder "added to the answer" | Covered (AD-4). The spine delivers the reminder as a `meta` flag that the page renders, not text in the answer. The addendum left the mechanism to architecture, so this is consistent. |
| `ADVISER_CONTACT` from config | Covered (AD-6, Config). |
| Two test layers | Covered (AD-13). |
| Demo mode `eval/demo-answers.yaml` with Thai answer, sources, English translation | **Path contradiction** (see below). Translation content is missing from the spine (G1). |
| Cost $4/$20, measured, reported in README | Minor gap (price source, report). |
| README with `.env.example`, example questions in EN/NO | `.env.example` covered. README: ok, PRD-owned (minor drift note). |
| Knowledge-base storage, one source list | Covered (AD-9). |
| UX sample dialogue | Ok, PRD/UX-owned. |

### Implementation plan (implementation-plan.md)

| Item | Status |
| --- | --- |
| Stack, model via env, retrieval approach | Covered. |
| Classifier incl. "contains personal data" category | Replaced by the pattern filter (AD-4) and 5 categories. The PRD addendum superseded the plan here and the memlog records it. Not a contradiction. |
| Demo mode = mock with stored answers; tests never call API | Covered (AD-2), but see G1 on one mock serving demo and tests. |
| EN translation button; README translations | Covered / ok, PRD-owned (see G1 for demo). |
| Checklist from structured data | Covered (AD-11). The plan had 2 visit types; the spine follows the PRD's 3. Ok. |
| Repository structure | Covered and refined (layered `app/`). `content/` added. |
| Phase 2 epics: `.env.example`, GitHub Actions, ingest (HTML and PDF), streamed answer with clickable sources, privacy banner, stats script, eval, README | All have a home in the spine. Ingest PDF handling: ok, implementation detail. |
| Open tasks for domain expert (sources, test facts, Thai review) | Partly covered: AD-9 covers sources. Test-set schema and content review are minor gaps. |

### Product brief (Technology, Privacy, Knowledge Base)

| Item | Status |
| --- | --- |
| Technology: stack, model in config, caching + Citations, no search DB | Covered. |
| Cost reported in README | Minor gap (see Cost). |
| `.env.example`, demo mode, "automated tests always use the demo mode" | Covered in spirit (AD-2). Literal tension: the brief says tests use *demo mode* (stored example answers only), while pytest needs every category and failure path. G1 asks the spine to say whether the mock is fixture-driven for tests. |
| EN/NO translations in README, translation button | Ok, PRD-owned / covered (G1 for demo). |
| Privacy: notice not to share personal info; page states questions go to the model provider | Covered as content text (AD-6). Wording: PRD-owned (FR9). |
| Privacy: only feedback answer and time stored | Spine also stores `conversation_id`. That follows the PRD (FR5, NFR5), which superseded the brief, so this is not a spine contradiction. |
| No real enquiries in repo | Ok, PRD-owned (NFR5). |
| Knowledge Base: 10–20 official sources, 4 publishers, Markdown with URL/publisher/date, one list file, re-fetch script, adviser review | Covered (AD-9). Publisher list: ok, PRD-owned. |

## Contradictions

1. **Internal: AD-7 vs AD-8** (G3). Zero-citation replacement is impossible after the text has already streamed, unless a buffer or replace rule is added.
2. **Demo answers path.** The addendum puts them in `eval/demo-answers.yaml`; the spine puts them in `content/demo-answers.yaml`. The memlog does not explain the move. The spine's location fits NFR8 (fixed Thai texts reviewed with other content) and AD-6, so it is probably deliberate. Record it in the memlog so the epics do not pick up the old path.
3. **Translation in demo mode.** Memlog line 19 decides "demo mode uses stored translations", but the spine never states it. The spine has silently dropped a decision rather than contradicting it (G1).

Deliberate differences explained by the memlog or PRD, so **not** contradictions: 5 classifier categories instead of 3 (or 4 in the plan); personal-info reminder through a `meta` flag; `conversation_id` stored (PRD over brief); feedback on the done signal rather than after each answer (PRD over brief); 3 visit purposes (PRD over plan).
