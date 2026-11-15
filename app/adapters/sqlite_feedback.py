"""`FeedbackStore` in a SQLite file (AD-10): the only server-side data.

One table, `feedback(conversation_id, answer, created_at)`. The file, its folder
and the table are created on the first write, so starting the app writes nothing.
`created_at` is stored as UTC ISO 8601 with milliseconds and `Z`, like the request log.
Uses `sqlite3` from the standard library; one connection per write.
"""

import sqlite3
import threading
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from app.ports.feedback import FeedbackAnswer, FeedbackStoreError

# Exactly these columns (NFR5): never question or answer text.
CREATE_TABLE = (
    "CREATE TABLE IF NOT EXISTS feedback ("
    "conversation_id TEXT, "
    "answer TEXT CHECK (answer IN ('yes','no')), "
    "created_at TEXT"
    ")"
)
INSERT = "INSERT INTO feedback (conversation_id, answer, created_at) VALUES (?, ?, ?)"
# Seconds a write waits for another connection's lock before it fails.
BUSY_TIMEOUT_SECONDS = 5.0


class SqliteFeedbackStore:
    """Appends feedback rows to the SQLite file at `path`. Thread-safe."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()

    def add(self, conversation_id: str, answer: FeedbackAnswer, created_at: datetime) -> None:
        """Store one row; any failure becomes `FeedbackStoreError` (class name only)."""
        stamp = created_at.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with closing(sqlite3.connect(self.path, timeout=BUSY_TIMEOUT_SECONDS)) as connection:
                    with connection:  # commits, or rolls back on an error
                        connection.execute(CREATE_TABLE)
                        connection.execute(INSERT, (conversation_id, answer, stamp))
            except (OSError, sqlite3.Error) as exc:
                raise FeedbackStoreError(type(exc).__name__) from exc
