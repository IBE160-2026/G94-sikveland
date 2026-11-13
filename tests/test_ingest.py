import io
import zipfile
from datetime import date
from pathlib import Path

import httpx
import pytest
import yaml

import scripts.ingest as ingest

OLD = date(2026, 1, 2)
TODAY = date(2026, 11, 13)

HTML_PAGE = """<!DOCTYPE html>
<html><head><title>Page</title><script>var tracking = 1;</script></head>
<body>
  <header><nav><a href="/menu">Menu item</a></nav></header>
  <div class="cookie">Outside main</div>
  <main>
    <h1>Visitor visa</h1>
    <p>Read the <a href="checklist.docx">checklist</a> and the
       <a href="/en/fees/#fee">fee page</a> or <a href="https://example.org/x">this</a>.</p>
    <h2></h2>
    <button class="to-top">To top</button>
    <button class="accordion-title" aria-controls="faq-1">Who can apply?</button>
    <div id="faq-1" aria-hidden="true"><p>Anyone with a passport.</p></div>
    <form><input name="q"><p>Search the site</p></form>
    <style>.x { color: red }</style>
    <noscript>Enable JavaScript</noscript>
    <svg><text>icon</text></svg>
    <span class="material-symbols-outlined">info</span>
    <footer>Main footer</footer>
  </main>
  <footer>Page footer</footer>
</body></html>
"""

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _docx(paragraphs: list[str]) -> bytes:
    """A minimal .docx. A paragraph starting with `<w:r>` is used as raw run XML."""
    body = "".join(
        f"<w:p>{text}</w:p>"
        if text.startswith("<w:r>")
        else f"<w:p><w:r><w:t xml:space=\"preserve\">{text}</w:t></w:r></w:p>"
        if text
        else "<w:p/>"
        for text in paragraphs
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{_W}"><w:body>{body}</w:body></w:document>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def _client(routes: dict[str, httpx.Response | BaseException]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        result = routes.get(str(request.url))
        if result is None:
            return httpx.Response(404)
        if isinstance(result, BaseException):
            raise result
        return result

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


def _html(text: str = HTML_PAGE) -> httpx.Response:
    return httpx.Response(200, text=text, headers={"content-type": "text/html; charset=utf-8"})


def test_html_keeps_main_content_with_absolute_links() -> None:
    url = "https://www.udi.no/en/visit/"
    text = ingest.fetch_text(_client({url: _html()}), url)

    assert text.startswith("# Visitor visa\n")
    assert "[checklist](https://www.udi.no/en/visit/checklist.docx)" in text
    assert "[fee page](https://www.udi.no/en/fees/#fee)" in text
    assert "[this](https://example.org/x)" in text
    assert "Who can apply?" in text
    assert "Anyone with a passport." in text
    for noise in [
        "Menu item", "Outside main", "tracking", "To top", "Search the site", "color: red",
        "Enable JavaScript", "icon", "info", "Main footer", "Page footer", "##\n",
    ]:
        assert noise not in text, noise
    assert "\n\n\n" not in text
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_html_without_main_uses_body() -> None:
    url = "https://www.udi.no/en/plain/"
    page = "<html><body><nav>Menu</nav><h2>Fee</h2><p>EUR 90</p><footer>Foot</footer></body></html>"
    text = ingest.fetch_text(_client({url: _html(page)}), url)

    assert text == "## Fee\n\nEUR 90\n"


def test_html_links_follow_redirect_target() -> None:
    url = "https://www.udi.no/old"
    routes = {
        url: httpx.Response(301, headers={"location": "https://www.udi.no/new/page/"}),
        "https://www.udi.no/new/page/": _html("<main><a href='doc.pdf'>Doc</a></main>"),
    }
    text = ingest.fetch_text(_client(routes), url)

    assert text == "[Doc](https://www.udi.no/new/page/doc.pdf)\n"


def test_docx_paragraphs_without_checkbox_only_lines() -> None:
    url = "https://www.norway.no/checklist.docx"
    content = _docx(["CHECKLIST", "", "", "", "☐", " ☐ ", "Passport valid for three months", "□", "Two photos"])
    docx_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    response = httpx.Response(200, content=content, headers={"content-type": docx_type})
    text = ingest.fetch_text(_client({url: response}), url)

    assert text == "CHECKLIST\n\nPassport valid for three months\n\nTwo photos\n"


def test_docx_tabs_and_line_breaks_keep_words_apart() -> None:
    url = "https://www.norway.no/form.docx"
    content = _docx(
        [
            "<w:r><w:t>Name</w:t><w:tab/><w:t>Date</w:t></w:r>",
            "<w:r><w:t>Line one</w:t><w:br/><w:t>Line two</w:t></w:r>",
        ]
    )
    docx_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    response = httpx.Response(200, content=content, headers={"content-type": docx_type})

    assert ingest.fetch_text(_client({url: response}), url) == "Name\tDate\n\nLine one\nLine two\n"


def test_html_base_href_and_images_are_made_absolute() -> None:
    url = "https://www.udi.no/en/page/"
    page = (
        "<html><head><base href='https://www.udi.no/assets/'></head><body><main>"
        "<p><a href='doc.pdf'>Doc</a> <img src='logo.png' alt='Logo'></p></main></body></html>"
    )
    text = ingest.fetch_text(_client({url: _html(page)}), url)

    assert text == "[Doc](https://www.udi.no/assets/doc.pdf) ![Logo](https://www.udi.no/assets/logo.png)\n"


def test_redirect_off_the_publisher_domain_fails(tmp_path: Path) -> None:
    kb = _kb(tmp_path, ["moved"], {"moved": "Old text\n"})
    routes = {
        "https://www.udi.no/moved/": httpx.Response(302, headers={"location": "https://evil.example.com/x"}),
        "https://evil.example.com/x": _page("<p>Not official</p>"),
    }
    out = io.StringIO()

    assert ingest.run(kb, _client(routes), TODAY, out) == 1
    assert out.getvalue().splitlines()[0] == (
        "moved: FAILED redirected off 'udi.no' to 'evil.example.com' (9 chars kept)"
    )
    assert (kb / "moved.md").read_text(encoding="utf-8") == "Old text\n"
    assert _dates(kb) == {"moved": OLD}


def test_type_falls_back_to_url_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingest, "pdf_to_text", lambda content: f"pdf of {content.decode()}")
    url = "https://www.udi.no/form.PDF"
    response = httpx.Response(200, content=b"bytes", headers={"content-type": "application/octet-stream"})

    assert ingest.fetch_text(_client({url: response}), url) == "pdf of bytes\n"


