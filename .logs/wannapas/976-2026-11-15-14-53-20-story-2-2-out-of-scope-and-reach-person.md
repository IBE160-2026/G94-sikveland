# Story 2.2: other visa types and requests for a person

## 2026-11-15 kl. 14:53 — WannapaS

### Task
Build Story 2.2: questions outside short-stay tourist and visitor visas to Norway get a fixed text with the adviser contact (FR14), and so do requests for a person or for help with the whole application (FR13).

### Plan
- `bmad-build` oneshot route (no intent gaps; the PRD defines "out of scope"), built inline on `main` with a blind-review subagent (user approved). Spec [spec-2-2-other-visa-types-and-requests-for-a-person.md](../../docs/implementation/spec-2-2-other-visa-types-and-requests-for-a-person.md).
- Reuse the Story 2.1 fixed-reply path: two more classifier categories, two text keys, classifier prompt version 2.

### Result
- Commit `c46b4c7` on `main` (not pushed). `CLASSIFIER_CATEGORIES` and `FIXED_REPLY_KEYS` grow by `out_of_scope` and `reach_person`; `reply-out-of-scope` and `reply-reach-person` in `content/texts.yaml` (Thai DRAFT); `prompts/classifier-system.md` v2 with rules for mixed questions, Norway plus other Schengen countries, greetings, follow-ups and precedence; README, MT-06 (new no-answer example: vaccinations, since the weather is now out of scope), new MT-13. Sprint status: Story 2.2 `review`.
- Behaviour change: a weather or other non-visa question now gets the out-of-scope text instead of the no-answer text (PRD glossary, FR14).
- Review: 13 findings; 11 patched, 1 deferred (demo mode cannot show the new categories), 1 rejected.
- `uv run pytest`: 853 passed; ruff clean. Live Ollama check (`qwen3.5:9b`): 22 of 22 questions sorted as intended, partly the prompt's own examples.

- The user approved both Thai texts; the DRAFT note in `content/texts.yaml` is replaced by the approval.

### Open items
- Run MT-13 with a real Claude key (and Ollama).
