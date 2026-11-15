"""App wiring and startup. Start with `uv run uvicorn app.main:app`."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.file_content import load_checklists, load_content
from app.adapters.file_demo_answers import load_demo_answers
from app.adapters.file_knowledge_base import load_knowledge_base
from app.adapters.file_prompts import load_prompt
from app.adapters.mock_llm import DEMO_ONLY_KEY, NO_USAGE, MockLLM
from app.adapters.mock_llm import MODEL_NAME as MOCK_MODEL_NAME
from app.adapters.ollama_llm import OllamaLLM
from app.adapters.sqlite_feedback import SqliteFeedbackStore
from app.config import ROOT, Settings, get_settings
from app.pipeline.cost import Prices
from app.ports.llm import LLMClient
from app.web import chat, checklists, feedback, health, texts
from app.web.request_log import RequestLog, answer_prices, small_prices

CONTENT_FILE = ROOT / "content" / "texts.yaml"
CHECKLISTS_FILE = ROOT / "content" / "checklists.yaml"
DEMO_ANSWERS_FILE = ROOT / "content" / "demo-answers.yaml"
KNOWLEDGE_BASE_DIR = ROOT / "knowledge-base"
ANSWER_PROMPT_FILE = ROOT / "prompts" / "answer-system.md"
CLASSIFIER_PROMPT_FILE = ROOT / "prompts" / "classifier-system.md"
# Read only with `LLM_PROVIDER=ollama`: how the model marks its sources as `[[id]]`.
CITING_PROMPT_FILE = ROOT / "prompts" / "answer-citing-markers.md"
STATIC_DIR = ROOT / "app" / "static"
# Wait between the chunks of a demo answer, so the page shows it arriving bit by bit.
DEMO_CHUNK_PAUSE_SECONDS = 0.05
NO_PRICES = Prices(input=0.0, output=0.0, cache_read=0.0, cache_write=0.0)


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings and a fake `llm`; uvicorn uses `.env`.

    Raises `ContentError` if `content/texts.yaml` is invalid, so the app never
    starts with missing or broken fixed texts, or if `content/checklists.yaml` is
    invalid or cites a source that is not in the knowledge base, `KnowledgeBaseError` if
    `knowledge-base/sources.yaml` or a source snapshot is missing or invalid, and
    `PromptError` if the answer or the classifier prompt is missing or malformed.
    Both are logged as prompt versions `answer` and `classifier`. The knowledge
    base is read from disk only; nothing is fetched at runtime.

    Without `llm`, answers go to the Anthropic API. Building that adapter needs no
    key: without `ANTHROPIC_API_KEY` every answer fails and the page shows the
    fixed error text. With `LLM_PROVIDER=ollama` they go to a local Ollama server
    instead (`OLLAMA_MODEL`, also for classifying, no cost); `prompts/answer-citing-markers.md` is then
    read too (`PromptError` stops startup) and logged as prompt version `citing`.
    If Ollama is not running, every answer fails with the fixed error text.

    In demo mode (`MOCK_LLM=true`) `content/demo-answers.yaml` is read and checked
    (`DemoContentError` stops startup) and, without `llm`, answers come from the
    `mock_llm` adapter. Questions it has no answer for get `reply-demo-only`, and
    the request log records model `mock_llm` at no cost, with zero tokens also
    when no usage arrived. Demo mode wins over `LLM_PROVIDER`. In real mode the
    demo answers file is never read. With Claude, the classify call is priced
    with `PRICE_SMALL_*`; it costs nothing in demo mode and with Ollama.
    """
    settings = settings if settings is not None else get_settings()
    app = FastAPI(title="Norway Visa Guide For Thai")
    app.state.settings = settings
    # The knowledge base first: the checklists' source ids are checked against it.
    app.state.knowledge_base = load_knowledge_base(KNOWLEDGE_BASE_DIR)
    checklist_items = load_checklists(CHECKLISTS_FILE, app.state.knowledge_base, settings.adviser_contact)
    app.state.content = load_content(CONTENT_FILE, settings.adviser_contact, checklist_items)
    # Which visit purposes each source's checklist items belong to: the `sources` event's
    # checklist flags (AD-8, AD-11), the same for Claude, Ollama and demo mode.
    app.state.checklist_purposes = chat.checklist_purposes_by_source(app.state.content.checklists())
    # Loaded even with a given `llm`, so a broken prompt file always stops startup.
    app.state.answer_prompt = load_prompt(ANSWER_PROMPT_FILE)
    app.state.classifier_prompt = load_prompt(CLASSIFIER_PROMPT_FILE)
    prompt_versions = {
        "answer": app.state.answer_prompt.version,
        "classifier": app.state.classifier_prompt.version,
    }
    if settings.mock_llm:
        examples = app.state.content.example_questions()
        demo = load_demo_answers(DEMO_ANSWERS_FILE, examples, app.state.knowledge_base)
        if llm is None:
            llm = MockLLM(demo, examples, app.state.content.texts(), pause_seconds=DEMO_CHUNK_PAUSE_SECONDS)
        app.state.no_answer_key = DEMO_ONLY_KEY
        app.state.answer_model = MOCK_MODEL_NAME
        app.state.answer_prices = NO_PRICES
        app.state.classify_prices = NO_PRICES
        # Also a request that ends without a usage report (client gone, error) cost nothing.
        app.state.fallback_usage = NO_USAGE
        app.state.prompt_versions = prompt_versions
    elif settings.llm_provider == "ollama":
        # Loaded even with a given `llm`, like the answer prompt, and logged with it.
        citing_prompt = load_prompt(CITING_PROMPT_FILE)
        if llm is None:
            llm = OllamaLLM(
                settings,
                app.state.knowledge_base,
                app.state.answer_prompt,
                citing_prompt,
                app.state.classifier_prompt,
            )
        app.state.no_answer_key = "reply-no-answer"
        app.state.answer_model = settings.ollama_model
        app.state.answer_prices = NO_PRICES
        app.state.classify_prices = NO_PRICES
        app.state.fallback_usage = None
        app.state.prompt_versions = {**prompt_versions, "citing": citing_prompt.version}
    else:
        if llm is None:
            llm = AnthropicLLM(
                settings, app.state.knowledge_base, app.state.answer_prompt, app.state.classifier_prompt
            )
        app.state.no_answer_key = "reply-no-answer"
        app.state.answer_model = settings.model_answer
        app.state.answer_prices = answer_prices(settings)
        app.state.classify_prices = small_prices(settings)
        app.state.fallback_usage = None
        app.state.prompt_versions = prompt_versions
    app.state.llm = llm
    # Nothing is written until the first chat request ends.
    app.state.request_log = RequestLog(_from_root(settings.request_log_path))
    # The only server-side data (AD-10), also in demo mode. The file, `data/` and the
    # table are created on the first `POST /api/feedback`, not at startup.
    app.state.feedback = SqliteFeedbackStore(_from_root(settings.database_path))
    app.add_exception_handler(RequestValidationError, _invalid_request)
    app.include_router(health.router)
    app.include_router(texts.router)
    app.include_router(chat.router)
    app.include_router(feedback.router)
    app.include_router(checklists.router)
    # Mounted last so every /api/* route is matched before the static files.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _from_root(path: str) -> Path:
    """`path` as given if absolute, else relative to the project root (not the working folder)."""
    return ROOT / Path(path)


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
