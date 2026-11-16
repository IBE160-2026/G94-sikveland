"""The English of one reply (FR7, AD-4): stored English first, else the model.

Pure logic. The personal-information filter runs first, so neither the lookup nor the
model ever sees an ID or passport number. A text that is the Thai of a fixed text or
an example question gets its stored English with no model call; anything else goes to
`LLMClient.translate`. Errors from the model are passed on to the caller.
"""

import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.pipeline.filter import remove_personal_info
from app.ports.content import ExampleQuestion, FixedText
from app.ports.llm import LLMClient, LLMError, Usage

# Normalised Thai -> its stored English.
StoredEnglish = Mapping[str, str]


@dataclass(frozen=True)
class Translation:
    """The English text; `usage` of the model call, `None` when the stored English was used."""

    text: str
    usage: Usage | None
    stored: bool


def normalise(text: str) -> str:
    """NFC form, trimmed, every run of whitespace collapsed to one space."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def lookup_key(text: str) -> str:
    """The key a text is looked up by: filtered like a request, then normalised."""
    return normalise(remove_personal_info(text).text)


def stored_english(
    texts: Mapping[str, FixedText], example_questions: Iterable[ExampleQuestion]
) -> StoredEnglish:
    """Every fixed text's and example question's Thai, keyed by `lookup_key`, to its English.

    Built once at startup (`app/main.py`). If two Thai texts are the same, the first wins.
    """
    english: dict[str, str] = {}
    pairs = [(text.th, text.en) for text in texts.values()]
    pairs += [(question.th, question.en) for question in example_questions]
    for thai, en in pairs:
        english.setdefault(lookup_key(thai), en)
    return english


def translate_reply(text: str, llm: LLMClient, stored: StoredEnglish) -> Translation:
    """The English of `text`: filter, then the stored English, else `llm.translate`.

    An empty model translation is an `LLMError`; every other model error is raised as is.
    """
    filtered = remove_personal_info(text).text
    english = stored.get(normalise(filtered))
    if english is not None:
        return Translation(text=english, usage=None, stored=True)
    translation, usage = llm.translate(filtered)
    if not translation.strip():
        raise LLMError("the translation is empty")
    return Translation(text=translation.strip(), usage=usage, stored=False)
