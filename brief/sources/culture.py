"""Culture / criticism RSS: LRB, n+1, Paris Review, Public Books, LitHub, Pitchfork, etc."""

from __future__ import annotations

from typing import Any

from brief.models import Item
from brief.sources import parse_rss, strip_html


def parse(body: str | bytes, feed: dict[str, Any]) -> list[Item]:
    items = parse_rss(body, feed)
    out: list[Item] = []
    for item in items:
        excerpt = strip_html(item.excerpt)[:2500]
        out.append(item.model_copy(update={"excerpt": excerpt, "is_serendipity": feed.get("category") == "serendipity"}))
    return out
