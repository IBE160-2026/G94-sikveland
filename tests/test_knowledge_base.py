import ast
from datetime import date
from pathlib import Path

import pytest
import yaml

from app.adapters.file_knowledge_base import (
    PUBLISHER_DOMAINS,
    KnowledgeBaseError,
    load_knowledge_base,
    load_sources,
)

ROOT = Path(__file__).resolve().parent.parent
# Not imported from `app.main`: importing it builds the app, so one bad committed
# snapshot would stop the loader tests below from even being collected.
KNOWLEDGE_BASE_DIR = ROOT / "knowledge-base"


def _entry(sid: str, publisher: str = "UDI", url: str | None = None) -> dict:
    return {
        "id": sid,
        "title": f"Title of {sid}",
        "url": url or f"https://www.udi.no/en/{sid}/",
        "publisher": publisher,
        "retrieved": date(2026, 11, 13),
        "file": f"{sid}.md",
    }


def _valid() -> list[dict]:
    # Deliberately not in id order: documents() must sort them.
    return [
        _entry("udi-sponsor"),
        _entry("embassy-checklist", "Royal Norwegian Embassy in Bangkok", "https://www.norway.no/en/thailand/x"),
        _entry("vfs-info", "VFS Global", "https://visa.vfsglobal.com/info.pdf"),
        _entry("eu-schengen", "European Commission", "https://home-affairs.ec.europa.eu/visa_en"),
    ]


def _write(tmp_path: Path, entries: object, snapshots: bool = True) -> Path:
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump(entries, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    if snapshots and isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                (tmp_path / f"{entry['id']}.md").write_text(
                    f"# {entry['id']}\n\nText of {entry['id']} ไทย\n", encoding="utf-8"
                )
    return tmp_path


def test_valid_knowledge_base_loads_sorted_by_id(tmp_path: Path) -> None:
    kb = load_knowledge_base(_write(tmp_path, _valid()))

    ids = [s.id for s in kb.documents()]
    assert ids == ["embassy-checklist", "eu-schengen", "udi-sponsor", "vfs-info"]
    assert isinstance(kb.documents(), tuple)
    source = kb.source("udi-sponsor")
    assert source.title == "Title of udi-sponsor"
    assert source.url == "https://www.udi.no/en/udi-sponsor/"
    assert source.publisher == "UDI"
    assert source.retrieved == date(2026, 11, 13)
    assert source.text == "# udi-sponsor\n\nText of udi-sponsor ไทย"


def test_unknown_source_id_is_a_key_error(tmp_path: Path) -> None:
    kb = load_knowledge_base(_write(tmp_path, _valid()))

    with pytest.raises(KeyError):
        kb.source("no-such-source")


def test_missing_snapshot_names_the_id(tmp_path: Path) -> None:
    _write(tmp_path, _valid())
    (tmp_path / "vfs-info.md").unlink()

    with pytest.raises(KnowledgeBaseError, match="'vfs-info'.*cannot read snapshot"):
        load_knowledge_base(tmp_path)


@pytest.mark.parametrize("content", ["", "  \n\n\t\n"])
def test_empty_snapshot_names_the_id(tmp_path: Path, content: str) -> None:
    _write(tmp_path, _valid())
    (tmp_path / "eu-schengen.md").write_text(content, encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="'eu-schengen'.*empty"):
        load_knowledge_base(tmp_path)


def test_non_utf8_snapshot_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, _valid())
    (tmp_path / "udi-sponsor.md").write_text("ไทย", encoding="utf-16")

    with pytest.raises(KnowledgeBaseError, match="'udi-sponsor'.*cannot read"):
        load_knowledge_base(tmp_path)


def _change(field: str, value: object):
    def apply(entry: dict) -> None:
        entry[field] = value

    return apply


