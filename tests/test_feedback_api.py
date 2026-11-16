"""`POST /api/feedback` and the SQLite feedback store (Story 2.3, AD-10, NFR5)."""

import json
import logging
import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.main
from app.adapters.sqlite_feedback import SqliteFeedbackStore
from app.config import Settings
from app.main import create_app
from app.ports.feedback import FeedbackStore, FeedbackStoreError
from tests.fakes.fake_llm import ScriptedLLM

CONVERSATION_ID = "1b4e28ba-2fa1-41d2-883f-0016d3cca427"
ENVELOPE_KEYS = {"code", "message"}


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings, llm=ScriptedLLM()))


def _rows(path: Path | str) -> list[tuple[Any, ...]]:
    with closing(sqlite3.connect(path)) as connection:
        return connection.execute(
            "SELECT conversation_id, answer, created_at FROM feedback ORDER BY rowid"
        ).fetchall()


def _columns(path: Path | str) -> list[tuple[str, str]]:
    with closing(sqlite3.connect(path)) as connection:
        return [(row[1], row[2]) for row in connection.execute("PRAGMA table_info(feedback)")]


def _post(client: TestClient, body: Any) -> Any:
    return client.post("/api/feedback", json=body)


@pytest.mark.parametrize("answer", ["yes", "no"])
def test_answer_is_stored_with_the_server_time_and_204(
    client: TestClient, settings: Settings, answer: str
) -> None:
    before = datetime.now(UTC)

    response = _post(client, {"conversation_id": CONVERSATION_ID, "answer": answer})

    after = datetime.now(UTC)
    assert response.status_code == 204
    assert response.content == b""
    [(conversation_id, stored_answer, created_at)] = _rows(settings.database_path)
    assert (conversation_id, stored_answer) == (CONVERSATION_ID, answer)
    # UTC ISO 8601 with milliseconds and `Z`, set by the server.
    assert created_at.endswith("Z") and len(created_at) == len("2026-11-15T12:00:00.000Z")
    moment = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    assert before - timedelta(milliseconds=1) <= moment <= after


def test_table_has_only_the_three_columns(client: TestClient, settings: Settings) -> None:
    _post(client, {"conversation_id": CONVERSATION_ID, "answer": "yes"})

    assert _columns(settings.database_path) == [
        ("conversation_id", "TEXT"),
        ("answer", "TEXT"),
        ("created_at", "TEXT"),
    ]
    with closing(sqlite3.connect(settings.database_path)) as connection:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    assert tables == ["feedback"]


def test_the_table_accepts_only_yes_and_no(settings: Settings) -> None:
    store = SqliteFeedbackStore(Path(settings.database_path))
    store.add(CONVERSATION_ID, "yes", datetime.now(UTC))

    with pytest.raises(FeedbackStoreError):
        store.add(CONVERSATION_ID, "maybe", datetime.now(UTC))  # type: ignore[arg-type]
    assert [row[1] for row in _rows(settings.database_path)] == ["yes"]


def test_one_row_per_tap_and_answers_in_order(client: TestClient, settings: Settings) -> None:
    other = str(uuid.uuid4())
    for body in (
        {"conversation_id": CONVERSATION_ID, "answer": "no"},
        {"conversation_id": CONVERSATION_ID, "answer": "yes"},
        {"conversation_id": other, "answer": "yes"},
    ):
        assert _post(client, body).status_code == 204

    assert [row[:2] for row in _rows(settings.database_path)] == [
        (CONVERSATION_ID, "no"),
        (CONVERSATION_ID, "yes"),
        (other, "yes"),
    ]


def test_upper_case_id_is_stored_in_lower_case(client: TestClient, settings: Settings) -> None:
    assert _post(client, {"conversation_id": CONVERSATION_ID.upper(), "answer": "no"}).status_code == 204

    assert _rows(settings.database_path)[0][0] == CONVERSATION_ID


