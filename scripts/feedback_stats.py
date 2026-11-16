"""Feedback statistics: the share of conversations whose first answer was "yes" (Story 5.3, SM-1).

Run from the project folder: `uv run python scripts/feedback_stats.py [--from YYYY-MM-DD] [--to YYYY-MM-DD]`.

Reads the SQLite file at `DATABASE_PATH` (from `.env`; a relative path counts from the
project root, as in the app) read-only, so it never creates or changes the database.
Only the first answer per `conversation_id` counts, the row stored first (AD-10): "no"
followed by "yes" counts as "no". `--from` and `--to` keep the conversations whose first
answer was created on or between those dates, both inclusive, in UTC as stored.

A missing file, a missing table or no feedback in the period prints that there is no
feedback yet. Exit codes: 0 when the statistics (or "no feedback yet") were printed,
2 for a usage error (an invalid date, `--from` after `--to`) or a database that cannot
be read.
"""

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings, get_settings  # noqa: E402

# SM-1: at least this share of conversations gets "yes" as the first answer.
TARGET_PERCENT = 80
EXIT_USAGE = 2
# The first answer of every conversation: the row stored first (lowest rowid).
FIRST_ANSWERS = (
    "SELECT f.answer, f.created_at FROM feedback f "
    "WHERE f.rowid = (SELECT MIN(rowid) FROM feedback WHERE conversation_id = f.conversation_id)"
)
TABLE_EXISTS = "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'feedback'"


class StatsError(Exception):
    """The database exists but cannot be read; the message says why."""


@dataclass(frozen=True)
class Stats:
    """First answers counted in the period."""

    conversations: int
    yes: int

    @property
    def percent(self) -> float:
        return 100 * self.yes / self.conversations

    @property
    def target_met(self) -> bool:
        return self.yes * 100 >= TARGET_PERCENT * self.conversations


def database_path(settings: Settings) -> Path:
    """`DATABASE_PATH` as the app resolves it: as given if absolute, else from the project root."""
    return ROOT / Path(settings.database_path)


def first_answers(path: Path) -> list[tuple[str, str]]:
    """`(answer, created_at)` of every conversation's first answer; `[]` without file or table."""
    if not path.is_file():
        return []
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            if connection.execute(TABLE_EXISTS).fetchone() is None:
                return []
            return [
                (str(answer), str(created_at)) for answer, created_at in connection.execute(FIRST_ANSWERS)
            ]
    except sqlite3.Error as exc:
        raise StatsError(f"cannot read {path}: {type(exc).__name__}: {exc}") from exc


def count(rows: Sequence[tuple[str, str]], start: date | None, end: date | None) -> Stats:
    """Count the first answers whose day (UTC) is within `start`..`end`, both inclusive."""
    conversations = 0
    yes = 0
    for answer, created_at in rows:
        if start is not None or end is not None:
            day = _day(created_at)
            if day is None or (start is not None and day < start) or (end is not None and day > end):
                continue
        conversations += 1
        if answer == "yes":
            yes += 1
    return Stats(conversations=conversations, yes=yes)


def _day(created_at: str) -> date | None:
    """The UTC day of a stored `created_at` (ISO 8601 with `Z`), or `None` if it is not one."""
    try:
        moment = datetime.fromisoformat(created_at)
    except ValueError:
        return None
    return (moment.astimezone(UTC) if moment.tzinfo is not None else moment).date()


def report(
    stats: Stats, start: date | None, end: date | None, out: TextIO, *, any_feedback: bool = True
) -> None:
    """Print the statistics, or that there is no feedback yet (`any_feedback`: any at all, in any period)."""
    period = _period(start, end)
    print(f"Feedback statistics (SM-1), {period}", file=out)
    if stats.conversations == 0:
        filtered = start is not None or end is not None
        print(
            "No feedback yet in this period." if filtered and any_feedback else "No feedback yet.", file=out
        )
        return
    print(f"Conversations with feedback: {stats.conversations}", file=out)
    print(f'First answer "yes": {stats.yes} ({stats.percent:.1f}%)', file=out)
    verdict = "met" if stats.target_met else "not met"
    print(f"Target: at least {TARGET_PERCENT}% - {verdict}", file=out)


def _period(start: date | None, end: date | None) -> str:
    if start is None and end is None:
        return "all time"
    if end is None:
        return f"from {start} (UTC)"
    if start is None:
        return f"up to {end} (UTC)"
    return f"{start} to {end} (UTC)"


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a date (YYYY-MM-DD): {value!r}") from None


def main(argv: Sequence[str] | None = None, settings: Settings | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Share of conversations whose first feedback answer was "yes" (SM-1, target 80%).'
    )
    parser.add_argument(
        "--from", dest="start", type=_date, metavar="YYYY-MM-DD", help="first day, inclusive (UTC)"
    )
    parser.add_argument(
        "--to", dest="end", type=_date, metavar="YYYY-MM-DD", help="last day, inclusive (UTC)"
    )
    args = parser.parse_args(argv)
    if args.start is not None and args.end is not None and args.start > args.end:
        parser.error("--from is after --to")

    path = database_path(settings if settings is not None else get_settings())
    try:
        rows = first_answers(path)
    except StatsError as exc:
        print(exc, file=sys.stderr)
        return EXIT_USAGE
    report(count(rows, args.start, args.end), args.start, args.end, sys.stdout, any_feedback=bool(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
