---
title: 'OLLAMA_THINK setting for models without thinking'
type: 'feature'
created: '2026-11-21'
status: 'done'
route: 'oneshot'
baseline_commit: '4589d3408418d4c947d67e6e3762e6d562340348'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `qwen3.5:9b` sometimes puts Chinese words into Thai answers (4 of about 265 replies in the last nine evaluation reports, and the user saw it in the app). The user wants to try a Thai-tuned model, starting with `scb10x/typhoon2.1-gemma3-12b`. The Ollama answer call always sends `"think": true` (`app/adapters/ollama_llm.py` `build_chat_request`), and Ollama rejects that with HTTP 400 for a model that lacks the thinking capability, which none of the Typhoon models on Ollama have. So every answer would fail.

**Approach:** A new setting `OLLAMA_THINK` (bool, default `true`, so `qwen3.5:9b` works exactly as today) decides the `think` value of the Ollama answer request. Classify and translate already send `think: false` and do not change. The evaluation report's header names the setting when the provider is Ollama, so runs with different models can be compared. `.env.example` and the README document the setting and replace "the model must support thinking" with "or set `OLLAMA_THINK=false`".

**Decisions (user, 2026-11-21):** try the recommended Typhoon 2.1 Gemma3 12B first; subagents allowed (one reviewer). Builder's choice: the report header shows the setting.

</frozen-after-approval>

## Implementation Notes

- `app/config.py`: `ollama_think: bool = True`. `app/adapters/ollama_llm.py`: `build_chat_request` takes a required keyword `think`, and the answer call passes `settings.ollama_think`; classify and translate keep `think: False`.
- `scripts/run_eval.py`: with Ollama the header gets `- Answer thinking: on|off` after the classify model; Claude reports have no such line.
- Docs: `.env.example` (`OLLAMA_THINK=true` with a comment), the README settings table, Ollama step 1 and the report description.
- Tests: config default, env override and invalid value; the request sends `think: false` when the setting is off; report line on/off/absent. `uv run pytest`: 1545 passed, exit code 0; ruff clean.
- Surprise: the live check showed that Ollama 0.40.16 lists `scb10x/typhoon2.1-gemma3-12b` with the `thinking` capability, and `think: true` works. Its ollama.com page shows no thinking badge, which is what the Problem statement relied on. The user chose (2026-11-21) to keep the setting and run the evaluation with Typhoon twice, thinking on and off. The setting is still needed for models without thinking, such as Typhoon 2.5, which is built on Qwen3 Instruct 2507 (not checked locally).
- Second surprise, from the first evaluation run with Typhoon 2.1 (thinking on): every case failed at classification with HTTP 400. Ollama refuses structured output for this model (`format` with a schema and also `format: "json"`: "Failed to initialize samplers"). Classification needs `format`, so this model cannot run the app; that is unrelated to thinking. The user chose (2026-11-21) to try `scb10x/typhoon2.5-qwen3-30b-a3b` next. Its docs now name Typhoon 2.1 as the example of a model without structured output, not as a model without thinking.
- Review fixes: `.env.example` and README describe a model without thinking in general terms (`ollama show` capabilities); README and the evaluation's all-failed message explain HTTP 400 (no thinking, or no structured output) against 404 (not pulled); the latency note says it holds with `OLLAMA_THINK=true`; the module docstring names the setting. 1545 passed, exit code 0; ruff clean.

## Review Triage Log

One reviewer (blind hunter).

- medium, patched: the docs named Typhoon 2.1 as a model without thinking; the live check showed it has thinking.
- low, patched: the evaluation's all-failed message didn't mention HTTP 400 and its causes.
- low, patched: the README troubleshooting didn't cover a model that doesn't fit (400 against 404).
- low, rejected: a fixed hint on HTTP 400 in the adapter log. Today's 400 came from structured output, not thinking, so a hint naming `OLLAMA_THINK` would mislead; the README now explains both causes.
- low, patched: the module docstring said thinking is always on.
- low, patched: the README latency note applies only with thinking on.
- low, rejected: README step 2 doesn't list `OLLAMA_THINK`. Step 1 explains when to set it, and the settings table lists it.
- low, rejected: the request log doesn't record the setting. The log has a fixed set of fields, and runs are compared through the evaluation report, whose header shows it.
- low, rejected: report file names don't show the model or the setting. The header shows both, and the README says so.
- maybe-false: `think: false` was never checked live against a model without thinking. It will be settled by a single request to Typhoon 2.5 once it is pulled, before its evaluation run.
- false: "the spec isn't finished". It was mid-workflow; the notes say the premise was wrong and the docs were corrected.
- low, rejected: no test checks that classify and translate ignore the setting. Their builders take no `think` argument and hard-code `False`, which existing tests pin, so threading the setting in would need a signature change those tests would catch.
