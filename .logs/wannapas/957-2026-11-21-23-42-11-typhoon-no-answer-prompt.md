# Typhoon-no-answer-prompt

## 2026-11-21 kl. 23:42 — WannapaS

### Oppgave
Prompt work so `scb10x/typhoon2.5-qwen3-30b-a3b` (`OLLAMA_THINK=false`) gives the no-answer text for questions the sources don't cover, without making `qwen3.5:9b` worse (no-answer was 1/4 in `eval/reports/2026-11-21-answer-1-classifier-4-citing-3-5.md`).

### Plan
- `bmad-build` started (subagents allowed); still in planning, so no spec has been written yet.
- Experiments first: a scratch script outside the repo runs chosen test cases through the real pipeline (`scripts/run_eval.run` with a filtered test set) and patches the prompt in memory, so each variant takes minutes instead of a full run.

### Resultat
No change in the repo: `prompts/answer-citing-markers.md` was edited for one trial and then restored exactly (version 3). Findings, from Typhoon 2.5 on the 4 no-answer cases (and on all 18 general cases where noted):
- Baseline, today's prompt: `document-translation`, `pregnancy` and `interpreter-at-vfs` missed 3 of 3 times each (confident made-up answers); `vaccination-certificate` was ok 3 of 3.
- A stricter rule in the citing addendum ("find the sentence that answers exactly…; that the documents mention no rule does not mean there is no rule"): no effect, the same three missed 3/3.
- The same reminder at the end of the system prompt, after the ~24,600 tokens of documents: no effect, the same three missed 3/3.
- The reminder appended to the applicant's question (the last user message), in English: no-answer 4/4 twice on the 4 cases. On all 18 general cases twice, all 14 answerable cases were answered both times, but `no-answer-document-translation` missed both times ("translation is not needed"; no source mentions translation), so about 50% on that case.
- The same reminder in Thai: no-answer 4/4 twice on the 4 cases, but on all 18 cases it over-refused. 5 answerable cases missed twice and 2 once (e.g. passport validity, child fee, ID card). Thai wording is worse.

### Åpne punkter
- Decide whether to build the English reminder after the question into the Ollama adapter (an app change: a new prompt file or section, Ollama only, also sent to qwen3.5). Before deciding, measure it on `qwen3.5:9b` too, and make it stronger for the translation case.

## 2026-11-22 kl. 21:21 — WannapaS

### Oppgave
Continue from 2026-11-21: measure the English reminder appended to the applicant's question on `qwen3.5:9b` (the app's model, thinking on) before deciding whether to build it.

### Plan
- Reused yesterday's scratch harness (`try_cases.py`, outside the repo) with `USER_REMINDER=user-en.md`. It patches only the answer call (`build_chat_request`), not the classifier.
- All 18 general cases twice, then the cases that missed four more times.

### Resultat
No change in the repo. Results on `qwen3.5:9b` with the reminder:
- No-answer 4/4 in both runs, including `no-answer-document-translation` (Typhoon still missed that one about half the time).
- Answerable cases, 18-case runs: `own-chances-and-employment-proof` missed once (the classifier sent it to IA; the classifier doesn't get the reminder, and this is the known 2-in-4 classifier miss). `thai-id-hand-in-in-person` missed once (`LLMError`), `passport-validity` once (`no_answer`).
- Recheck, 4 runs: `passport-validity` `no_answer` 4/4, 5 of 6 in total. Without the reminder, qwen3.5 refused it once in 9 earlier reports. `thai-id-hand-in-in-person`: ok, `no_answer`, `LLMError`, ok.
- Conclusion: the reminder makes qwen3.5:9b refuse answerable questions that need a small step of reasoning ("my passport expires in 2 months", while the source gives a validity rule). As written, it isn't safe to send to both models.

### Åpne punkter
- Decide on the reminder: drop it (recommended with part 1 due 2026-11-23 23:59; qwen3.5 without it gets no-answer 3-4/4 with the guard), send it only to Typhoon (needs a model-specific setting), or soften the wording and measure again.
- The `LLMError` on `thai-id-hand-in-in-person` with the reminder (2 of 6 runs) was not investigated. It only matters if the reminder is built.
