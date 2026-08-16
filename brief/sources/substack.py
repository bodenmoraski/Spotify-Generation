"""Substack (and similar newsletter) RSS. full_text feeds keep the body as-is."""

from __future__ import annotations

import re
from typing import Any

from brief.models import Item
from brief.sources import parse_rss, strip_html


def parse(body: str | bytes, feed: dict[str, Any]) -> list[Item]:
    items = parse_rss(body, feed)
    source = feed.get("source") or ""
    suffix = f" - {source}" if source else ""
    cleaned: list[Item] = []
    for item in items:
        title = item.title
        if suffix and title.endswith(suffix):
            title = title[: -len(suffix)].strip()
        title = re.sub(r"\s+\u2014\s+.*$", "", title).strip() or title
        excerpt = item.excerpt
        if not feed.get("full_text"):
            excerpt = strip_html(excerpt)[:1500]
        else:
            excerpt = strip_html(excerpt)[:8000]
        excerpt = re.sub(r"^\s*Subscribe now\s*", "", excerpt, flags=re.I)
        excerpt = re.sub(r"\s*Share this post\s*", " ", excerpt, flags=re.I)
        cleaned.append(item.model_copy(update={"title": title, "excerpt": excerpt}))
    return cleaned
