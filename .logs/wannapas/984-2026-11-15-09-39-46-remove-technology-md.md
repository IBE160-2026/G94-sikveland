# Remove technology.md

## 2026-11-15 kl. 09:39 — WannapaS

### Task
Remove `docs/planning/architecture/technology.md` before the part 1 deadline. It describes another app (Pytagoras Forlag's website), and the grading guide lists "planning documents describe a different app" as a warning sign.

### Plan
- Checked that no file in the repo links to it (only session logs mention it).
- Deleted it with `git rm`; it is still in history at `9d809eb`.

### Result
- Deleted in `0a5aa83` (not pushed). `uv run pytest`: 584 passed.
- Closes two items in issues.md: the decision about technology.md, and asking Bård whether it belongs in the repo (no longer needed).

### Open items
- None.
