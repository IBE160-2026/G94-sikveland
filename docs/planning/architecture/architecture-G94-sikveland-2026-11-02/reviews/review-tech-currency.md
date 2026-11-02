---
review: tech-currency
target: docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md
date: 2026-11-02
lens: Every committed decision in the spine was checked against the web or a live command, not taken from training data
verdict: PASS WITH CONDITIONS
---

# Review: technology currency and API reality check

## Verdict

**Pass with conditions.** I could confirm every named technology, version and API capability in the spine against PyPI or the official docs as of 2026-11-02. Nothing in the spine is wrong or out of date. Three things need to be added before stories are written:

1. **Zero-citation fallback vs. streaming.** AD-7 and AD-8 contradict each other: text has already been streamed before the server can know that an answer has no citations.
2. **Rules for Opus 5.5 and API version 2026-10-21.** The SDK version the spine pins brings behaviour changes that the spine does not mention: thinking cannot be turned off, `temperature` cannot be set, and forced tool use is not allowed.
3. **Where the documents go in the request.** The spine does not say where the cached documents sit in the request. A stateless server that resends history must place them correctly to get cache hits.

Facebook in-app browser support for streaming is very likely but **not directly confirmed**. Test it on real devices.

## 1. Versions (re-run 2026-11-02)

Command: `pip index versions <pkg>`, plus the PyPI JSON API for `requires_python` and upload dates.

