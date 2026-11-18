---
title: 'Pipeline guard for the no-answer sentence'
type: 'feature'
created: '2026-11-18'
status: 'done'
route: 'dispatch'
baseline_commit: '98efb9c6a36484f92b38850e6d3d8f599ee40532'
review_loop_iteration: 1
context:
  - '{project-root}/docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The no-answer text (`reply-no-answer`) shows only when an answer ends with zero known citations (AD-7). In the Ollama evaluation `eval/reports/2026-11-18-answer-1-classifier-4-citing-3.md`, case `no-answer-interpreter-at-vfs` opened with the prompt's not-available sentence ("ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ") and then went on with cited advice and "เอกสารที่ให้มา", so the applicant got advice the sources do not support instead of the no-answer text. In an earlier run the model also cited the not-available sentence itself. Prompt rules alone do not stop this every time.

**Approach:** In the answer pipeline, once the first known citation has arrived and the whole first line is held (nothing has been shown yet), look at the held text. If it opens with a not-available sentence, send `no_answer_text` instead of the reply, with no sources, exactly as for zero citations. Nothing already shown is ever replaced. The guard sits in the pipeline, so it applies to Claude and Ollama alike.

**Decisions (user, 2026-11-18):** the guard, chosen over more prompt work, knowing that it changes `app/` and amends AD-7. Narrow scope: the guard fires only when the first line of the held text (up to the first line break, trimmed) starts with an optional ขออภัย (optionally followed by ค่ะ, ครับ, นะคะ or นะครับ) and then ไม่มีข้อมูล, ไม่พบข้อมูล or ไม่พบคำตอบ, and that line holds neither แต่ ("but") nor อย่างไรก็ตาม ("however"). A reply such as `application-steps` ("ขออภัย ไม่มีข้อมูลเรื่อง… แต่สามารถบอกขั้นตอน…ได้ดังนี้:" and then a cited answer) stays answered. Spec kept whole despite its size; subagents allowed. After review pass 1 (2026-11-18): the decision needs the whole first line, so the pipeline keeps holding after the first known citation only while the held text could still be a not-available opening (empty after trimming, or starting like ขออภัย, ไม่มีข้อมูล, ไม่พบข้อมูล or ไม่พบคำตอบ, or a beginning of one of these); it decides at the first line break or at the end of the answer. Every other answer starts streaming at the first known citation, as today. แต่ and อย่างไรก็ตาม count as words, not inside other words (แต่ละ, ตั้งแต่, แต่ง… are not a turn). Leading Markdown marks (`*`, `_`, `#`, `>`, `-`) and zero-width spaces are ignored before the pattern is matched.

## Boundaries & Constraints

**Always:**
- The check runs once, before anything is shown: at the first known citation when the held text cannot be a not-available opening, otherwise when the first line is complete (line break) or the answer ends. A reply that has started streaming is never replaced (AD-7).
- Chunk shapes from both adapters count: Claude sends a citation as `AnswerChunk("", (id,))`, possibly before the text it cites; Ollama releases a chunk at each `[[id]]` marker, possibly in the middle of the first line.
- After the guard fires: one `TextDelta(no_answer_text)` at once, then the stream is read to the end only to get `Usage`, so the cost is still logged (`Spent` for the answer call before `Sources`). `Sources` is empty, so the request log and `scripts/run_eval.py` record `no_answer` without any change of their own. Event order stays as the module docstring says.
- The not-available patterns are a named constant in `app/pipeline/answer.py`, with a comment saying where they come from (the citing addendum's example sentence and the fixed no-answer text's wording).
- AD-7 in `ARCHITECTURE-SPINE.md` gets the new rule and "*(Amended 2026-11-18.)*"; README's no-answer sentence (line ~190) gets one sentence about it.

**Never:** no prompt, test-set, knowledge-base, request-log schema or stream-event change; no model call to decide it; no change to the zero-citation and unknown-id behaviour.

## I/O & Edge-Case Matrix

