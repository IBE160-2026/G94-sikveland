# Testset-pregnancy-partial-answer

## 2026-11-18 kl. 23:05 — WannapaS

### Oppgave
The user accepted the Ollama partial answer to the pregnancy question ("you can apply as usual" with sources, then "no information about special conditions") and asked to update the test case.

### Plan
- Move the case from no-answer to answered with an expected fact the sources state.
- FR4/NFR4 need at least four no-answer cases and 20-30 cases in all, so: a new no-answer case whose topic no snapshot covers (checked by grep: no snapshot mentions colour or black-and-white copies, only the colour photo), and one case removed (user chose `fee-adult-and-child`; fee stays covered by `fee-where-to-pay-typo` and `follow-up-young-child-fee`).

### Resultat
- Commit `e734fe5` (Norwegian message), `eval/testset.yaml` only: `no-answer-pregnancy` → `pregnancy-apply-as-usual` (answered; fact: the usual steps, register and pay online at UDI, hand in at VFS; sources `udi-how-to-apply-visitor-visa`, `embassy-online-registration`, `embassy-hand-in-documents`; tags partial-answer, steps), new `no-answer-colour-copies` (สำเนาเอกสารที่ต้องยื่น ถ่ายเอกสารขาวดำได้ไหม หรือต้องเป็นสำเนาสีคะ), `fee-adult-and-child` removed. Still 30 cases: 15 answered, 4 no-answer.
- Thai question and expected fact approved by the user as adviser review (NFR8); recorded in the file header.
- `uv run pytest`: 1509 passed, exit code 0.
- Pushed to `origin/main` at the user's request.
- Closed in issues.md: the pregnancy partial-answer decision.

### Åpne punkter
- The new case and the changed one have not been through an evaluation run yet; the next Ollama (and Claude) run shows how they score. Older reports still list the old ids.
