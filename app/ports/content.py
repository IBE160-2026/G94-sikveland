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
        # Category `individual_assessment` (FR3): only the embassy decides.
        "reply-embassy-decides",
        # Category `out_of_scope` (FR14) and `reach_person` (FR13): the adviser contact.
        "reply-out-of-scope",
        "reply-reach-person",
        # Demo mode (MOCK_LLM=true): the reply to anything but an example question.
        "reply-demo-only",
        "error",
        "demo-label",
        # UI labels, so the page holds no Thai of its own.
        "send-button",
        "question-placeholder",
        # Saved chats on this device (AD-3): top bar, history panel, delete confirmations.
        "history-button",
        "new-chat-button",
        "history-title",
        "history-close",
        "history-empty",
        "delete-chat",
        "delete-all-chats",
        "confirm-delete-chat",
        "confirm-delete-all-chats",
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
