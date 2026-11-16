"""The evaluation test set `eval/testset.yaml`: loading and validation (Story 5.1, NFR4).

The file holds made-up Thai questions, each with the category the classifier should
choose, the outcome the pipeline should reach (the request-log values `answered`,
`no_answer` or `fixed_reply`), the facts an answer must contain and the sources it
must cite. `scripts/run_eval.py` (Story 5.2) reads the cases through `load_testset`.
Nothing here calls a model or the network.

Rules checked per case (a broken rule raises `TestsetError` naming the case):

- exactly the fields in `FIELDS` plus the optional ones in `OPTIONAL_FIELDS`;
- `id` is kebab-case and unique; `question` and every history turn contain Thai,
  `en` and the facts contain none;
- `category` is one of the classifier's categories; `general` expects `answered` or
  `no_answer`, every other category `fixed_reply`;
- `answered` needs at least one fact and one source; `no_answer` and `fixed_reply`
  have neither; every source id is in the knowledge base;
- `history` has 1-2 `{question, answer}` exchanges, and exactly the cases tagged
  `follow-up` have one; `personal_info` lists `thai_id`, `passport` or `phone`.

Coverage (which tags and how many cases of each kind) is a property of the committed
file and is checked by `tests/test_testset.py`, not here.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, get_args

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ports.knowledge_base import KnowledgeBase  # noqa: E402
from app.ports.llm import Category, Exchange  # noqa: E402

TESTSET_FILE = ROOT / "eval" / "testset.yaml"

# The outcomes a chat question can end in when nothing fails (a subset of the request log's).
ExpectedOutcome = Literal["answered", "no_answer", "fixed_reply"]
PersonalInfo = Literal["thai_id", "passport", "phone"]

CATEGORIES: tuple[str, ...] = get_args(Category)
OUTCOMES: tuple[str, ...] = get_args(ExpectedOutcome)
PERSONAL_INFO: tuple[str, ...] = get_args(PersonalInfo)
FIELDS = ("id", "question", "en", "category", "outcome", "facts", "sources", "tags")
OPTIONAL_FIELDS = ("history", "personal_info")
HISTORY_FIELDS = ("question", "answer")
MAX_HISTORY = 2
FOLLOW_UP_TAG = "follow-up"

_KEBAB_CASE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_THAI = re.compile("[฀-๿]")


class TestsetError(Exception):
    """The test set file is missing, malformed or breaks a rule."""

    __test__ = False  # not a pytest test class


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
                raise TestsetError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class TestCase:
    """One test question with what the pipeline is expected to do with it."""

    __test__ = False  # not a pytest test class

    id: str
    question: str
    en: str
    category: Category
    outcome: ExpectedOutcome
    facts: tuple[str, ...]
    sources: tuple[str, ...]
    tags: tuple[str, ...]
    history: tuple[Exchange, ...] = ()
    personal_info: tuple[PersonalInfo, ...] = ()


def load_testset(path: Path, knowledge_base: KnowledgeBase) -> list[TestCase]:
    """Read and validate the test set. Raises `TestsetError` on any problem."""
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise TestsetError(f"cannot read test set {path}: {exc}") from exc
    try:
        data = yaml.load(raw, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise TestsetError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {"cases"}:
        raise TestsetError(f"{path} must be a mapping with exactly one key, 'cases'")
    items = data["cases"]
    if not isinstance(items, list) or not items:
        raise TestsetError(f"'cases' in {path} must be a non-empty list")

    cases: list[TestCase] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        case = _case(item, index, knowledge_base)
        if case.id in seen:
            raise TestsetError(f"duplicate case id {case.id!r}")
        seen.add(case.id)
        cases.append(case)
    return cases


def _case(item: object, index: int, knowledge_base: KnowledgeBase) -> TestCase:
    if not isinstance(item, dict):
        raise TestsetError(f"case #{index + 1} must be a mapping of {', '.join(FIELDS)}")
    cid = item.get("id")
    if not isinstance(cid, str) or not _KEBAB_CASE.fullmatch(cid):
        raise TestsetError(f"case #{index + 1} needs a kebab-case 'id', got {cid!r}")
    where = f"case {cid!r}"

    extra = sorted(str(key) for key in item if key not in FIELDS + OPTIONAL_FIELDS)
    if extra:
        raise TestsetError(f"{where} has unknown field(s): {', '.join(extra)}")
    missing = [name for name in FIELDS if name not in item]
    if missing:
        raise TestsetError(f"{where} is missing field(s): {', '.join(missing)}")

    question = _thai_text(item["question"], f"{where} 'question'")
    en = _english_text(item["en"], f"{where} 'en'")
    category = _choice(item["category"], CATEGORIES, f"{where} 'category'")
    outcome = _choice(item["outcome"], OUTCOMES, f"{where} 'outcome'")
    facts = tuple(_english_text(fact, f"{where} fact") for fact in _list(item["facts"], f"{where} 'facts'"))
    sources = _sources(item["sources"], where, knowledge_base)
    tags = _tags(item["tags"], where)
    history = _history(item.get("history", []), where)
    personal_info = tuple(
        _choice(value, PERSONAL_INFO, f"{where} 'personal_info'")
        for value in _list(item.get("personal_info", []), f"{where} 'personal_info'")
    )
    if len(set(personal_info)) != len(personal_info):
        raise TestsetError(f"{where} lists a 'personal_info' kind more than once")

    _check_consistency(where, category, outcome, facts, sources)
    if bool(history) != (FOLLOW_UP_TAG in tags):
        raise TestsetError(f"{where} must have 'history' exactly when it is tagged {FOLLOW_UP_TAG!r}")

    return TestCase(
        id=cid,
        question=question,
        en=en,
        category=category,
        outcome=outcome,
        facts=facts,
        sources=sources,
        tags=tags,
        history=history,
        personal_info=personal_info,
    )


def _check_consistency(
    where: str, category: str, outcome: str, facts: tuple[str, ...], sources: tuple[str, ...]
) -> None:
    if category == "general" and outcome == "fixed_reply":
        raise TestsetError(
            f"{where}: a 'general' question expects 'answered' or 'no_answer', not 'fixed_reply'"
        )
    if category != "general" and outcome != "fixed_reply":
        raise TestsetError(f"{where}: a {category!r} question expects 'fixed_reply', not {outcome!r}")
    if outcome == "answered" and not (facts and sources):
        raise TestsetError(f"{where}: an 'answered' case needs at least one fact and one source")
    if outcome != "answered" and (facts or sources):
        raise TestsetError(f"{where}: a {outcome!r} case has no facts and no sources")


def _list(value: object, what: str) -> list[Any]:
    if not isinstance(value, list):
        raise TestsetError(f"{what} must be a list, got {value!r}")
    return value


def _text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TestsetError(f"{what} must be a non-empty string, got {value!r}")
    return value.strip()


def _thai_text(value: object, what: str) -> str:
    text = _text(value, what)
    if not _THAI.search(text):
        raise TestsetError(f"{what} contains no Thai")
    return text


def _english_text(value: object, what: str) -> str:
    text = _text(value, what)
    if _THAI.search(text):
        raise TestsetError(f"{what} must be English, without Thai: {text!r}")
    return text


def _choice(value: object, allowed: tuple[str, ...], what: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise TestsetError(f"{what} is {value!r}; expected one of {', '.join(allowed)}")
    return value


def _sources(value: object, where: str, knowledge_base: KnowledgeBase) -> tuple[str, ...]:
    ids: list[str] = []
    for source_id in _list(value, f"{where} 'sources'"):
        if not isinstance(source_id, str) or not source_id:
            raise TestsetError(f"{where} has a source id that is not a string: {source_id!r}")
        if source_id in ids:
            raise TestsetError(f"{where} lists source {source_id!r} more than once")
        try:
            knowledge_base.source(source_id)
        except KeyError:
            raise TestsetError(f"{where} has unknown source id {source_id!r} (not in sources.yaml)") from None
        ids.append(source_id)
    return tuple(ids)


def _tags(value: object, where: str) -> tuple[str, ...]:
    tags: list[str] = []
    for tag in _list(value, f"{where} 'tags'"):
        if not isinstance(tag, str) or not _KEBAB_CASE.fullmatch(tag):
            raise TestsetError(f"{where} has a tag that is not kebab-case: {tag!r}")
        if tag in tags:
            raise TestsetError(f"{where} lists tag {tag!r} more than once")
        tags.append(tag)
    return tuple(tags)


def _history(value: object, where: str) -> tuple[Exchange, ...]:
    turns = _list(value, f"{where} 'history'")
    if len(turns) > MAX_HISTORY:
        raise TestsetError(f"{where} 'history' has {len(turns)} exchanges; at most {MAX_HISTORY}")
    history: list[Exchange] = []
    for number, turn in enumerate(turns, start=1):
        what = f"{where} history exchange #{number}"
        if not isinstance(turn, dict) or set(turn) != set(HISTORY_FIELDS):
            raise TestsetError(f"{what} must be a mapping with exactly 'question' and 'answer'")
        history.append(
            Exchange(
                question=_thai_text(turn["question"], f"{what} 'question'"),
                answer=_thai_text(turn["answer"], f"{what} 'answer'"),
            )
        )
    return tuple(history)
