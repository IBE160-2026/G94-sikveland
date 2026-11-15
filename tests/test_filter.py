import ast
from pathlib import Path

import pytest

import app.pipeline.filter as filter_module
from app.adapters.file_content import load_content
from app.main import CONTENT_FILE
from app.pipeline.filter import REMOVED_MARKER, FilterResult, remove_personal_info

FILTER_FILE = Path(filter_module.__file__)

# Invisible and full-width characters are written as escapes so each case is readable;
# Thai text is written as is.
NBSP = "\u00a0"
EN_DASH = "\u2013"
ZWSP = "\u200b"

THAI_IDS = [
    "1234567890123",
    "1-2345-67890-12-3",
    "1 2345 67890 12 3",
    "1234 5678 90123",
    "๑๒๓๔๕๖๗๘๙๐๑๒๓",  # Thai digits
    # Extra cases (Design Notes): other separators in the 1-4-5-2-1 shape.
    f"1{NBSP}2345{NBSP}67890{NBSP}12{NBSP}3",
    f"1{EN_DASH}2345{EN_DASH}67890{EN_DASH}12{EN_DASH}3",
    "1\t2345\t67890\t12\t3",
    f"1{ZWSP}2345{ZWSP}67890{ZWSP}12{ZWSP}3",
    "1 - 2345 - 67890 - 12 - 3",
    "1.2345.67890.12.3",
    # Full-width digits.
    "\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19\uff10\uff11\uff12\uff13",
]

PASSPORTS = [
    "AA1234567",
    "A1234567",
    "aa1234567",
    "AA 1234567",
    "AA-1234567",
    # Extra cases (Design Notes).
    "\uff21\uff211234567",  # full-width letters
    "AA - 1234567",
    "AA๑๒๓๔๕๖๗",  # Thai digits
    "AA１２３４５６７",  # full-width digits
]

KEPT = [
    # Phone numbers are not removed.
    "081-234-5678",
    "+66 81 234 5678",
    "+47 412 34 567",
    "98765432",
    # Dates, times, amounts.
    "05-11-2026 10:00",
    "2026-12-01 - 2026-12-20",
    "15.11.2026",
    "ปี 2569",  # "year 2569"
    "THB 1500000",
    "costs 1500000 baht",
    "COVID-1234567",
    "100000-200000 บาท",  # "... baht"
    "30,000 euro",
    "90 euro",
    # No personal info.
    "ขอวีซ่าท่องเที่ยว",
    "ขอ visa ท่องเที่ยว Norway",
    "",
    # Extra kept cases (Design Notes).
    "12345678901234",
    "x 12345678901234",
    "AA12345678",
    "COVID1234567",
    "ref1234567",
    "is 1500000",
    "kr 1500000",
    "up to 1500000 baht",
    "No 1234567",
    "1 2 3 4 5 6 7 8 9 10 11",
    "0066 81 234 5678",
    "aa 1234567",  # lowercase letters with a separator
]

# Thai words used around the numbers: "My card number is ... please" / "fee".
THAI_PREFIX = "เลขบัตร"
THAI_SUFFIX = "ครับ"


@pytest.mark.parametrize("number", THAI_IDS + PASSPORTS)
def test_number_alone_is_removed(number: str) -> None:
    assert remove_personal_info(number) == FilterResult(text=REMOVED_MARKER, removed=True)


@pytest.mark.parametrize("number", THAI_IDS + PASSPORTS)
def test_number_in_sentence_is_removed(number: str) -> None:
    result = remove_personal_info(f"My number is {number} , what now?")

    assert result == FilterResult(text=f"My number is {REMOVED_MARKER} , what now?", removed=True)


@pytest.mark.parametrize("text", KEPT)
def test_kept_text_alone_is_unchanged(text: str) -> None:
    assert remove_personal_info(text) == FilterResult(text=text, removed=False)


