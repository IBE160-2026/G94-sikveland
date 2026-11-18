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

## 2026-11-18 kl. 23:20 — WannapaS

### Oppgave
Run the Ollama evaluation on the updated test set; then, after the result, the user chose option 3: put the pregnancy case back as a no-answer case and take the colour-copies case out again. Commit the report and push.

### Plan
- Ollama evaluation; direct model calls on the two failing cases to see the raw replies (the report cannot tell a guard decline from zero citations).
- Option 3 (user): `no-answer-pregnancy` back as it was, `no-answer-colour-copies` removed, `fee-adult-and-child` stays out.

### Resultat
- Report `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-3.md`: no-answer 4 of 4 (colour copies worked), general 13 of 15 automatic (`pregnancy-apply-as-usual` and `passport-validity` got the no-answer text), individual assessment 3 of 3, reach person 4 of 4.
- Raw replies: `passport-validity` was a cited answer in two direct calls (the guard did not fire), so the miss was most likely a reply without citations; `pregnancy-apply-as-usual` opened with "ขออภัย ไม่มีข้อมูล…" and cited nothing in both calls (once adding uncited advice about a doctor's certificate), so the accepted partial answer was the less common shape.
- Commit `67f2b95`: `eval/testset.yaml` (29 cases: 14 answered, 4 no-answer; header records the 2026-11-18 changes), README (29 questions, 18 of 29 go to the answer model), and the report. `uv run pytest`: 1508 passed, exit code 0. Pushed at the user's request.

### Åpne punkter
- `passport-validity` came back as a no-answer once although direct calls cite correctly; watch it in the next runs.

## 2026-11-18 kl. 23:32 — WannapaS

### Oppgave
Run the Ollama evaluation again on the 29-case test set; commit the report and push.

### Plan
- Ollama run; direct model calls on the failing cases (three each) to see the raw replies.

### Resultat
- Report `eval/reports/2026-11-18-answer-1-classifier-4-citing-3-4.md`, committed 7ce3ea3 and pushed: no-answer 4 of 4, individual assessment 3 of 3, reach person 4 of 4, general 12 of 14 automatic.
- `sponsorship-form-validity` got the no-answer text with one dropped unknown id; a direct call showed the model misspelling an id (`udi-sponsor-for-visators`), so most likely only unknown ids were cited (the existing rule). `application-steps` got the no-answer text with no dropped id; three direct calls were cited step lists and the guard did not fire, so the cause in the run (zero citations or the guard) cannot be told from the report.

### Åpne punkter
- Offered, not decided: let the evaluation report say why a reply became the no-answer text (no citation, only unknown ids, or the guard), so misses like `application-steps` can be explained.
