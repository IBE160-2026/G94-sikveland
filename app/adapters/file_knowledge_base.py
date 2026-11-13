"""`KnowledgeBase` read from `knowledge-base/`, validated once at startup.

`sources.yaml` lists the official sources; each has a committed Markdown snapshot
`<id>.md` written by `scripts/ingest.py`. Nothing here fetches over the network.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any
from urllib.parse import urlsplit

import yaml

from app.ports.knowledge_base import Source

SOURCES_FILE = "sources.yaml"
# The only publishers allowed, each tied to the domain its URLs must be on.
PUBLISHER_DOMAINS: Mapping[str, str] = MappingProxyType(
    {
        "UDI": "udi.no",
        "VFS Global": "vfsglobal.com",
        "Royal Norwegian Embassy in Bangkok": "norway.no",
        "European Commission": "europa.eu",
    }
)
FIELDS = ("id", "title", "url", "publisher", "retrieved", "file")
_KEBAB_CASE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class KnowledgeBaseError(Exception):
    """The source list or a snapshot is missing, malformed or invalid. The app must not start."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys instead of keeping the last."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in seen
            except TypeError:  # unhashable key: SafeLoader reports it below
                continue
            if duplicate:
                raise KnowledgeBaseError(
                    f"duplicate key {key!r} at line {key_node.start_mark.line + 1}"
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class SourceEntry:
    """One validated entry of `sources.yaml` (without its snapshot text)."""

    id: str
    title: str
    url: str
    publisher: str
    retrieved: date
    file: str

    def as_dict(self) -> dict[str, Any]:
        """The entry as written in `sources.yaml`, fields in their fixed order."""
        return {name: getattr(self, name) for name in FIELDS}


class FileKnowledgeBase:
    """Validated sources with their snapshot texts, held in memory, sorted by id."""

    def __init__(self, sources: Sequence[Source]) -> None:
        self._documents = tuple(sorted(sources, key=lambda s: s.id))
        self._by_id = MappingProxyType({s.id: s for s in self._documents})

    def documents(self) -> Sequence[Source]:
        return self._documents

    def source(self, source_id: str) -> Source:
        return self._by_id[source_id]


def load_sources(path: Path) -> list[SourceEntry]:
    """Read and validate `sources.yaml` (no snapshots). Raises `KnowledgeBaseError`."""
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise KnowledgeBaseError(f"cannot read source list {path}: {exc}") from exc
    try:
        data = yaml.load(raw, Loader=_UniqueKeyLoader)
    except (yaml.YAMLError, ValueError) as exc:  # ValueError: impossible date, e.g. 2026-02-30
        raise KnowledgeBaseError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, list) or not data:
        raise KnowledgeBaseError(f"{path} must be a non-empty list of sources")

    entries: list[SourceEntry] = []
    seen: set[str] = set()
    for index, item in enumerate(data):
        entry = _entry(item, index)
        if entry.id in seen:
            raise KnowledgeBaseError(f"duplicate source id {entry.id!r}")
        seen.add(entry.id)
        entries.append(entry)
    return entries


def load_knowledge_base(directory: Path) -> FileKnowledgeBase:
    """Load the source list and every snapshot. Raises `KnowledgeBaseError` on any problem."""
    sources: list[Source] = []
    for entry in load_sources(directory / SOURCES_FILE):
        snapshot = directory / entry.file
        try:
            text = snapshot.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise KnowledgeBaseError(
                f"source {entry.id!r}: cannot read snapshot {snapshot}: {exc}"
            ) from exc
        text = text.strip()
        if not text:
            raise KnowledgeBaseError(f"source {entry.id!r}: snapshot {snapshot} is empty")
        sources.append(
            Source(
                id=entry.id,
                title=entry.title,
                url=entry.url,
                publisher=entry.publisher,
                retrieved=entry.retrieved,
                text=text,
            )
        )
    return FileKnowledgeBase(sources)


def _entry(item: object, index: int) -> SourceEntry:
    if not isinstance(item, dict):
        raise KnowledgeBaseError(f"source #{index + 1} must be a mapping of {', '.join(FIELDS)}")
    sid = item.get("id")
    if not isinstance(sid, str) or not _KEBAB_CASE.fullmatch(sid):
        raise KnowledgeBaseError(f"source #{index + 1} needs a kebab-case 'id', got {sid!r}")
    where = f"source {sid!r}"

    extra = sorted(str(k) for k in item if k not in FIELDS)
    if extra:
        raise KnowledgeBaseError(f"{where} has unknown field(s): {', '.join(extra)}")
    missing = [name for name in FIELDS if name not in item]
    if missing:
        raise KnowledgeBaseError(f"{where} is missing field(s): {', '.join(missing)}")

    title, url, publisher, file = (
        _text(item, name, where) for name in ("title", "url", "publisher", "file")
    )
    if publisher not in PUBLISHER_DOMAINS:
        allowed = ", ".join(repr(p) for p in PUBLISHER_DOMAINS)
        raise KnowledgeBaseError(f"{where} has unknown publisher {publisher!r} (allowed: {allowed})")
    _check_url(url, PUBLISHER_DOMAINS[publisher], where)
    if file != f"{sid}.md":
        raise KnowledgeBaseError(f"{where} 'file' must be {sid + '.md'!r}, got {file!r}")

    retrieved = item["retrieved"]
    # A datetime is also a date; only a plain YYYY-MM-DD date is allowed.
    if not isinstance(retrieved, date) or isinstance(retrieved, datetime):
        raise KnowledgeBaseError(
            f"{where} 'retrieved' must be a date (YYYY-MM-DD), got {retrieved!r}"
        )
    return SourceEntry(
        id=sid, title=title, url=url, publisher=publisher, retrieved=retrieved, file=file
    )


def _text(item: dict[Any, Any], name: str, where: str) -> str:
    value = item[name]
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeBaseError(f"{where} needs a non-empty {name!r}")
    return value.strip()


def on_domain(host: str | None, domain: str) -> bool:
    """Whether `host` is `domain` or one of its subdomains."""
    return bool(host) and (host == domain or host.endswith("." + domain))


def _check_url(url: str, domain: str, where: str) -> None:
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError as exc:
        raise KnowledgeBaseError(f"{where} has an invalid url {url!r}: {exc}") from exc
    if parts.scheme != "https" or not host:
        raise KnowledgeBaseError(f"{where} url must be an https URL, got {url!r}")
    if not on_domain(host, domain):
        raise KnowledgeBaseError(f"{where} url host {host!r} is not on the publisher's domain {domain!r}")
