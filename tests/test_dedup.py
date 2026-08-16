"""Near-duplicate collapse and 14-day covered-store suppression."""

from __future__ import annotations

from datetime import date

from brief.dedup import collapse_near_duplicates, dedup, looks_like_development, suppress_covered
from brief.models import Item, canonical_url, item_id_from_url, normalize_title


def _item(title: str, url: str, **kwargs) -> Item:
    return Item(id=item_id_from_url(url), title=title, url=url, **kwargs)


def test_near_identical_titles_collapse() -> None:
    a = _item("Interpretability Hits a Wall", "https://arxiv.org/abs/2606.01234")
    b = _item("interpretability hits a wall!", "https://arxiv.org/pdf/2606.01234v1.pdf", excerpt="longer abstract that should win")
    kept = collapse_near_duplicates([a, b], threshold=88)
    assert len(kept) == 1
    assert kept[0].excerpt.startswith("longer")


def test_canonical_url_strips_tracking_and_arxiv_pdf() -> None:
    assert canonical_url("http://www.arxiv.org/pdf/2606.01234v1.pdf") == "https://arxiv.org/abs/2606.01234"
    a = canonical_url("https://thezvi.substack.com/p/x?utm_source=rss")
    b = canonical_url("https://thezvi.substack.com/p/x")
    assert a == b
    assert normalize_title("Hello, World!") == "hello world"


def test_covered_story_is_suppressed() -> None:
    today = date(2026, 6, 16)
    original = _item("Sahel security pact framed locally", "https://example.ng/sahel-pact")
    covered = [{"id": original.id, "title": original.title, "url": original.url, "covered_date": "2026-06-15"}]
    fresh, suppressed = suppress_covered(
        [original], covered, today=today, window_days=14, threshold=88
    )
    assert fresh == []
    assert len(suppressed) == 1


def test_material_development_escapes_suppression() -> None:
    today = date(2026, 6, 16)
    original = _item("Sahel security pact framed locally", "https://example.ng/sahel-pact")
    update = _item(
        "Sahel security pact framed locally (update: new evidence)",
        "https://example.ng/sahel-pact-followup",
        excerpt="Follow-up with new evidence from local desks.",
    )
    covered = [{"id": original.id, "title": original.title, "url": original.url, "covered_date": "2026-06-15"}]
    fresh, suppressed = suppress_covered([update], covered, today=today, window_days=14, threshold=88)
    assert looks_like_development(update)
    assert len(fresh) == 1
    assert suppressed == []
    assert fresh[0].material_development is True


def test_dedup_prunes_old_covered(settings: dict) -> None:
    today = date(2026, 6, 16)
    old = _item("Ancient story", "https://example.com/old")
    covered = [{"id": old.id, "title": old.title, "url": old.url, "covered_date": "2026-01-01"}]
    fresh, suppressed, live = dedup([old], covered, settings, today=today)
    assert suppressed == []
    assert len(fresh) == 1
    assert live == []