| Scenario | Answer chunks (`[s1]` = a known citation) | Expected |
|---|---|---|
| Sentence alone, then cited advice | "ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ\n\nแนะนำให้ติดต่อ VFS [s1]" | no-answer text, empty `Sources`, answer `Spent`, `Done`; none of the reply shown |
| The sentence itself cited | "ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ [s1]" | no-answer text |
| Variants | "ขออภัยค่ะ ไม่มีข้อมูล…", "ไม่พบข้อมูล…", "ขออภัย ไม่พบคำตอบ…" | no-answer text |
| Opening split over several uncited chunks | "ขออภัย " + "ไม่มีข้อ" + "มูลค่ะ\nX [s1]" | no-answer text |
| Partial answer, sentence later | "ต้องใช้หนังสือรับรอง [s1] … ขออภัย ไม่มีข้อมูลเรื่อง…" | answered, all text shown |
| Not-available, but the first line turns to an answer | "ขออภัย ไม่มีข้อมูลเรื่อง X แต่สามารถบอกขั้นตอนได้ดังนี้:" + "\n1. … [s1]" | answered, all text shown |
| Turn word after a mid-line citation (Ollama) | "ขออภัย ไม่มีข้อมูลเรื่อง X [s1]" + " แต่สามารถบอกได้ดังนี้\n1. …" | answered, all text shown |
| Citation chunk before its text (Claude) | `("", s1)` + "ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ" + "\nคำแนะนำ" | no-answer text |
| แต่ inside another word | "ขออภัย ไม่มีข้อมูลเรื่องวีซ่าแต่งงานค่ะ\nคำแนะนำ [s1]" | no-answer text |
| Leading Markdown or zero-width space | "**ขออภัย** ไม่มีข้อมูล…", "\u200bขออภัย ไม่มีข้อมูล…" | no-answer text |
| Ordinary answer | "ค่าธรรมเนียม 90 ยูโร [s1]" + " ต่อคน" | first text shown at the first citation, not held to the line end |
| Possible opening, the stream ends with no line break | "ขออภัย ไม่มีข้อมูล [s1]" (end) | no-answer text |
| Unknown id in a declined answer | "ขออภัย ไม่มีข้อมูลค่ะ\n" + "X [s1][nope]" + "Y [nope2]" | no-answer text, `Sources((), unknown_source_ids=2)` |
| Apology that is not "not available" | "ขออภัย เราไม่สามารถทราบผลอนุมัติล่วงหน้าได้ … [s1]" | answered |
| Zero citations / unknown ids only | as today | as today |
| Model error while reading after the guard fired | `LLMError` | `Failed`, as for any error after text |

</frozen-after-approval>

## Code Map

- `app/pipeline/answer.py` `answer_question` -- the held/cited loop (`held`, `cited`, `if not cited: held.append…`; release at `text = "".join([*held, item.text])`) is where the guard goes; update the function and module docstrings.
- `app/ports/llm.py` `AnswerChunk(text, source_ids)` -- chunks from both adapters; Ollama's `[[id]]` markers are already stripped from `text`.
- `app/adapters/anthropic_llm.py` `_chunk` (~line 236) -- a `citations_delta` becomes `AnswerChunk("", (id,))`; the recorded fixture in `tests/test_anthropic_llm.py` (~line 644) has text before its citation, but the order is not guaranteed, so test both.
- `app/adapters/ollama_llm.py` `MarkerParser.feed` (~lines 138-156) -- releases text up to each `[[id]]` marker as one chunk, so a citation can arrive mid-line.
- `app/web/chat.py:212`, `scripts/run_eval.py:201` -- outcome is `no_answer` when `Sources.items` is empty; reuse, do not change.
- `tests/test_answer_pipeline.py` -- `ScriptedLLM`, `StandInKnowledgeBase("s1","s2","s3")`, `_run`, `NO_ANSWER`; follow `test_zero_citations_sends_only_the_no_answer_text` for the expected event lists.
- `content/texts.yaml` `reply-no-answer` -- the fixed text ("ขออภัย ไม่พบคำตอบสำหรับคำถามนี้…"); `prompts/answer-citing-markers.md` -- the example sentence "ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ".
- `docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md` AD-7; `README.md` ~line 190.

## Tasks & Acceptance

