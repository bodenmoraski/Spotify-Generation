"""SRS queue: days 1, 3, 7, 16, 35; cap; retire after last."""

from __future__ import annotations

from datetime import date, timedelta

from brief.models import Item, item_id_from_url
from brief.srs import (
    Queue,
    QueueItem,
    compute_review_dates,
    due_today,
    ingest_item,
    mark_emitted,
    merge_new,
)

D0 = date(2026, 6, 13)
INTERVALS = [1, 3, 7, 16, 35]
EXPECTED = ["2026-06-14", "2026-06-16", "2026-06-20", "2026-06-29", "2026-07-18"]


def _paper() -> Item:
    url = "https://arxiv.org/abs/2606.01234"
    return Item(
        id=item_id_from_url(url),
        title="Interpretability Hits a Wall",
        url=url,
        one_line_reason="SAEs plateau on frontier models.",
        excerpt="Sparse autoencoders plateau.",
    )


def test_review_dates_match_spec_example() -> None:
    assert compute_review_dates(D0, INTERVALS) == EXPECTED
    q = ingest_item(_paper(), D0, INTERVALS)
    assert q.ingested_date == "2026-06-13"
    assert q.review_dates == EXPECTED
    assert q.reviews_done == 0
    assert q.retired is False


def test_due_exactly_on_interval_days() -> None:
    queue = Queue(items=[ingest_item(_paper(), D0, INTERVALS)])
    due_days = []
    for offset in range(0, 40):
        day = D0 + timedelta(days=offset)
        if due_today(queue, day, cap=4):
            due_days.append(day.isoformat())
    assert due_days == EXPECTED


def test_reviews_per_day_cap_oldest_first() -> None:
    items = []
    for i in range(6):
        items.append(
            QueueItem(
                id=f"id-{i}",
                title=f"Item {i}",
                one_line="fact",
                ingested_date=(D0 - timedelta(days=6 - i)).isoformat(),
                review_dates=[D0.isoformat()],
            )
        )
    queue = Queue(items=items)
    due = due_today(queue, D0, cap=4)
    assert len(due) == 4
    assert [d.id for d in due] == ["id-0", "id-1", "id-2", "id-3"]


def test_due_today_skips_architecture_filler() -> None:
    keep = QueueItem(
        id="keep",
        title="Civilisational handoff",
        one_line="fact",
        ingested_date=D0.isoformat(),
        review_dates=[D0.isoformat()],
        source="LessWrong",
    )
    skip = QueueItem(
        id="skip",
        title="Pavillon Monk / L. McComber",
        one_line="a pavilion",
        ingested_date=D0.isoformat(),
        review_dates=[D0.isoformat()],
        source="ArchDaily",
    )
    due = due_today(Queue(items=[skip, keep]), D0, cap=4)
    assert [d.id for d in due] == ["keep"]


def test_retire_after_last_interval() -> None:
    item = ingest_item(_paper(), D0, INTERVALS)
    queue = Queue(items=[item])
    last = date.fromisoformat(EXPECTED[-1])
    emitted = due_today(queue, last, cap=4)
    assert len(emitted) == 1
    updated = mark_emitted(queue, emitted, last)
    assert updated.items[0].retired is True
    assert updated.items[0].reviews_done == 1
    assert due_today(updated, last, cap=4) == []


def test_merge_does_not_duplicate() -> None:
    q = ingest_item(_paper(), D0, INTERVALS)
    queue = merge_new(Queue(), [q])
    queue = merge_new(queue, [q])
    assert len(queue.items) == 1
