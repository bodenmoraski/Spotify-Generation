"""ntfy / Telegram / webhook failure alerts."""

from __future__ import annotations

import os
from typing import Any

import httpx

from brief.logutil import log


def ntfy_url(topic: str | None = None) -> str | None:
    topic = (topic or os.environ.get("NTFY_TOPIC") or "").strip()
    if not topic:
        return None
    if topic.startswith("http://") or topic.startswith("https://"):
        return topic
    return f"https://ntfy.sh/{topic}"


def notify(message: str, *, title: str = "daily-audio-brief", dry_run: bool = False) -> None:
    if dry_run:
        log(event="notify_skipped", reason="dry_run", title=title)
        return
    sent = False
    url = ntfy_url()
    if url:
        try:
            httpx.post(url, content=message.encode("utf-8"), headers={"Title": title}, timeout=15)
            sent = True
        except Exception as exc:
            log(event="notify_failed", channel="ntfy", error=str(exc))
    bot = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    chat = os.environ.get("TELEGRAM_CHAT_ID") or ""
    if bot and chat:
        try:
            httpx.post(
                f"https://api.telegram.org/bot{bot}/sendMessage",
                json={"chat_id": chat, "text": f"{title}\n{message}"[:4000]},
                timeout=15,
            )
            sent = True
        except Exception as exc:
            log(event="notify_failed", channel="telegram", error=str(exc))
    webhook = os.environ.get("WEBHOOK_URL") or ""
    if webhook:
        try:
            httpx.post(webhook, json={"title": title, "message": message}, timeout=15)
            sent = True
        except Exception as exc:
            log(event="notify_failed", channel="webhook", error=str(exc))
    if not sent:
        log(event="notify_no_channel", title=title, message=message[:300])


def heartbeat(url: str | None = None, *, dry_run: bool = False) -> None:
    target = (url or os.environ.get("HEALTHCHECK_URL") or "").strip()
    if dry_run or not target:
        log(event="heartbeat_skipped", reason="dry_run" if dry_run else "no_url")
        return
    try:
        httpx.get(target, timeout=15, follow_redirects=True)
        log(event="heartbeat_ok")
    except Exception as exc:
        log(event="heartbeat_failed", error=str(exc))
