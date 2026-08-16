"""Shared RSS/Atom helpers for source modules."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any

import feedparser

from brief.models import Item


class _Strip(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def strip_html(text: str) -> str:
    if not text:
        return ""
    parser = _Strip()
    try:
        parser.feed(text)
        parser.close()
        cleaned = unescape(" ".join(parser.parts))
    except Exception:
        cleaned = unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if getattr(value, "tm_year", None) is not None:
        try:
            return datetime(*value[:6], tzinfo=timezone.utc)  # type: ignore[index]
        except Exception:
            return None
    iso = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _struct_time_to_dt(st: Any) -> datetime | None:
    if st is None:
        return None
    try:
        return datetime(*st[:6], tzinfo=timezone.utc)
    except Exception:
        return None


def parse_rss(body: str | bytes, feed: dict[str, Any], *, limit: int = 40) -> list[Item]:
    parsed = feedparser.parse(body)
    items: list[Item] = []
    for entry in parsed.entries[:limit]:
        title = strip_html(getattr(entry, "title", "") or "")
        link = (getattr(entry, "link", None) or "").strip()
        if not link:
            links = getattr(entry, "links", None) or []
            for cand in links:
                href = cand.get("href") if isinstance(cand, dict) else getattr(cand, "href", "")
                if href:
                    link = href
                    break
        if not title and not link:
            continue
        summary = (
            getattr(entry, "summary", None)
            or getattr(entry, "description", None)
            or ""
        )
        content = getattr(entry, "content", None)
        if content:
            try:
                summary = content[0].get("value") or summary
            except Exception:
                pass
        authors: list[str] = []
        if getattr(entry, "author", None):
            authors.append(str(entry.author))
        for a in getattr(entry, "authors", None) or []:
            name = a.get("name") if isinstance(a, dict) else getattr(a, "name", None)
            if name and name not in authors:
                authors.append(str(name))
        published = _struct_time_to_dt(getattr(entry, "published_parsed", None)) or parse_datetime(
            getattr(entry, "published", None)
        )
        if published is None:
            published = _struct_time_to_dt(getattr(entry, "updated_parsed", None)) or parse_datetime(
                getattr(entry, "updated", None)
            )
        items.append(
            Item.from_parts(
                title=title or link,
                url=link or f"urn:feed:{feed.get('id')}:{title}",
                feed=feed,
                excerpt=strip_html(str(summary))[:4000],
                authors=authors,
                published=published,
            )
        )
    return items
