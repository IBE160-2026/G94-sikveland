"""Feedback answers: the port for the only data the server stores (AD-10, NFR5).

A stored answer is the page's `conversation_id`, "yes" or "no", and the time the
server received it. No question or answer text ever passes through here.
"""

from datetime import datetime
from typing import Literal, Protocol

FeedbackAnswer = Literal["yes", "no"]


class FeedbackStoreError(Exception):
    """The answer could not be stored. The message never holds the stored values."""


class FeedbackStore(Protocol):
    """Where feedback answers go. Only `POST /api/feedback` writes to it."""

    def add(self, conversation_id: str, answer: FeedbackAnswer, created_at: datetime) -> None:
        """Store one answer. `created_at` is timezone-aware. Raises `FeedbackStoreError`."""
        ...
