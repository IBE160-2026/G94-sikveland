# PRD: Norway Visa Guide For Thai

## 2026-11-02 kl. 22:16 — WannapaS

### Task
Continue the PRD from the previous session (BMAD `bmad-prd`, coaching path, journey-led) and finish it. Then commit, merge into main and push.

### Plan
- Recover the UJ-2 sample dialogue (Michael visits his aunt) from the previous session, which had not been saved, and draft UJ-2.
- Draft the remaining sections with the user: Glossary, Features/FRs, NFRs, Success Metrics, Non-Goals, MVP Scope, Open Questions, Assumptions.
- Finalize: memlog audit → reconcile with 4 inputs (subagents) → rubric review → triage open items → light polish → status final.
- Decision log: `docs/planning/prds/prd-G94-sikveland-2026-10-19/.memlog.md`.

### Result
- `docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md` is complete with `status: final`:
  - UJ-1 and UJ-2 confirmed, plus a Glossary.
  - FR1–FR14 (FR1–FR11 IDs kept; new FR12 application steps in order, FR13 reach a person, FR14 out-of-scope questions).
  - NFR1–NFR8 (new NFR8: the adviser reviews Thai texts).
  - Success metrics: SM-2 test set (during the course), SM-1 "Yes" share (after launch), SM-C1 counter-metric.
  - Scope: hosting is out of the MVP; local run + demo mode is enough for the course.
- Key decisions:
  - Individual-assessment questions get the answer "the embassy decides".
  - The feedback question is asked on a done signal.
  - Personal information (passport, ID and phone number) is deleted, and the rest of the question is answered.
  - Checklists are fixed per visit purpose (tourism, visiting family, visiting friends), with ticks saved on the phone.
  - The person in Norway is called "the sponsor".
- `addendum.md`: technical notes for the architecture, plus Michael's dialogue word for word.
- Reconciled with the product brief, the teacher's feedback, the implementation plan and epics-and-stories (`reconcile-*.md`). Rubric review (`review-rubric.md`): 0 critical and 2 high findings, both fixed.
- Commit `00518c5` ("Ferdigstill PRD …") is on main and pushed. It was rebased onto Bård's two sesjonslogg commits, with no conflicts.

### Open items
- `epics-and-stories.md` and `implementation-plan.md` are out of date compared with the PRD: FR3, FR5, FR6 and FR9 changed meaning; FR12–FR14 and NFR8 are new; about 12 stories need updating. Use `bmad-correct-course` or `bmad-create-epics-and-stories`.
- PRD §9: IBE160 deadline and group size, which decide the priority order in §8.1.
- PRD §9: response-time limit and measurable mobile limits for NFR1.
- PRD §9: how to measure that the checklist replaces the adviser's document check.
- PRD §10: unconfirmed assumptions: Fah is a first-time applicant, and Michael reads Thai.
- The grading guide (Sensorveiledning IBE160 Del 1, PDF) is not in the repo, so the PRD has not been checked against it.
- The full structure and language review (`bmad-review` lenses structure, prose) was skipped at finalization.
- Next planning steps: `bmad-ux` and `bmad-architecture`.
