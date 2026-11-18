# Manual Test Plan: Norway Visa Guide For Thai

This plan lists the checks that the automated tests cannot do, and records when they were run. It collects the manual checks from the story specs (`spec-*.md` in this folder) in one place.

## What the automated tests cover, and what they do not

`uv run pytest` runs on every push (see the [CI workflow](../../.github/workflows/ci.yml)). The tests use a fake model client, so they never call the Claude API or Ollama. They cover the server: the privacy filter, the answer pipeline and its event stream, the API endpoints, the request log and costs, demo mode, loading the texts, knowledge base and prompt, and the layer rules.

They do not cover:

- **The page in a browser.** No test runs `app/static/app.js`; `tests/test_static.py` only checks its source text. The storage logic in `history.js` and `checklist.js` does run, in Node. A browser-level test (Playwright) is deferred until after part 1 ([deferred-work.md](deferred-work.md)).
- **The real Claude API.** Answers in Thai, cited sources and prompt caching only happen with a real key, which costs money.
- **A real Ollama model** (`LLM_PROVIDER=ollama`): whether a local model answers in Thai, cites with `[[id]]` markers the adapter can read, and keeps to Thai script.
- **Real phones**, and Facebook's in-app browser in particular.

## Setup

| Mode | How to start | Used for |
|---|---|---|
| Demo | `MOCK_LLM=true`, no key (see the [README](../../README.md#kjør-i-demomodus-uten-api-nøkkel)) | MT-01, MT-02, MT-11, MT-14, MT-15, MT-16, MT-17 |
| No key | `MOCK_LLM=false`, `ANTHROPIC_API_KEY` empty | MT-03, MT-07 (error turn) |
| Real key | `.env` with `ANTHROPIC_API_KEY`, `MOCK_LLM=false` | MT-04 to MT-09, MT-12, MT-13, MT-14 (part B), MT-17 (part B) |
| Ollama | `LLM_PROVIDER=ollama`, `MOCK_LLM=false`, Ollama running with `OLLAMA_MODEL` pulled (see the [README](../../README.md#kjør-med-ollama-lokal-modell-uten-nøkkel)) | MT-10, MT-12, MT-13, MT-14 (part B), MT-17 (part B) |

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

1. Ask a question about short-stay visas that no source answers, e.g. `ต้องฉีดวัคซีนอะไรก่อนขอวีซ่าไหม` (which vaccinations do I need before applying for the visa?). (Before Story 2.2 this case used a weather question; that is now out of scope, see MT-13.)

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
2. Ask the no-answer question from MT-06.
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

### MT-12 The embassy decides (Story 2.1)

Mode: real key, then Ollama. Run every step in both modes.

1. In a new chat, ask `จะได้วีซ่าไหม` (will I get the visa?).
2. Ask `ฉันเคยถูกปฏิเสธวีซ่าเมื่อปีที่แล้ว ปีนี้จะได้ไหม` (I was refused last year, will I get it this time?).
3. In a new chat, ask `ต้องใช้เอกสารอะไรบ้าง` (which documents do I need?), then `แล้วค่าธรรมเนียมเท่าไร` (and how much is the fee?).
4. Ask `จะได้วีซ่าไหม แล้วต้องใช้เอกสารอะไรบ้าง` (will I get the visa, and which documents do I need?).
5. In a new chat, ask `ต้องใช้เอกสารอะไรบ้าง` (which documents do I need?), then `แล้วปีนี้จะได้ไหม` (and will I get it this year?).
6. Open `data/requests.jsonl` and read the last lines.

Expected: (1, 2) the fixed "only the embassy decides" text, no source links, no estimate of the chances; (3) both get cited answers with source links, the follow-up in the context of the first; (4) a cited answer about the documents, not the fixed text, which gives no estimate of the applicant's chances and, if it mentions them, says the embassy decides (FR3); (5) a cited answer to the first question, then the fixed "only the embassy decides" text for the follow-up; (6) lines for (1, 2) and the follow-up in (5) have `category: "individual_assessment"`, `outcome: "fixed_reply"` and null answer tokens; every line has `classify_input_tokens`, `classify_output_tokens` and `prompt_versions.classifier`; with a real key `cost_usd` includes the classify call, with Ollama it is 0.

### MT-13 Other visa types and requests for a person (Story 2.2)

Mode: real key, then Ollama. Run every step in both modes.

1. In a new chat, ask `ขอวีซ่าทำงานที่นอร์เวย์ต้องทำอย่างไร` (how do I get a work visa for Norway?).
2. Ask `พรุ่งนี้ที่ออสโลฝนจะตกไหม` (will it rain in Oslo tomorrow?).
3. Ask `ขอคุยกับเจ้าหน้าที่ได้ไหม` (can I talk to a staff member?).
4. Ask `ช่วยดูเรื่องยื่นวีซ่าให้ทั้งหมดได้ไหม` (can you handle my whole visa application?).
5. Ask `ไปเยี่ยมแฟนที่นอร์เวย์ต้องมีจดหมายเชิญไหม` (do I need an invitation letter to visit my partner in Norway?).
6. Ask `อยากคุยกับคนจริงๆ ว่าจะได้วีซ่าไหม` (I want to talk to a real person about whether I will get the visa).
7. Ask `วีซ่าทำงานกับวีซ่าท่องเที่ยว อันไหนดีกว่าสำหรับไปเยี่ยมแฟน` (work visa or tourist visa, which is better for visiting my partner?).
8. In a new chat, ask `ต้องใช้เอกสารอะไรบ้าง` (which documents do I need?), then `แล้ววีซ่าทำงานล่ะ` (and for a work visa?).
9. Ask `จะไปฝรั่งเศสกับนอร์เวย์ ต้องยื่นวีซ่าที่สถานทูตไหน` (I am going to France and Norway, which embassy do I apply to?).
10. Open `data/requests.jsonl` and read the last lines.

Expected: (1, 2) the fixed text saying the chatbot only covers short-stay tourist and visitor visas to Norway, with the adviser contact and no source links; (3, 4) the fixed text with the adviser contact, no source links; (5) a cited answer (a short visit to a partner is in scope); (6) the fixed adviser-contact text (a request for a person wins); (7) a cited answer, not the out-of-scope text; (8) a cited answer, then the out-of-scope text for the follow-up; (9) a cited answer (a trip to Norway and other Schengen countries is in scope); (10) lines for (1, 2) have `category: "out_of_scope"`, lines for (3, 4) `category: "reach_person"`, all four with `outcome: "fixed_reply"` and null answer tokens; `prompt_versions.classifier` is `"4"` (it was `"3"` before the prompt fixes from the first evaluation).

### MT-14 Feedback question at the end (Story 2.3)

Part A, the page and the stored answers. Mode: demo, 360 px and then 320 px. Start with `DATABASE_PATH` pointing to a fresh file, or delete `data/feedback.sqlite3` first.

1. In a new chat, tap an example question, then send `ขอบคุณค่ะ 🙏` (thank you).
2. Tap No.
3. Send `ok.`, then tap Yes.
4. Type or tap any question.
5. Send `Thanks!`, reload the page before tapping a button, then send `ขอบคุณค่ะ` again.
6. Tap the new-chat button, tap an example question and send `thanks, and the fee?`.
7. Send `ok` so the buttons show, stop the server and tap Yes; start the server again and tap Yes once more.
8. Run `sqlite3 data/feedback.sqlite3 "select * from feedback"` (or with your `DATABASE_PATH`), then `uv run python scripts/feedback_stats.py`.

Expected: (1) the fixed Thai feedback question with Yes and No buttons under it, large enough to tap, side by side or wrapped, no sideways scroll at 320 px; (2) both buttons are disabled, the chosen one stays marked, the follow-up text ("what else would you like to know?") is shown below and the field stays open; (3) the question and buttons come again; after Yes the thanks text is shown under the buttons and the chat stays on screen; (4) the page opens an empty new chat and asks the question there; the saved chats list holds both chats; (5) after the reload the feedback question is shown without buttons; asking again shows them; (6) `thanks, and the fee?` is not answered with the feedback question (in demo mode it gets the "demo only" text); (7) with the server stopped the buttons come back with the fixed error text; with the server running, Yes is stored, the error text goes and the thanks text is shown; (8) one row per successful tap, with `conversation_id`, `answer` (`yes` or `no`) and `created_at` (UTC, ending in `Z`) only: steps 2 and 3 share one `conversation_id`, every later chat has its own; `feedback_stats.py` counts each conversation once, by its first answer.

Part B, how the real classifier sorts done signals (the riskiest change: classifier prompt version 3). Mode: real key, then Ollama. Run every step in both modes, each in a new chat after one example question.

1. Send `ขอบคุณค่ะ 🙏` (thank you).
2. Send `Thanks!`.
3. Send `ok.`.
4. Send `ขอบคุณค่ะ แล้วค่าธรรมเนียมเท่าไร` (thank you, and how much is the fee?).
5. Send `สวัสดีค่ะ` (hello).
6. Open `data/requests.jsonl` and read the last lines.

Expected: (1, 2, 3) the feedback question with Yes and No buttons, no source links; (4) a cited answer about the fee, not the feedback question; (5) not the feedback question (a greeting is `general`); (6) lines for (1, 2, 3) have `category: "done"` and `outcome: "fixed_reply"`, and `prompt_versions.classifier` is `"4"`.

### MT-15 Document checklist with kept ticks (Story 3.2)

Mode: demo, 360 px and then 320 px; then a real phone if one is at hand (MT-09 setup).

1. Tap an example question, and while the answer is still arriving tap the Checklist button (รายการเอกสาร) in the top bar.
2. Choose visiting family (เยี่ยมครอบครัว).
3. Tick three items. On one item that starts with a condition (e.g. the one for employees, ถ้าเป็นลูกจ้าง), tap "doesn't apply to me" (ไม่ต้องใช้สำหรับฉัน). Then tap it again, and once more. Then tap that item's big tick box.
4. With F12 open on the Network tab, tick and untick an item.
5. Tap change purpose (เปลี่ยนวัตถุประสงค์การเดินทาง), choose tourism, then go back to family.
6. Tap back (กลับไปที่แชท); open the checklist again and press Escape.
7. Close the browser completely, open it again, open the page and the family checklist.
8. In F12, Application, Local storage, set `checklist:family` to `["old-id","passport"]` and reload; open the family checklist.
9. Set `checklist:family` to `{bad` and reload; open the family checklist.
10. Tick every item that applies.
11. Stop the server and choose a purpose; start it again and tap the retry button.
12. Keyboard only (desktop, no mouse): Tab to the Checklist button, Enter, Tab through the purposes, choose one with Enter, Tab through the tick boxes, "doesn't apply" boxes and links, toggle with Space, then press Escape. Repeat with the server stopped: choose a purpose, start the server, Tab to the retry button, Enter, then press Escape.
13. In F12, Network, set throttling to "Slow 3G" and choose a purpose.

Expected: (1) the button can be tapped while the answer arrives; the view covers the chat and offers the three purposes; (2) each item has a large tick box, its text and a source link that opens in a new tab; items with a condition also have the smaller "doesn't apply" choice; the progress line reads e.g. "0 of 18"; (3) the progress goes up with each tick; "doesn't apply" clears the item's tick, dims it and lowers the total by one; tapping it again makes the item count again; ticking a dimmed item clears "doesn't apply" and ticks it; (4) no request is made for a tick; (5) tourism has no ticks; family still has them; (6) the chat is exactly as before, and the answer from step 1 has finished with its source links; focus is on the Checklist button; (7) the same ticks and "doesn't apply" choices; (8) only `passport` is ticked, nothing breaks; (9) nothing is ticked, nothing breaks; (10) the all-done text is shown: every item that applies is ticked, hand in the documents with the signed embassy checklist at VFS, the embassy decides; (11) the fixed error text with a retry button; retry loads the list; (12) every control can be reached and used with the keyboard, focus is always visible, Escape closes the view and focus returns to the Checklist button, also after the failed load and retry (focus moves to the purpose heading when the list appears); a screen reader names the retry button (ลองอีกครั้ง); (13) the loading text (กำลังโหลดรายการเอกสาร) shows until the list appears. At 320 px nothing scrolls sideways, also with the longest items (the minor consent letter, the invitation letter).

### MT-16 Open the checklist from the chat (Story 3.3)

Mode: demo, 360 px and then 320 px. Part B: real key or Ollama.

1. Tap the example question about tourist visa documents (ขอวีซ่าท่องเที่ยวนอร์เวย์ต้องใช้เอกสารอะไรบ้าง) and wait for the answer.
2. Tap "Open checklist" (เปิดรายการเอกสาร) under the answer. Choose tourism, tick one item, then tap back (กลับไปที่แชท).
3. Tap the example question on how to start (ถ้าจะขอวีซ่าไปนอร์เวย์ ต้องเริ่มต้นอย่างไร), and tap "Open checklist" under its answer; press Escape.
4. Tap the example question about the visa fee.
5. Send `ขอบคุณค่ะ`.
6. Reload the page. Tap "Open checklist" under the first answer and choose tourism.
7. Open the saved chats, open another chat or start a new one, then reopen this chat from the saved chats; tap the button under the first answer again.
8. Ask the first example again, and while the answer is still arriving tap "Open checklist" under an earlier answer; go back.
9. Keyboard only: Tab to "Open checklist" under an answer, Enter, then press Escape.
10. In F12, Application, Local storage, edit `conversations`: on one exchange set `checklistPurposes` to `["visa"]`, on another delete the field; reload.
11. Part B (real key or Ollama): ask "ผู้สนับสนุนต้องกรอกแบบฟอร์มอะไร" (which form does the sponsor fill in?), then "ค่าธรรมเนียมวีซ่าเท่าไร" (how much is the visa fee?).

Expected: (1) the answer with its source links, and the "Open checklist" button under them; (2) the purpose choice with all three purposes (the answer cites the embassy's checklist, which every checklist links); the tick is saved; back shows the chat unchanged with focus on the button under the answer; (3) the button names the purpose (เปิดรายการเอกสาร: เยี่ยมครอบครัว), and the family checklist opens directly, without the purpose choice, with focus on its heading (the answer cites a source only the family checklist links); Escape returns to the chat; (4) no button under the fee answer; (5) the feedback question without a button; (6, 7) the buttons come back under the same answers only, and the tourism checklist still has the tick from step 2; (8) the checklist opens, and after going back the new answer has kept arriving and finishes normally; (9) focus is visible on the button, Escape returns focus to it; (10) no button on those two exchanges, nothing breaks, the others keep theirs; (11) for each answer, first read the source links shown under it: the button is there exactly when one of them is a checklist-linked source (“Document checklist Schengen visa to Norway”, “Gather the necessary documentation”, “Proof of sponsorship and/or private accommodation” or “Invitation for a visitor visa”), and absent otherwise; it opens the matching purposes (the embassy's checklist: the choice of all three; necessary documents only: the family checklist directly; the sponsorship form or invitation page: the choice of family and friends). At 320 px the button wraps its text and nothing scrolls sideways; it is at least 48 px high.

### MT-17 Show English (Story 4.1, FR7)

Mode: demo, 360 px and then 320 px. Part B: real key, then Ollama.

1. Tap the example question about the visa fee and wait for the answer. Tap "Show English" (แปลเป็นภาษาอังกฤษ (English)) under it.
2. Send `จะได้วีซ่าไหม` (will I get the visa?) in part B, or in demo mode any other question (e.g. `วีซ่าทำงานต้องใช้เอกสารอะไร`); tap "Show English" under the fixed reply.
3. Send `ขอบคุณค่ะ` and tap "Show English" under the feedback question, before answering Yes or No.
4. Reload the page; tap "Show English" under an earlier answer.
5. Stop the server, tap "Show English" under another reply; start the server and tap it again.
6. In F12, Network, set throttling to "Slow 3G". Tap "Show English" under a reply, then at once tap "New chat".
7. Open the Checklist, choose tourism, tap "Show English", tick one item, then tap "Change purpose" and choose family.
8. Keyboard only: Tab to "Show English" under a reply and press Enter.
9. Look at `data/requests.jsonl` after steps 1 to 3.
10. Part B (real key, then Ollama): ask "ค่าธรรมเนียมวีซ่าเท่าไร" (how much is the visa fee?) and tap "Show English"; then ask a question with a made-up passport number, e.g. "พาสปอร์ต AA1234567 ต้องใช้เอกสารอะไร", and tap "Show English" under the answer.

Expected: (1) the button sits under the source links (and "Open checklist"), is disabled while the request runs, and is replaced by the English under the Thai answer; the Thai text, the source links and other buttons are unchanged; in demo mode the English is the stored demo English; (2) the stored English of the fixed reply ("Sorry, we cannot assess whether you will get the visa…" or the demo-only text), with no model call; (3) the English of the feedback question, with the Yes and No buttons still under it, after the English; (4) every saved reply has the button again; no English is shown until it is tapped (the English is never saved); (5) the fixed error text (ขออภัย เกิดข้อผิดพลาด…) under the reply and the button back; the second tap shows the English; (6) the new chat opens and nothing appears in it when the slow translation returns; (7) the English appears under every tourism item, stays after the tick, and the family list opens without English and with the button back; (8) focus is visible on the button, Enter shows the English, and focus moves to the English text; (9) one line with `"endpoint": "translate"` and `"model": "mock_llm"`, `cost_usd` 0, for the demo answer in step 1 and for any other text; no line for the fixed texts or the feedback question; no line holds any text; (10) the English keeps the amount, the URLs and `[removed]` in place of the passport number, and adds nothing of its own; the log has a `translate` line with `MODEL_SMALL` (Claude) or `OLLAMA_MODEL` (Ollama) and its tokens. At 320 px the button and the English wrap and nothing scrolls sideways; the button is at least 48 px high.

### MT-18 The README on a clean machine (Story 4.3, NFR2)

Mode: a computer that has never run the app (no clone, no `.venv`, no `.env`), with only Git and uv installed. Follow the [README](../../README.md#kom-i-gang) and nothing else; note every place you had to guess.

1. Clone and install as in "Installer".
2. Start demo mode in your shell as in "Kjør i demomodus", open the page and tap each of the four example questions; tap "Show English" under one answer.
3. Stop the app. Start it with `--host 0.0.0.0` as in "Åpne siden fra en mobil på samme Wi-Fi" and open it from a phone on the same Wi-Fi.
4. Stop the app, open a new terminal, copy `.env.example` to `.env`, set your own `ANTHROPIC_API_KEY`, start the app and ask one question of your own.
5. Run `uv run pytest`.

Expected: (1) `uv sync` finishes without errors; (2) the demo label is shown, each example gives a Thai answer with source links, and the English appears; (3) the page opens on the phone; (4) no demo label, a streamed Thai answer with sources, and one line in `data/requests.jsonl` with a `cost_usd`; (5) every test passes. Any missing or unclear step is fixed in the README.
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
| 2026-11-15 | MT-10 | Wannapa Sikveland | Browser, branch `integration`, `LLM_PROVIDER=ollama` (qwen3.5:9b) | Pass | Reported by the tester as fine; tested together with saved chats. Ran before Stories 2.1/2.2, when step 2 used the weather question (now out of scope); rerun step 2 with the current MT-06 question |
| 2026-11-15 | MT-11 | Wannapa Sikveland | Browser, branch `integration` | Pass | Reported by the tester as fine; tested together with Ollama |
| | MT-12 | | | Not run | Needs a real key, and Ollama |
| | MT-13 | | | Not run | Needs a real key, and Ollama |
| | MT-14 | | | Not run | Part B needs a real key, and Ollama. A one-off headless Edge run (demo mode, 320 px) of steps 1 to 5, the failure in step 7 and the rows in step 8 passed on 2026-11-15; not a manual-test result |
| | MT-15 | | | Not run | A one-off headless Edge run (demo mode, 320 px) of steps 1 to 11 (before steps 12 and 13 were added), with the browser closed and reopened for step 7 and a simulated failure for step 11, passed on 2026-11-15; not a manual-test result |
| | MT-16 | | | Not run | Part B needs a real key or Ollama. A one-off headless Edge run in demo mode at 320 px passed 18 checks on 2026-11-15; not a manual-test result |
| | MT-17 | | | Not run | Part B needs a real key, and Ollama |
| | MT-18 | | | Not run | Needs a clean machine and a real key; a fresh clone in demo mode (steps 1–2 by request, not in a browser) worked on 2026-11-16, not a manual-test result |
