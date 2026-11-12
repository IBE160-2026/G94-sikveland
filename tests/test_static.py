import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import STATIC_DIR, create_app

THAI = re.compile("[\u0e00-\u0e7f]")
# Text assets only: binary files (icons, fonts) cannot hold Thai text or links.
TEXT_SUFFIXES = {".html", ".css", ".js"}
STATIC_FILES = sorted(
    p for p in Path(STATIC_DIR).rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES
)
# An absolute or protocol-relative URL (`https://`, `//`) used as a resource:
# in an HTML attribute (double, single or no quotes), a CSS url(...) or @import,
# or a JS fetch(...).
EXTERNAL = re.compile(
    r"""(?:\b(?:src|href|action)\s*=\s*["']?"""
    r"""|\burl\(\s*["']?"""
    r"""|@import\s+(?:url\(\s*)?["']?"""
    r"""|\bfetch\(\s*["'`]?)"""
    r"""(?:[a-z][a-z0-9+.-]*:)?//""",
    re.IGNORECASE,
)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def test_root_serves_the_chat_page(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert '<html lang="th">' in html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert 'src="/app.js"' in html and 'href="/style.css"' in html
    # Retry button for when /api/texts cannot be loaded: a symbol, no words.
    assert 'id="retry"' in html


@pytest.mark.parametrize(("path", "kind"), [("/app.js", "javascript"), ("/style.css", "text/css")])
def test_assets_are_served(client: TestClient, path: str, kind: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert kind in response.headers["content-type"]


def test_api_routes_win_over_static_files(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/texts").status_code == 200


def test_static_folder_has_the_page_files() -> None:
    names = {p.name for p in STATIC_FILES}
    assert {"index.html", "style.css", "app.js"} <= names


@pytest.mark.parametrize("path", STATIC_FILES, ids=lambda p: p.name)
def test_no_thai_in_static_files(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    assert not THAI.search(text), f"Thai text in {path.name}; put it in content/texts.yaml"


@pytest.mark.parametrize("path", STATIC_FILES, ids=lambda p: p.name)
def test_page_uses_no_external_resources(path: Path) -> None:
    match = EXTERNAL.search(path.read_text(encoding="utf-8"))

    assert match is None, f"external resource in {path.name}: {match and match.group(0)}"


@pytest.mark.parametrize(
    "snippet",
    [
        '<script src="https://cdn.example.com/x.js">',
        "<link href='//cdn.example.com/x.css'>",
        "<img src=https://cdn.example.com/x.png>",
        "body { background: url(//cdn.example.com/x.png); }",
        "@font-face { src: url('https://cdn.example.com/f.woff2'); }",
        '@import "https://cdn.example.com/x.css";',
        "@import url(https://cdn.example.com/x.css);",
        'fetch("https://api.example.com/texts")',
        "fetch(`//api.example.com/texts`)",
    ],
)
def test_external_resource_pattern_catches(snippet: str) -> None:
    assert EXTERNAL.search(snippet)


@pytest.mark.parametrize(
    "snippet",
    ['<script src="/app.js">', "url(/img.png)", 'fetch("/api/texts")', "// a comment"],
)
def test_external_resource_pattern_allows_local(snippet: str) -> None:
    assert not EXTERNAL.search(snippet)
