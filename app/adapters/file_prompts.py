"""Versioned prompt files in `prompts/`.

A prompt file starts with a `version: <value>` line; the rest is the prompt text.
The version is for the request log (Story 1.8) and eval reports, so answers can be
traced to a prompt.
"""

from dataclasses import dataclass
from pathlib import Path

_VERSION_PREFIX = "version:"


class PromptError(Exception):
    """The prompt file is missing or malformed. The app must not start."""


@dataclass(frozen=True)
class Prompt:
    """A prompt text and its version."""

    version: str
    text: str


def load_prompt(path: Path) -> Prompt:
    """Read a prompt file. Raises `PromptError` on any problem."""
    try:
        # utf-8-sig also reads files saved with a BOM.
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise PromptError(f"cannot read prompt file {path}: {exc}") from exc

    first, _, rest = raw.partition("\n")
    first = first.strip()
    if not first.startswith(_VERSION_PREFIX):
        raise PromptError(f"{path}: first line must be 'version: <value>', got {first!r}")
    version = first[len(_VERSION_PREFIX) :].strip()
    if not version:
        raise PromptError(f"{path}: the version line has no value")
    text = rest.strip()
    if not text:
        raise PromptError(f"{path}: the prompt has no text after the version line")
    return Prompt(version=version, text=text)
