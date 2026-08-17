"""Markdown/RSS rendering is never empty and follows the schema headings."""

from __future__ import annotations

from datetime import date

from brief.models import Item, item_id_from_url
from brief.render import MARKDOWN_SCHEMA, STUB_BRIEF, extract_episode_title, render_markdown, render_rss
from brief.srs import QueueItem

DAY = date(2026, 6, 16)


def test_schema_contains_worked_example_headings() -> None:
    for heading in (
        "# Daily Brief — Tuesday, 16 June 2026",
        "## The World",
        "## Paper of the Day",
        "## One Idea",
        "## Quick Reviews",
        "_End of brief._",
    ):
        assert heading in MARKDOWN_SCHEMA
    assert "## AI & AI Safety" not in MARKDOWN_SCHEMA
    assert "## Odds & Ends" not in MARKDOWN_SCHEMA
    assert "## Read These Three Today" not in MARKDOWN_SCHEMA


def test_template_render_never_empty() -> None:
    item = Item(
        id=item_id_from_url("https://arxiv.org/abs/1"),
        title="A new argument",
        url="https://arxiv.org/abs/1",
        category="world",
        excerpt="It reframes the question.",
        one_line_reason="Reframes the safety case.",
        source="FT",
    )
    idea = item.model_copy(
        update={
            "id": item_id_from_url("https://aeon.co/cathedral"),
            "title": "Cathedral geometry",
            "url": "https://aeon.co/cathedral",
            "category": "serendipity",
            "source": "Aeon",
        }
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
        serendipity=[idea],
        reviews=[review],
    )
    assert md.strip()
    assert md.startswith("# Daily Brief")
    assert "## The World" in md
    assert "## Paper of the Day" in md
    assert "## One Idea" in md
    assert "## Quick Reviews" in md
    assert "**Assigned.**" in md
    assert "**Today.**" not in md
    assert "## Odds & Ends" not in md
    assert "## Read These Three Today" not in md
    assert "_End of brief._" in md
    rss = render_rss(title="Daily Brief — 16 June 2026", markdown=md, day=DAY, page_url="https://example.com/b/x/brief-latest.md")
    assert "<rss" in rss
    assert "Daily Brief" in rss


def test_extract_episode_title_prefers_comment_then_heading() -> None:
    dated = extract_episode_title("# Daily Brief — Sunday, 16 August 2026\n", DAY)
    assert dated.startswith("Daily Brief")
    cool = extract_episode_title(
        "# Daily Brief — Sunday, 16 August 2026\n\n<!-- episode_title: When the fare is too dangerous to speak -->\n",
        DAY,
    )
    assert cool == "When the fare is too dangerous to speak"
    from_heading = extract_episode_title(
        "# Daily Brief\n\n### 1. A former Iranian president publicly breaks with war logic\n",
        DAY,
    )
    assert from_heading.startswith("A former Iranian president")


def test_empty_inputs_still_produce_a_brief() -> None:
    md = render_markdown(day=DAY, new_items=[], paper=None, serendipity=[], reviews=[], note="Sources were thin today.")
    assert "Daily Brief" in md
    assert "## One Idea" in md
    assert "## Quick Reviews" in md
    assert "Read These Three Today" not in md
    assert STUB_BRIEF.strip().startswith("# Daily Brief")
    assert "Read These Three Today" not in STUB_BRIEF


def test_editorial_markdown_drops_read_later() -> None:
    sneaky = """# Daily Brief — Tuesday, 16 June 2026

## The World

### 1. A development

## Quick Reviews

No reviews due today.

## Read These Three Today
1. A thing to read later.

_End of brief._
"""
    md = render_markdown(
        day=DAY,
        new_items=[],
        paper=None,
        serendipity=[],
        reviews=[],
        editorial_markdown=sneaky,
    )
    assert "Read These Three Today" not in md
    assert "_End of brief._" in md
    assert "## The World" in md
