"""App wiring and startup. Start with `uv run uvicorn app.main:app`."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.file_content import load_content
from app.adapters.file_knowledge_base import load_knowledge_base
from app.adapters.file_prompts import load_prompt
from app.config import ROOT, Settings, get_settings
from app.ports.llm import LLMClient
from app.web import chat, health, texts

CONTENT_FILE = ROOT / "content" / "texts.yaml"
KNOWLEDGE_BASE_DIR = ROOT / "knowledge-base"
ANSWER_PROMPT_FILE = ROOT / "prompts" / "answer-system.md"
STATIC_DIR = ROOT / "app" / "static"


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings and a fake `llm`; uvicorn uses `.env`.

    Raises `ContentError` if `content/texts.yaml` is invalid, so the app never
    starts with missing or broken fixed texts, `KnowledgeBaseError` if
    `knowledge-base/sources.yaml` or a source snapshot is missing or invalid, and
    `PromptError` if the answer prompt is missing or malformed. The knowledge base
    is read from disk only; nothing is fetched at runtime.

    Without `llm`, answers go to the Anthropic API. Building that adapter needs no
    key: without `ANTHROPIC_API_KEY` every answer fails and the page shows the
    fixed error text.
    """
    settings = settings if settings is not None else get_settings()
    app = FastAPI(title="Norway Visa Guide For Thai")
    app.state.settings = settings
    app.state.content = load_content(CONTENT_FILE, settings.adviser_contact)
    app.state.knowledge_base = load_knowledge_base(KNOWLEDGE_BASE_DIR)
    # Loaded even with a given `llm`, so a broken prompt file always stops startup.
    app.state.answer_prompt = load_prompt(ANSWER_PROMPT_FILE)
    app.state.llm = (
        llm
        if llm is not None
        else AnthropicLLM(settings, app.state.knowledge_base, app.state.answer_prompt)
    )
    app.add_exception_handler(RequestValidationError, _invalid_request)
    app.include_router(health.router)
    app.include_router(texts.router)
    app.include_router(chat.router)
    # Mounted last so every /api/* route is matched before the static files.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


async def _invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 in the error shape of the conventions. The input itself is never echoed."""
    problems = []
    for error in exc.errors():
        message = error.get("msg", "invalid")
        if error.get("type") == "extra_forbidden":
            # The location of an extra field is the client's own key: never echo it.
            problems.append(f"unknown field: {message}")
            continue
        where = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
        problems.append(f"{where}: {message}" if where else message)
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "invalid_request", "message": "; ".join(problems)}},
    )


app = create_app()
