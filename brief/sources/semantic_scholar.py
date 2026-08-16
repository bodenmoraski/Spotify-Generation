"""Semantic Scholar Graph API v1. Optional S2_API_KEY (~1 req/s)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from brief.models import Item
from brief.sources import strip_html

API_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,authors,year,url,externalIds,publicationDate,venue"


def build_search_url(feed: dict[str, Any] | None = None) -> str:
    feed = feed or {}
    query = feed.get("query") or "artificial intelligence"
    params = {
        "query": query,
        "fields": FIELDS,
        "limit": str(int(feed.get("max_results") or 30)),
        "sort": "publicationDate:desc",
    }
    return f"{API_BASE}?{urlencode(params)}"


def parse(body: dict[str, Any] | str, feed: dict[str, Any] | None = None) -> list[Item]:
    """Parse a Graph API search JSON body (dict or JSON string)."""
    import json

    feed = feed or {
        "id": "s2",
        "category": "ai",
        "is_paper": True,
        "source": "Semantic Scholar",
    }
    if isinstance(body, (str, bytes)):
        data = json.loads(body)
    else:
        data = body
    rows = data.get("data") or data.get("papers") or []
    items: list[Item] = []
    for row in rows:
        title = strip_html(row.get("title") or "")
        abstract = strip_html(row.get("abstract") or "")
        url = (row.get("url") or "").strip()
        ext = row.get("externalIds") or {}
        if not url and ext.get("ArXiv"):
            url = f"https://arxiv.org/abs/{ext['ArXiv']}"
        if not url and row.get("paperId"):
            url = f"https://www.semanticscholar.org/paper/{row['paperId']}"
        if not title or not url:
            continue
        authors = []
        for a in row.get("authors") or []:
            name = a.get("name") if isinstance(a, dict) else str(a)
            if name:
                authors.append(name)
        published = None
        pub = row.get("publicationDate")
        if pub:
            try:
                published = datetime.fromisoformat(str(pub)).replace(tzinfo=timezone.utc)
            except ValueError:
                year = row.get("year")
                if year:
                    try:
                        published = datetime(int(year), 1, 1, tzinfo=timezone.utc)
                    except (TypeError, ValueError):
                        published = None
        elif row.get("year"):
            try:
                published = datetime(int(row["year"]), 1, 1, tzinfo=timezone.utc)
            except (TypeError, ValueError):
                published = None
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
