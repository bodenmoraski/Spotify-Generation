"""Feed parsers: fixtures only, no network."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from brief.fetch import fetch_one, parse_body, read_cache, write_cache, AsyncInterval
from brief.models import item_id_from_url
from brief.sources import arxiv as arxiv_src
from brief.sources import forums as forums_src
from brief.sources import news as news_src
from brief.sources import semantic_scholar as s2_src
from brief.sources import substack as substack_src

ARXIV_FEED = {
    "id": "arxiv_cs",
    "type": "arxiv",
    "category": "ai",
    "is_paper": True,
    "source": "arXiv",
    "weight": 1.15,
}
SUBSTACK_FEED = {
    "id": "zvi",
    "type": "rss",
    "category": "ai",
    "source": "Don't Worry About the Vase",
    "full_text": True,
    "url": "https://thezvi.substack.com/feed",
    "weight": 1.35,
}
GRAPHQL_FEED = {
    "id": "ea_forum",
    "type": "graphql",
    "category": "econ",
    "source": "EA Forum",
    "karma_threshold": 30,
    "url": "https://forum.effectivealtruism.org/graphql",
}


def test_arxiv_atom_fixture(fixtures_dir: Path) -> None:
    body = (fixtures_dir / "arxiv_atom.xml").read_text()
    items = arxiv_src.parse_atom(body, ARXIV_FEED)
    assert len(items) == 2
    first = items[0]
    assert first.title == "Interpretability Hits a Wall"
    assert "2606.01234" in first.url
    assert "Nelson Elhage" in first.authors
    assert "Sparse autoencoders" in first.excerpt
    assert first.is_paper
    assert first.published is not None
    via_fetch = parse_body(body, ARXIV_FEED)
    assert {i.id for i in via_fetch} == {i.id for i in items}


def test_substack_rss_fixture(fixtures_dir: Path) -> None:
    body = (fixtures_dir / "substack_rss.xml").read_text()
    items = substack_src.parse(body, SUBSTACK_FEED)
    assert len(items) == 2
    assert items[0].title == "The Comparative Advantage Debate, Sharpened"
    assert "technological unemployment" in items[0].excerpt
    assert items[0].source == "Don't Worry About the Vase"
    tracked = item_id_from_url("https://thezvi.substack.com/p/comparative-advantage?utm_source=rss")
    clean = item_id_from_url("https://thezvi.substack.com/p/comparative-advantage")
    assert tracked == clean
    assert items[0].id == clean


def test_graphql_json_fixture(fixtures_dir: Path) -> None:
    body = (fixtures_dir / "graphql.json").read_text()
    items = forums_src.parse_graphql(body, GRAPHQL_FEED)
    assert len(items) == 1
    assert items[0].title.startswith("Why open-weight")
    assert items[0].karma == 72
    assert items[0].authors == ["Ajeya Cotra"]
    low = forums_src.parse_graphql(json.loads(body), {**GRAPHQL_FEED, "karma_threshold": 0})
    assert len(low) == 2


def test_s2_and_gdelt_and_gnews(fixtures_dir: Path) -> None:
    s2 = s2_src.parse((fixtures_dir / "s2.json").read_text(), {"id": "s2", "type": "s2", "category": "ai", "is_paper": True, "source": "S2"})
    assert s2[0].authors == ["Dario Amodei"]
    gdelt = news_src.parse_gdelt((fixtures_dir / "gdelt.json").read_text(), {"id": "gdelt", "type": "gdelt", "category": "world", "source": "GDELT"})
    assert gdelt[0].extra["sourcecountry"] == "Nigeria"
    gnews = news_src.parse_google_news(
        (fixtures_dir / "google_news.xml").read_text(),
        {"id": "gnews", "type": "google_news", "category": "world", "source": "Google News"},
    )
    assert "Daily Trust" not in gnews[0].title
    assert "Sahel" in gnews[0].title


@pytest.mark.asyncio
async def test_fetch_one_uses_last_good_cache(tmp_path: Path, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    feed = dict(ARXIV_FEED)
    body = (fixtures_dir / "arxiv_atom.xml").read_text()
    write_cache(tmp_path, feed["id"], body, "application/atom+xml", "http://export.arxiv.org/api/query")
    assert read_cache(tmp_path, feed["id"])["body"].startswith("<?xml")

    async def boom(*_args, **_kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("brief.fetch.http_get", boom)
    limiter = AsyncInterval(0)
    client = httpx.AsyncClient()
    try:
        items, health = await fetch_one(client, feed, {"http_timeout_seconds": 1, "max_items_per_feed": 40}, limiter, tmp_path)
    finally:
        await client.aclose()
    assert health.cached is True
    assert health.ok is True
    assert len(items) == 2


def test_arxiv_query_url_contains_cats() -> None:
    url = arxiv_src.build_query_url({"cats": ["cs.AI", "cs.LG"], "max_results": 10})
    from urllib.parse import unquote

    decoded = unquote(url)
    assert "export.arxiv.org/api/query" in url
    assert "cat:cs.AI" in decoded
    assert "max_results=10" in decoded
