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
