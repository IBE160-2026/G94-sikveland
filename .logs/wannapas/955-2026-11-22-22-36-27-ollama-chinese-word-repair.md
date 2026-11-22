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
- Review: 7 findings fixed, 8 rejected, 1 deferred to `deferred-work.md` (the repair call may push the cached knowledge base out of Ollama, as the classifier call may; unverified).

### Åpne punkter
- Not yet tried in the running app or in a full eval run. Ask a Thai reader to check how repaired answers read.
- The held part of an answer appears only when the answer is finished, so the answer pauses after the first Chinese character.
