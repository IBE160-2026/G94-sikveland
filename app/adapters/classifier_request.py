"""What both real classifiers send and how they read the reply (AD-5, AD-14).

The categories the classifiers return, the JSON schema their structured
output must follow, the user message that carries the question and the recent
history as data, and the parsing of the model's JSON reply. No SDK, no network.
"""

import json
from collections.abc import Sequence
from html import escape
from typing import Any

from app.ports.llm import Category, Exchange, LLMError

# The whole closed set (AD-5): Stories 2.1 and 2.2 built the first four, 2.3 adds `done`.
CLASSIFIER_CATEGORIES: tuple[Category, ...] = (
    "general",
    "individual_assessment",
    "out_of_scope",
    "reach_person",
    "done",
)

# Each earlier answer is cut to this many characters (whole code points) in the classifier
# message: its start is enough context, and the whole answer would add cost and latency.
MAX_HISTORY_ANSWER_CHARS = 600
ELLIPSIS = "…"

CATEGORY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"category": {"type": "string", "enum": list(CLASSIFIER_CATEGORIES)}},
    "required": ["category"],
    "additionalProperties": False,
}


def classifier_user_message(question: str, recent_history: Sequence[Exchange]) -> str:
    """The question, after the recent exchanges (if any), each in its own tag.

    Questions go in whole; each earlier answer is cut to `MAX_HISTORY_ANSWER_CHARS`
    characters, with `ELLIPSIS` when cut. `<`, `>` and `&` in the texts are escaped
    (after cutting), so a question can never close a tag and pass itself off as
    instructions.
    """
    parts: list[str] = []
    if recent_history:
        parts.append("<recent_history>")
        for exchange in recent_history:
            parts.append(
                "<exchange>\n"
                f"<question>{_text(exchange.question)}</question>\n"
                f"<answer>{_text(_shortened(exchange.answer))}</answer>\n"
                "</exchange>"
            )
        parts.append("</recent_history>")
    parts.append(f"<question>{_text(question)}</question>")
    return "\n".join(parts)


def parse_category(text: str) -> Category:
    """The category in the model's JSON reply. Anything else is an `LLMError`.

    The error message never holds the reply itself.
    """
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise LLMError("the classifier reply is not JSON") from exc
    category = data.get("category") if isinstance(data, dict) else None
    for known in CLASSIFIER_CATEGORIES:
        if category == known:
            return known
    raise LLMError("the classifier reply has no known category")


def _shortened(answer: str) -> str:
    if len(answer) <= MAX_HISTORY_ANSWER_CHARS:
        return answer
    return answer[:MAX_HISTORY_ANSWER_CHARS] + ELLIPSIS


def _text(text: str) -> str:
    return escape(text, quote=False)
