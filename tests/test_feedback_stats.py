"""`scripts/feedback_stats.py`: the share of first answers that were "yes" (Story 5.3, SM-1)."""

import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

import scripts.feedback_stats as feedback_stats
from app.adapters.sqlite_feedback import SqliteFeedbackStore
from app.config import Settings


def _settings(path: Path) -> Settings:
    return Settings(_env_file=None, database_path=str(path))


def _at(day: str, time: str = "12:00:00") -> datetime:
    return datetime.fromisoformat(f"{day}T{time}+00:00").astimezone(UTC)


def _store(path: Path, rows: list[tuple[str, str, datetime]]) -> None:
    """Rows written through the app's own store, in order."""
    store = SqliteFeedbackStore(path)
    for conversation_id, answer, created_at in rows:
        store.add(conversation_id, answer, created_at)  # type: ignore[arg-type]


def _run(path: Path, capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str]:
    code = feedback_stats.main(list(argv), settings=_settings(path))
    return code, capsys.readouterr().out


def test_a_missing_database_has_no_feedback_yet_and_is_not_created(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "data" / "feedback.sqlite3"

    code, out = _run(path, capsys)

    assert code == 0
    assert "No feedback yet." in out
    assert not path.exists()
    assert not path.parent.exists()


def test_a_database_without_the_table_has_no_feedback_yet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "feedback.sqlite3"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE other (x TEXT)")
        connection.commit()

    code, out = _run(path, capsys)

    assert code == 0
    assert "No feedback yet." in out


def test_an_empty_table_has_no_feedback_yet(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(path, [("a", "yes", _at("2026-11-10"))])
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("DELETE FROM feedback")
        connection.commit()

    code, out = _run(path, capsys)

    assert code == 0
    assert "No feedback yet." in out


def test_counts_the_share_of_first_answers_that_were_yes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(
        path,
        [
            ("a", "yes", _at("2026-11-10")),
            ("b", "yes", _at("2026-11-10")),
            ("c", "no", _at("2026-11-11")),
            ("d", "yes", _at("2026-11-12")),
        ],
    )

    code, out = _run(path, capsys)

    assert code == 0
    assert "all time" in out
    assert "Conversations with feedback: 4" in out
    assert 'First answer "yes": 3 (75.0%)' in out
    assert "Target: at least 80% - not met" in out


def test_no_followed_by_yes_counts_as_no(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(
        path,
        [
            ("a", "no", _at("2026-11-10", "09:00:00")),
            ("b", "yes", _at("2026-11-10", "09:30:00")),
            ("a", "yes", _at("2026-11-10", "10:00:00")),
            ("b", "no", _at("2026-11-10", "11:00:00")),
        ],
    )

    code, out = _run(path, capsys)

    assert code == 0
    assert "Conversations with feedback: 2" in out
    assert 'First answer "yes": 1 (50.0%)' in out


def test_exactly_80_percent_meets_the_target(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(path, [(c, "yes", _at("2026-11-10")) for c in "abcd"] + [("e", "no", _at("2026-11-10"))])

    code, out = _run(path, capsys)

    assert code == 0
    assert 'First answer "yes": 4 (80.0%)' in out
    assert "Target: at least 80% - met" in out


def test_the_date_filter_is_inclusive_in_utc(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(
        path,
        [
            ("before", "yes", _at("2026-10-31", "23:59:59")),
            ("first-day", "yes", _at("2026-11-01", "00:00:00")),
            ("last-day", "no", _at("2026-11-30", "23:59:59")),
            ("after", "yes", _at("2026-12-01", "00:00:00")),
        ],
    )

    code, out = _run(path, capsys, "--from", "2026-11-01", "--to", "2026-11-30")

    assert code == 0
    assert "2026-11-01 to 2026-11-30 (UTC)" in out
    assert "Conversations with feedback: 2" in out
    assert 'First answer "yes": 1 (50.0%)' in out


def test_a_conversation_belongs_to_the_day_of_its_first_answer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "feedback.sqlite3"
    # "no" in October, "yes" in November: the conversation counts in October, as "no".
    _store(path, [("a", "no", _at("2026-10-31")), ("a", "yes", _at("2026-11-01"))])

    code, november = _run(path, capsys, "--from", "2026-11-01")
    assert code == 0
    assert "No feedback yet in this period." in november

    code, october = _run(path, capsys, "--to", "2026-10-31")
    assert code == 0
    assert "Conversations with feedback: 1" in october
    assert 'First answer "yes": 0 (0.0%)' in october


def test_only_from_or_only_to_is_accepted(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(path, [("a", "yes", _at("2026-11-10")), ("b", "no", _at("2026-11-20"))])

    code, out = _run(path, capsys, "--from", "2026-11-15")
    assert code == 0
    assert "from 2026-11-15 (UTC)" in out
    assert "Conversations with feedback: 1" in out

    code, out = _run(path, capsys, "--to", "2026-11-15")
    assert code == 0
    assert "up to 2026-11-15 (UTC)" in out
    assert 'First answer "yes": 1 (100.0%)' in out


@pytest.mark.parametrize(
    "argv",
    [
        ["--from", "2026-11-31"],
        ["--to", "16.11.2026"],
        ["--from", "2026-11-20", "--to", "2026-11-10"],
    ],
)
def test_a_bad_date_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        feedback_stats.main(argv, settings=_settings(tmp_path / "feedback.sqlite3"))

    assert exit_info.value.code == 2
    assert "error" in capsys.readouterr().err


def test_the_database_is_never_changed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(path, [("a", "yes", _at("2026-11-10")), ("a", "no", _at("2026-11-11"))])
    before = path.read_bytes()

    _run(path, capsys)
    _run(path, capsys, "--from", "2026-11-01", "--to", "2026-11-30")

    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["feedback.sqlite3"]


def test_a_file_that_is_not_a_database_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "feedback.sqlite3"
    path.write_bytes(b"this is not a SQLite file, " * 40)

    code = feedback_stats.main([], settings=_settings(path))

    assert code == 2
    assert "cannot read" in capsys.readouterr().err


def test_a_relative_database_path_counts_from_the_project_root() -> None:
    settings = Settings(_env_file=None, database_path="data/feedback.sqlite3")

    assert feedback_stats.database_path(settings) == feedback_stats.ROOT / "data" / "feedback.sqlite3"


def test_the_readme_command_runs_against_a_database_the_app_wrote(tmp_path: Path) -> None:
    readme = (feedback_stats.ROOT / "README.md").read_text(encoding="utf-8")
    assert "uv run python scripts/feedback_stats.py\n" in readme
    path = tmp_path / "data" / "feedback.sqlite3"
    _store(
        path,
        [("a", "no", _at("2026-11-10")), ("a", "yes", _at("2026-11-10")), ("b", "yes", _at("2026-11-11"))],
    )
    env = {**os.environ, "DATABASE_PATH": str(path), "PYTHONIOENCODING": "utf-8"}

    done = subprocess.run(
        [sys.executable, str(feedback_stats.ROOT / "scripts" / "feedback_stats.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    assert "Conversations with feedback: 2" in done.stdout
    assert 'First answer "yes": 1 (50.0%)' in done.stdout


def test_a_single_day_is_both_ends_of_the_period(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "feedback.sqlite3"
    _store(
        path,
        [("a", "yes", _at("2026-11-09")), ("b", "no", _at("2026-11-10")), ("c", "yes", _at("2026-11-11"))],
    )

    code, out = _run(path, capsys, "--from", "2026-11-10", "--to", "2026-11-10")

    assert code == 0
    assert "Conversations with feedback: 1" in out
    assert 'First answer "yes": 0 (0.0%)' in out


def test_from_after_to_names_the_problem(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        feedback_stats.main(
            ["--from", "2026-11-20", "--to", "2026-11-10"], settings=_settings(tmp_path / "f.sqlite3")
        )

    assert "--from is after --to" in capsys.readouterr().err


def test_no_database_with_a_period_says_there_is_no_feedback_at_all(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run(tmp_path / "feedback.sqlite3", capsys, "--from", "2026-11-01")

    assert code == 0
    assert "No feedback yet." in out
    assert "in this period" not in out