def _drop(field: str):
    def apply(entry: dict) -> None:
        del entry[field]

    return apply


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (_drop("title"), r"'udi-sponsor' is missing field\(s\): title"),
        (_drop("retrieved"), r"'udi-sponsor' is missing field\(s\): retrieved"),
        (_change("version", 2), r"'udi-sponsor' has unknown field\(s\): version"),
        (_change("title", "  "), r"'udi-sponsor' needs a non-empty 'title'"),
        (_change("url", "http://www.udi.no/en/x/"), r"'udi-sponsor' url must be an https URL"),
        (_change("url", "https:///no-host"), r"'udi-sponsor' url must be an https URL"),
        (_change("url", "www.udi.no/en/x/"), r"'udi-sponsor' url must be an https URL"),
        (_change("url", "https://www.norway.no/en/x"), r"'udi-sponsor' url host 'www.norway.no'"),
        (_change("url", "https://udi.no.example.com/x"), r"'udi-sponsor' url host"),
        (_change("url", "https://fakeudi.no/x"), r"'udi-sponsor' url host 'fakeudi.no'"),
        (_change("publisher", "Wikipedia"), r"'udi-sponsor' has unknown publisher 'Wikipedia'"),
        (_change("publisher", "udi"), r"'udi-sponsor' has unknown publisher 'udi'"),
        (_change("file", "other.md"), r"'udi-sponsor' 'file' must be 'udi-sponsor.md'"),
        (_change("file", "udi-sponsor.txt"), r"'udi-sponsor' 'file' must be"),
        (_change("retrieved", "13.11.2026"), r"'udi-sponsor' 'retrieved' must be a date"),
        (_change("retrieved", 20261113), r"'udi-sponsor' 'retrieved' must be a date"),
    ],
)
def test_bad_entry_names_it(tmp_path: Path, mutate, message: str) -> None:
    entries = _valid()
    mutate(entries[0])

    with pytest.raises(KnowledgeBaseError, match=message):
        load_knowledge_base(_write(tmp_path, entries))


def test_impossible_date_is_a_knowledge_base_error(tmp_path: Path) -> None:
    _write(tmp_path, _valid())
    body = (tmp_path / "sources.yaml").read_text(encoding="utf-8")
    body = body.replace("retrieved: 2026-11-13", "retrieved: 2026-02-30", 1)
    (tmp_path / "sources.yaml").write_text(body, encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="invalid YAML"):
        load_knowledge_base(tmp_path)


def test_datetime_is_not_a_date(tmp_path: Path) -> None:
    body = yaml.safe_dump(_valid(), sort_keys=False).replace(
        "retrieved: 2026-11-13", "retrieved: 2026-11-13 10:00:00", 1
    )
    _write(tmp_path, _valid())
    (tmp_path / "sources.yaml").write_text(body, encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="'udi-sponsor' 'retrieved' must be a date"):
        load_knowledge_base(tmp_path)


@pytest.mark.parametrize("bad_id", ["Udi-Sponsor", "udi_sponsor", "udi--sponsor", "", None, 7])
def test_id_must_be_kebab_case(tmp_path: Path, bad_id: object) -> None:
    entries = _valid()
    entries[1]["id"] = bad_id

    with pytest.raises(KnowledgeBaseError, match="source #2 needs a kebab-case 'id'"):
        load_knowledge_base(_write(tmp_path, entries))


def test_duplicate_id_names_it(tmp_path: Path) -> None:
    entries = [*_valid(), _entry("udi-sponsor")]

    with pytest.raises(KnowledgeBaseError, match="duplicate source id 'udi-sponsor'"):
        load_knowledge_base(_write(tmp_path, entries))


def test_duplicate_yaml_key_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, _valid())
    body = (tmp_path / "sources.yaml").read_text(encoding="utf-8")
    # A second `title:` in the first entry - plain YAML would keep the last one.
    body = body.replace("  title: Title of udi-sponsor\n", "  title: A\n  title: B\n", 1)
    (tmp_path / "sources.yaml").write_text(body, encoding="utf-8")

    with pytest.raises(KnowledgeBaseError, match="duplicate key 'title' at line 3"):
        load_knowledge_base(tmp_path)


