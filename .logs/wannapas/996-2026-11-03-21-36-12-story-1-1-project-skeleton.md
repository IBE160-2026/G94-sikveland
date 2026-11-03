# Story 1.1: Project skeleton with CI

## 2026-11-03 kl. 21:36 — WannapaS

### Task
Build Story 1.1 from `docs/planning/epics.md` with `bmad-build`: a runnable project skeleton with configuration, tests and CI, so later stories start from the same structure.

### Plan
- Compiled `docs/implementation/epic-1-context.md` (inline, no subagent).
- Spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md` (route dispatch, approved by the user). Prices and effort values taken from the claude-api skill reference.
- Implemented directly in the main session; review with three reviewer subagents (Blind Hunter, Edge Case Hunter, Verification Gap), which the user approved.

### Result
- New: `pyproject.toml` + `uv.lock` (Python 3.12, stack pins from the architecture), `.python-version`, folder layout with `.gitkeep`, `app/config.py` (16 settings from `.env` in the project root), `app/web/health.py` (`GET /api/health`), `app/main.py` (`create_app()`, `app.main:app`), `.env.example`, `tests/` (30 tests), `.github/workflows/ci.yml` (`actions/checkout@v7`, `astral-sh/setup-uv@v10`, `uv sync --locked`, `uv run pytest`, `permissions: contents: read`). `.gitignore` ignores `data/*` except `data/.gitkeep`.
- Defaults: `claude-opus-5-5` (effort medium) for answers, `claude-haiku-5-5` (effort low) for small calls; prices Opus 4.00/20.00/0.20/5.00 and Haiku 0.10/0.50/0.01/0.125 USD per million tokens.
- Review: 22 findings, 13 fixed in the same pass. The main fix: importing `app.main` during test collection read the local `.env` and key, and now it can't. Also fixed: BOM-safe `.env` (`utf-8-sig`), typos in `.env` fail (`extra="forbid"`), `.env` found from any working directory, prices must be non-negative and finite, plus new tests for the uvicorn app object, the git-ignore rules and `EFFORT_SMALL`. Triage log in the spec.
- Verified: `uv sync --locked` clean, `uv run pytest` 30 passed (also with a fake local `.env` key, a bad value and shell overrides), uvicorn `/api/health` → `{"status":"ok"}`, `git check-ignore` OK.
- Sprint status: `epic-1: in-progress`, `1-1-project-skeleton-with-ci: review`. Spec `status: done`.
- Commit `7ef864c` on main, pushed. The first Actions run failed before the tests: `astral-sh/setup-uv@v10` does not exist (the project publishes no moving major tag). Fixed in `7a0d12c` by pinning `@v10.3.3`; the next run passed with 30 tests (https://github.com/IBE160-2026/G94-sikveland/actions/runs/41714502720).

### Open items
- Story 2.3: resolve `DATABASE_PATH` against the project root (in `docs/implementation/deferred-work.md`).
- Story 1.5: add a test for the layer/import rules, and clear `ANTHROPIC_AUTH_TOKEN` in tests (in `deferred-work.md`).
- `README.md` still links to the deleted `docs/planning/epics-and-stories.md`.
