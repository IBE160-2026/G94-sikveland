"""The request log: one JSON line per finished chat request and per model translation
(NFR5, NFR6, AD-12).

A line holds what a request cost and how it ended, never what was asked, answered or
translated: no question, answer, history, source titles, translated text or
personal-information flags. `endpoint` tells chat lines from translate lines. Writing
it never breaks an answer; a failure is reported by class name, once per run of
failures (a successful write re-arms the warning).
"""

import json
import logging
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.config import Settings
from app.pipeline.cost import COST_DECIMALS, Prices, cost_usd
from app.ports.llm import Category, Usage

# `fixed_reply`: a category with a fixed text (e.g. `reply-embassy-decides`), no answer call.
# `translated`: a model translation (`POST /api/translate`); stored English is not logged.
Outcome = Literal["answered", "no_answer", "fixed_reply", "translated", "error", "incomplete"]
# The route a line belongs to.
Endpoint = Literal["chat", "translate"]

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


def small_prices(settings: Settings) -> Prices:
    """The prices of the small model (`PRICE_SMALL_*`), which classifies and translates."""
    return Prices(
        input=settings.price_small_input,
        output=settings.price_small_output,
        cache_read=settings.price_small_cache_read,
        cache_write=settings.price_small_cache_write,
    )


def request_line(
    *,
    endpoint: Endpoint,
    outcome: Outcome,
    category: Category | None,
    prompt_versions: Mapping[str, str],
    model: str,
    usage: Usage | None,
    prices: Prices,
    classify_usage: Usage | None,
    classify_prices: Prices,
    unknown_source_ids: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """The log line for one request.

    `endpoint` is `chat` or `translate`. `usage` is the answer call's (priced with
    `prices`), `classify_usage` the classify call's (priced with `classify_prices`); the
    answer token fields are `None` without `usage`, the classify ones without
    `classify_usage`. `cost_usd` is the sum of both costs, `None` when neither call
    reported usage. `prompt_versions` holds `answer`, `classifier` and, with Ollama,
    `citing`. `unknown_source_ids` is how many cited ids were dropped as unknown (0 when
    none), `None` if the stream ended before the sources were known.

    A translate line has the translate call's `usage` and `prices` in the answer fields,
    no classify call, `category` and `unknown_source_ids` `None`, and `prompt_versions`
    `{"translate": version}`.
    """
    moment = (now if now is not None else datetime.now(UTC)).astimezone(UTC)
    costs = [
        cost_usd(spent, priced)
        for spent, priced in ((usage, prices), (classify_usage, classify_prices))
        if spent is not None
    ]
    return {
        "timestamp": moment.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "endpoint": endpoint,
        "outcome": outcome,
        "category": category,
        "prompt_versions": dict(prompt_versions),
        "model": model,
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "cache_read_tokens": usage.cache_read_tokens if usage else None,
        "cache_write_tokens": usage.cache_write_tokens if usage else None,
        "classify_input_tokens": classify_usage.input_tokens if classify_usage else None,
        "classify_output_tokens": classify_usage.output_tokens if classify_usage else None,
        "cost_usd": round(sum(costs), COST_DECIMALS) if costs else None,
        "unknown_source_ids": unknown_source_ids,
    }
