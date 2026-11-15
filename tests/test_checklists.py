"""Checklists per visit purpose (Story 3.1, FR6, AD-11): loading, startup checks and the endpoint."""

import copy
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NoReturn

import pytest
import yaml
from fastapi.testclient import TestClient

import app.main
from app.adapters.file_content import ContentError, FileContentStore, load_checklists, load_content
from app.adapters.file_knowledge_base import load_knowledge_base
from app.config import Settings
from app.main import CHECKLISTS_FILE, CONTENT_FILE, KNOWLEDGE_BASE_DIR, create_app
from app.ports.content import VISIT_PURPOSES
from app.web.checklists import UNKNOWN_PURPOSE_ERROR

CONTACT = "adviser@example.com"
KNOWLEDGE_BASE = load_knowledge_base(KNOWLEDGE_BASE_DIR)
THAI = re.compile("[฀-๿]")
# Every checklist has at least these general items (acceptance criterion).
GENERAL_ITEMS = ("passport", "photo", "application-form", "travel-insurance")
SPONSOR_ITEMS = {
    "sponsorship-form": "udi-sponsorship-form",
    "invitation-letter": "udi-invitation-for-visitor-visa",
}


def _item(item_id: str, source: str = "embassy-visitor-visa-checklist") -> dict[str, str]:
    return {"id": item_id, "th": f"ไทย {item_id}", "en": f"English {item_id}", "source": source}


def _valid() -> dict[str, list[dict[str, str]]]:
    return {
        "tourism": [_item("passport"), _item("photo")],
        # The same id in two checklists is allowed.
        "family": [_item("passport"), _item("sponsorship-form", "udi-sponsorship-form")],
        "friends": [_item("passport")],
    }


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "checklists.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _load(tmp_path: Path, data: object):
    return load_checklists(_write(tmp_path, data), KNOWLEDGE_BASE, CONTACT)


# --- Loader rules ---------------------------------------------------------------------------------


def test_valid_checklists_load_in_file_order(tmp_path: Path) -> None:
    checklists = _load(tmp_path, _valid())

    assert list(checklists) == list(VISIT_PURPOSES)
    assert [item.id for item in checklists["tourism"]] == ["passport", "photo"]
    assert [item.id for item in checklists["family"]] == ["passport", "sponsorship-form"]
    family_form = checklists["family"][1]
    assert (family_form.th, family_form.en) == ("ไทย sponsorship-form", "English sponsorship-form")
    assert family_form.source_id == "udi-sponsorship-form"


def test_content_store_serves_the_checklists(tmp_path: Path) -> None:
    checklists = _load(tmp_path, _valid())

    store = load_content(CONTENT_FILE, CONTACT, checklists)

    assert [item.id for item in store.checklists()["friends"]] == ["passport"]


@pytest.mark.parametrize(
    "purposes",
    [(), ("tourism", "family"), ("tourism", "family", "friends", "business")],
    ids=["none", "missing", "extra"],
)
def test_content_store_rejects_checklists_not_for_exactly_the_visit_purposes(
    tmp_path: Path, purposes: tuple[str, ...]
) -> None:
    # A wiring path that forgets the checklists must fail at startup, not 404 a known purpose.
    item = _load(tmp_path, _valid())["tourism"]
    checklists = {purpose: item for purpose in purposes}

    with pytest.raises(ContentError, match="exactly the visit purposes"):
        FileContentStore({}, (), checklists)
    with pytest.raises(ContentError, match="exactly the visit purposes"):
        load_content(CONTENT_FILE, CONTACT, checklists)


def test_unknown_source_names_checklist_and_item(tmp_path: Path) -> None:
    data = _valid()
    data["family"][1]["source"] = "no-such-source"

    with pytest.raises(ContentError, match=r"'family' item 'sponsorship-form'.*'no-such-source'"):
        _load(tmp_path, data)


def test_duplicate_item_id_in_one_checklist_names_the_id(tmp_path: Path) -> None:
    data = _valid()
    data["tourism"].append(_item("passport"))

    with pytest.raises(ContentError, match=r"'tourism'.*duplicate item id 'passport'"):
        _load(tmp_path, data)


@pytest.mark.parametrize("bad_id", ["Passport_Copy", "passport copy", "passport-", "", 7, None])
def test_bad_item_id_is_rejected(tmp_path: Path, bad_id: object) -> None:
    data = _valid()
    data["tourism"][0]["id"] = bad_id

    with pytest.raises(ContentError, match="kebab-case"):
        _load(tmp_path, data)


@pytest.mark.parametrize("purpose", VISIT_PURPOSES)
def test_missing_purpose_is_rejected(tmp_path: Path, purpose: str) -> None:
    data = _valid()
    del data[purpose]

    with pytest.raises(ContentError, match=rf"missing checklist.*{purpose}"):
        _load(tmp_path, data)


def test_extra_purpose_is_rejected(tmp_path: Path) -> None:
    data = _valid()
    data["business"] = [_item("passport")]

    with pytest.raises(ContentError, match=r"unknown visit purpose.*business"):
        _load(tmp_path, data)


