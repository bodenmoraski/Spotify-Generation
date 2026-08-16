"""World news: GDELT DOC 2.0 JSON + Google News RSS (non-US-centric ceid)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus, urlencode

from brief.models import Item
from brief.sources import parse_rss, strip_html

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
GNEWS_BASE = "https://news.google.com/rss/search"


def build_gdelt_url(feed: dict[str, Any]) -> str:
    query = feed.get("query") or "geopolitics"
    timespan = feed.get("timespan") or "24h"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "timespan": timespan,
        "maxrecords": str(int(feed.get("max_results") or 30)),
        "sort": "DateDesc",
    }
    return f"{GDELT_BASE}?{urlencode(params)}"


def build_google_news_url(feed: dict[str, Any]) -> str:
    query = feed.get("query") or "world news"
    hl = feed.get("hl") or "en"
    gl = feed.get("gl") or "US"
    ceid = feed.get("ceid") or "US:en"
    return f"{GNEWS_BASE}?q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={quote_plus(str(ceid))}"


def _parse_gdelt_seen(value: str | None) -> datetime | None:
    if not value:
        return None
    # 20260816T120000Z
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_gdelt(body: dict[str, Any] | str | bytes, feed: dict[str, Any]) -> list[Item]:
    if isinstance(body, (str, bytes)):
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
        text = text.strip()
        if not text:
            return []
        data = json.loads(text)
    else:
        data = body
    rows = data.get("articles") or data.get("articles") or []
    items: list[Item] = []
    for row in rows:
        title = strip_html(row.get("title") or "")
        url = (row.get("url") or "").strip()
        if not title or not url:
            continue
        country = row.get("sourcecountry") or ""
        lang = row.get("language") or ""
        domain = row.get("domain") or ""
        excerpt_bits = [b for b in (domain, country, lang, row.get("seendate")) if b]
        items.append(
            Item.from_parts(
                title=title,
                url=url,
                feed=feed,
                excerpt=" · ".join(str(b) for b in excerpt_bits),
                published=_parse_gdelt_seen(row.get("seendate")),
                extra={"sourcecountry": country, "domain": domain},
            )
        )
    return items


_SOURCE_SUFFIX = re.compile(r"\s+[-–—]\s+[^-–—]+$")


def parse_google_news(body: str | bytes, feed: dict[str, Any]) -> list[Item]:
    items = parse_rss(body, feed)
    out: list[Item] = []
    for item in items:
        title = _SOURCE_SUFFIX.sub("", item.title).strip() or item.title
        out.append(item.model_copy(update={"title": title}))
    return out


def parse(body: Any, feed: dict[str, Any]) -> list[Item]:
    if feed.get("type") == "gdelt" or isinstance(body, dict):
        return parse_gdelt(body, feed)
    return parse_google_news(body, feed)