@pytest.mark.parametrize("text", [t for t in KEPT if t])
def test_kept_text_in_sentence_is_unchanged(text: str) -> None:
    sentence = f"Question: {text} , is that ok?"

    assert remove_personal_info(sentence) == FilterResult(text=sentence, removed=False)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"{THAI_PREFIX}1234567890123{THAI_SUFFIX}", f"{THAI_PREFIX}{REMOVED_MARKER}{THAI_SUFFIX}"),
        ("passportAA1234567", f"passport{REMOVED_MARKER}"),
        ("passportA1234567", f"passport{REMOVED_MARKER}"),
        (f"passport{THAI_SUFFIX}AA1234567", f"passport{THAI_SUFFIX}{REMOVED_MARKER}"),
        ("ID 1234567890123 2 people", f"ID {REMOVED_MARKER} 2 people"),
        ("1234567890123 1234567890123", f"{REMOVED_MARKER} {REMOVED_MARKER}"),
        ("AA 1234567 2", f"{REMOVED_MARKER} 2"),
        # An ID after another number in the same digit run.
        ("born 01.02.1990 1234567890123", f"born 01.02.1990 {REMOVED_MARKER}"),
        ("tel 081 234 5678 1234567890123", f"tel 081 234 5678 {REMOVED_MARKER}"),
        (f"{THAI_PREFIX}๑๒๓๔๕๖๗๘๙๐๑๒๓{THAI_SUFFIX}", f"{THAI_PREFIX}{REMOVED_MARKER}{THAI_SUFFIX}"),
        # Punctuation and a digit next to a passport.
        ("(AA1234567)", f"({REMOVED_MARKER})"),
        ("AA1234567,", f"{REMOVED_MARKER},"),
        ("1AA1234567", f"1{REMOVED_MARKER}"),
    ],
)
def test_exact_output(text: str, expected: str) -> None:
    assert remove_personal_info(text) == FilterResult(text=expected, removed=True)


def test_several_matches_are_each_replaced() -> None:
    text = "ID 1-2345-67890-12-3 and passport AA1234567, travel 15.11.2026 for 90 euro"

    result = remove_personal_info(text)

    assert result == FilterResult(
        text=f"ID {REMOVED_MARKER} and passport {REMOVED_MARKER}, travel 15.11.2026 for 90 euro",
        removed=True,
    )


def test_phone_next_to_id_is_kept() -> None:
    result = remove_personal_info("ID 1-2345-67890-12-3 tel 081-234-5678 fee 90 euro")

    assert result == FilterResult(text=f"ID {REMOVED_MARKER} tel 081-234-5678 fee 90 euro", removed=True)


ACCEPTED_FALSE_POSITIVES = ["081 234 5678 123", "A 1234567"]


@pytest.mark.parametrize("text", ACCEPTED_FALSE_POSITIVES)
def test_known_accepted_false_positives(text: str) -> None:
    # Accepted trade-off (Design Notes): these shapes match an ID or a passport.
    assert remove_personal_info(text) == FilterResult(text=REMOVED_MARKER, removed=True)


@pytest.mark.parametrize("text", ACCEPTED_FALSE_POSITIVES)
def test_known_accepted_false_positives_in_sentence(text: str) -> None:
    result = remove_personal_info(f"Question: {text} , is that ok?")

    assert result == FilterResult(text=f"Question: {REMOVED_MARKER} , is that ok?", removed=True)


def test_marker_is_plain_ascii() -> None:
    assert REMOVED_MARKER == "[removed]"
    assert REMOVED_MARKER.isascii()


def test_module_source_is_ascii() -> None:
    assert FILTER_FILE.read_text(encoding="utf-8").isascii()


def test_module_is_pure() -> None:
    tree = ast.parse(FILTER_FILE.read_text(encoding="utf-8"))
    allowed_modules = {"re", "dataclasses"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in allowed_modules, alias.name
                imported.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            assert node.module in allowed_modules, node.module
            for alias in node.names:
                imported.add(alias.asname or alias.name)

    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert imported <= used, f"unused imports: {imported - used}"
    forbidden = {"open", "print", "__import__", "eval", "exec"}
    assert not used & forbidden, used & forbidden


def test_committed_privacy_texts_say_phone_numbers_are_not_removed() -> None:
    texts = load_content(CONTENT_FILE, "adviser@example.com").texts()

    notice = texts["privacy-notice"]
    reminder = texts["personal-info-reminder"]
    assert notice.th and notice.en and reminder.th and reminder.en
    # "but phone numbers ... are not removed"
    assert "แต่จะไม่ลบเบอร์โทรศัพท์" in notice.th
    assert "but phone numbers, names, addresses and emails are not" in notice.en
    # The reminder only claims what the filter removes.
    assert "เบอร์โทรศัพท์" not in reminder.th
    assert "phone" not in reminder.en
