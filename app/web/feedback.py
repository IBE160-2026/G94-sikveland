"""`POST /api/feedback`: the applicant's Yes/No answer to the feedback question (FR5, AD-10).

Stores only `conversation_id`, the answer and the time the server received it,
through the `FeedbackStore` port. An invalid body gets the app-wide 422 envelope, a
body sent without `Content-Type: application/json` a 415 envelope, and a storage
failure a 500 envelope. The body is never echoed or logged.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StringConstraints

from app.ports.feedback import FeedbackAnswer, FeedbackStore

# A UUID v4 in 8-4-4-4-12 form. The page always sends lower case; upper case is also
# accepted and stored in lower case.
UUID4_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
NOT_STORED_ERROR = {"error": {"code": "feedback_not_stored", "message": "the feedback could not be stored"}}
# FastAPI reads a body without a Content-Type as JSON. Any website can send such a body
# from the applicant's browser (a no-cors fetch), so only `application/json` is stored.
JSON_MEDIA_TYPE = "application/json"
WRONG_MEDIA_TYPE_ERROR = {
    "error": {"code": "unsupported_media_type", "message": "Content-Type must be application/json"}
}

logger = logging.getLogger(__name__)
router = APIRouter()

ConversationId = Annotated[str, StringConstraints(pattern=UUID4_PATTERN)]


class FeedbackRequest(BaseModel):
    """The request body. Anything else, also an extra field, is rejected with 422."""

    model_config = ConfigDict(extra="forbid")

    conversation_id: ConversationId
    answer: FeedbackAnswer


@router.post("/api/feedback", status_code=204, response_class=Response)
def feedback(body: FeedbackRequest, request: Request) -> Response:
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != JSON_MEDIA_TYPE:
        return JSONResponse(status_code=415, content=WRONG_MEDIA_TYPE_ERROR)
    store: FeedbackStore = request.app.state.feedback
    try:
        # Lower case, so SM-1 counts one conversation once whatever case the page sent.
        store.add(body.conversation_id.lower(), body.answer, datetime.now(UTC))
    except Exception as exc:  # noqa: BLE001 - every failure gets the same envelope
        logger.error("feedback not stored: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content=NOT_STORED_ERROR)
    return Response(status_code=204)
