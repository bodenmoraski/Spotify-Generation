"""Heuristic ranker + circuit breaker, no API keys."""

from __future__ import annotations

from datetime import date

from brief.config import load_allowlist
from brief.models import Item, Spend, item_id_from_url
from brief.rank import allowlist_match, editorial_pass, heuristic_triage, select_shortlist
from brief.render import MARKDOWN_SCHEMA


def _item(title: str, url: str, **kwargs) -> Item:
    return Item(id=item_id_from_url(url), title=title, url=url, **kwargs)


def test_allowlist_does_not_match_ssi_inside_possible() -> None:
    allow = load_allowlist()
    assert allowlist_match([], "this is possible in classification and confession", allow) is False
    assert allowlist_match([], "Researchers at Anthropic published an SAE paper", allow) is True
    assert allowlist_match(["Nelson Elhage"], "unrelated abstract", allow) is True


def test_heuristic_kills_funding_and_shortlists_allowlisted_author() -> None:
    allow = load_allowlist()
    junk = _item("Acme raises $40M Series B", "https://example.com/funding", excerpt="funding round and product launch")
    paper = _item(
        "Interpretability Hits a Wall",
        "https://arxiv.org/abs/2606.01234",
        authors=["Nelson Elhage"],
        excerpt="An argument that sparse autoencoders plateau.",
        is_paper=True,
        category="ai",
        weight=1.2,
    )
    scored = heuristic_triage([junk, paper], allow)
    by_title = {i.title: i for i in scored}
    assert by_title[junk.title].score < 0.2
    assert by_title[paper.title].auto_shortlist is True
    assert by_title[paper.title].score >= 0.35


def test_serendipity_force_included(settings: dict) -> None:
    items = [
        _item(f"AI paper {i}", f"https://arxiv.org/abs/{i}", category="ai", score=0.9, excerpt="argument " * 20)
        for i in range(12)
    ]
    stretch = _item(
        "Cathedral geometry",
        "https://aeon.co/cathedral",
        category="serendipity",
        is_serendipity=True,
        score=0.5,
        source="Aeon",
        excerpt="Tacit knowledge in stone.",
    )
    items.append(stretch)
    shortlist, paper, serendipity = select_shortlist(items, settings)
    assert stretch.id in {s.id for s in serendipity}
    assert len(shortlist) >= settings["new_items_min"]


def test_circuit_breaker_skips_editorial(settings: dict, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    spend = Spend(cost_usd=0.21)
    md = editorial_pass(
        [],
        None,
        [],
        [],
        settings,
        spend,
        date(2026, 6, 16),
        MARKDOWN_SCHEMA,
        "Tuesday",
    )
    assert md is None
