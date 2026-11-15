"""`ContentStore` read from `content/texts.yaml` and `content/checklists.yaml`, validated once at startup."""

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from app.ports.content import (
    PAGE_PLACEHOLDERS,
    REQUIRED_TEXT_KEYS,
    VISIT_PURPOSES,
    ChecklistItem,
    ExampleQuestion,
    FixedText,
)
from app.ports.knowledge_base import KnowledgeBase

LANGUAGES = ("th", "en")
CONTACT_PLACEHOLDER = "{ADVISER_CONTACT}"
_KEBAB_CASE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_TOP_LEVEL_KEYS = {"texts", "example-questions"}


class ContentError(Exception):
    """The content file is missing, malformed or incomplete. The app must not start."""


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
                raise ContentError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


class FileContentStore:
    """Validated texts, example questions and checklists, held in memory."""

    def __init__(
        self,
        texts: Mapping[str, FixedText],
        questions: Sequence[ExampleQuestion],
        checklists: Mapping[str, Sequence[ChecklistItem]],
    ) -> None:
        # Exactly one checklist per visit purpose, so a known purpose can never 404.
        if set(checklists) != set(VISIT_PURPOSES) or len(checklists) != len(VISIT_PURPOSES):
            raise ContentError(
                f"checklists must be given for exactly the visit purposes {', '.join(VISIT_PURPOSES)}"
            )
        self._texts = MappingProxyType(dict(texts))
        self._questions = tuple(questions)
        self._checklists = MappingProxyType(
            {purpose: tuple(checklists[purpose]) for purpose in VISIT_PURPOSES}
        )

    def texts(self) -> Mapping[str, FixedText]:
        return self._texts

    def example_questions(self) -> Sequence[ExampleQuestion]:
        return self._questions

    def checklists(self) -> Mapping[str, Sequence[ChecklistItem]]:
        return self._checklists


def load_content(
    path: Path,
    adviser_contact: str,
    checklists: Mapping[str, Sequence[ChecklistItem]],
) -> FileContentStore:
    """Read, validate and fill in the content file. Raises `ContentError` on any problem.

    `checklists` comes from `load_checklists`; it must hold exactly the `VISIT_PURPOSES`.
    """
    data = _read_yaml(path, "content file")
    if not isinstance(data, dict):
        raise ContentError("content file must be a mapping with 'texts' and 'example-questions'")
    unknown = sorted(set(data) - _TOP_LEVEL_KEYS, key=str)
    if unknown:
        raise ContentError(f"unknown top-level key(s): {', '.join(map(str, unknown))}")
    missing = sorted(_TOP_LEVEL_KEYS - set(data))
    if missing:
        raise ContentError(f"missing top-level key(s): {', '.join(missing)}")

    texts = _load_texts(data["texts"], adviser_contact)
    questions = _load_questions(data["example-questions"], adviser_contact)
    return FileContentStore(texts, questions, checklists)


def load_checklists(
    path: Path, knowledge_base: KnowledgeBase, adviser_contact: str
) -> Mapping[str, tuple[ChecklistItem, ...]]:
    """Read and validate `content/checklists.yaml` (AD-11). Raises `ContentError` on any problem.

    The file maps each visit purpose in `VISIT_PURPOSES`, no more and no fewer, to a
    non-empty list of items `{id, th, en, source}`, plus an optional boolean
    `conditional` (default false). Item ids are kebab-case and unique within their
    checklist (the same id may appear in another checklist), and every `source` must be
    a source id in the knowledge base.
    """
    data = _read_yaml(path, "checklists file")
    if not isinstance(data, dict):
        raise ContentError("checklists file must be a mapping of visit purpose to a list of items")
    unknown = sorted(str(k) for k in data if k not in VISIT_PURPOSES)
    if unknown:
        raise ContentError(f"unknown visit purpose(s) in checklists: {', '.join(unknown)}")
    missing = [purpose for purpose in VISIT_PURPOSES if purpose not in data]
    if missing:
        raise ContentError(f"missing checklist(s) for visit purpose(s): {', '.join(missing)}")
    return MappingProxyType(
        {
            purpose: _load_checklist(purpose, data[purpose], knowledge_base, adviser_contact)
            for purpose in VISIT_PURPOSES
        }
    )


