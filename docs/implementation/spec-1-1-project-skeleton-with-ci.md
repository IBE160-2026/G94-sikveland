---
title: 'Story 1.1: Project skeleton with CI'
type: 'chore'
created: '2026-11-03'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'af619a1681d66d25f79e3f4ba7a6ea64bd53e5b5'
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repository holds only planning documents. Every later story needs the same runnable structure, configuration and automated tests, checked on every push.

**Approach:** A uv-managed Python 3.12 FastAPI app with the architecture's folder layout, a pydantic-settings config module reading every setting from `.env`, a health endpoint, a pytest suite, and a GitHub Actions workflow that runs it without an API key.

## Boundaries & Constraints

**Always:**
- Folder layout and layer rules from the architecture: `app/{web,pipeline,ports,adapters,static}`, `app/main.py`, `app/config.py`, plus `content/`, `prompts/`, `knowledge-base/`, `scripts/`, `eval/`, `tests/`, `data/`. Routes live in `app/web/`; `main.py` only wires.
- Stack pins at the architecture's minor versions (compatible-release `~=X.Y.0`): fastapi 0.162, uvicorn 0.54, anthropic 2.4.0, pydantic-settings 2.16, PyYAML 6.0, httpx 0.28, markdownify 1.2, pypdf 6.21; pytest 9.2 in a dev group. `uv.lock` committed.
- Settings (exact env names): `ANTHROPIC_API_KEY` (optional), `MODEL_ANSWER`, `MODEL_SMALL`, `EFFORT_ANSWER`, `EFFORT_SMALL`, `MOCK_LLM`, `ADVISER_CONTACT`, `DATABASE_PATH`, `PRICE_ANSWER_{INPUT,OUTPUT,CACHE_READ,CACHE_WRITE}`, `PRICE_SMALL_{INPUT,OUTPUT,CACHE_READ,CACHE_WRITE}`.
- Decisions: defaults `MODEL_ANSWER=claude-opus-5-5`, `MODEL_SMALL=claude-haiku-5-5`, `EFFORT_ANSWER=medium`, `EFFORT_SMALL=low` (effort limited to `low|medium|high|xhigh|max`), `MOCK_LLM=false`, `ADVISER_CONTACT=ngan.visaa@gmail.com`, `DATABASE_PATH=data/feedback.sqlite3`. Prices (USD per million tokens): answer 4.00 / 20.00 / 0.20 / 5.00; small 0.10 / 0.50 / 0.01 / 0.125.
- `data/` is git-ignored except `data/.gitkeep`, so it exists in a fresh clone. Empty folders hold a `.gitkeep`.
- Tests never see a real API key: they build settings without the `.env` file and with `ANTHROPIC_API_KEY` removed from the environment.

**Never:**
- No Claude calls, LLM port, chat page, content files or README rewrite (later stories).
- No secrets in the repo; `.env` stays ignored.
- No `anthropic` import outside `app/adapters/` (none needed yet).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Health | `GET /api/health` | 200 `{"status": "ok"}` | N/A |
| No `.env`, no env vars | fresh clone, CI | app starts with defaults, key is `None` | N/A |
| Env override | `EFFORT_ANSWER=high` in env or `.env` | setting is `high` | N/A |
| Bad effort | `EFFORT_ANSWER=extreme` | settings fail to load | pydantic `ValidationError` names the field |

</frozen-after-approval>

## Code Map

