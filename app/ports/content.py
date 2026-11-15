"""Fixed texts, example questions and checklists: the port every reader of `content/` uses."""

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
        # Category `done` (FR5): the feedback question with Yes/No buttons, the page's
        # text after "No" and after "Yes", and the two button labels (AD-10).
        "feedback-question",
        "feedback-follow-up",
        "feedback-thanks",
        "feedback-yes",
        "feedback-no",
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
        # Document checklist view (Story 3.2, FR6): top-bar button, view title, purpose
        # choice and the three purpose names (`checklist-purpose-` + each `VISIT_PURPOSES`
        # value), back, change purpose, "doesn't apply to me", the progress line and all done.
        "checklist-button",
        "checklist-title",
        "checklist-choose-purpose",
        "checklist-purpose-tourism",
        "checklist-purpose-family",
        "checklist-purpose-friends",
        "checklist-back",
        "checklist-change-purpose",
        "checklist-not-applicable",
        # `{done}` and `{total}` stay in the served text; the page fills them in.
        "checklist-progress",
        "checklist-all-done",
        # Shown while a checklist loads, and the name of the retry button (a symbol only).
        "checklist-loading",
        "checklist-retry",
        # The "Open checklist" button under an answer that cites a checklist-linked source
        # (Story 3.3, AD-11).
        "checklist-open",
    }
)

# Placeholders the page fills in, allowed (and required) only in these keys. Every other
# brace in a text is still rejected at startup, except `{ADVISER_CONTACT}`.
PAGE_PLACEHOLDERS: Mapping[str, tuple[str, ...]] = {"checklist-progress": ("{done}", "{total}")}


# The visit purposes that have a checklist (AD-11), in the order the page offers them.
VISIT_PURPOSES: tuple[str, ...] = ("tourism", "family", "friends")


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


@dataclass(frozen=True)
class ChecklistItem:
    """One document on a visit purpose's checklist (AD-11).

    `id` is stable: the page keeps ticks by it, so it is never reused for other content.
    `source_id` is the id of the knowledge-base source the item comes from.
    `conditional` marks an item that only applies to some applicants ("if employed"):
    the page then also offers "doesn't apply to me" for it.
    """

    id: str
    th: str
    en: str
    source_id: str
    conditional: bool = False


class ContentStore(Protocol):
    """Validated fixed texts, with `{ADVISER_CONTACT}` already filled in."""

    def texts(self) -> Mapping[str, FixedText]: ...

    def example_questions(self) -> Sequence[ExampleQuestion]: ...

    def checklists(self) -> Mapping[str, Sequence[ChecklistItem]]:
        """Visit purpose → its items in file order; one entry per `VISIT_PURPOSES` value."""
        ...