@pytest.mark.parametrize("data", [None, [], {"sources": []}, "text", ["not-a-mapping"]])
def test_malformed_structure_is_rejected(tmp_path: Path, data: object) -> None:
    with pytest.raises(KnowledgeBaseError):
        load_knowledge_base(_write(tmp_path, data))


def test_missing_source_list_and_bad_yaml(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeBaseError, match="cannot read source list"):
        load_knowledge_base(tmp_path)

    (tmp_path / "sources.yaml").write_text("- id: [unclosed", encoding="utf-8")
    with pytest.raises(KnowledgeBaseError, match="invalid YAML"):
        load_knowledge_base(tmp_path)


def test_load_sources_checks_yaml_only(tmp_path: Path) -> None:
    entries = load_sources(_write(tmp_path, _valid(), snapshots=False) / "sources.yaml")

    assert [e.id for e in entries] == ["udi-sponsor", "embassy-checklist", "vfs-info", "eu-schengen"]
    assert entries[0].as_dict() == _valid()[0]


def test_app_refuses_to_start_with_missing_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings
) -> None:
    import app.main

    _write(tmp_path, _valid())
    (tmp_path / "udi-sponsor.md").unlink()
    monkeypatch.setattr(app.main, "KNOWLEDGE_BASE_DIR", tmp_path)

    with pytest.raises(KnowledgeBaseError, match="udi-sponsor"):
        app.main.create_app(settings)


def test_app_loads_the_knowledge_base(settings) -> None:
    import app.main

    kb = app.main.create_app(settings).state.knowledge_base

    assert len(kb.documents()) == len(load_sources(KNOWLEDGE_BASE_DIR / "sources.yaml"))


def test_committed_knowledge_base_loads() -> None:
    kb = load_knowledge_base(KNOWLEDGE_BASE_DIR)
    documents = kb.documents()

    assert 10 <= len(documents) <= 20
    assert [s.id for s in documents] == sorted(s.id for s in documents)
    # No VFS Global source for now: VFS blocks the ingest client and its PDF had an
    # outdated fee (user decision 2026-11-13). The publisher stays allowed for later.
    assert {s.publisher for s in documents} == set(PUBLISHER_DOMAINS) - {"VFS Global"}
    for source in documents:
        assert source.title != "TBD", source.id
        assert source.retrieved <= date.today(), source.id


@pytest.mark.parametrize(
    ("topic", "keywords"),
    [
        ("sponsorship form", ["sponsorship form"]),
        ("invitation letter", ["invitation letter"]),
        ("proof of relationship", ["proof of relationship"]),
        ("visa fee", ["visa fee"]),
        ("VFS", ["vfs"]),
    ],
)
def test_committed_knowledge_base_covers_required_topics(topic: str, keywords: list[str]) -> None:
    text = "\n".join(s.text for s in load_knowledge_base(KNOWLEDGE_BASE_DIR).documents()).lower()

    for keyword in keywords:
        assert keyword in text, f"no source mentions {topic!r} ({keyword!r})"


def test_committed_folder_has_no_stray_snapshots() -> None:
    listed = {e.file for e in load_sources(KNOWLEDGE_BASE_DIR / "sources.yaml")}
    on_disk = {p.name for p in KNOWLEDGE_BASE_DIR.glob("*.md")}

    assert on_disk == listed


FORBIDDEN_MODULES = ("httpx", "requests", "urllib.request")


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


@pytest.mark.parametrize(
    "path", sorted((ROOT / "app").rglob("*.py")), ids=lambda p: p.relative_to(ROOT).as_posix()
)
def test_app_never_fetches_over_the_network(path: Path) -> None:
    for name in _imports(path):
        for module in FORBIDDEN_MODULES:
            assert name != module and not name.startswith(module + "."), f"{path} imports {name}"
