"""`ContentStore` read from `content/texts.yaml`, validated once at startup."""

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from app.ports.content import REQUIRED_TEXT_KEYS, ExampleQuestion, FixedText

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
    """Validated texts and example questions, held in memory."""

    def __init__(self, texts: Mapping[str, FixedText], questions: Sequence[ExampleQuestion]) -> None:
        self._texts = MappingProxyType(dict(texts))
        self._questions = tuple(questions)

    def texts(self) -> Mapping[str, FixedText]:
        return self._texts

    def example_questions(self) -> Sequence[ExampleQuestion]:
        return self._questions


def load_content(path: Path, adviser_contact: str) -> FileContentStore:
    """Read, validate and fill in the content file. Raises `ContentError` on any problem."""
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContentError(f"cannot read content file {path}: {exc}") from exc
    try:
        data = yaml.load(raw, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ContentError(f"invalid YAML in {path}: {exc}") from exc

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
    return FileContentStore(texts, questions)


def _load_texts(section: object, adviser_contact: str) -> dict[str, FixedText]:
    if not isinstance(section, dict):
        raise ContentError("'texts' must be a mapping of text key to {th, en}")
    unknown = sorted((str(k) for k in section if k not in REQUIRED_TEXT_KEYS))
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
        th, en = (_language(entry, lang, where, adviser_contact) for lang in LANGUAGES)
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


def _language(entry: dict[Any, Any], lang: str, where: str, adviser_contact: str) -> str:
    """The text for one language, trimmed, checked and with the contact filled in."""
    value = entry.get(lang)
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{where} is missing a non-empty {lang!r} text")
    value = value.strip()
    # Any brace left once the known placeholder is removed is an unknown or mistyped
    # placeholder. Checked before filling, so braces in the contact value are allowed.
    rest = value.replace(CONTACT_PLACEHOLDER, "")
    if "{" in rest or "}" in rest:
        raise ContentError(f"{where} ({lang}) has an unknown or mistyped placeholder: {value!r}")
    return value.replace(CONTACT_PLACEHOLDER, adviser_contact)
