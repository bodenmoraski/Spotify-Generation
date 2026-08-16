"""Near-duplicate detection and 14-day covered-item suppression."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from brief.models import Item, canonical_url, item_id_from_url, normalize_title

DEVELOPMENT_MARKERS = (
    "update:",
    "updated:",
    "follow-up",
    "follow up",
    "new evidence",
    "retraction",
    "retracted",
    "correction:",
    "material development",
)


def _parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def load_covered(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return list(data.get("items") or [])


def save_covered(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"items": items}, indent=2) + "\n", encoding="utf-8")


def prune_covered(records: list[dict[str, Any]], today: date, window_days: int) -> list[dict[str, Any]]:
    cutoff = today - timedelta(days=window_days)
    kept: list[dict[str, Any]] = []
    for rec in records:
        day = _parse_day(str(rec.get("covered_date") or rec.get("date") or ""))
        if day is None or day >= cutoff:
            kept.append(rec)
    return kept


def looks_like_development(item: Item) -> bool:
    if item.material_development:
        return True
    blob = f"{item.title} {item.excerpt}".lower()
    return any(marker in blob for marker in DEVELOPMENT_MARKERS)


def is_near_duplicate(a: Item, b: Item, threshold: int) -> bool:
    if a.id == b.id:
        return True
    if canonical_url(a.url) and canonical_url(a.url) == canonical_url(b.url):
        return True
    ta, tb = normalize_title(a.title), normalize_title(b.title)
    if not ta or not tb:
        return False
    return fuzz.token_set_ratio(ta, tb) >= threshold


def _prefer(a: Item, b: Item) -> Item:
    """Keep the richer / higher-weight copy of a near-duplicate pair."""
    if a.auto_shortlist and not b.auto_shortlist:
        return a
    if b.auto_shortlist and not a.auto_shortlist:
        return b
    if len(a.excerpt) != len(b.excerpt):
        return a if len(a.excerpt) > len(b.excerpt) else b
    return a if a.weight >= b.weight else b


def collapse_near_duplicates(items: list[Item], threshold: int) -> list[Item]:
    kept: list[Item] = []
    for item in items:
        dup_idx = next((i for i, other in enumerate(kept) if is_near_duplicate(item, other, threshold)), None)
        if dup_idx is None:
            kept.append(item)
        else:
            kept[dup_idx] = _prefer(kept[dup_idx], item)
    return kept


def suppress_covered(
    items: list[Item],
    covered: list[dict[str, Any]],
    *,
    today: date,
    window_days: int,
    threshold: int,
) -> tuple[list[Item], list[Item]]:
    """Drop items seen in the last window unless flagged as a material development."""
    live = prune_covered(covered, today, window_days)
    covered_items = [
        Item(
            id=str(rec.get("id") or item_id_from_url(str(rec.get("url") or rec.get("id") or ""))),
            title=str(rec.get("title") or rec.get("title_norm") or ""),
            url=str(rec.get("url") or ""),
        )
        for rec in live
        if rec.get("id") or rec.get("url") or rec.get("title")
    ]
    fresh: list[Item] = []
    suppressed: list[Item] = []
    for item in items:
        hit = next((c for c in covered_items if is_near_duplicate(item, c, threshold)), None)
        if hit is None:
            fresh.append(item)
            continue
        if looks_like_development(item):
            item.material_development = True
            fresh.append(item)
        else:
            suppressed.append(item)
    return fresh, suppressed


def record_coverage(items: list[Item], today: date) -> list[dict[str, Any]]:
    records = []
    for item in items:
        records.append(
            {
                "id": item.id,
                "title": item.title,
                "title_norm": normalize_title(item.title),
                "url": item.url,
                "covered_date": today.isoformat(),
                "one_line": item.one_line_reason or item.why_this_matters,
            }
        )
    return records


def dedup(
    items: list[Item],
    covered: list[dict[str, Any]],
    settings: dict[str, Any],
    today: date | None = None,
) -> tuple[list[Item], list[Item], list[dict[str, Any]]]:
    today = today or datetime.now(timezone.utc).date()
    threshold = int(settings.get("title_similarity_threshold") or 88)
    window = int(settings.get("covered_window_days") or 14)
    collapsed = collapse_near_duplicates(items, threshold)
    fresh, suppressed = suppress_covered(
        collapsed, covered, today=today, window_days=window, threshold=threshold
    )
    return fresh, suppressed, prune_covered(covered, today, window)