**Execution:**
- [x] `app/pipeline/answer.py` -- pattern constant and the guard at the release point, docstrings -- FR4, AD-7
- [x] `tests/test_answer_pipeline.py` -- one test per matrix row, full event lists where the order matters -- NFR3
- [x] `ARCHITECTURE-SPINE.md` AD-7, `README.md` -- the amended rule -- examiner

**Acceptance Criteria:**
- Given the test suite, when it runs, then it passes and covers every matrix row.
- Given a new Ollama evaluation run, when it is compared with `2026-11-18-answer-1-classifier-4-citing-3.md`, then every general case that was answered is still answered (no false positive), and the no-answer result is reported, worse or better.

## Implementation Notes

- First implementation reverted after review pass 1 (intent gap: the check ran on an incomplete first line); the user chose to hold only while the text could still be a not-available opening; re-derived by a fresh implementer.
- `app/pipeline/answer.py`: `NOT_AVAILABLE_OPENING` (built from `NOT_AVAILABLE_APOLOGY`, `NOT_AVAILABLE_PARTICLES`, `NOT_AVAILABLE_PHRASES`), `TURN_WORD` (แต่ as a word, not in ตั้งแต่/แต่ละ/แต่ง…; อย่างไรก็ตาม), `opens_with_not_available`, `_held_reply_declines`, `_could_open_with_not_available`. Leading whitespace, Markdown marks and zero-width characters are skipped. After a decline the stream is read on for `Usage` and unknown ids.
- Review pass 2 patches: hold only while the text can still match (an apology such as "ขออภัย เราไม่สามารถ…" streams at the first citation); tests that the citing prompt's example sentence and the Thai `reply-no-answer` text match the pattern; docstrings. `uv run pytest`: 1509 passed, exit code 0; ruff clean.
- Ollama run `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-2.md` (guard before the pass-2 patches, which change only when text streams, not what is declined) compared with `2026-11-18-answer-1-classifier-4-citing-3.md`: no false positive (every general case answered before is still answered, incl. `when-to-apply-mixed-language`, which got `no_answer` in an aborted run); `no-answer-interpreter-at-vfs` is now `no_answer`; no-answer stays 3 of 4 because `no-answer-pregnancy` was a partial answer ("you can apply as usual" cited, then "no information about special conditions"), which the narrow rule leaves answered by design; general 14 of 15 automatic because the classifier sent `own-chances-and-employment-proof` to `individual_assessment` this run (classifier variance, not the guard); individual assessment 3 of 3, reach person 4 of 4. A 20-case run with the first implementation also gave no-answer 4 of 4.

## Spec Change Log

## Review Triage Log

