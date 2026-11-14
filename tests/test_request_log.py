"""The request log file and the shape of one line (NFR5, NFR6, AD-12)."""

import json
import logging
import re
import threading
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.config import Settings
from app.pipeline.cost import Prices
from app.ports.llm import Usage
from app.web.request_log import RequestLog, answer_prices, request_line

FIELDS = {
    "timestamp",
    "outcome",
    "category",
    "prompt_versions",
    "model",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "cost_usd",
}
PRICES = Prices(input=4.00, output=20.00, cache_read=0.20, cache_write=5.00)
USAGE = Usage(input_tokens=1000, output_tokens=200, cache_read_tokens=50000, cache_write_tokens=0)


def _read(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_line_with_usage() -> None:
    line = request_line(
        outcome="answered",
        category="general",
        answer_prompt_version="3",
        model="claude-opus-5-5",
        usage=USAGE,
        prices=PRICES,
        now=datetime(2026, 11, 14, 9, 30, 5, 123456, tzinfo=UTC),
    )

    assert line == {
        "timestamp": "2026-11-14T09:30:05.123Z",
        "outcome": "answered",
        "category": "general",
        "prompt_versions": {"answer": "3"},
        "model": "claude-opus-5-5",
        "input_tokens": 1000,
        "output_tokens": 200,
        "cache_read_tokens": 50000,
        "cache_write_tokens": 0,
        "cost_usd": 0.018,
    }


def test_line_without_usage_has_null_tokens_and_cost() -> None:
    line = request_line(
        outcome="error",
        category="general",
        answer_prompt_version="1",
        model="m",
        usage=None,
        prices=PRICES,
    )

    assert set(line) == FIELDS
    assert [line[k] for k in sorted(FIELDS) if k.endswith("_tokens") or k == "cost_usd"] == [None] * 5


def test_timestamp_is_utc_with_z() -> None:
    oslo = timezone(timedelta(hours=1))
    line = request_line(
        outcome="answered",
        category="general",
        answer_prompt_version="1",
        model="m",
        usage=None,
        prices=PRICES,
        now=datetime(2026, 11, 14, 10, 0, 0, tzinfo=oslo),
    )

    assert line["timestamp"] == "2026-11-14T09:00:00.000Z"


def test_timestamp_now_is_iso_utc() -> None:
    line = request_line(
        outcome="answered", category=None, answer_prompt_version="1", model="m", usage=None, prices=PRICES
    )

    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", str(line["timestamp"]))


def test_answer_prices_come_from_the_answer_settings(settings: Settings) -> None:
    assert answer_prices(settings) == PRICES


def test_write_creates_the_folder_and_appends_lines(tmp_path: Path) -> None:
    path = tmp_path / "new" / "folder" / "requests.jsonl"
    log = RequestLog(path)

    log.write({"n": 1})
    log.write({"n": 2})

    assert path.read_bytes() == b'{"n": 1}\n{"n": 2}\n'


def test_write_keeps_non_ascii_as_utf8(tmp_path: Path) -> None:
    path = tmp_path / "requests.jsonl"

    RequestLog(path).write({"model": "ทดสอบ"})

    assert "ทดสอบ" in path.read_text(encoding="utf-8")


def test_unwritable_path_is_reported_once_per_run_of_failures_by_class_name(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("x", encoding="utf-8")
    log = RequestLog(blocker / "sub" / "requests.jsonl")

    def warnings() -> list[logging.LogRecord]:
        return [r for r in caplog.records if r.name == "app.web.request_log"]

    with caplog.at_level(logging.WARNING, logger="app.web.request_log"):
        log.write({"n": 1})
        log.write({"n": 2})
        assert len(warnings()) == 1

        # A successful write re-arms the warning for a later failure.
        log.path = tmp_path / "ok.jsonl"
        log.write({"n": 3})
        log.path = blocker / "sub" / "requests.jsonl"
        log.write({"n": 4})
        log.write({"n": 5})

    assert len(warnings()) == 2
    for record in warnings():
        assert re.search(r"request log not written: \w+Error$", record.getMessage())
    assert str(tmp_path) not in caplog.text


def test_write_is_reentrant_on_the_same_thread(tmp_path: Path) -> None:
    # Garbage collection can finish an abandoned stream inside `write` on the same thread.
    path = tmp_path / "requests.jsonl"
    log = RequestLog(path)
    with log._lock:
        log.write({"n": 1})

    assert _read(path) == [{"n": 1}]


def test_concurrent_writes_give_whole_lines(tmp_path: Path) -> None:
    path = tmp_path / "requests.jsonl"
    log = RequestLog(path)
    threads = [
        threading.Thread(target=lambda i=i: [log.write({"t": i, "n": n}) for n in range(50)])
        for i in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = _read(path)
    assert len(lines) == 400
    assert {(line["t"], line["n"]) for line in lines} == {(i, n) for i in range(8) for n in range(50)}
