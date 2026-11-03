import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

FOLDERS = [
    "app/web",
    "app/pipeline",
    "app/ports",
    "app/adapters",
    "app/static",
    "content",
    "prompts",
    "knowledge-base",
    "scripts",
    "eval",
    "tests",
    "data",
]


@pytest.mark.parametrize("folder", FOLDERS)
def test_folder_exists(folder: str) -> None:
    assert (ROOT / folder).is_dir()


def _is_ignored(path: str) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    assert result.returncode in (0, 1), "git check-ignore failed"
    return result.returncode == 0


@pytest.mark.parametrize("path", [".env", "data/feedback.sqlite3"])
def test_secret_and_data_files_are_ignored(path: str) -> None:
    assert _is_ignored(path)


@pytest.mark.parametrize("path", [".env.example", "data/.gitkeep"])
def test_example_and_placeholder_are_tracked(path: str) -> None:
    assert not _is_ignored(path)
