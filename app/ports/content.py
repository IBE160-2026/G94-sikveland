"""Fixed texts and example questions: the port every reader of `content/` uses."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

# Closed list of fixed-text keys (AD-6). Later epics add keys here.
REQUIRED_TEXT_KEYS: frozenset[str] = frozenset(
    {
        "privacy-notice",
        "personal-info-reminder",
        "reply-no-answer",
        "error",
        "demo-label",
        # UI labels, so the page holds no Thai of its own.
        "send-button",
        "question-placeholder",
    }
)


@dataclass(frozen=True)
class FixedText:
    """One fixed text in Thai, with the stored English version."""

    th: str
    en: str


@dataclass(frozen=True)
class ExampleQuestion:
    """An example question the applicant can tap."""

    id: str
    th: str
    en: str


class ContentStore(Protocol):
    """Validated fixed texts, with `{ADVISER_CONTACT}` already filled in."""

    def texts(self) -> Mapping[str, FixedText]: ...

    def example_questions(self) -> Sequence[ExampleQuestion]: ...
