"""`GET /api/checklists/{purpose}`: the fixed document checklist for one visit purpose (FR6, AD-11).

Served from `ContentStore` and the knowledge base only, never from the LLM. Each
item's source is resolved to `{title, url}`. An unknown purpose gets a 404 in the
error envelope; the requested value is never echoed. The route takes the whole rest
of the path, so `/api/checklists/`, `/api/checklists/tourism/` and deeper paths get
the same envelope instead of falling through to the static files.
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.ports.content import VISIT_PURPOSES, ContentStore
from app.ports.knowledge_base import KnowledgeBase

UNKNOWN_PURPOSE_ERROR = {
    "error": {
        "code": "unknown_purpose",
        "message": f"unknown visit purpose; use one of: {', '.join(VISIT_PURPOSES)}",
    }
}

router = APIRouter()


@router.get("/api/checklists/{purpose:path}", response_model=None)
def checklist(purpose: str, request: Request) -> dict[str, Any] | JSONResponse:
    content: ContentStore = request.app.state.content
    knowledge_base: KnowledgeBase = request.app.state.knowledge_base
    items = content.checklists().get(purpose)
    if items is None:
        return JSONResponse(status_code=404, content=UNKNOWN_PURPOSE_ERROR)
    return {
        "purpose": purpose,
        "items": [
            {"id": item.id, "text": item.th, "source": _source(knowledge_base, item.source_id)}
            for item in items
        ],
    }


def _source(knowledge_base: KnowledgeBase, source_id: str) -> dict[str, str]:
    # Every source id was checked against the knowledge base at startup.
    source = knowledge_base.source(source_id)
    return {"title": source.title, "url": source.url}
