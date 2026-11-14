"""Personal-information filter: removes Thai ID numbers and passport numbers.

Pure, pattern-based logic. Phone numbers, names, addresses and emails are not
removed; the privacy notice tells the applicant not to write them.

Patterns run in this order on the original text (the text is never normalised,
because NFKC changes Thai vowels):

1. Thai ID: digit runs (digit groups joined by 1-3 separators) are scanned from
   the left; the first consecutive groups with exactly 13 digits in total and an
   allowed shape (one group of 13, the official 1-4-5-2-1 grouping, or every
   group 3+ digits) are replaced. Other groups and separators stay.
2. Passport: 1-2 Latin letters (ASCII or full-width) then 7 digits not followed
   by a digit, either glued (the letters start a word, or are uppercase after a
   lowercase letter) or with 1-3 separators (uppercase letters that start a word).

`\\d` matches any Unicode decimal digit, so Thai and full-width digits count.
The module stays ASCII-only (AD-6): non-ASCII characters are written as escapes.
"""

import re
from dataclasses import dataclass

REMOVED_MARKER = "[removed]"

# Space, tab, NBSP, thin space, narrow NBSP, ideographic space, zero-width
# characters, hyphen and dashes, minus, small/full-width hyphen-minus, dot, slash.
_SEP = (
    r"[ \t\u00a0\u2009\u202f\u3000\u200b-\u200d\ufeff"
    r"\-\u2010-\u2015\u2212\ufe63\uff0d./]"
)

_DIGIT_RUN = re.compile(rf"(?<!\d)\d+(?:{_SEP}{{1,3}}\d+)*(?!\d)")
_DIGIT_GROUP = re.compile(r"\d+")
_THAI_ID_DIGITS = 13
_THAI_ID_OFFICIAL_SHAPE = (1, 4, 5, 2, 1)

_UPPER = r"A-Z\uff21-\uff3a"
_LOWER = r"a-z\uff41-\uff5a"
_LETTER = _UPPER + _LOWER
_PASSPORT = re.compile(
    "(?:"
    # Glued, letters start a word (any case): `AA1234567`, `aa1234567`.
    rf"(?<![{_LETTER}])[{_LETTER}]{{1,2}}"
    # Glued, uppercase after a lowercase letter: `passportAA1234567`.
    rf"|(?<=[{_LOWER}])[{_UPPER}]{{1,2}}"
    # With separators, uppercase letters that start a word: `AA 1234567`.
    rf"|(?<![{_LETTER}])[{_UPPER}]{{1,2}}{_SEP}{{1,3}}"
    ")"
    r"\d{7}(?!\d)"
)


@dataclass(frozen=True)
class FilterResult:
    """The filtered text and whether anything was removed from it."""

    text: str
    removed: bool


def remove_personal_info(text: str) -> FilterResult:
    """Replace Thai ID and passport numbers in `text` with `REMOVED_MARKER`."""
    text, id_count = _remove_thai_ids(text)
    text, passport_count = _PASSPORT.subn(REMOVED_MARKER, text)
    return FilterResult(text=text, removed=id_count + passport_count > 0)


def _remove_thai_ids(text: str) -> tuple[str, int]:
    count = 0

    def replace_run(match: re.Match[str]) -> str:
        nonlocal count
        run = match.group()
        spans = _thai_id_spans(run)
        if not spans:
            return run
        count += len(spans)
        parts: list[str] = []
        end = 0
        for start, stop in spans:
            parts.append(run[end:start])
            parts.append(REMOVED_MARKER)
            end = stop
        parts.append(run[end:])
        return "".join(parts)

    return _DIGIT_RUN.sub(replace_run, text), count


def _thai_id_spans(run: str) -> list[tuple[int, int]]:
    """Spans in `run` of consecutive digit groups that form a Thai ID number."""
    groups = [(m.start(), m.end()) for m in _DIGIT_GROUP.finditer(run)]
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(groups):
        lengths: list[int] = []
        for start, stop in groups[i:]:
            lengths.append(stop - start)
            if sum(lengths) >= _THAI_ID_DIGITS:
                break
        if sum(lengths) == _THAI_ID_DIGITS and _is_thai_id_shape(lengths):
            last = i + len(lengths) - 1
            spans.append((groups[i][0], groups[last][1]))
            i = last + 1
        else:
            i += 1
    return spans


def _is_thai_id_shape(lengths: list[int]) -> bool:
    return (
        len(lengths) == 1
        or tuple(lengths) == _THAI_ID_OFFICIAL_SHAPE
        or all(length >= 3 for length in lengths)
    )