def test_data_folder_and_table_are_created_on_the_first_write(settings: Settings, tmp_path: Path) -> None:
    database = tmp_path / "new" / "deeper" / "feedback.sqlite3"
    client = TestClient(create_app(settings.model_copy(update={"database_path": str(database)})))

    # Starting the app writes nothing.
    assert not database.parent.exists()

    assert _post(client, {"conversation_id": CONVERSATION_ID, "answer": "yes"}).status_code == 204
    assert [row[:2] for row in _rows(database)] == [(CONVERSATION_ID, "yes")]


def test_relative_database_path_is_under_the_project_root(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "project"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setattr(app.main, "ROOT", root)
    monkeypatch.chdir(elsewhere)
    client = TestClient(create_app(settings.model_copy(update={"database_path": "data/feedback.sqlite3"})))

    assert _post(client, {"conversation_id": CONVERSATION_ID, "answer": "no"}).status_code == 204

    assert (root / "data" / "feedback.sqlite3").is_file()
    assert not (elsewhere / "data").exists()


@pytest.mark.parametrize(
    "body",
    [
        {"answer": "yes"},
        {"conversation_id": CONVERSATION_ID},
        {},
        {"conversation_id": CONVERSATION_ID, "answer": "maybe"},
        {"conversation_id": CONVERSATION_ID, "answer": "Yes"},
        {"conversation_id": CONVERSATION_ID, "answer": True},
        {"conversation_id": CONVERSATION_ID, "answer": None},
        {"conversation_id": "not-a-uuid", "answer": "yes"},
        {"conversation_id": "", "answer": "yes"},
        {"conversation_id": 42, "answer": "yes"},
        # Not version 4, or not in the 8-4-4-4-12 form.
        {"conversation_id": "1b4e28ba-2fa1-11d2-883f-0016d3cca427", "answer": "yes"},
        {"conversation_id": "1b4e28ba2fa141d2883f0016d3cca427", "answer": "yes"},
        {"conversation_id": "{" + CONVERSATION_ID + "}", "answer": "yes"},
        {"conversation_id": CONVERSATION_ID + "\n", "answer": "yes"},
        # Never any question or answer text.
        {"conversation_id": CONVERSATION_ID, "answer": "yes", "question": "secret question"},
        {"conversation_id": CONVERSATION_ID, "answer": "yes", "created_at": "2020-01-01T00:00:00Z"},
        [CONVERSATION_ID, "yes"],
        "yes",
    ],
)
def test_invalid_body_is_422_with_the_envelope_and_nothing_is_stored(
    client: TestClient, settings: Settings, body: Any
) -> None:
    response = _post(client, body)

    assert response.status_code == 422
    error = response.json()["error"]
    assert set(error) == ENVELOPE_KEYS
    assert error["code"] == "invalid_request"
    assert "secret" not in response.text
    assert not Path(settings.database_path).exists()


def test_body_that_is_not_json_is_422(client: TestClient, settings: Settings) -> None:
    response = client.post(
        "/api/feedback", content=b"answer=yes", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert set(response.json()["error"]) == ENVELOPE_KEYS
    assert not Path(settings.database_path).exists()


class FailingStore:
    def add(self, conversation_id: str, answer: Any, created_at: datetime) -> None:
        raise FeedbackStoreError("OperationalError")


class BrokenStore:
    def add(self, conversation_id: str, answer: Any, created_at: datetime) -> None:
        raise RuntimeError(f"secret {conversation_id}")


@pytest.mark.parametrize("store", [FailingStore(), BrokenStore()], ids=["store-error", "other-error"])
def test_storage_failure_is_500_with_the_envelope_and_no_echo(
    client: TestClient, store: FeedbackStore, caplog: pytest.LogCaptureFixture
) -> None:
    client.app.state.feedback = store

    with caplog.at_level(logging.INFO):
        response = _post(client, {"conversation_id": CONVERSATION_ID, "answer": "yes"})

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "feedback_not_stored", "message": "the feedback could not be stored"}
    }
    assert CONVERSATION_ID not in response.text and CONVERSATION_ID not in caplog.text
    assert "secret" not in caplog.text


