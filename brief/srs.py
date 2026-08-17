"""Spaced-repetition queue: expanding intervals, no user input required."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel, Field

from brief.models import Item

DEFAULT_INTERVALS = [1, 3, 7, 16, 35]


class QueueItem(BaseModel):
    id: str
    title: str
    one_line: str = ""
    ingested_date: str
    review_dates: list[str] = Field(default_factory=list)
    reviews_done: int = 0
    retired: bool = False
    missed: bool = False
    source: str = ""


class Queue(BaseModel):
    items: list[QueueItem] = Field(default_factory=list)


def compute_review_dates(ingested: date, intervals: list[int] | None = None) -> list[str]:
    intervals = intervals or DEFAULT_INTERVALS
    return [(ingested + timedelta(days=int(d))).isoformat() for d in intervals]


def load_queue(path: Path) -> Queue:
    if not path.exists():
        return Queue()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Queue()
    if isinstance(data, list):
        data = {"items": data}
    return Queue.model_validate(data)


def save_queue(path: Path, queue: Queue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(queue.model_dump_json(indent=2) + "\n", encoding="utf-8")


def ingest_item(
    item: Item,
    ingested: date,
    intervals: list[int] | None = None,
) -> QueueItem:
    one_line = (item.one_line_reason or item.why_this_matters or item.excerpt or item.title).strip()
    one_line = " ".join(one_line.split())[:240]
    return QueueItem(
        id=item.id,
        title=item.title,
        one_line=one_line,
        ingested_date=ingested.isoformat(),
        review_dates=compute_review_dates(ingested, intervals),
        reviews_done=0,
        retired=False,
        source=item.source or "",
    )


ARCHDAILY_TITLE_RE = re.compile(r" / [A-Z0-9]")


def is_filler_review(item: QueueItem) -> bool:
    """Architecture slideshows should not occupy the SRS slots."""
    if "archdaily" in (item.source or "").lower():
        return True
    return bool(ARCHDAILY_TITLE_RE.search(item.title or ""))


def due_today(
    queue: Queue,
    today: date,
    cap: int,
) -> list[QueueItem]:
    """Items whose calendar says today is a review day. Oldest-due first, capped."""
    today_s = today.isoformat()
    due: list[QueueItem] = []
    for item in queue.items:
        if item.retired or is_filler_review(item):
            continue
        if today_s in item.review_dates:
            due.append(item)
    due.sort(key=lambda i: (i.ingested_date, i.id))
    return due[: max(0, cap)]


def mark_emitted(queue: Queue, emitted: list[QueueItem], today: date) -> Queue:
    """Advance reviews_done after a day's reviews are written into the brief.

    Retire when the last scheduled date has been used, or when today is past
    the last interval (missed reviews still retire — scheduling is date-driven).
    """
    emitted_ids = {e.id for e in emitted}
    today_s = today.isoformat()
    updated: list[QueueItem] = []
    for item in queue.items:
        rec = item.model_copy()
        last = rec.review_dates[-1] if rec.review_dates else None
        if rec.id in emitted_ids and not rec.retired:
            rec.reviews_done = min(rec.reviews_done + 1, len(rec.review_dates) or rec.reviews_done + 1)
            if rec.reviews_done >= len(rec.review_dates) or (last and today_s >= last):
                rec.retired = True
        elif last and today_s > last:
            rec.retired = True
        updated.append(rec)
    return Queue(items=updated)


def merge_new(queue: Queue, new_items: list[QueueItem]) -> Queue:
    existing = {i.id for i in queue.items}
    merged = list(queue.items)
    for item in new_items:
        if item.id not in existing:
            merged.append(item)
            existing.add(item.id)
    return Queue(items=merged)


def apply_missed(queue: Queue, item_id: str, intervals: list[int] | None = None) -> Queue:
    """Optional upgrade: reinsert one interval back if the listener missed it."""
    intervals = intervals or DEFAULT_INTERVALS
    updated: list[QueueItem] = []
    for item in queue.items:
        if item.id != item_id or item.retired:
            updated.append(item)
            continue
        rec = item.model_copy()
        rec.missed = True
        rec.reviews_done = max(0, rec.reviews_done - 1)
        rec.retired = False
        ingested = date.fromisoformat(rec.ingested_date)
        rec.review_dates = compute_review_dates(ingested, intervals)
        updated.append(rec)
    return Queue(items=updated)


def today_in_tz(tz_name: str, now: datetime | None = None) -> date:
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    current = now or datetime.now(tz)
    if current.tzinfo is None:
        current = current.replace(tzinfo=tz)
    else:
        current = current.astimezone(tz)
    return current.date()
