# Story 1.5: Claude connection with a test version

## 2026-11-14 kl. 22:14 — WannapaS

_Updated 22:40 after review and commit._

### Task
Implement Story 1.5 from its spec (dispatched implementation step): the `LLMClient` port, a scripted test fake, the Anthropic adapter with the fixed cache-friendly answer request, and a versioned answer prompt. Wiring into `/api/chat` is Story 1.6.

### Plan
- Spec: [spec-1-5-claude-connection-with-a-test-version.md](../../docs/implementation/spec-1-5-claude-connection-with-a-test-version.md); context: [epic-1-context.md](../../docs/implementation/epic-1-context.md).
- Checked the installed SDK (`anthropic` 2.4.0) for stream events, `output_config.effort`, adaptive thinking, usage fields and exception classes before writing the adapter.
- Port and fake first, then prompt loader and prompt, then adapter, then tests (stand-in client and the real SDK over `httpx2.MockTransport`).

### Result
- New: `app/ports/llm.py`, `app/adapters/file_prompts.py`, `app/adapters/anthropic_llm.py`, `prompts/answer-system.md` (`version: 1`), `tests/fakes/fake_llm.py`, `tests/test_llm_port.py`, `tests/test_anthropic_llm.py`, `tests/test_prompts.py`, `tests/test_layering.py`.
- Changed: `tests/conftest.py` also clears `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_PROFILE`; the resolved entry removed from `docs/implementation/deferred-work.md`; spec tasks ticked and Implementation Notes added.
- Choices beyond the spec matrix: any stop reason other than `end_turn`/`stop_sequence` raises `LLMError`; every exception from the SDK call becomes `LLMError` (the SDK lets `httpx2` transport errors through mid-stream); `answer` without a key raises `LLMError`; the fake raises its error/refusal after the scripted chunks.
- Review (3 reviewers, triage in the spec's Review Triage Log): 9 findings patched — documents sorted by id inside `answer`, SDK client built in `__init__` (no lazy race), tests for the real-key client path, `None` cache tokens and port signatures, layering test also forbids `app.adapters`/`app.web` imports from pipeline/ports, prompt explains `[removed]`, treats documents as information only, names udi.no in step 3. 1 deferred (explicit timeout/retries, Story 1.6), 6 rejected.
- `uv run pytest`: 381 passed, no network, no key.
- Committed to main as `dba4e2d` (Story 1.5). Spec `done`, sprint status `review`. Not pushed.
- Closed in issues.md: layer/import test and clearing `ANTHROPIC_AUTH_TOKEN`.

### Open items
- Story 1.6: set an explicit timeout and retries on the Anthropic client (deferred-work.md).
- Manual check with a real `ANTHROPIC_API_KEY` (Thai answer with a source id; cache write on the first call, cache read on the second) not run: no `.env` in the workspace.