def test_database_that_cannot_be_written_is_500(settings: Settings, tmp_path: Path) -> None:
    # The database path is a folder: SQLite cannot open it.
    folder = tmp_path / "a-folder"
    folder.mkdir()
    client = TestClient(create_app(settings.model_copy(update={"database_path": str(folder)})))

    response = _post(client, {"conversation_id": CONVERSATION_ID, "answer": "yes"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "feedback_not_stored"


def test_store_writes_utc_with_z_whatever_the_given_zone(tmp_path: Path) -> None:
    path = tmp_path / "f.sqlite3"
    bangkok = timezone(timedelta(hours=7))

    SqliteFeedbackStore(path).add(CONVERSATION_ID, "no", datetime(2026, 11, 15, 19, 30, 0, 123000, bangkok))

    assert _rows(path) == [(CONVERSATION_ID, "no", "2026-11-15T12:30:00.123Z")]


def test_the_chat_never_writes_feedback(settings: Settings) -> None:
    client = TestClient(create_app(settings, llm=ScriptedLLM(category="done")))

    response = client.post("/api/chat", json={"question": "ขอบคุณค่ะ", "history": []})

    assert response.status_code == 200
    assert '"category": "done"' in response.text  # the feedback question was sent
    assert not Path(settings.database_path).exists()


VALID_BODY = json.dumps({"conversation_id": CONVERSATION_ID, "answer": "yes"}).encode()


@pytest.mark.parametrize("content_type", ["application/merge-patch+json", "application/csp-report+json"])
def test_json_with_another_json_content_type_is_415_and_nothing_is_stored(
    client: TestClient, settings: Settings, content_type: str
) -> None:
    # FastAPI parses `+json` types as JSON; only `application/json` is stored.
    response = client.post("/api/feedback", content=VALID_BODY, headers={"Content-Type": content_type})

    assert response.status_code == 415
    assert response.json() == {
        "error": {"code": "unsupported_media_type", "message": "Content-Type must be application/json"}
    }
    assert CONVERSATION_ID not in response.text
    assert not Path(settings.database_path).exists()


@pytest.mark.parametrize(
    "headers",
    [{}, {"Content-Type": "text/plain"}, {"Content-Type": "application/x-www-form-urlencoded"}],
    ids=["no-content-type", "text-plain", "form"],
)
def test_json_without_a_json_content_type_is_rejected_and_nothing_is_stored(
    client: TestClient, settings: Settings, headers: dict[str, str]
) -> None:
    # What another website can send from the applicant's browser without CORS, e.g. a
    # no-cors fetch of a typeless Blob. FastAPI (strict content type) answers 422 first.
    response = client.post("/api/feedback", content=VALID_BODY, headers=headers)

    assert response.status_code in (415, 422)
    assert set(response.json()["error"]) == ENVELOPE_KEYS
    assert CONVERSATION_ID not in response.text
    assert not Path(settings.database_path).exists()


@pytest.mark.parametrize("content_type", ["application/json; charset=utf-8", "Application/JSON"])
def test_json_content_type_with_parameters_or_any_case_is_accepted(
    client: TestClient, settings: Settings, content_type: str
) -> None:
    response = client.post("/api/feedback", content=VALID_BODY, headers={"Content-Type": content_type})

    assert response.status_code == 204
    assert len(_rows(settings.database_path)) == 1


def test_feedback_store_is_the_sqlite_adapter_at_the_settings_path(settings: Settings) -> None:
    store = create_app(settings, llm=ScriptedLLM()).state.feedback

    assert isinstance(store, SqliteFeedbackStore)
    assert store.path == Path(settings.database_path)
