"""Fetch every source in `knowledge-base/sources.yaml` into its Markdown snapshot.

Run offline, by hand: `uv run python scripts/ingest.py`. Each source is reported as
`new`, `changed`, `unchanged` or `FAILED <reason>`. A changed snapshot is rewritten
and its `retrieved` date set to today; a failed one keeps its old snapshot and date.
Review the diff (with the adviser) before committing. Exit code 1 if any source failed.
"""

import io
import re
import sys
import zipfile
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import TextIO
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

import httpx
import yaml
from bs4 import BeautifulSoup, Tag
from markdownify import ATX, markdownify
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.file_knowledge_base import (  # noqa: E402
    PUBLISHER_DOMAINS,
    SOURCES_FILE,
    KnowledgeBaseError,
    load_sources,
    on_domain,
)

KNOWLEDGE_BASE_DIR = ROOT / "knowledge-base"
USER_AGENT = "Mozilla/5.0 (compatible; norway-visa-guide-ingest)"
TIMEOUT_SECONDS = 30.0

_DROPPED_HTML_TAGS = ["script", "style", "nav", "header", "footer", "form", "noscript", "svg"]
_CONTENT_TYPES = {
    "text/html": "html",
    "application/xhtml+xml": "html",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}
_SUFFIXES = {".html": "html", ".htm": "html", ".pdf": "pdf", ".docx": "docx"}
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_CHECKBOX_ONLY = re.compile(r"[\s☐☑☒□■▪▫]*")


class IngestError(Exception):
    """One source could not be turned into snapshot text."""


def html_to_markdown(html: str, base_url: str) -> str:
    """Main content of an HTML page as Markdown, with absolute links."""
    soup = BeautifulSoup(html, "html.parser")
    base = soup.find("base", href=True)
    if base is not None:
        base_url = urljoin(base_url, str(base["href"]))
    root = soup.find("main") or soup.body or soup
    for tag in root.find_all(_DROPPED_HTML_TAGS):
        tag.decompose()
    # Page furniture that is not content: icon-font ligatures ("info", "print"),
    # action buttons ("To top", "Print"), rules, and headings left empty.
    # Collapsed sections (accordions) are content and are kept.
    for tag in root.find_all(_is_furniture):
        tag.decompose()
    for tag in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if not tag.get_text(strip=True):
            tag.decompose()
    for tag in root.find_all("a", href=True):
        tag["href"] = urljoin(base_url, str(tag["href"]))
    for tag in root.find_all("img", src=True):
        tag["src"] = urljoin(base_url, str(tag["src"]))
    return markdownify(str(root), heading_style=ATX)


def _is_furniture(tag: Tag) -> bool:
    if tag.name == "hr":
        return True
    # An accordion title is a button that controls content; any other button is an action.
    if tag.name == "button" and not tag.has_attr("aria-controls"):
        return True
    classes = tag.get("class") or []
    return any(c.startswith(("material-symbols", "material-icons")) for c in classes)


def pdf_to_text(content: bytes) -> str:
    """The text of every page of a PDF, pages separated by a blank line."""
    reader = PdfReader(io.BytesIO(content))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)


def docx_to_text(content: bytes) -> str:
    """The paragraphs of a Word document, one per line, without checkbox-only paragraphs."""
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    lines: list[str] = []
    for paragraph in root.iter(f"{_W}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{_W}t":
                parts.append(node.text or "")
            elif node.tag == f"{_W}tab":
                parts.append("\t")
            elif node.tag in (f"{_W}br", f"{_W}cr"):
                parts.append("\n")
        text = "".join(parts)
        if text and _CHECKBOX_ONLY.fullmatch(text):
            continue
        lines.append(text.strip())
    return "\n\n".join(lines)


def tidy(text: str) -> str:
    """Normalise line endings, trim line ends, collapse runs of blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + "\n" if text else ""


def _kind(content_type: str, urls: list[str]) -> str:
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type in _CONTENT_TYPES:
        return _CONTENT_TYPES[media_type]
    for url in urls:
        suffix = Path(urlsplit(url).path).suffix.lower()
        if suffix in _SUFFIXES:
            return _SUFFIXES[suffix]
    raise IngestError(f"unsupported type {media_type or 'unknown'!r}")


_CONVERTERS: dict[str, Callable[[httpx.Response], str]] = {
    "html": lambda r: html_to_markdown(r.text, str(r.url)),
    "pdf": lambda r: pdf_to_text(r.content),
    "docx": lambda r: docx_to_text(r.content),
}


def fetch_text(client: httpx.Client, url: str, domain: str | None = None) -> str:
    """Fetch one source and return its snapshot text. Raises on any failure.

    With `domain`, a page that redirects off the publisher's domain is rejected.
    """
    response = client.get(url)
    response.raise_for_status()
    host = response.url.host
    if domain is not None and not on_domain(host, domain):
        raise IngestError(f"redirected off {domain!r} to {host!r}")
    kind = _kind(response.headers.get("content-type", ""), [str(response.url), url])
    try:
        text = tidy(_CONVERTERS[kind](response))
    except Exception as exc:  # any parser error: report it, keep the old snapshot
        raise IngestError(f"cannot read {kind}: {type(exc).__name__}: {exc}") from exc
    if not text:
        raise IngestError("empty text")
    return text


def _reason(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return f"timeout ({type(exc).__name__})"
    if isinstance(exc, IngestError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


def _read_snapshot(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def run(kb_dir: Path, client: httpx.Client, today: date, out: TextIO) -> int:
    """Ingest every source into `kb_dir`. Returns the exit code: 1 if any source failed."""
    sources_path = kb_dir / SOURCES_FILE
    try:
        entries = load_sources(sources_path)
    except KnowledgeBaseError as exc:
        print(f"FAILED {exc}", file=out)
        return 1

    dated: dict[str, date] = {}
    failed = 0
    total = 0
    try:
        for entry in entries:
            snapshot = kb_dir / entry.file
            try:
                old = _read_snapshot(snapshot)
            except (OSError, UnicodeDecodeError) as exc:
                failed += 1
                print(f"{entry.id}: FAILED cannot read snapshot: {exc} (kept)", file=out)
                continue
            try:
                text = fetch_text(client, entry.url, PUBLISHER_DOMAINS[entry.publisher])
            except Exception as exc:  # report and go on with the next source
                failed += 1
                size = f"{len(old)} chars kept" if old is not None else "no snapshot"
                print(f"{entry.id}: FAILED {_reason(exc)} ({size})", file=out)
                total += len(old or "")
                continue

            if old is not None and tidy(old) == text:
                status = "unchanged"
            else:
                status = "new" if old is None else "changed"
                snapshot.write_text(text, encoding="utf-8", newline="\n")
                dated[entry.id] = today
            print(f"{entry.id}: {status} ({len(text)} chars)", file=out)
            total += len(text)
    finally:
        # Also on an abort (error, Ctrl-C): every rewritten snapshot gets its new date.
        if dated:
            body = yaml.safe_dump(
                [
                    replace(e, retrieved=dated[e.id]).as_dict() if e.id in dated else e.as_dict()
                    for e in entries
                ],
                sort_keys=False,
                allow_unicode=True,
            )
            sources_path.write_text(body, encoding="utf-8", newline="\n")
    print(f"total: {len(entries)} sources, {failed} failed, {total} characters", file=out)
    return 1 if failed else 0


def main() -> int:
    # Windows consoles may not use UTF-8; never crash on a Thai or special character.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    with httpx.Client(
        follow_redirects=True,
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        return run(KNOWLEDGE_BASE_DIR, client, date.today(), sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
