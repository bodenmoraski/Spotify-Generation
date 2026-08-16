"""Shared schemas for pipeline items, feed health, and spend tracking."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import BaseModel, Field

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "s",
}


def canonical_url(url: str) -> str:
    """Normalize a URL for identity: host, path, no tracking params."""
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower() if parsed.scheme else "https"
    if scheme == "http":
        scheme = "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path or ""
    if "arxiv.org" in netloc:
        path = re.sub(r"/pdf/(\d+\.\d+)(?:v\d+)?(?:\.pdf)?", r"/abs/\1", path)
        path = re.sub(r"(/abs/\d+\.\d+)v\d+", r"\1", path)
        netloc = "arxiv.org"
    path = re.sub(r"/+", "/", path).rstrip("/")
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunparse((scheme, netloc, path, "", query, ""))


def item_id_from_url(url: str) -> str:
    canon = canonical_url(url) or url.strip()
    return hashlib.sha1(canon.encode("utf-8")).hexdigest()


def normalize_title(title: str) -> str:
    text = (title or "").lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


class Item(BaseModel):
    id: str
    title: str
    url: str
    source: str = ""
    feed_id: str = ""
    category: str = "ai"
    authors: list[str] = Field(default_factory=list)
    published: datetime | None = None
    excerpt: str = ""
    is_paper: bool = False
    is_serendipity: bool = False
    serendipity_domain: str = ""
    weight: float = 1.0
    score: float = 0.0
    one_line_reason: str = ""
    auto_shortlist: bool = False
    material_development: bool = False
    why_this_matters: str = ""
    summary: str = ""
    karma: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_parts(
        cls,
        *,
        title: str,
        url: str,
        feed: dict[str, Any],
        excerpt: str = "",
        authors: list[str] | None = None,
        published: datetime | None = None,
        **kwargs: Any,
    ) -> Item:
        category = feed.get("category") or "ai"
        return cls(
            id=item_id_from_url(url),
            title=(title or "").strip() or "(untitled)",
            url=url.strip(),
            source=feed.get("source") or feed.get("id") or "",
            feed_id=feed.get("id") or "",
            category=category,
            authors=authors or [],
            published=published,
            excerpt=(excerpt or "").strip(),
            is_paper=bool(feed.get("is_paper")),
            is_serendipity=category == "serendipity",
            serendipity_domain=feed.get("domain") or "",
            weight=float(feed.get("weight") or 1.0),
            **kwargs,
        )


class FeedHealth(BaseModel):
    feed_id: str
    ok: bool
    status: int | None = None
    n_items: int = 0
    error: str | None = None
    cached: bool = False
    url: str = ""


class Spend(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    calls: list[dict[str, Any]] = Field(default_factory=list)

    def add(self, model: str, input_tokens: int, output_tokens: int, prices: dict[str, Any]) -> float:
        info = prices.get(model) or {"input": 0.0, "output": 0.0}
        cost = (input_tokens / 1_000_000) * float(info.get("input") or 0) + (
            output_tokens / 1_000_000
        ) * float(info.get("output") or 0)
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost_usd += cost
        self.calls.append(
            {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
            }
        )
        return cost
