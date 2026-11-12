import re
from pathlib import Path

import pytest
import yaml

from app.adapters.file_content import ContentError, load_content
from app.main import CONTENT_FILE
from app.ports.content import REQUIRED_TEXT_KEYS

CONTACT = "adviser@example.com"


def _valid() -> dict:
    texts = {key: {"th": f"th {key}", "en": f"en {key}"} for key in sorted(REQUIRED_TEXT_KEYS)}
    texts["reply-no-answer"] = {"th": "ติดต่อ {ADVISER_CONTACT}", "en": "Contact {ADVISER_CONTACT}."}
    return {
        "texts": texts,
        "example-questions": [
            {"id": "visa-fee", "th": "ค่าธรรมเนียม", "en": "Fee"},
            {"id": "how-to-start", "th": "เริ่มต้น", "en": "Start"},
        ],
    }


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "texts.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def _load(tmp_path: Path, data: object):
    return load_content(_write(tmp_path, data), CONTACT)


def test_valid_content_loads_and_fills_contact(tmp_path: Path) -> None:
    store = _load(tmp_path, _valid())

    assert set(store.texts()) == REQUIRED_TEXT_KEYS
    assert store.texts()["reply-no-answer"].th == f"ติดต่อ {CONTACT}"
    assert store.texts()["reply-no-answer"].en == f"Contact {CONTACT}."
    assert [q.id for q in store.example_questions()] == ["visa-fee", "how-to-start"]
    assert store.example_questions()[0].th == "ค่าธรรมเนียม"


def test_committed_content_file_loads() -> None:
    store = load_content(CONTENT_FILE, CONTACT)

    ids = [q.id for q in store.example_questions()]
    assert ids == ["tourist-visa-documents", "how-to-start", "visa-fee", "processing-time"]
    assert CONTACT in store.texts()["reply-no-answer"].th
    assert CONTACT in store.texts()["reply-no-answer"].en
    thai = re.compile("[\u0e00-\u0e7f]")
    for key, text in store.texts().items():
        assert "{" not in text.th and "{" not in text.en, key
        assert thai.search(text.th), key
    for question in store.example_questions():
        assert thai.search(question.th), question.id


def test_missing_key_names_it(tmp_path: Path) -> None:
    data = _valid()
    del data["texts"]["error"]

    with pytest.raises(ContentError, match="missing text key.*'?error"):
        _load(tmp_path, data)


def test_unknown_key_names_it(tmp_path: Path) -> None:
    data = _valid()
    data["texts"]["privcy-notice"] = {"th": "x", "en": "x"}

    with pytest.raises(ContentError, match="privcy-notice"):
        _load(tmp_path, data)


@pytest.mark.parametrize(
    ("entry", "lang"),
    [
        ({"th": "ข้อความ"}, "en"),
        ({"th": "", "en": "text"}, "th"),
        ({"th": "   ", "en": "text"}, "th"),
        ({"th": None, "en": "text"}, "th"),
    ],
)
def test_missing_or_empty_language_names_key_and_language(
    tmp_path: Path, entry: dict, lang: str
) -> None:
    data = _valid()
    data["texts"]["error"] = entry

    with pytest.raises(ContentError, match=rf"'error'.*'{lang}'"):
        _load(tmp_path, data)


def test_example_question_missing_language(tmp_path: Path) -> None:
    data = _valid()
    del data["example-questions"][0]["en"]

    with pytest.raises(ContentError, match=r"'visa-fee'.*'en'"):
        _load(tmp_path, data)


def test_duplicate_example_id_names_it(tmp_path: Path) -> None:
    data = _valid()
    data["example-questions"].append({"id": "visa-fee", "th": "ซ้ำ", "en": "Again"})

    with pytest.raises(ContentError, match="duplicate example question id 'visa-fee'"):
        _load(tmp_path, data)


@pytest.mark.parametrize("bad_id", ["Visa-Fee", "visa_fee", "visa--fee", "", None])
def test_example_id_must_be_kebab_case(tmp_path: Path, bad_id: object) -> None:
    data = _valid()
    data["example-questions"][0]["id"] = bad_id

    with pytest.raises(ContentError, match="kebab-case"):
        _load(tmp_path, data)