def test_extra_field_is_rejected(tmp_path: Path) -> None:
    data = _valid()
    data["tourism"][1]["sources"] = ["udi-fees"]

    with pytest.raises(ContentError, match=r"'tourism' item 'photo' has unknown field.*sources"):
        _load(tmp_path, data)


@pytest.mark.parametrize("lang", ["th", "en"])
@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_or_empty_text_is_rejected(tmp_path: Path, lang: str, value: str | None) -> None:
    data = _valid()
    if value is None:
        del data["friends"][0][lang]
    else:
        data["friends"][0][lang] = value

    with pytest.raises(ContentError, match=f"'friends' item 'passport'.*'{lang}'"):
        _load(tmp_path, data)


@pytest.mark.parametrize("source", [None, "", 3])
def test_missing_source_is_rejected(tmp_path: Path, source: object) -> None:
    data = _valid()
    if source is None:
        del data["tourism"][0]["source"]
    else:
        data["tourism"][0]["source"] = source

    with pytest.raises(ContentError, match=r"'tourism' item 'passport' needs a 'source'"):
        _load(tmp_path, data)


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {"tourism": [], "family": [_item("passport")], "friends": [_item("passport")]},
        {"tourism": {"passport": "x"}, "family": [_item("passport")], "friends": [_item("passport")]},
        {"tourism": ["passport"], "family": [_item("passport")], "friends": [_item("passport")]},
    ],
)
def test_malformed_structure_is_rejected(tmp_path: Path, data: object) -> None:
    with pytest.raises(ContentError):
        _load(tmp_path, data)


def test_duplicate_purpose_key_is_rejected(tmp_path: Path) -> None:
    body = yaml.safe_dump(_valid(), allow_unicode=True, sort_keys=False)
    path = tmp_path / "checklists.yaml"
    path.write_text(
        body + "tourism:\n- id: photo\n  th: ไทย\n  en: x\n  source: udi-fees\n", encoding="utf-8"
    )

    with pytest.raises(ContentError, match="duplicate key 'tourism'"):
        load_checklists(path, KNOWLEDGE_BASE, CONTACT)


def test_missing_file_and_bad_yaml(tmp_path: Path) -> None:
    with pytest.raises(ContentError, match="cannot read checklists file"):
        load_checklists(tmp_path / "missing.yaml", KNOWLEDGE_BASE, CONTACT)

    path = tmp_path / "bad.yaml"
    path.write_text("tourism: [unclosed", encoding="utf-8")
    with pytest.raises(ContentError, match="invalid YAML"):
        load_checklists(path, KNOWLEDGE_BASE, CONTACT)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["family"][1].update(source="no-such-source"),
        lambda d: d["tourism"].append(_item("photo")),
        lambda d: d["tourism"][0].update(id="Passport_Copy"),
        lambda d: d.pop("friends"),
        lambda d: d["tourism"][0].update(note="extra"),
        lambda d: d["tourism"][0].update(th=""),
    ],
    ids=["unknown-source", "duplicate-id", "bad-id", "missing-purpose", "extra-field", "empty-text"],
)
def test_app_refuses_to_start_with_invalid_checklists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings: Settings, change: Any
) -> None:
    data = copy.deepcopy(_valid())
    change(data)
    monkeypatch.setattr(app.main, "CHECKLISTS_FILE", _write(tmp_path, data))

    with pytest.raises(ContentError):
        create_app(settings)


# --- The committed file ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed() -> dict[str, Any]:
    return dict(load_checklists(CHECKLISTS_FILE, KNOWLEDGE_BASE, CONTACT))


def test_committed_file_has_every_purpose_and_resolvable_sources(committed: dict[str, Any]) -> None:
    assert list(committed) == list(VISIT_PURPOSES)
    for purpose, items in committed.items():
        ids = [item.id for item in items]
        for general in GENERAL_ITEMS:
            assert general in ids, (purpose, general)
        for item in items:
            source = KNOWLEDGE_BASE.source(item.source_id)
            assert source.url.startswith("https://"), item.id
            assert THAI.search(item.th), (purpose, item.id)
            assert not THAI.search(item.en), (purpose, item.id)


@pytest.mark.parametrize("purpose", ["family", "friends"])
def test_family_and_friends_have_the_sponsor_items(committed: dict[str, Any], purpose: str) -> None:
    # Checked by id and source only: the wording changes with the adviser's review.
    items = {item.id: item for item in committed[purpose]}

    for item_id, source_id in SPONSOR_ITEMS.items():
        item = items[item_id]
        assert item.source_id == source_id
        assert item.th.strip() and item.en.strip(), item_id


def test_tourism_has_no_sponsor_items(committed: dict[str, Any]) -> None:
    assert not set(SPONSOR_ITEMS) & {item.id for item in committed["tourism"]}