| Spine | Latest on PyPI today | requires_python | Status |
| --- | --- | --- | --- |
| Python 3.12 (local 3.12.10) | n/a | n/a | Confirmed. 3.12 gets **security fixes only**, with end of life 2028-10. 3.14 and 3.15 are the bugfix branches. Fine for a course prototype ([devguide](https://devguide.python.org/versions/)). |
| FastAPI 0.162 | 0.162.0 | >=3.10 | Confirmed latest |
| uvicorn 0.54 | 0.54.0 | >=3.10 | Confirmed latest |
| anthropic 2.4 | 2.4.0 (uploaded 2026-11-02 19:08 UTC) | >=3.10 | Confirmed latest. **Very new:** 2.0.0 came out 2026-10-21, and five releases followed in 12 days. |
| pytest 9.2 | 9.2.0 | >=3.10 | Confirmed latest |

The memlog version claims are correct.

**Risk:** almost all tutorials, Stack Overflow answers and model training data describe anthropic 0.x/1.x and API version 2023-06-01. Pin exact versions (`anthropic==2.4.0`) in the requirements file. Expect the coding agent to produce 1.x-style code that fails, for example code that sets `temperature` (see §3).

## 2. Model id `claude-opus-5-5`

**Confirmed.** The [Models overview](https://platform.claude.com/docs/en/models/overview) and the [Opus 5.5 page](https://platform.claude.com/docs/en/models/opus-5-5/overview) agree:

- Claude API id is `claude-opus-5-5`, a dateless pinned snapshot.
- Released 2026-09-22. Status "Active (latest)". Retirement not sooner than 2027-09-22, so it lasts the whole course.
- Pricing: $4 / $20 per MTok. 5-minute cache write $5/MTok. Cache read $0.20/MTok (0.05x input price).
- 1M context window. Minimum cacheable prompt is 512 tokens, so a knowledge base of 10–20 documents is far above it.

**Facts the spine does not reflect** ([What's new in Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5)):

- **Thinking is always on and cannot be turned off.** Sending `thinking: {"type": "disabled"}` returns 400. Every response, including the classifier call and the translation call, may start with `thinking` blocks. With the default `display: "omitted"` these blocks are empty. Their tokens are billed as output.
  - Consequence for AD-8 and the adapter: pick content blocks and stream deltas **by type**, never by position. Do not forward thinking deltas.
  - Consequence for NFR6: the cost log must count thinking tokens.
  - Thinking depth is controlled with `output_config.effort`. The default on Opus 5.5 is `medium`.
- **Forced tool use is rejected.** `tool_choice` `any` or `tool` returns 400. A common way to build a classifier is "force a tool call", and that does not work on this model. AD-5's choice of structured outputs is the correct, supported route. Write this into AD-5 so nobody falls back to a forced tool.
- **Refusals** come back as HTTP 200 with `stop_reason: "refusal"`. The answer adapter should map a refusal to the no-answer or error path. AD-7's zero-citation check partly covers this.
- **Cheaper classifier model (Deferred).** The docs describe Claude Haiku 5.5 (`claude-haiku-5-5`) as made "for high-volume, latency-sensitive tasks such as classification, extraction, and routing". It supports both Citations and structured outputs. This backs the deferred item "separate model setting for classify/translate". Given that thinking is always on with Opus, latency and cost suggest raising its priority.

## 3. API version 2026-10-21, which SDK 2.x sends by default

The [migration guide](https://platform.claude.com/docs/en/api/migration-2026-10-21) says to upgrade the Python SDK to 2.0.0 to use 2026-10-21, so SDK 2.4 sends 2026-10-21. Changes in the Messages API ([Versions](https://platform.claude.com/docs/en/api/versioning)):

- **`temperature`, `top_p` and `top_k` are removed.** Sending any of them returns 400, even at the default value. "No other setting replaces it." So the classifier and the eval cannot rely on `temperature=0` to get repeatable results. AD-13 and NFR4 evaluation should expect run-to-run variation, and could run each question more than once or accept small swings in the score.
- **A `text` block with non-empty `citations` in a user message returns 400.** This does not apply to AD-3 if the page resends prior turns as **plain text**. Say that explicitly in AD-3 or AD-8: history turns are plain strings, never citation-bearing blocks.
- **A `document` block in an assistant message returns 400.** Documents must go in a user turn. That is consistent with the spine's intent.

## 4. Citations with document blocks

**Confirmed**: [Citations docs](https://platform.claude.com/docs/en/build-with-claude/citations), status stable, `claude-opus-5-5` in `supportedModels`.

| Spine claim | Docs say | Status |
| --- | --- | --- |
| Whole knowledge base as document blocks with Citations on | Plain text, PDF and custom-content documents are supported. "Citations must be enabled on all or none of the documents within a request." | Confirmed. All documents must have citations enabled. |
| Prompt caching on documents works with Citations | "Citations and prompt caching can be used together effectively… apply `cache_control` to your top-level document content blocks." | Confirmed |
| Citations cannot be combined with structured outputs | Warning: enabling citations on any document while also sending `output_config.format` "returns a 400 error". | Confirmed. AD-7's last sentence is correct. |
| Toggling citations invalidates the cache (memlog) | In the [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) invalidation table, a "Citations toggle" invalidates the system and messages caches. | Confirmed. "Always on" is correct. |
| `{id, title, url}` sources taken from citations | A citation carries `document_index` (0-indexed across all documents in the request), `document_title` and `cited_text`. `title` is length-limited, and `context` is the place for metadata. | Feasible. Map `document_index` to the source `id` through the loader's fixed order (Story 2.3 already asks for a fixed order). |

**Notes:**

- **Chunking.** Plain-text documents are automatically split into sentences. The docs suggest custom-content documents "for bullet points or transcripts". The Markdown snapshots from UDI and VFS will contain many lists, so citations of single bullets may come out too coarse or oddly cut. Consider custom-content documents (one block per paragraph or list item) and settle it with the eval. If any source is in **Thai** (for example a Thai VFS page), sentence splitting of Thai text, which has no sentence-final punctuation, is **unverified**. Custom content avoids the question.
- `cited_text` does not count toward output tokens. Enabling citations adds a few input tokens.

## 5. Prompt caching, and where the documents go

**Confirmed** ([Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)):

- Default TTL is 5 minutes, refreshed for free on each hit. A 1-hour TTL is available at 2x the write cost.
- The cache prefix follows the order `tools` → `system` → `messages`, up to the block marked with `cache_control`.
- Documents are cacheable as content blocks in user turns.

**Gap in the spine:** AD-7 says "prompt caching on the documents" but does not say *where* the documents go. Because AD-3 resends history on every request, the documents must sit in a **fixed position before any history**, for example as the first user turn followed by the conversation, with `cache_control` on the last document block. If they are attached to the latest user turn, every follow-up becomes a cache miss.

Other things that invalidate the cache:

- Changing `output_config.effort`. Keep it fixed per call type.
- Changing the thinking configuration.
- Changing anything earlier in the prompt (system prompt version, AD-12).

Also note that with a 5-minute TTL, demo or adviser sessions spaced more than 5 minutes apart pay the cache write again ($5/MTok). Include this in the NFR6 cost estimate.

## 6. Structured outputs for the classifier

**Confirmed** ([Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)):

- Status stable. No beta header is needed.
- The parameter is `output_config.format` with `type: "json_schema"`. The old `output_format` is deprecated and returns 400 unless the old beta header is sent.
- `claude-opus-5-5` and `claude-haiku-5-5` are both in `supportedModels`.
- The Python helper is `client.messages.parse()` with a Pydantic model, and the result comes back in `parsed_output`. A JSON-schema `enum` gives exactly AD-5's closed set.
- The first use of a schema adds latency while the grammar compiles. Compiled grammars are cached for 24 hours.

Combined with §2 (thinking is always on), the classifier call carries thinking overhead on Opus 5.5. Use a low `effort` for this call, or Haiku 5.5.

## 7. Streaming responses that include citations

**Confirmed** ([Citations, streaming support](https://platform.claude.com/docs/en/build-with-claude/citations#streaming-support)): "citations arrive as a `citations_delta` delta type inside `content_block_delta` events. Each delta contains a single citation to add to the `citations` list on the current `text` content block." Text deltas and citation deltas are interleaved per text block.

**Finding (design consequence, high):** citations arrive interleaved with the text, and the first text block (often an introductory sentence) can carry no citation at all. So **"zero citations" is only known when the message ends**. AD-8 streams `text` deltas as they arrive. AD-7 then cannot "replace" an uncited answer: the user has already seen it. Choose one of these and write it into AD-7/AD-8:

- (a) buffer text deltas until the first `citations_delta` arrives, then stream. If the message ends with none, send the fixed no-answer reply;
- (b) add a `replace` (or `retract`) event to the stream contract; or
- (c) accept the risk and define the rule as "sources event empty → page appends the no-answer text".

Option (a) keeps the contract unchanged and matches AD-7's intent.

The mock adapter (AD-2) must reproduce the same interleaving: some text first, then citations.

## 8. fetch + ReadableStream in mobile and in-app browsers

**Data:** MDN browser-compat-data 8.1.8 (published 2026-11-02), queried locally.

| API | Chrome Android | Android WebView | Safari iOS | WKWebView (iOS) | Samsung Internet |
| --- | --- | --- | --- | --- | --- |
| `fetch` | 42 | 42 | 10.3 | 10.3 | 4.0 |
| `Response.body` | 43 | 43 | 10.3 | 10.3 | 4.0 |
| `ReadableStream.getReader` | 43 | 43 | 10.3 | 10.3 | 4.0 |
| `TextDecoder` | 38 | 38 | 10.3 | 10.3 | 3.0 |
| `TextDecoderStream` | 71 | 71 | 14.5 | 14.5 | 10.0 |
| `ReadableStream` async iteration (`for await`) | **124** | **124** | **27** | **27** | **27.0** |

[caniuse Response.body](https://caniuse.com/mdn-api_response_body) agrees for iOS Safari (10.3+).

**In-app browsers:**

- On iOS, every in-app browser, including Facebook's and LINE's, uses WebKit (WKWebView), so iOS 10.3+ is covered.
- On Android, Facebook has used **its own Chromium-based WebView** since 2022 instead of the system WebView ([9to5Google](https://9to5google.com/2022/09/30/facebook-android-webview/), [Search Engine Journal](https://www.searchenginejournal.com/facebook-launching-new-in-app-browser-for-android/466775/)). It is still Chromium, so streaming fetch should work.
- **Unconfirmed:** I found no source that confirms or rules out streaming-fetch problems in Facebook's in-app browser. There are only old, unrelated WKWebView load-failure reports, such as [WebKit bug 199267](https://bugs.webkit.org/show_bug.cgi?id=199267). Add a manual device test: Facebook and LINE in-app browsers on Android and iOS. LINE is likely more relevant than Facebook for Thai users.

**Conditions for the page code:**

- Read with `response.body.getReader()` in a loop. **Do not use `for await (const chunk of response.body)`.** It needs iOS 27 or Chrome 124, and older iPhones used by the target group will not have it.
- Decode with `new TextDecoder()` and `decode(chunk, {stream: true})`, and split on `\n` while keeping the unfinished last line in a buffer. Thai characters are 3 bytes in UTF-8, so a chunk boundary can split a character. Without `stream: true` the text gets corrupted.

## 9. FastAPI fit for the NDJSON stream

**Confirmed and better than assumed.** FastAPI added native JSON Lines streaming in **0.134.0** ([Stream JSON Lines](https://fastapi.tiangolo.com/tutorial/stream-json-lines/)): a path operation that `yield`s Pydantic models is streamed as one JSON object per line. It also has first-class SSE support. The content type is **`application/jsonl`**. AD-8 says "newline-delimited JSON", which is the same format, but the page should not check for `application/x-ndjson`.

The docs page does not cover POST bodies or client disconnects. A plain `StreamingResponse` is the fallback if the `yield` form causes problems with the POST body.

## Findings summary

| # | Severity | Finding | Suggested action |
| --- | --- | --- | --- |
| 1 | High | AD-7 (replace answers with zero citations) and AD-8 (stream text deltas) conflict: zero citations is only known at the end of the message. | Choose buffer-until-first-citation (or a `replace` event) and record it in AD-7/AD-8. Make the mock reproduce the interleaving. |
| 2 | Medium | Opus 5.5: thinking always on, forced `tool_choice` returns 400, refusals arrive as `stop_reason: "refusal"`. Not in the spine. | AD-5: structured outputs only, never a forced tool. Adapter: select blocks by type, drop thinking, handle refusals. Count thinking tokens in cost logs. Set `effort` explicitly. |
| 3 | Medium | API 2026-10-21 (SDK 2.x) removes `temperature`/`top_p`/`top_k` (400). History with citation blocks in user turns returns 400. | Note in conventions: never send sampling parameters, history is plain text. The eval (AD-13) must tolerate non-deterministic output. Pin `anthropic==2.4.0`. |
| 4 | Medium | The cache position of the documents is unspecified. With history resent on every request, the documents must come before the history. | Add to AD-7: documents first, in a fixed order, `cache_control` on the last document, effort and thinking settings fixed. |
| 5 | Low | Facebook and LINE in-app browser streaming is unconfirmed. `for await` on a stream needs iOS 27. Thai multi-byte characters can be split across chunks. | Use `getReader()` + `TextDecoder({stream:true})`. Add a device test to the test plan. |
| 6 | Low | Sentence chunking of Markdown lists, and of any Thai-language source, is unverified. | Try custom-content documents and decide with the eval. |
| 7 | Info | Haiku 5.5 is documented for classification and supports structured outputs and citations. | Consider moving the "cheaper model" deferred item forward. |
| 8 | Info | FastAPI 0.134+ has native JSON Lines streaming (`application/jsonl`). Python 3.12 gets security fixes only (EOL 2028-10). | Use the native feature. No change needed for Python. |

## Sources

- PyPI, `pip index versions` and `https://pypi.org/pypi/<pkg>/<ver>/json`, run 2026-11-02
- Python versions: https://devguide.python.org/versions/
- Models overview: https://platform.claude.com/docs/en/models/overview
- Claude Opus 5.5: https://platform.claude.com/docs/en/models/opus-5-5/overview
- What's new in Opus 5.5: https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5
- Citations: https://platform.claude.com/docs/en/build-with-claude/citations
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- API versions: https://platform.claude.com/docs/en/api/versioning
- Migration to 2026-10-21: https://platform.claude.com/docs/en/api/migration-2026-10-21
- anthropic-sdk-python changelog: https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md
- FastAPI, Stream JSON Lines: https://fastapi.tiangolo.com/tutorial/stream-json-lines/
- MDN browser-compat-data 8.1.8: https://unpkg.com/@mdn/browser-compat-data/data.json
- caniuse, Response.body: https://caniuse.com/mdn-api_response_body
- Facebook Android in-app browser: https://9to5google.com/2022/09/30/facebook-android-webview/ and https://www.searchenginejournal.com/facebook-launching-new-in-app-browser-for-android/466775/
- WebKit bug 199267 (in-app WebView load failures, background only): https://bugs.webkit.org/show_bug.cgi?id=199267