Review pass 1 (implementation since reverted for the intent gap in row 1).

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | blind, edge-case, verification-gap | The check runs once, at the first known citation, on a first line that may not be complete: an empty held text (Claude's `AnswerChunk("", (id,))`) disarms the guard, and a turn word after a mid-line citation is never seen | high | `app/adapters/anthropic_llm.py:236` yields citation-only chunks with empty text; Ollama's `MarkerParser.feed` releases a chunk at each marker (`app/adapters/ollama_llm.py:138-156`), so "ขออภัย ไม่มีข้อมูลเรื่อง X [[s1]] แต่สามารถ…" is checked as "ขออภัย ไม่มีข้อมูลเรื่อง X " and declined: the `application-steps` shape the decision keeps answered. Root cause is the frozen rule "the check runs once, at … first known citation" | intent_gap |
| 2 | blind, edge-case | `แต่` is matched as a substring, so แต่ละ, ตั้งแต่ and แต่งงาน count as a turn | medium | "ขออภัย ไม่มีข้อมูลเรื่องวีซ่าแต่งงานค่ะ" would not be declined; the decision names the word แต่ | moot (loopback); fold into re-derivation |
| 3 | blind, edge-case | A leading Markdown mark (`**`, `>`, `#`, `-`) or a zero-width space stops the pattern from matching | low | `NOT_AVAILABLE_OPENING.match` is anchored at the first character and `\s` does not match U+200B | moot (loopback); fold into re-derivation |
| 4 | blind, edge-case, verification-gap | Unknown ids cited after the guard fired are not counted, unlike the zero-citation path | low | `if declined: continue` comes before the source-id loop; no test has an unknown id in a declined answer | moot (loopback); fold into re-derivation with a test |
| 5 | blind | Rewordings such as ขอโทษ or "ในเอกสารไม่มีข้อมูล" are not caught | low | true, but the user chose the narrow pattern | reject |
| 6 | blind, edge-case | A factual opening such as "ไม่มีข้อมูลว่าต้องใช้ตั๋ว…" would be declined | low | it matches the decided rule, and such an opening itself says the information is missing; the evaluation checks for false positives | reject |
| 7 | blind | A decline cannot be told apart from zero citations in the log | false | the acceptance check works without it: a declined general case shows as an outcome FAIL in the evaluation report; a log schema change is excluded by the intent | reject |
| 8 | blind | AD-7 points to an untracked spec; no evaluation evidence in the diff | false | the spec is committed with the change; the evaluation is run by the orchestrator after review | reject |
| 9 | blind | `opens_with_not_available` has no direct unit tests | low | covered through the pipeline tests; the re-derivation adds the real chunk shapes | reject |

Review pass 2 (after the re-derivation).

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 10 | blind, edge-case, verification-gap | Any held text starting with ขออภัย is held to its line break, also when it can no longer match ("ขออภัย เราไม่สามารถ…"), so such a one-paragraph answer does not stream | medium | `_held_reply_declines` returns `None` on `start.startswith("ขออภัย")`; `own-chances-and-employment-proof` replied "ขออภัย เราไม่สามารถทราบผลอนุมัติ…" in the last run; the decision says hold only while it "could still be" an opening | patch |
| 11 | blind | No test ties the patterns to the texts they come from | low | rewording the prompt's example sentence or `reply-no-answer` would silently disarm the guard; the fix is one direct test | patch |
| 12 | blind | Docstrings: declined `Spent` shown as unconditional; "the check runs once" though it runs per chunk until it decides | low | module and `answer_question` docstrings vs the loop | patch |
| 13 | edge-case | The apology alone on the first line and "ไม่มีข้อมูล…" on the next line bypass the guard | low | true, but not seen in any run (the model writes the sentence on one line), and the fix adds a branch | reject |
| 14 | edge-case | A turn word that starts the second line ("…เรื่อง X\nแต่สามารถ…") does not stop a decline | low | the decided rule looks at the first line only; the seen `application-steps` shape has แต่ on the first line | reject |
| 15 | blind | A partial answer that puts its "not covered" sentence first is declined | low | the citing prompt puts the answered part first; the decided rule declines a first line that is only the not-available sentence | reject |
| 16 | edge-case | A leading quote, emoji or list number hides the opening | low | not seen in any run; the decision lists the marks to skip | reject |
| 17 | blind, edge-case | Compounds such as เพียงแต่, แต่ก่อน count as a turn; อย่างไรก็ดี does not | low | errs towards answering; the decision names แต่ and อย่างไรก็ตาม with three excluded compounds | reject |
| 18 | blind | Particle and punctuation variants (คะ, ด้วยค่ะ, a comma after ขออภัย) are missed | low | the decision lists the particles; not seen in any run | reject |
| 19 | blind, edge-case | U+2028 / `<br>` line breaks, `\r\n` untested, a few edge branches untested | low | not produced by either adapter in any run; `\r` ends the line before `\n` | reject |
| 20 | blind | Claude's wording is not tied to the patterns | false | no bad outcome: if Claude words it differently the guard does not fire and the answer is handled as before; a Claude run is already deferred | reject |
| 21 | blind | After a decline the chat stays busy until the model stops writing | low | true; the spec reads the stream to the end so the cost is logged (Claude cost matters) | reject (decided in the spec) |
| 22 | blind | A model error after a decline shows the error text under the no-answer text | low | the matrix row decides `Failed` as for any error after text | reject (decided in the spec) |
| 23 | blind | The spec is untracked; no web-level decline test; no evaluation evidence yet | false | the spec is committed with the change; consumers are unchanged and tested; the evaluation runs after review | reject |

## Verification

**Commands:**
- `uv run pytest` -- expected: exit code 0
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean

**Manual checks (if no CLI):**
- `LLM_PROVIDER=ollama MOCK_LLM=false uv run python scripts/run_eval.py` (local, free); the orchestrator runs it and compares.
