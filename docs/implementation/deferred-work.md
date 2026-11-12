# Deferred Work

- source_spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md`
  summary: Resolve `DATABASE_PATH` against the project root, not the working directory, when Story 2.3 creates the SQLite file.
  evidence: `database_path` is the relative string `data/feedback.sqlite3`; started from another folder, the feedback file would be created in the wrong place. Nothing uses it before Story 2.3.
- source_spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md`
  summary: Add a test that only `app/adapters/anthropic_llm.py` imports `anthropic` and that `app/pipeline/` imports neither FastAPI nor the SDK, in Story 1.5.
  evidence: The architecture's main layer rules are backed only by docstrings; the first `anthropic` import arrives in Story 1.5. Story 1.5 should also clear `ANTHROPIC_AUTH_TOKEN` in tests, since the SDK reads it and `ant` profiles as well as `ANTHROPIC_API_KEY`.
- source_spec: `docs/implementation/spec-1-2-chat-page-with-thai-texts.md`
  summary: Add a browser-level test (e.g. Playwright via pytest) for the chat page's JavaScript in Story 1.6: rendering from `/api/texts`, tap-to-fill, the retry button on load failure, and the streamed answer.
  evidence: No test runs `app/static/app.js`; changing `example.text` to `example.th`, dropping the tap handler, or removing `loadFailed.hidden = false` all pass CI. Story 1.6 adds much more page logic (stream reading), so the gap grows there.