def test_at_least_one_example_question(tmp_path: Path) -> None:
    data = _valid()
    data["example-questions"] = []

    with pytest.raises(ContentError, match="example-questions"):
        _load(tmp_path, data)


def test_duplicate_yaml_text_key_is_rejected(tmp_path: Path) -> None:
    body = yaml.safe_dump(_valid(), allow_unicode=True)
    # Add a second `error:` entry under `texts:` - plain YAML would keep the last one.
    body = body.replace("texts:\n", "texts:\n  error:\n    en: first\n    th: first\n", 1)
    path = tmp_path / "texts.yaml"
    path.write_text(body, encoding="utf-8")

    with pytest.raises(ContentError, match="duplicate key 'error'"):
        load_content(path, CONTACT)


def test_leftover_placeholder_names_key(tmp_path: Path) -> None:
    data = _valid()
    data["texts"]["error"]["th"] = "ติดต่อ {SOMETHING}"

    with pytest.raises(ContentError, match=r"'error' \(th\).*\{SOMETHING\}"):
        _load(tmp_path, data)


@pytest.mark.parametrize(
    "typo",
    ["{ADVISER CONTACT}", "{ ADVISER_CONTACT }", "{ADVISER_CONTACT", "ADVISER_CONTACT}", "{adviser_contact}"],
)
def test_mistyped_placeholder_names_key_and_language(tmp_path: Path, typo: str) -> None:
    data = _valid()
    data["texts"]["error"]["en"] = f"Contact {typo}."

    with pytest.raises(ContentError, match=r"'error' \(en\)"):
        _load(tmp_path, data)


def test_mistyped_placeholder_in_example_question_names_id(tmp_path: Path) -> None:
    data = _valid()
    data["example-questions"][0]["th"] = "ติดต่อ {ADVISER_CONTACT"

    with pytest.raises(ContentError, match=r"'visa-fee' \(th\)"):
        _load(tmp_path, data)


def test_contact_with_braces_is_not_a_leftover_placeholder(tmp_path: Path) -> None:
    store = load_content(_write(tmp_path, _valid()), "{ODD}")

    assert store.texts()["reply-no-answer"].th == "ติดต่อ {ODD}"


@pytest.mark.parametrize(
    "data",
    [None, [], {"texts": {}}, {"texts": [], "example-questions": []}],
)
def test_malformed_structure_is_rejected(tmp_path: Path, data: object) -> None:
    with pytest.raises(ContentError):
        _load(tmp_path, data)


def test_unknown_field_in_entry_is_rejected(tmp_path: Path) -> None:
    data = _valid()
    data["texts"]["error"]["no"] = "Feil"

    with pytest.raises(ContentError, match=r"'error'.*no"):
        _load(tmp_path, data)


def test_non_utf8_file_is_a_content_error(tmp_path: Path) -> None:
    path = tmp_path / "texts.yaml"
    # PowerShell 5.1 may save files as UTF-16.
    path.write_text(yaml.safe_dump(_valid(), allow_unicode=True), encoding="utf-16")

    with pytest.raises(ContentError, match="cannot read"):
        load_content(path, CONTACT)


def test_missing_file_and_bad_yaml(tmp_path: Path) -> None:
    with pytest.raises(ContentError, match="cannot read"):
        load_content(tmp_path / "missing.yaml", CONTACT)

    path = tmp_path / "bad.yaml"
    path.write_text("texts: [unclosed", encoding="utf-8")
    with pytest.raises(ContentError, match="invalid YAML"):
        load_content(path, CONTACT)


def test_app_refuses_to_start_with_invalid_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings
) -> None:
    import app.main

    data = _valid()
    del data["texts"]["error"]
    monkeypatch.setattr(app.main, "CONTENT_FILE", _write(tmp_path, data))

    with pytest.raises(ContentError, match="error"):
        app.main.create_app(settings)
