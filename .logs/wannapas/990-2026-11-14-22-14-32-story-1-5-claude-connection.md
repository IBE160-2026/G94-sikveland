# Story 1.5: Claude connection with a test version

## 2026-11-14 kl. 22:14 — WannapaS

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
- `uv run pytest`: 368 passed, no network, no key.
- Not committed (left for the build workflow's review step).
- Closed in issues.md: layer/import test and clearing `ANTHROPIC_AUTH_TOKEN`.

### Open items
- Manual check with a real `ANTHROPIC_API_KEY` (Thai answer with a source id; cache write on the first call, cache read on the second) not run: no `.env` in the workspace.
