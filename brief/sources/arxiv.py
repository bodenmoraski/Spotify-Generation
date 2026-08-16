"""arXiv Atom API: export.arxiv.org, ≤1 request / 3 seconds, no auth."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from brief.models import Item
from brief.sources import strip_html

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
DEFAULT_CATS = ["cs.AI", "cs.LG", "cs.CY", "cs.CL"]
API_BASE = "http://export.arxiv.org/api/query"


def build_query_url(feed: dict[str, Any] | None = None) -> str:
    feed = feed or {}
    cats = feed.get("cats") or DEFAULT_CATS
    search = " OR ".join(f"cat:{c}" for c in cats)
    max_results = int(feed.get("max_results") or 100)
    params = {
        "search_query": search,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    return f"{API_BASE}?{urlencode(params)}"


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _parse_dt(text: str) -> datetime | None:
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse_atom(body: str | bytes, feed: dict[str, Any] | None = None) -> list[Item]:
    """Parse an arXiv Atom <feed> document into Items."""
    feed = feed or {"id": "arxiv_cs", "category": "ai", "is_paper": True, "source": "arXiv"}
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    root = ET.fromstring(body)
    items: list[Item] = []
    for entry in root.findall(f"{ATOM}entry"):
        title = strip_html(_text(entry.find(f"{ATOM}title")))
        abstract = strip_html(_text(entry.find(f"{ATOM}summary")))
        published = _parse_dt(_text(entry.find(f"{ATOM}published")))
        authors = [
            strip_html(_text(a.find(f"{ATOM}name")))
            for a in entry.findall(f"{ATOM}author")
        ]
        authors = [a for a in authors if a]
        url = ""
        arxiv_id = _text(entry.find(f"{ATOM}id"))
        for link in entry.findall(f"{ATOM}link"):
            rel = link.attrib.get("rel", "")
            href = link.attrib.get("href", "")
            if rel == "alternate" and href:
                url = href
                break
        if not url:
            url = arxiv_id
        if not title:
            continue
        items.append(
            Item.from_parts(
                title=title,
                url=url,
                feed=feed,
                excerpt=abstract,
                authors=authors,
                published=published,
            )
        )
    return items


# Alias used by fetch.py
parse = parse_atom
