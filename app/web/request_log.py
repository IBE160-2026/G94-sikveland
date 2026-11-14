"""The request log: one JSON line per finished chat request (NFR5, NFR6, AD-12).

A line holds what a question cost and how it ended, never what was asked or
answered: no question, answer, history, source titles or personal-information
flags. Writing it never breaks an answer; a failure is reported by class name, once
per run of failures (a successful write re-arms the warning).
"""

import json
import logging
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.config import Settings
from app.pipeline.cost import Prices, cost_usd
from app.ports.llm import Category, Usage

Outcome = Literal["answered", "no_answer", "error", "incomplete"]

logger = logging.getLogger(__name__)


class RequestLog:
    """Appends JSON lines to one file, creating its folder when needed. Thread-safe."""

    def __init__(self, path: Path) -> None:
        self.path = path
        # Reentrant: garbage collection can finish an abandoned stream, which writes its
        # line, on a thread that is already inside `write`.
        self._lock = threading.RLock()
        self._warned = False

    def write(self, line: Mapping[str, Any]) -> None:
        """Append `line`. A failure is swallowed; the first of a run is logged by class name."""
        with self._lock:
            try:
                text = json.dumps(line, ensure_ascii=False) + "\n"
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8", newline="\n") as file:
                    file.write(text)
                self._warned = False
            except Exception as exc:  # noqa: BLE001 - the log must never break an answer
                if not self._warned:
                    self._warned = True
                    logger.warning("request log not written: %s", type(exc).__name__)


def answer_prices(settings: Settings) -> Prices:
    """The prices of the answer model (`PRICE_ANSWER_*`)."""
    return Prices(
        input=settings.price_answer_input,
        output=settings.price_answer_output,
        cache_read=settings.price_answer_cache_read,
        cache_write=settings.price_answer_cache_write,
    )


def request_line(
    *,
    outcome: Outcome,
    category: Category | None,
    answer_prompt_version: str,
    model: str,
    usage: Usage | None,
    prices: Prices,
    now: datetime | None = None,
) -> dict[str, Any]:
    """The log line for one request. Token fields and `cost_usd` are `None` without `usage`."""
    moment = (now if now is not None else datetime.now(UTC)).astimezone(UTC)
    return {
        "timestamp": moment.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "outcome": outcome,
        "category": category,
        "prompt_versions": {"answer": answer_prompt_version},
        "model": model,
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "cache_read_tokens": usage.cache_read_tokens if usage else None,
        "cache_write_tokens": usage.cache_write_tokens if usage else None,
        "cost_usd": cost_usd(usage, prices) if usage else None,
    }
