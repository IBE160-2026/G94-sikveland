"""Official sources the answers are based on: the port every reader of `knowledge-base/` uses."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class Source:
    """One reviewed official page, with the snapshot text answers may use.

    `retrieved` is the date the snapshot text was captured: the source's version.
    """

    id: str
    title: str
    url: str
    publisher: str
    retrieved: date
    text: str


class KnowledgeBase(Protocol):
    """The validated knowledge base, loaded once at startup and never fetched at runtime."""

    def documents(self) -> Sequence[Source]:
        """All sources, sorted by `id` (fixed order keeps the prompt cache stable)."""
        ...

    def source(self, source_id: str) -> Source:
        """The source with this id. Raises `KeyError` if there is none."""
        ...