def test_pdf_dispatch_by_content_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingest, "pdf_to_text", lambda content: "Page 1\n\n\n\n\nPage 2   ")
    url = "https://www.udi.no/form"
    response = httpx.Response(200, content=b"%PDF", headers={"content-type": "application/pdf"})

    assert ingest.fetch_text(_client({url: response}), url) == "Page 1\n\nPage 2\n"


def _pdf(objects: list[bytes]) -> bytes:
    """A PDF from numbered object bodies, with a correct xref table."""
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return out


def _text_stream(text: bytes) -> bytes:
    content = b"BT /F1 12 Tf 20 100 Td (" + text + b") Tj ET"
    return b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"


def test_pdf_to_text_reads_every_page_with_text() -> None:
    page = b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 7 0 R >> >> /Contents %d 0 R >>"
    content = _pdf(
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
            page % 4,
            _text_stream(b"Sponsorship form page one"),
            page % 6,
            _text_stream(b"Page two text"),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
    )

    assert ingest.pdf_to_text(content) == "Sponsorship form page one\n\nPage two text"


def test_pdf_to_text_reads_pages() -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    assert ingest.pdf_to_text(buffer.getvalue()) == ""


# --- run(): statuses, dates and exit code ---------------------------------


def _entry(sid: str) -> dict:
    return {
        "id": sid,
        "title": f"Title {sid}",
        "url": f"https://www.udi.no/{sid}/",
        "publisher": "UDI",
        "retrieved": OLD,
        "file": f"{sid}.md",
    }


