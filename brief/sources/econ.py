"""Economics sources: NBER RSS/RePEc, VoxEU, IMF, Fed, BIS."""

from __future__ import annotations

import re
from typing import Any

from brief.models import Item
from brief.sources import parse_rss

NBER_TITLE_RE = re.compile(r"^(?:NBER\s+Working\s+Paper\s+\d+\s*[:\-–]\s*)", re.I)


def parse(body: str | bytes, feed: dict[str, Any]) -> list[Item]:
    items = parse_rss(body, feed)
    out: list[Item] = []
    for item in items:
        title = NBER_TITLE_RE.sub("", item.title).strip() or item.title
        is_paper = bool(feed.get("is_paper")) or "nber" in (feed.get("id") or "")
        authors = list(item.authors)
        # NBER RSS sometimes puts authors in the title after an em-dash.
        if " — " in title and not authors:
            left, right = title.split(" — ", 1)
            if len(right) < 80:
                title, authors = left.strip(), [a.strip() for a in right.split(",") if a.strip()]
        out.append(item.model_copy(update={"title": title, "authors": authors, "is_paper": is_paper}))
    return out