def _load_checklist(
    purpose: str, section: object, knowledge_base: KnowledgeBase, adviser_contact: str
) -> tuple[ChecklistItem, ...]:
    if not isinstance(section, list) or not section:
        raise ContentError(f"checklist {purpose!r} must be a non-empty list of {{id, th, en, source}}")

    items: list[ChecklistItem] = []
    seen: set[str] = set()
    for index, entry in enumerate(section):
        if not isinstance(entry, dict):
            raise ContentError(
                f"checklist {purpose!r} item #{index + 1} must be a mapping with id, th, en, source"
            )
        item_id = entry.get("id")
        if not isinstance(item_id, str) or not _KEBAB_CASE.fullmatch(item_id):
            raise ContentError(
                f"checklist {purpose!r} item #{index + 1} needs a kebab-case 'id', got {item_id!r}"
            )
        if item_id in seen:
            raise ContentError(f"checklist {purpose!r} has duplicate item id {item_id!r}")
        seen.add(item_id)
        where = f"checklist {purpose!r} item {item_id!r}"
        _reject_extra_fields(entry, {"id", "source", "conditional", *LANGUAGES}, where)
        th, en = (_language(entry, lang, where, adviser_contact) for lang in LANGUAGES)
        source_id = entry.get("source")
        if not isinstance(source_id, str) or not source_id:
            raise ContentError(f"{where} needs a 'source' id from knowledge-base/sources.yaml")
        try:
            knowledge_base.source(source_id)
        except KeyError:
            raise ContentError(f"{where} cites unknown source {source_id!r}") from None
        conditional = entry.get("conditional", False)
        if not isinstance(conditional, bool):
            raise ContentError(f"{where} has a 'conditional' that is not true or false: {conditional!r}")
        items.append(ChecklistItem(id=item_id, th=th, en=en, source_id=source_id, conditional=conditional))
    return tuple(items)


def _read_yaml(path: Path, what: str) -> object:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContentError(f"cannot read {what} {path}: {exc}") from exc
    try:
        return yaml.load(raw, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ContentError(f"invalid YAML in {path}: {exc}") from exc


def _load_texts(section: object, adviser_contact: str) -> dict[str, FixedText]:
    if not isinstance(section, dict):
        raise ContentError("'texts' must be a mapping of text key to {th, en}")
    unknown = sorted(str(k) for k in section if k not in REQUIRED_TEXT_KEYS)
    if unknown:
        raise ContentError(f"unknown text key(s): {', '.join(unknown)}")
    missing = sorted(REQUIRED_TEXT_KEYS - set(section))
    if missing:
        raise ContentError(f"missing text key(s): {', '.join(missing)}")

    texts: dict[str, FixedText] = {}
    for key in sorted(section):
        entry = section[key]
        where = f"text {key!r}"
        if not isinstance(entry, dict):
            raise ContentError(f"{where} must be a mapping with 'th' and 'en'")
        _reject_extra_fields(entry, set(LANGUAGES), where)
        placeholders = PAGE_PLACEHOLDERS.get(key, ())
        th, en = (_language(entry, lang, where, adviser_contact, placeholders) for lang in LANGUAGES)
        texts[key] = FixedText(th=th, en=en)
    return texts


def _load_questions(section: object, adviser_contact: str) -> list[ExampleQuestion]:
    if not isinstance(section, list) or not section:
        raise ContentError("'example-questions' must be a non-empty list of {id, th, en}")

    questions: list[ExampleQuestion] = []
    seen: set[str] = set()
    for index, entry in enumerate(section):
        if not isinstance(entry, dict):
            raise ContentError(f"example question #{index + 1} must be a mapping with id, th, en")
        qid = entry.get("id")
        if not isinstance(qid, str) or not _KEBAB_CASE.fullmatch(qid):
            raise ContentError(f"example question #{index + 1} needs a kebab-case 'id', got {qid!r}")
        if qid in seen:
            raise ContentError(f"duplicate example question id {qid!r}")
        seen.add(qid)
        where = f"example question {qid!r}"
        _reject_extra_fields(entry, {"id", *LANGUAGES}, where)
        th, en = (_language(entry, lang, where, adviser_contact) for lang in LANGUAGES)
        questions.append(ExampleQuestion(id=qid, th=th, en=en))
    return questions


def _reject_extra_fields(entry: dict[Any, Any], allowed: set[str], where: str) -> None:
    extra = sorted(str(k) for k in entry if k not in allowed)
    if extra:
        raise ContentError(f"{where} has unknown field(s): {', '.join(extra)}")


def _language(
    entry: dict[Any, Any],
    lang: str,
    where: str,
    adviser_contact: str,
    page_placeholders: tuple[str, ...] = (),
) -> str:
    """The text for one language, trimmed, checked and with the contact filled in.

    `page_placeholders` (from `PAGE_PLACEHOLDERS`) must each be in the text and stay in
    it as they are: the page fills them in.
    """
    value = entry.get(lang)
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{where} is missing a non-empty {lang!r} text")
    value = value.strip()
    rest = value.replace(CONTACT_PLACEHOLDER, "")
    for placeholder in page_placeholders:
        if placeholder not in rest:
            raise ContentError(f"{where} ({lang}) must contain {placeholder}: {value!r}")
        rest = rest.replace(placeholder, "")
    # Any brace left once the known placeholders are removed is an unknown or mistyped
    # placeholder. Checked before filling, so braces in the contact value are allowed.
    if "{" in rest or "}" in rest:
        raise ContentError(f"{where} ({lang}) has an unknown or mistyped placeholder: {value!r}")
    return value.replace(CONTACT_PLACEHOLDER, adviser_contact)