def _kb(tmp_path: Path, ids: list[str], snapshots: dict[str, str]) -> Path:
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump([_entry(i) for i in ids], sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    for sid, text in snapshots.items():
        (tmp_path / f"{sid}.md").write_text(text, encoding="utf-8")
    return tmp_path


def _page(body: str) -> httpx.Response:
    return _html(f"<main>{body}</main>")


def _dates(kb: Path) -> dict[str, date]:
    return {e["id"]: e["retrieved"] for e in yaml.safe_load((kb / "sources.yaml").read_text("utf-8"))}


def test_run_reports_each_status_and_updates_only_changed_dates(tmp_path: Path) -> None:
    ids = ["changed", "new", "same", "http-error", "timeout", "unsupported", "empty"]
    kb = _kb(
        tmp_path,
        ids,
        {"changed": "Old text\n", "same": "Same text\n", "http-error": "Kept text\n"},
    )
    routes: dict[str, httpx.Response | Exception] = {
        "https://www.udi.no/changed/": _page("<p>New text ไทย</p>"),
        "https://www.udi.no/new/": _page("<p>Brand new</p>"),
        "https://www.udi.no/same/": _page("<p>Same text</p>"),
        "https://www.udi.no/http-error/": httpx.Response(503),
        "https://www.udi.no/timeout/": httpx.ReadTimeout("too slow"),
        "https://www.udi.no/unsupported/": httpx.Response(
            200, content=b"{}", headers={"content-type": "application/json"}
        ),
        "https://www.udi.no/empty/": _page("<script>x()</script>"),
    }
    out = io.StringIO()

    code = ingest.run(kb, _client(routes), TODAY, out)

    lines = out.getvalue().splitlines()
    assert lines[:7] == [
        "changed: changed (13 chars)",
        "new: new (10 chars)",
        "same: unchanged (10 chars)",
        "http-error: FAILED HTTP 503 (10 chars kept)",
        "timeout: FAILED timeout (ReadTimeout) (no snapshot)",
        "unsupported: FAILED unsupported type 'application/json' (no snapshot)",
        "empty: FAILED empty text (no snapshot)",
    ]
    assert lines[7] == "total: 7 sources, 4 failed, 43 characters"
    assert code == 1

    assert (kb / "changed.md").read_text(encoding="utf-8") == "New text ไทย\n"
    assert (kb / "new.md").read_text(encoding="utf-8") == "Brand new\n"
    assert (kb / "same.md").read_text(encoding="utf-8") == "Same text\n"
    assert (kb / "http-error.md").read_text(encoding="utf-8") == "Kept text\n"
    assert not (kb / "timeout.md").exists()
    assert _dates(kb) == {
        "changed": TODAY, "new": TODAY, "same": OLD, "http-error": OLD,
        "timeout": OLD, "unsupported": OLD, "empty": OLD,
    }
    # Field order is kept when the file is rewritten.
    first = yaml.safe_load((kb / "sources.yaml").read_text(encoding="utf-8"))[0]
    assert list(first) == ["id", "title", "url", "publisher", "retrieved", "file"]


def test_run_unchanged_writes_nothing_and_exits_zero(tmp_path: Path) -> None:
    # A snapshot checked out with CRLF line endings still counts as unchanged.
    kb = _kb(tmp_path, ["same"], {})
    (kb / "same.md").write_bytes(b"## Fee\r\n\r\nEUR 90\r\n")
    sources_before = (kb / "sources.yaml").read_bytes()
    out = io.StringIO()

    code = ingest.run(kb, _client({"https://www.udi.no/same/": _page("<h2>Fee</h2><p>EUR 90</p>")}), TODAY, out)

    assert code == 0
    assert out.getvalue().splitlines() == [
        "same: unchanged (15 chars)",
        "total: 1 sources, 0 failed, 15 characters",
    ]
    assert (kb / "sources.yaml").read_bytes() == sources_before
    assert (kb / "same.md").read_bytes() == b"## Fee\r\n\r\nEUR 90\r\n"


def test_run_with_invalid_source_list_fails(tmp_path: Path) -> None:
    (tmp_path / "sources.yaml").write_text("- id: Bad_Id\n", encoding="utf-8")
    out = io.StringIO()

    assert ingest.run(tmp_path, _client({}), TODAY, out) == 1
    assert out.getvalue().startswith("FAILED source #1 needs a kebab-case 'id'")


def test_unreadable_snapshot_fails_that_source_and_run_continues(tmp_path: Path) -> None:
    kb = _kb(tmp_path, ["broken", "fine"], {})
    (kb / "broken.md").write_text("ไทย", encoding="utf-16")
    before = (kb / "broken.md").read_bytes()
    routes = {
        "https://www.udi.no/broken/": _page("<p>New</p>"),
        "https://www.udi.no/fine/": _page("<p>Fine</p>"),
    }
    out = io.StringIO()

    assert ingest.run(kb, _client(routes), TODAY, out) == 1
    lines = out.getvalue().splitlines()
    assert lines[0].startswith("broken: FAILED cannot read snapshot")
    assert lines[1] == "fine: new (5 chars)"
    assert (kb / "broken.md").read_bytes() == before
    assert _dates(kb) == {"broken": OLD, "fine": TODAY}


def test_aborted_run_still_dates_rewritten_snapshots(tmp_path: Path) -> None:
    kb = _kb(tmp_path, ["first", "second", "third"], {})
    routes: dict[str, httpx.Response | BaseException] = {
        "https://www.udi.no/first/": _page("<p>First</p>"),
        "https://www.udi.no/second/": KeyboardInterrupt(),
    }

    with pytest.raises(KeyboardInterrupt):
        ingest.run(kb, _client(routes), TODAY, io.StringIO())

    assert (kb / "first.md").read_text(encoding="utf-8") == "First\n"
    assert _dates(kb) == {"first": TODAY, "second": OLD, "third": OLD}


def test_rewritten_sources_yaml_still_loads(tmp_path: Path) -> None:
    from app.adapters.file_knowledge_base import load_knowledge_base

    kb = _kb(tmp_path, ["one"], {})
    ingest.run(kb, _client({"https://www.udi.no/one/": _page("<p>ไทย text</p>")}), TODAY, io.StringIO())

    (source,) = load_knowledge_base(kb).documents()
    assert source.retrieved == TODAY
    assert source.text == "ไทย text"
