# Manual Test Plan: Norway Visa Guide For Thai

This plan lists the checks that the automated tests cannot do, and records when they were run. It collects the manual checks from the story specs (`spec-*.md` in this folder) in one place.

## What the automated tests cover, and what they do not

`uv run pytest` runs on every push (see the [CI workflow](../../.github/workflows/ci.yml)). The tests use a fake model client, so they never call the Claude API or Ollama. They cover the server: the privacy filter, the answer pipeline and its event stream, the API endpoints, the request log and costs, demo mode, loading the texts, knowledge base and prompt, and the layer rules.

They do not cover:

- **The page in a browser.** No test runs `app/static/app.js`; `tests/test_static.py` only checks its source text. A browser-level test (Playwright) is deferred until after part 1 ([deferred-work.md](deferred-work.md)).
- **The real Claude API.** Answers in Thai, cited sources and prompt caching only happen with a real key, which costs money.
- **A real Ollama model** (`LLM_PROVIDER=ollama`): whether a local model answers in Thai, cites with `[[id]]` markers the adapter can read, and keeps to Thai script.
- **Real phones**, and Facebook's in-app browser in particular.

## Setup

| Mode | How to start | Used for |
|---|---|---|
| Demo | `MOCK_LLM=true`, no key (see the [README](../../README.md#kjør-i-demomodus-uten-api-nøkkel)) | MT-01, MT-02, MT-11 |
| No key | `MOCK_LLM=false`, `ANTHROPIC_API_KEY` empty | MT-03, MT-07 (error turn) |
| Real key | `.env` with `ANTHROPIC_API_KEY`, `MOCK_LLM=false` | MT-04 to MT-09 |
| Ollama | `LLM_PROVIDER=ollama`, `MOCK_LLM=false`, Ollama running with `OLLAMA_MODEL` pulled (see the [README](../../README.md#kjør-med-ollama-lokal-modell-uten-nøkkel)) | MT-10 |

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

Expected: (2) the follow-up is answered in the context of the first answer; (3) after the reload the whole conversation is back, with its source links, scrolled to the newest exchange; (4) a new tab starts with an empty new chat, and the conversation is in the saved chats; (5) after the reload the failed turn is not in the conversation.

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

### MT-10 Answers from Ollama (Ollama provider)

Mode: Ollama, 360 px. No key and no cost.

1. Tap each of the four example questions.
2. Ask the weather question from MT-06.
3. Ask a follow-up to the first answer, e.g. `แล้วค่าธรรมเนียมเท่าไร` (and how much is the fee?).
4. Open `data/requests.jsonl` and read the last lines.
5. Stop Ollama and ask a question.

Expected: (1) each answer is in Thai, arrives in parts after the typing dots, and has at least one source link; no `[[...]]` marker is ever visible, not even for a moment; the text has no Chinese characters (a native Thai reader judges the language, NFR8); (2) the fixed "we have no answer" text, no links; (3) the follow-up is answered in context and still has source links; (4) `model` is `OLLAMA_MODEL`, `prompt_versions` has `answer` and `citing`, `cost_usd` and both cache fields are 0, `unknown_source_ids` is a number; (5) the fixed error text. Answers take from a few seconds to over a minute (the model thinks first), and the first answer after starting Ollama also reads the whole knowledge base.

### MT-11 Saved chats and new chat

Mode: demo, 360 px and 320 px.

1. Tap an example question, then tap the new-chat button and tap another example question.
2. Close the tab, open a new tab and open the page again.
3. Open the saved chats and tap the first chat; ask a follow-up (type any question).
4. Reload the page.
5. Open the saved chats; delete one chat (first cancel, then confirm), then delete all.
6. Ask a question, then open the page in a second tab and open that chat there. In the first tab, delete the chat. In the second tab, ask a follow-up.
7. Open the page in a private (incognito) window and tap an example question. Then open the saved chats, and check the browser's storage (F12, Application, Local storage).

Expected: (1) the new chat starts empty with the example questions; (2) the page opens an empty new chat, and the saved chats list both, newest first, with the first question and the date; (3) the chat is shown with its source links, the follow-up is added to it and it moves to the top of the list; (4) the same chat is shown; (5) cancel changes nothing, confirm removes it (deleting the open chat leaves an empty new chat), delete all empties the list. The new-chat and saved-chats buttons cannot be tapped while an answer is arriving; nothing scrolls sideways at 320 px with the list open; the privacy notice says chats are saved on this device; (6) the follow-up is answered, and the deleted chat does not come back: the list shows a new chat with only the follow-up; (7) the answer is shown; note what is saved (the chat while the window is open, nothing after it is closed, or nothing at all if storage is blocked) and that the page does not break.

## Results

Add one row per run. A failed check gets a line in `.logs/<user>/issues.md`.

| Date | Case | Tester | Device / browser | Result | Notes |
|---|---|---|---|---|---|
| 2026-11-15 | MT-01 | Wannapa Sikveland | Desktop browser, device mode 360 px | Pass | All four examples, other question, demo label |
| 2026-11-15 | MT-02 | Wannapa Sikveland | Browser device mode, 360 and 320 px | Pass | |
| | MT-03 | | | Not run | |
| | MT-04 | | | Not run | Needs a real key |
| | MT-05 | | | Not run | Needs a real key |
| | MT-06 | | | Not run | Needs a real key |
| | MT-07 | | | Not run | Needs a real key |
| | MT-08 | | | Not run | Needs a real key |
| | MT-09 | | | Not run | Needs a real key and a phone |
| 2026-11-15 | MT-10 | Wannapa Sikveland | Browser, branch `integration`, `LLM_PROVIDER=ollama` (qwen3.5:9b) | Pass | Reported by the tester as fine; tested together with saved chats |
| 2026-11-15 | MT-11 | Wannapa Sikveland | Browser, branch `integration` | Pass | Reported by the tester as fine; tested together with Ollama |
