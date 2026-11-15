# Manual Test Plan: Norway Visa Guide For Thai

This plan lists the checks that the automated tests cannot do, and records when they were run. It collects the manual checks from the story specs (`spec-*.md` in this folder) in one place.

## What the automated tests cover, and what they do not

`uv run pytest` runs on every push (see the [CI workflow](../../.github/workflows/ci.yml)). The tests use a fake Claude client, so they never call the API. They cover the server: the privacy filter, the answer pipeline and its event stream, the API endpoints, the request log and costs, demo mode, loading the texts, knowledge base and prompt, and the layer rules.

They do not cover:

- **The page in a browser.** No test runs `app/static/app.js`; `tests/test_static.py` only checks its source text. A browser-level test (Playwright) is deferred until after part 1 ([deferred-work.md](deferred-work.md)).
- **The real Claude API.** Answers in Thai, cited sources and prompt caching only happen with a real key, which costs money.
- **Real phones**, and Facebook's in-app browser in particular.

## Setup

| Mode | How to start | Used for |
|---|---|---|
| Demo | `MOCK_LLM=true`, no key (see the [README](../../README.md#kjør-i-demomodus-uten-api-nøkkel)) | MT-01, MT-02 |
| No key | `MOCK_LLM=false`, `ANTHROPIC_API_KEY` empty | MT-03, MT-07 (error turn) |
| Real key | `.env` with `ANTHROPIC_API_KEY`, `MOCK_LLM=false` | MT-04 to MT-09 |

Start the app with `uv run uvicorn app.main:app` and open <http://127.0.0.1:8000>. For the narrow-screen checks, use the browser's device mode (F12, then Ctrl+Shift+M) and set the width to 360 px and then 320 px (NFR1: works from 360 px, no horizontal scrolling down to 320 px).

A run with a real key costs a few cents per question. Each question adds a line to `data/requests.jsonl`.

## Test cases

Each case says which story or requirement it checks. "Pass" means every expected point holds.

### MT-01 Demo mode (Story 4.2)

Mode: demo, 360 px.

1. Open the page.
2. Tap each of the four example questions.
3. Type a question that is not an example, e.g. `วีซ่าทำงานต้องทำอย่างไร` (how do I get a work visa?).
4. Scroll down the conversation.

Expected: the demo label (โหมดสาธิต) is shown; each example gives a Thai answer that arrives in parts, with source links; the other question gives the fixed "demo only" text with the adviser contact; the label stays visible while scrolling.

### MT-02 Layout at 360 and 320 px (Story 1.2, Story 1.4, NFR1)

Mode: demo (no key needed).

1. Open the page at 360 px, then at 320 px.
2. Read the whole privacy notice and the example questions.
3. Tap an example question and wait for the answer.

Expected: no horizontal scroll at either width; the privacy notice wraps; the example buttons and the send button are large enough to tap easily; long source links wrap instead of widening the page.

### MT-03 No API key (Story 1.6)

Mode: no key.

1. Open the page and tap an example question.

Expected: the page shows the fixed Thai error text with the adviser contact; the question is put back in the input field so it can be sent again, and the buttons work again.

### MT-04 Streamed answer with sources (Story 1.5, Story 1.6)

Mode: real key, 360 px and 320 px.

1. Tap an example question, e.g. the one about documents.
2. Click each source link under the answer.

Expected: typing dots appear first; the Thai answer arrives in parts, not all at once; at least one source link is shown under the answer; each link opens the official page (UDI, the embassy, or the EU); no horizontal scroll.

### MT-05 Privacy filter on the page (Story 1.4)

Mode: real key.

1. Type a question with a made-up passport number and Thai ID number, e.g. `เลขพาสปอร์ต AA1234567 และเลขบัตร 1-2345-67890-12-1 ต้องใช้เอกสารอะไรบ้าง` (my passport number is … and ID number is …, which documents do I need?).
2. Reload the page.

Expected: a reminder above the answer says the numbers were removed before sending; the answer is a normal answer; after the reload the stored question shows `[removed]` in place of both numbers. Phone numbers, names, addresses and emails are not removed (by design; the privacy notice says so).

### MT-06 No answer in the sources

Mode: real key.

1. Ask something the knowledge base does not cover, e.g. `พรุ่งนี้ที่ออสโลฝนจะตกไหม` (will it rain in Oslo tomorrow?).

Expected: the fixed "we have no answer" text with the adviser contact, and no source links.

### MT-07 Follow-up questions and the stored conversation (Story 1.7)

Mode: real key for steps 1–4, no key for step 5.

1. Tap the example about how to start.
2. Ask a follow-up that only makes sense with the earlier answer, e.g. `แล้วค่าธรรมเนียมเท่าไร` (and how much is the fee?).
3. Reload the page.
4. Close the tab, open a new tab and open the page again.
5. Restart without a key, ask a question (you get the error text), then reload.

Expected: (2) the follow-up is answered in the context of the first answer; (3) after the reload the whole conversation is back, with its source links, scrolled to the newest exchange; (4) a new tab starts empty; (5) after the reload the failed turn is not in the conversation.

### MT-08 Request log and prompt cache (Story 1.8)

Mode: real key.

1. Ask two questions within five minutes.
2. Open `data/requests.jsonl` and read the last two lines.

Expected: each line has `outcome`, `model`, token counts and `cost_usd`, and no question or answer text; the first line has `cache_write_tokens` > 0; the second has `cache_read_tokens` > 0 and a lower `cost_usd`. (The total-cost command is in the [README](../../README.md#forespørselslogg-kostnad-og-cache).)

### MT-09 Real phone in Facebook's in-app browser (Story 1.6, NFR1)

Mode: real key, on a real Android phone or iPhone.

1. Start the app with `uv run uvicorn app.main:app --host 0.0.0.0`, with the phone on the same Wi-Fi network as the computer.
2. Send yourself the link `http://<computer's IP>:8000` in Messenger, and open it from there so it opens in Facebook's in-app browser.
3. Tap an example question.

Expected: the page loads in Thai; the answer arrives in parts (not all at once after a long wait); source links work; no horizontal scroll. If the answer stops halfway, note how long it ran: this decides the deferred heartbeat/timeout work in [deferred-work.md](deferred-work.md).

## Results

Add one row per run. A failed check gets a line in `.logs/<user>/issues.md`.

| Date | Case | Tester | Device / browser | Result | Notes |
|---|---|---|---|---|---|
| 2026-11-15 | MT-01 | Wannapa Sikveland | Desktop browser, device mode 360 px | Pass | All four examples, other question, demo label |
| | MT-02 | | | Not run | |
| | MT-03 | | | Not run | |
| | MT-04 | | | Not run | Needs a real key |
| | MT-05 | | | Not run | Needs a real key |
| | MT-06 | | | Not run | Needs a real key |
| | MT-07 | | | Not run | Needs a real key |
| | MT-08 | | | Not run | Needs a real key |
| | MT-09 | | | Not run | Needs a real key and a phone |
