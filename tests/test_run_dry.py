"""Dry-run must not publish, notify, or mutate brief/state/."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from brief.models import FeedHealth, Item, item_id_from_url
from brief.notify import notify
from brief.run import COVERED_PATH, QUEUE_PATH, pipeline
from brief.srs import load_queue


def _item() -> Item:
    url = "https://arxiv.org/abs/2606.01234"
    return Item(
        id=item_id_from_url(url),
        title="Interpretability Hits a Wall",
        url=url,
        category="ai",
        is_paper=True,
        excerpt="Sparse autoencoders plateau on frontier models.",
        authors=["Nelson Elhage"],
        source="arXiv",
        weight=1.2,
        one_line_reason="Reframes SAE safety cases.",
    )


@pytest.mark.asyncio
async def test_dry_run_does_not_mutate_state_or_notify(monkeypatch, tmp_path: Path) -> None:
    queue_before = QUEUE_PATH.read_text(encoding="utf-8")
    covered_before = COVERED_PATH.read_text(encoding="utf-8")
    notified: list[str] = []

    async def fake_fetch_all(feeds, settings, **kwargs):
        return [_item()], [FeedHealth(feed_id="arxiv_cs", ok=True, n_items=1)]

    def capture_notify(message: str, **kwargs):
        notified.append(message)

    monkeypatch.setattr("brief.run.fetch_all", fake_fetch_all)
    monkeypatch.setattr("brief.run.notify", capture_notify)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("NTFY_TOPIC", raising=False)

    summary = await pipeline(dry_run=True, want_tts=True)
    assert summary["dry_run"] is True
    assert QUEUE_PATH.read_text(encoding="utf-8") == queue_before
    assert COVERED_PATH.read_text(encoding="utf-8") == covered_before
    assert notified == []
    latest = Path(summary["publish"]["written"]["latest"])
    assert latest.as_posix().endswith("/out/brief-latest.md") or "out" in latest.as_posix()
    assert latest.exists()
    text = latest.read_text(encoding="utf-8")
    assert "Daily Brief" in text
    assert text.strip()


def test_notify_skipped_on_dry_run(monkeypatch) -> None:
    called = []

    def fake_post(*args, **kwargs):
        called.append(args)
        raise AssertionError("httpx.post should not run in dry-run")

    monkeypatch.setattr("brief.notify.httpx.post", fake_post)
    monkeypatch.setenv("NTFY_TOPIC", "should-not-fire")
    notify("hello", dry_run=True)
    assert called == []