- Greenfield: no Python code exists. Reuse nothing; keep `_bmad/`, `.claude/`, `docs/`, `.logs/` untouched.
- `.gitignore` -- already ignores `.env`, `.env.*` (keeps `.env.example`), `.venv/`, `__pycache__/`, `.pytest_cache/`; add only the `data/` rules.
- Local tools: uv 0.13.1 and CPython 3.12.10 are installed.
- `README.md` -- out of scope (Story 4.3); leave as is.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `.python-version`, `uv.lock` -- project `norway-visa-guide`, `requires-python = ">=3.12,<3.13"`, `[tool.uv] package = false`, dev group with pytest, `[tool.pytest.ini_options]` with `pythonpath = ["."]` and `testpaths = ["tests"]`; run `uv lock` -- pinned, reproducible install.
- [x] `app/__init__.py`, `app/{web,pipeline,ports,adapters}/__init__.py`, `app/static/.gitkeep`, `.gitkeep` in `content/`, `prompts/`, `knowledge-base/`, `scripts/`, `eval/`, `data/` -- the layout.
- [x] `app/config.py` -- `Settings(BaseSettings)` reading `.env` (UTF-8), fields and defaults as above, `ANTHROPIC_API_KEY` as optional `SecretStr`; `get_settings()` cached -- one config source.
- [x] `app/web/health.py` -- `APIRouter` with `GET /api/health` -- first route in the web layer.
- [x] `app/main.py` -- `create_app(settings: Settings | None = None)` stores settings on `app.state`, includes the health router; module-level `app = create_app()` for uvicorn -- wiring only.
- [x] `.env.example` -- every setting with its default, empty `ANTHROPIC_API_KEY`, one comment line per group (prices from Anthropic's pricing page) -- setup reference.
- [x] `.gitignore` -- add `data/*` and `!data/.gitkeep`.
- [x] `tests/conftest.py`, `tests/test_health.py`, `tests/test_config.py`, `tests/test_layout.py` -- autouse fixture removing `ANTHROPIC_API_KEY`; health test via `TestClient`; config tests for defaults, env override, `.env` file in `tmp_path`, bad effort, and that `.env.example` keys equal the `Settings` fields; layout test that the folders exist.
- [x] `.github/workflows/ci.yml` -- on push and pull request: checkout, `astral-sh/setup-uv` (latest major, checked via `gh`), `uv sync --locked`, `uv run pytest`; no secrets passed.

**Acceptance Criteria:**
- Given a fresh clone, when I run `uv sync` and `uv run uvicorn app.main:app`, then the app starts and `GET /api/health` returns `{"status": "ok"}`.
- Given the repository, when I list it, then every folder named above exists, and `.env` and `data/` contents are git-ignored.
- Given a push to GitHub, when Actions runs, then `uv run pytest` passes with no API key and no call to the Claude API.

## Implementation Notes

- Implemented directly in the main session (no subagent).
- `env_ignore_empty=True` in `Settings`: an empty `ANTHROPIC_API_KEY=` (as in `.env.example`) loads as `None`, not an empty secret.
- `Settings(_env_file=None)` in tests keeps a developer's local `.env` out; `tests/conftest.py` also removes `ANTHROPIC_API_KEY` from the environment.
- CI uses `actions/checkout@v7` and `astral-sh/setup-uv@v10.3.3`. setup-uv publishes no moving major tag, so `@v10` failed the first Actions run ("unable to find version `v10`"); it is pinned to the full release tag.
- `uv lock` resolved 40 packages; `uv sync --locked` is clean. `uv run pytest`: 19 passed. Server started with uvicorn and `/api/health` returned `{"status":"ok"}`. `git check-ignore` confirms `.env` and `data/feedback.sqlite3` are ignored while `data/.gitkeep` and `.env.example` are tracked.
- Matrix coverage: health → `test_health_returns_ok`, `test_module_app_serves_health`; no `.env` → `test_defaults_without_env_file`, `test_module_app_serves_health`; env override → `test_env_var_overrides_default`, `test_reads_env_file`; bad effort → `test_invalid_effort_fails` (both effort fields).
- Review patches (pass 1): `tests/conftest.py` now sets `Settings.model_config["env_file"] = None` and removes every settings variable from the environment at import, before test modules load, so importing `app.main` never reads a local `.env` or key. `Settings` reads `.env` from the project root (`ROOT / ".env"`), with `utf-8-sig` (BOM-safe) and `extra="forbid"` (typos in `.env` fail). Prices are non-negative finite floats. New tests: module-level app, git-ignore rules, `EFFORT_SMALL`, invalid prices, BOM, misspelled key. CI has `permissions: contents: read`. `.env.example` says which prices are derived. 30 tests pass; checked with a local `.env` holding a fake key and a bad value plus shell overrides: tests still pass. Uvicorn health check repeated: `{"status":"ok"}`.

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | edge, blind, verif | `app.main` import at collection runs `create_app()` → real `.env`/key cached in tests | medium | `tests/test_health.py` imports `app.main` before the autouse fixture ran; contradicts "tests never see a real key". patch: conftest disables env file and clears env at import |
| 2 | edge, blind, verif | Shell-exported settings leak into config tests | low | only `ANTHROPIC_API_KEY` was removed; `MOCK_LLM` etc. in a shell broke defaults test. patch (same conftest change) |
| 3 | edge | `.env` with UTF-8 BOM drops first key silently | medium | PowerShell 5.1 `Out-File` writes a BOM on this machine; `extra=ignore` hid `﻿KEY`. patch: `utf-8-sig` + test |
| 4 | edge, blind | Misspelled `.env` key ignored silently | low | `extra="ignore"`; direct one-word fix. patch: `extra="forbid"` + test |
| 5 | edge, blind | `.env` resolved against CWD | low | `env_file=".env"`; uvicorn from another folder skipped it. patch: `ROOT / ".env"`. `database_path` resolution deferred to Story 2.3 (creates the DB) |
| 6 | edge, blind | No startup error when `MOCK_LLM=false` and no key | false | frozen matrix requires "No `.env`, no env vars → app starts, key is `None`"; key check belongs to adapter wiring (Story 1.5) |
| 7 | edge, blind | Prices accept negative/NaN/inf | low | plain `float`. patch: `Price` type with `ge=0`, no inf/nan + test |
| 8 | blind | Nothing enforces "no Claude API call"; `ANTHROPIC_AUTH_TOKEN`/profiles not cleared | false | no `anthropic` import exists (grep), so no call path. Note for Story 1.5: the SDK also reads `ANTHROPIC_AUTH_TOKEN` and `ant` profiles |
| 9 | blind | No test enforces layer/import rules | low | no violation possible yet; deferred to Story 1.5 when `anthropic` is first imported |
| 10 | blind, verif | Git-ignore AC checked by hand only | low | no test called `git check-ignore`. patch: `tests/test_layout.py` ignore/tracked tests |
| 11 | blind | Layout test skips `.gitkeep`, `main.py`, `config.py`, `tests/fakes/` | false | CI runs on a fresh checkout, so a missing `.gitkeep` fails `test_folder_exists`; `main.py`/`config.py` are imported by tests; `tests/fakes/` is Story 1.5 |
| 12 | blind | `.env.example` price comment overstates source | low | Haiku cache read and cache writes are derived. patch: comment says which |
| 13 | blind | CI hardening (permissions, branch filter, concurrency, timeout, cache, SHA pins) | low | default token scope is wider than needed. patch: `permissions: contents: read`; rest rejected (low, no everyday harm) |
| 14 | blind | No linter/type checker | low | not required by intent; adds tooling. rejected |
| 15 | blind | Sprint status `in-progress` vs spec `in-review`; MM-DD date | false | sprint sync to `review` happens at the present step; date format is the sprint script's contract |
| 16 | blind | Epic context: demo mode in Epic 1 requirements but adapter in Epic 4 | low | wording error in a doc. patch: line now says demo mode arrives in Epic 4 |
| 17 | blind | Personal email as code default | false | the adviser's agency contact is the PRD's adviser contact and a frozen default |
| 18 | blind | Two HTTP stacks (`httpx` and SDK's own) | false | `httpx` 0.28 is pinned by the architecture for ingest and is FastAPI `TestClient`'s dependency |
| 19 | blind | Health handler docstring; no typed settings accessor | low | cosmetic; accessor comes with the first route that needs settings. rejected |
| 20 | blind | Review patch omits the spec file | false | intentional: the spec goes to the edge-case layer only as claims file |
| 21 | verif | `app.main:app` and `get_settings()` path untested | medium | pre-verified: renaming `app` broke uvicorn with CI green. patch: `test_module_app_serves_health` |
| 22 | verif | `EFFORT_SMALL` validation not pinned | low | pre-verified. patch: parametrized `test_invalid_effort_fails` |

## Design Notes

Haiku 5.5 cache-read price is not in the reference used; 0.01 follows the general 0.1× input rule. Small-model calls send no cached prefix, so it does not affect reported cost; check it on the pricing page when Story 1.8 lands. Cache write uses the 1.25× input rule (5-minute cache).

## Verification

**Commands:**
- `uv sync --locked` -- expected: installs without changing `uv.lock`
- `uv run pytest` -- expected: all tests pass
- `uv run uvicorn app.main:app` then `curl http://127.0.0.1:8000/api/health` -- expected: `{"status":"ok"}`
- `git check-ignore .env data/feedback.sqlite3` -- expected: both paths printed
