# Ollama-chinese-word-repair

## 2026-11-22 kl. 22:36 — WannapaS

### Oppgave
The user tested the app on Ollama and still saw Chinese words in the Thai answers. Fix it so applicants never see them. User decision: replace each Chinese word with Thai (not just remove it, and no switch to Typhoon).

### Plan
- `bmad-build` with subagents (one implementer, three reviewers). Spec: [`docs/implementation/spec-ollama-chinese-word-repair.md`](../../docs/implementation/spec-ollama-chinese-word-repair.md).
- Ollama adapter only: from the first CJK character, hold the rest of the answer. After the stream ends, one small call (same model, thinking off, JSON schema) gives a Thai word per CJK word, and code puts it in place. A word without a usable Thai word, or every word when the call fails, is removed.

### Resultat
- Commit `3cb0533` on `main` (not pushed):
  - `app/adapters/ollama_llm.py` (hold, `normalise_script`, `find_cjk_runs`, `build_repair_request`, `parse_repair_reply`, `apply_replacements`, `_repair`)
  - new `prompts/ollama-script-repair.md` (version 1, logged as `repair`)
  - `app/main.py`; tests; README; AD-2 and AD-12 notes in the architecture spine
- Fullwidth digits and letters and CJK punctuation (`９０`, `，`, `（）`, `。`) are turned into ordinary characters in code. They don't trigger a model call.
- Ollama eval report names now end in `-repair-1`. The repair call's tokens are added to the answer's tokens in the request log.
- Live check by the implementer on qwen3.5:9b: the five Chinese words from the eval reports all got Thai words (e.g. 申请人 → ผู้ยื่นคำขอ, 申请表 → ใบสมัคร); about 0.5 s per call after the model was loaded. Two of them are loose: 你们是 → คู่รัก, 并提交 → พร้อมกับยื่นแบบฟอร์ม.
- 1606 tests pass (pytest exit 0), ruff clean.
- Full Ollama eval run, report `eval/reports/2026-11-22-answer-1-classifier-4-citing-3-repair-1.md` (commit `35962a7`):
  - No Chinese left in any of the 29 replies.
  - General questions: 11 of 14 pass the automatic checks; earlier runs got 11-14.
  - No-answer 4 of 4, individual assessment 3 of 3, reach a person 4 of 4.
  - None of the misses come from the repair:
    - `relationship-proof-unmarried-partner` and `passport-validity` opened with the not-available sentence.
    - `own-chances-and-employment-proof` cited the wrong source.
    - In `passport-validity` and `own-chances-and-employment-proof`, the model also wrote `embassy-visa-checklist`, which scored 0.84 against `embassy-visitor-visa-checklist`, just under the 0.85 cutoff.
  - The repair's info log line isn't shown by the eval script, so the number of repaired answers is unknown.
- Pushed to `origin/main` (with the deadline change and the logs).
- Review: 7 findings fixed, 8 rejected, 1 deferred to `deferred-work.md` (the repair call may push the cached knowledge base out of Ollama, as the classifier call may; unverified).

### Åpne punkter
- Not yet tried in the running app. Ask a Thai reader to check how repaired answers read.
- `embassy-visa-checklist` missed the 0.85 cutoff at 0.84 twice in this run (3 times in total). That supports lowering the cutoff to 0.80; see the open item from 2026-11-21.
- The held part of an answer appears only when the answer is finished, so the answer pauses after the first Chinese character.
