---
title: 'Story 4.3: README for running and following the app'
type: 'feature'
created: '2026-11-16'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The examiner must be able to run and follow the app from the README alone (NFR2, Story 4.3). The README has been updated story by story, but it still lacks parts the story asks for: the example questions have no English translation, the eight `PRICE_*` settings share one row instead of each being listed with what it does, the phone instructions do not say how to find the machine's address, there is no cost per question, and the status section is dated part 1 and leaves out Epic 5.

**Approach:** Complete the Norwegian README, without restructuring it: an English column for the four example questions; one row per `.env.example` setting (each `PRICE_*` with its default and use); copy commands for `.env` in PowerShell and Bash; a phone step with the full command, how to find the IP address on Windows and macOS/Linux, and the firewall prompt; an estimated cost per question in the cost-log section, marked as an estimate from the prices until a real run is logged; and a current status section that includes Epic 5. A pytest keeps it true: every setting in `.env.example` and every example question (Thai, English and Norwegian) must appear in the README. The clean-machine check by a group member stays a manual step for the user; in this session a fresh clone is run in demo mode as the closest substitute, and own-key mode is left to the user.

</frozen-after-approval>

## Implementation Notes

- README (Norwegian), no restructuring: status section dated 2026-11-16 with Story 4.3 and Epic 5 added and a note that stories wait on the manual tests; an English column in the example-question table (taken from `content/texts.yaml` `example-questions`) and a pointer to "Show English"; a new subsection "Åpne siden fra en mobil på samme Wi-Fi" with the `--host 0.0.0.0` command, how to find the IP (PowerShell `ipconfig`, macOS `ipconfig getifaddr en0`, Linux `hostname -I`), the Windows firewall prompt and what to check when it fails; the `.env` copy commands for both shells, a note that a `$env:MOCK_LLM` left from demo mode overrides `.env`, and that the demo label must not show; one settings row per `PRICE_*` with its default from `.env.example` and its use; "Kostnad per spørsmål (anslag)" in the cost-log section, from the earlier estimate in `.logs/wannapas/980-…-ollama.md` (first question ~0.15–0.20 USD, then ~0.05), marked as not measured; `prompt_versions` examples updated to classifier version 3.
- New `tests/test_readme.py` (24 tests): every setting in `.env.example` has its own filled row in the settings table; the example-question table lists exactly the questions in `content/texts.yaml`, in order, with the stored English and a Norwegian cell; the phone command, `uv run pytest` and the cost-log section are present.
- Clean-machine substitute: a fresh `git clone` into the session scratchpad, `uv sync`, `MOCK_LLM=true uv run uvicorn app.main:app` (port 8765). `GET /` 200, `/api/texts` `demo_mode: true` with 4 examples, the visa-fee example streamed `meta`/`text`/`sources`/`done` with `embassy-online-registration` and `udi-fees`, and `/api/translate` gave the stored English. Own-key mode and a real clean machine remain the user's manual check (story AC 3). Note: Thai sent with `curl` on the Git Bash command line arrives mangled on Windows; a UTF-8 file body works.
- After review: the phone step gives demo mode for both shells; IP hints (`en1`, pick `192.168.`/`10.`); firewall advice for a public network or an earlier "no", and the macOS prompt; the "Show English" pointer leads with the visible Thai label and links to the section; the cost estimate no longer quotes Ollama's token count as Claude's and mentions the translate calls; status bullets link to their sections; MT-18 (the README on a clean machine) added to `manual-test-plan.md` with a results row, so the open check is tracked there; `tests/test_readme.py` checks each `PRICE_*` default against `.env.example` and the new commands (now 33 tests). `sprint-status.yaml` `last_updated` corrected to the real clock (earlier edits in this session wrote made-up times such as `11-17-2026 00:25`).

## Review Triage Log

One blind review (edge-case and verification-gap layers are not part of the one-shot route).

| # | Finding | Verdict | Route | Evidence |
|---|---------|---------|-------|----------|
| 1 | The phone step drops demo mode for Bash users | medium | patch | Bash demo mode is set inline, so `uv run uvicorn app.main:app --host 0.0.0.0` alone gives the error text without `.env`. Both forms now shown. |
| 2 | The cost estimate quotes Ollama's 24,600-token count as if it were Claude's, and leaves out translate calls | low | patch | The figure comes from `spec-ollama-provider.md`; the README now says so and calls the numbers rough. |
| 3 | The "Show English" line uses a label the examiner never sees | low | patch | The visible button text is Thai; it now leads with it and links to the section. |
| 4 | The README test does not check the `PRICE_*` defaults against `.env.example` | low | patch | A price change in `.env.example` alone would leave the README stale; one test per price added. |
| 5 | The README test only checks `.env.example` → README, not the reverse or `app/config.py` | low | reject | `tests/test_config.py` already ties settings to `.env.example`; a reverse README check adds parsing for a rare case. |
| 6 | The general README test asserts things that are always true | low | patch | Replaced with checks for both shells' commands, the copy commands and the IP commands. |
| 7 | Firewall advice misses a public network or an earlier "no", and macOS | low | patch | The common reasons a phone cannot load the page; one sentence added. |
| 8 | `ipconfig getifaddr en0` and `hostname -I` can give the wrong address | low | patch | Hint added (`en1`, pick `192.168.`/`10.`). |
| 9 | The status section presents 4.3 as delivered | false | reject | Its first paragraph says every story waits on the manual tests; the sprint status becomes `review` at commit. |
| 10 | The open clean-machine check is not tracked anywhere | low | patch | Added as MT-18 in the manual test plan and as an open item in the session log. |
| 11 | `last_updated` in the sprint status disagrees with the dates elsewhere | medium | patch | Real: the session wrote made-up times (`11-17-2026 00:25`); corrected to the clock. |
| 12 | Section references in the status list are plain text | low | patch | Now anchor links. |