@pytest.mark.parametrize("purpose", VISIT_PURPOSES)
def test_every_checklist_points_to_the_embassy_checklist_and_asks_for_occupation(
    committed: dict[str, Any], purpose: str
) -> None:
    items = {item.id: item for item in committed[purpose]}
    ids = list(items)

    assert items["signed-embassy-checklist"].source_id == "embassy-visitor-visa-checklist"
    assert items["proof-of-occupation"].source_id == "embassy-visitor-visa-checklist"
    # The unconditional item comes before the two conditional ones.
    assert (
        ids.index("proof-of-occupation") < ids.index("employment-proof") < ids.index("self-employment-proof")
    )


def test_only_family_points_to_the_eu_eea_checklist(committed: dict[str, Any]) -> None:
    family = {item.id: item for item in committed["family"]}

    assert family["eu-eea-family-member"].source_id == "embassy-necessary-documents"
    for purpose in ("tourism", "friends"):
        assert "eu-eea-family-member" not in {item.id for item in committed[purpose]}


def test_an_id_shared_by_checklists_has_the_same_content(committed: dict[str, Any]) -> None:
    # The file's own rule: an id never stands for different content, also across checklists.
    seen: dict[str, Any] = {}
    for items in committed.values():
        for item in items:
            assert seen.setdefault(item.id, item) == item, item.id


def test_committed_file_records_the_thai_review_and_the_id_rule() -> None:
    header = CHECKLISTS_FILE.read_text(encoding="utf-8").split("\ntourism:")[0]

    # The Thai was approved by the user (NFR8); a later change is a DRAFT again until reviewed.
    assert "NFR8" in header and ("approved" in header or "DRAFT" in header)
    assert "NEVER reuse an id" in header


# --- The endpoint ---------------------------------------------------------------------------------


class ExplodingLLM:
    """An `LLMClient` that fails the test on any call: the checklists must never reach the LLM."""

    def classify(self, *args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("classify called")

    def answer(self, *args: object, **kwargs: object) -> Iterator[Any]:
        raise AssertionError("answer called")

    def translate(self, *args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("translate called")


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings, llm=ExplodingLLM()))


@pytest.mark.parametrize("purpose", VISIT_PURPOSES)
def test_endpoint_serves_thai_items_with_resolved_sources(
    client: TestClient, committed: dict[str, Any], purpose: str
) -> None:
    response = client.get(f"/api/checklists/{purpose}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"purpose", "items"}
    assert body["purpose"] == purpose
    assert [item["id"] for item in body["items"]] == [item.id for item in committed[purpose]]
    for served, stored in zip(body["items"], committed[purpose], strict=True):
        assert set(served) == {"id", "text", "source"}
        assert served["text"] == stored.th
        source = KNOWLEDGE_BASE.source(stored.source_id)
        assert served["source"] == {"title": source.title, "url": source.url}
        assert served["source"]["url"].startswith("https://")


def test_family_endpoint_has_the_sponsor_items(client: TestClient) -> None:
    items = {item["id"]: item for item in client.get("/api/checklists/family").json()["items"]}

    assert items["sponsorship-form"]["source"]["url"] == KNOWLEDGE_BASE.source("udi-sponsorship-form").url
    assert items["invitation-letter"]["source"]["url"] == (
        KNOWLEDGE_BASE.source("udi-invitation-for-visitor-visa").url
    )
    assert items["sponsorship-form"]["text"].strip() and items["invitation-letter"]["text"].strip()


@pytest.mark.parametrize(
    "path",
    [
        "/api/checklists/business",
        "/api/checklists/Family",
        "/api/checklists/tourism%20",
        "/api/checklists/" + "x" * 300,
        "/api/checklists/<script>",
        # Not left to the static files: the same envelope, not `{"detail": "Not Found"}`.
        "/api/checklists/",
        "/api/checklists/tourism/",
        "/api/checklists/family/x",
    ],
)
def test_unknown_purpose_is_a_404_envelope_without_echo(client: TestClient, path: str) -> None:
    response = client.get(path, follow_redirects=False)

    assert response.status_code == 404
    # One fixed envelope whatever was asked for, so the requested value is never echoed.
    assert response.json() == UNKNOWN_PURPOSE_ERROR
    assert UNKNOWN_PURPOSE_ERROR["error"]["code"] == "unknown_purpose"


def test_demo_mode_serves_the_same_checklists(settings: Settings) -> None:
    real = TestClient(create_app(settings, llm=ExplodingLLM()))
    demo = TestClient(create_app(settings.model_copy(update={"mock_llm": True})))

    for purpose in VISIT_PURPOSES:
        response = demo.get(f"/api/checklists/{purpose}")
        assert response.status_code == 200
        assert response.json() == real.get(f"/api/checklists/{purpose}").json()
    assert demo.get("/api/checklists/business").status_code == 404


def test_demo_mode_with_exploding_llm_still_serves(settings: Settings) -> None:
    demo = TestClient(create_app(settings.model_copy(update={"mock_llm": True}), llm=ExplodingLLM()))

    assert demo.get("/api/checklists/family").status_code == 200
