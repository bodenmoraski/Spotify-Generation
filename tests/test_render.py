"""Markdown/RSS rendering is never empty and follows the schema headings."""

from __future__ import annotations

from datetime import date

from brief.models import Item, item_id_from_url
from brief.render import MARKDOWN_SCHEMA, STUB_BRIEF, render_markdown, render_rss
from brief.srs import QueueItem

DAY = date(2026, 6, 16)


def test_schema_contains_worked_example_headings() -> None:
    for heading in (
        "# Daily Brief — Tuesday, 16 June 2026",
        "## AI & AI Safety",
        "## Paper of the Day",
        "## One Stretch Pick",
        "## Quick Reviews",
        "## Read These Three Today",
        "_End of brief._",
    ):
        assert heading in MARKDOWN_SCHEMA


def test_template_render_never_empty() -> None:
    item = Item(
        id=item_id_from_url("https://arxiv.org/abs/1"),
        title="A new argument",
        url="https://arxiv.org/abs/1",
        category="ai",
        excerpt="It reframes the question.",
        one_line_reason="Reframes the safety case.",
        source="arXiv",
    )
    review = QueueItem(
        id="r1",
        title="Open weights",
        one_line="Release is irreversible.",
        ingested_date="2026-06-13",
        review_dates=["2026-06-16"],
    )
    md = render_markdown(
        day=DAY,
        new_items=[item],
        paper=item,
        serendipity=[item.model_copy(update={"title": "Cathedral geometry", "category": "serendipity"})],
        reviews=[review],
    )
    assert md.strip()
    assert md.startswith("# Daily Brief")
    assert "## AI & AI Safety" in md
    assert "## Paper of the Day" in md
    assert "## Quick Reviews" in md
    assert "## Read These Three Today" in md
    assert "_End of brief._" in md
    rss = render_rss(title="Daily Brief — 16 June 2026", markdown=md, day=DAY, page_url="https://example.com/b/x/brief-latest.md")
    assert "<rss" in rss
    assert "Daily Brief" in rss


def test_empty_inputs_still_produce_a_brief() -> None:
    md = render_markdown(day=DAY, new_items=[], paper=None, serendipity=[], reviews=[], note="Sources were thin today.")
    assert "Daily Brief" in md
    assert "Read These Three Today" in md
    assert STUB_BRIEF.strip().startswith("# Daily Brief")
