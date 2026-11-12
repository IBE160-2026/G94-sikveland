"""Fixed Thai texts for the page: its only source of Thai (AD-6)."""

from typing import Any

from fastapi import APIRouter, Request

from app.ports.content import ContentStore

router = APIRouter()


@router.get("/api/texts")
def texts(request: Request) -> dict[str, Any]:
    content: ContentStore = request.app.state.content
    return {
        "demo_mode": request.app.state.settings.mock_llm,
        "texts": {key: text.th for key, text in content.texts().items()},
        "example_questions": [
            {"id": question.id, "text": question.th} for question in content.example_questions()
        ],
    }
