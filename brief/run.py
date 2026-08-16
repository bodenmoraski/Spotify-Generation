"""Entrypoint: fetch → dedup → rank → SRS → render → publish. Silent-safe."""

from __future__ import annotations

import argparse
import os
import sys

from brief.config import CACHE_DIR, OUT_DIR, STATE_DIR, load_allowlist, load_feeds, load_settings
from brief.dedup import dedup, record_coverage, save_covered, load_covered
from brief.fetch import fetch_all
from brief.logutil import log
from brief.models import FeedHealth, Item, Spend
from brief.notify import notify
from brief.publish import publish, republish_yesterday
from brief.rank import has_llm_keys, rank
from brief.render import MARKDOWN_SCHEMA, STUB_BRIEF, render_markdown, weekday_name
from brief.srs import (
    due_today,
    ingest_item,
    load_queue,
    mark_emitted,
    merge_new,
    save_queue,
    today_in_tz,
)

QUEUE_PATH = STATE_DIR / "queue.json"
COVERED_PATH = STATE_DIR / "covered.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the daily audio brief.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch, rank, and render to ./out/. Do not publish, notify, or mutate brief/state/.",
    )
    parser.add_argument(
        "--tts",
        action="store_true",
        help="Generate an MP3 if OPENAI_API_KEY is set (ignored with --dry-run).",
    )
    return parser.parse_args(argv)


def _fail_share(health: list[FeedHealth]) -> float:
    if not health:
        return 1.0
    return sum(1 for h in health if not h.ok) / len(health)


async def pipeline(*, dry_run: bool, want_tts: bool = False) -> dict:
    settings = load_settings()
    feeds = load_feeds()
    allowlist = load_allowlist()
    today = today_in_tz(str(settings.get("timezone") or "Europe/Zurich"))
    weekday = weekday_name(today)
    spend = Spend()

    items, health = await fetch_all(feeds, settings, cache_dir=CACHE_DIR)
    if _fail_share(health) > 0.30:
        log(event="feed_health_alert", fail_share=round(_fail_share(health), 3))
        if not dry_run:
            notify(
                f"{int(_fail_share(health)*100)}% of feeds failed. Brief will use whatever was retrieved.",
                title="daily-audio-brief feeds",
                dry_run=False,
            )

    covered = load_covered(COVERED_PATH)
    queue = load_queue(QUEUE_PATH)
    fresh, suppressed, live_covered = dedup(items, covered, settings, today=today)
    log(event="dedup", n_in=len(items), n_fresh=len(fresh), n_suppressed=len(suppressed))

    reviews = due_today(queue, today, int(settings.get("reviews_per_day") or 4))
    shortlist, paper, serendipity, editorial, spend = rank(
        fresh,
        settings,
        allowlist,
        reviews,
        today,
        MARKDOWN_SCHEMA,
        weekday,
        spend,
    )

    triage_only = editorial is None and has_llm_keys()
    markdown = render_markdown(
        day=today,
        new_items=shortlist,
        paper=paper,
        serendipity=serendipity,
        reviews=reviews,
        editorial_markdown=editorial,
        triage_only=triage_only and editorial is None,
        note=None if shortlist or paper or serendipity or reviews else "Sources were thin today.",
    )
    if not markdown.strip():
        markdown = STUB_BRIEF

    result = publish(
        markdown=markdown,
        day=today,
        settings=settings,
        dry_run=dry_run,
        want_tts=want_tts and not dry_run,
        success_heartbeat=not dry_run,
    )

    if not dry_run:
        selected = list(shortlist)
        if paper:
            selected.append(paper)
        selected.extend(serendipity)
        # Unique by id, preserve order.
        seen: set[str] = set()
        uniq: list[Item] = []
        for it in selected:
            if it.id in seen:
                continue
            seen.add(it.id)
            uniq.append(it)
        new_q = [ingest_item(it, today, settings.get("review_intervals_days")) for it in uniq]
        queue = merge_new(queue, new_q)
        queue = mark_emitted(queue, reviews, today)
        save_queue(QUEUE_PATH, queue)
        save_covered(COVERED_PATH, live_covered + record_coverage(uniq, today))

    summary = {
        "date": today.isoformat(),
        "dry_run": dry_run,
        "n_fetched": len(items),
        "n_fresh": len(fresh),
        "n_shortlist": len(shortlist),
        "n_reviews": len(reviews),
        "cost_usd": round(spend.cost_usd, 5),
        "tokens_in": spend.input_tokens,
        "tokens_out": spend.output_tokens,
        "publish": result,
        "markdown_chars": len(markdown),
    }
    log(event="run_complete", **summary)
    if dry_run:
        print(f"estimated_cost_usd={summary['cost_usd']}", file=sys.stderr)
        print(f"wrote={result.get('written', {}).get('latest')}", file=sys.stderr)
    return summary


def _silent_safe(exc: BaseException, dry_run: bool) -> int:
    log(event="run_failed", error=f"{type(exc).__name__}: {exc}")
    try:
        republish_yesterday(dry_run=dry_run)
    except Exception as republish_exc:
        log(event="republish_failed", error=str(republish_exc))
        if dry_run:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUT_DIR / "brief-latest.md").write_text(STUB_BRIEF, encoding="utf-8")
    notify(f"Pipeline failed: {type(exc).__name__}: {exc}", dry_run=dry_run)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        import asyncio

        asyncio.run(pipeline(dry_run=args.dry_run, want_tts=args.tts))
        return 0
    except Exception as exc:
        return _silent_safe(exc, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
