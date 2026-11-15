"""The committed checklists, for tests that build a `ContentStore` from the texts file alone."""

from collections.abc import Mapping
from functools import cache

from app.adapters.file_content import load_checklists
from app.adapters.file_knowledge_base import load_knowledge_base
from app.main import CHECKLISTS_FILE, KNOWLEDGE_BASE_DIR
from app.ports.content import ChecklistItem


@cache
def committed_checklists() -> Mapping[str, tuple[ChecklistItem, ...]]:
    """`content/checklists.yaml`, loaded and checked against the committed knowledge base."""
    return load_checklists(CHECKLISTS_FILE, load_knowledge_base(KNOWLEDGE_BASE_DIR), "adviser@example.org")
