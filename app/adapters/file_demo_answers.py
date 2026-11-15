"""Stored demo answers read from `content/demo-answers.yaml`, validated once at startup.

Read only in demo mode (`MOCK_LLM=true`) and only for the `mock_llm` adapter
(AD-2, AD-15). The file holds one answer per example question and the phrases
that end a conversation. Nothing here fetches over the network.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, get_args

import yaml

from app.ports.content import ExampleQuestion
from app.ports.knowledge_base import KnowledgeBase
from app.ports.llm import Category

LANGUAGES = ("th", "en")
ANSWER_FIELDS = frozenset({"category", "th", "en", "sources"})
# `done` ends a conversation; it is never the category of a stored answer.
CATEGORIES: frozenset[str] = frozenset(get_args(Category)) - {"done"}
_TOP_LEVEL_KEYS = {"answers", "done_phrases"}
_THAI = re.compile("[\u0e00-\u0e7f]")


class DemoContentError(Exception):
    """The demo answers file is missing, malformed or incomplete. The app must not start."""


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
                raise DemoContentError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class DemoAnswer:
    """The stored answer to one example question, with the sources it is drawn from."""

    id: str
    category: Category
    th: str
    en: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class DemoAnswers:
    """All demo answers, keyed by example question id, and the done phrases."""

    answers: Mapping[str, DemoAnswer]
    done_phrases: tuple[str, ...]


def load_demo_answers(
    path: Path, example_questions: Sequence[ExampleQuestion], knowledge_base: KnowledgeBase
) -> DemoAnswers:
    """Read and validate the demo answers. Raises `DemoContentError` on any problem.

    Every example question needs exactly one answer, and every cited source must
    be in the knowledge base.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DemoContentError(f"cannot read demo answers file {path}: {exc}") from exc
    try:
        data = yaml.load(raw, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise DemoContentError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise DemoContentError("demo answers file must be a mapping with 'answers' and 'done_phrases'")
    unknown = sorted(str(key) for key in data if key not in _TOP_LEVEL_KEYS)
    if unknown:
        raise DemoContentError(f"unknown top-level key(s): {', '.join(unknown)}")
    missing = sorted(_TOP_LEVEL_KEYS - set(data))
    if missing:
        raise DemoContentError(f"missing top-level key(s): {', '.join(missing)}")

    answers = _load_answers(data["answers"], example_questions, knowledge_base)
    done_phrases = _load_done_phrases(data["done_phrases"])
    return DemoAnswers(answers=MappingProxyType(answers), done_phrases=done_phrases)


def _load_answers(
    section: object, example_questions: Sequence[ExampleQuestion], knowledge_base: KnowledgeBase
) -> dict[str, DemoAnswer]:
    if not isinstance(section, dict):
        raise DemoContentError("'answers' must be a mapping of example question id to an answer")
    example_ids = [question.id for question in example_questions]
    unknown = sorted(str(key) for key in section if key not in example_ids)
    if unknown:
        raise DemoContentError(f"demo answer for unknown example question id(s): {', '.join(unknown)}")
    missing = [qid for qid in example_ids if qid not in section]
    if missing:
        raise DemoContentError(f"no demo answer for example question id(s): {', '.join(missing)}")

    answers: dict[str, DemoAnswer] = {}
    for qid in example_ids:
        entry = section[qid]
        where = f"demo answer {qid!r}"
        if not isinstance(entry, dict):
            raise DemoContentError(f"{where} must be a mapping with category, th, en and sources")
        extra = sorted(str(key) for key in entry if key not in ANSWER_FIELDS)
        if extra:
            raise DemoContentError(f"{where} has unknown field(s): {', '.join(extra)}")

        category = entry.get("category")
        if not isinstance(category, str) or category not in CATEGORIES:
            raise DemoContentError(
                f"{where} has an invalid category {category!r}; "
                f"expected one of {', '.join(sorted(CATEGORIES))}"
            )
        th, en = (_text(entry, lang, where) for lang in LANGUAGES)
        if not _THAI.search(th):
            raise DemoContentError(f"{where} 'th' text contains no Thai")
        answers[qid] = DemoAnswer(
            id=qid,
            category=category,
            th=th,
            en=en,
            source_ids=_source_ids(entry.get("sources"), where, qid, knowledge_base),
        )
    return answers


def _text(entry: dict[Any, Any], lang: str, where: str) -> str:
    value = entry.get(lang)
    if not isinstance(value, str) or not value.strip():
        raise DemoContentError(f"{where} is missing a non-empty {lang!r} text")
    return value.strip()


def _source_ids(value: object, where: str, qid: str, knowledge_base: KnowledgeBase) -> tuple[str, ...]:
    """The cited source ids, each once and each in the knowledge base."""
    if not isinstance(value, list) or not value:
        raise DemoContentError(f"{where} needs a non-empty 'sources' list of source ids")
    ids: list[str] = []
    for source_id in value:
        if not isinstance(source_id, str) or not source_id:
            raise DemoContentError(f"{where} has a source id that is not a string: {source_id!r}")
        if source_id in ids:
            raise DemoContentError(f"{where} cites source {source_id!r} more than once")
        try:
            knowledge_base.source(source_id)
        except KeyError:
            raise DemoContentError(
                f"demo answer {qid!r} cites unknown source id {source_id!r} (not in sources.yaml)"
            ) from None
        ids.append(source_id)
    return tuple(ids)


def _load_done_phrases(section: object) -> tuple[str, ...]:
    if not isinstance(section, list) or not section:
        raise DemoContentError("'done_phrases' must be a non-empty list of phrases")
    phrases: list[str] = []
    for index, phrase in enumerate(section):
        if not isinstance(phrase, str) or not phrase.strip():
            raise DemoContentError(f"done phrase #{index + 1} must be a non-empty string")
        phrases.append(phrase.strip())
    return tuple(phrases)
