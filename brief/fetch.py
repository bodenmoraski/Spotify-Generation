"""Async feed fetching with per-source rate limits, retries, and last-good cache."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from brief.config import CACHE_DIR
from brief.logutil import log
from brief.models import FeedHealth, Item
from brief.sources import arxiv as arxiv_src
from brief.sources import culture as culture_src
from brief.sources import econ as econ_src
from brief.sources import forums as forums_src
from brief.sources import news as news_src
from brief.sources import semantic_scholar as s2_src
from brief.sources import substack as substack_src

# Hard ToU: arXiv ≤ 1 request every 3 seconds, single connection.
ARXIV_MIN_INTERVAL = 3.0
S2_MIN_INTERVAL = 1.0
DEFAULT_MIN_INTERVAL = 0.4


class RateLimitError(Exception):
    def __init__(self, status_code: int, retry_after: float | None = None) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code
        self.retry_after = retry_after


class AsyncInterval:
    """Single-flight min-interval limiter (token-bucket degenerate case)."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self.min_interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, httpx.HTTPError):
        return True
    return False


def limiter_for(feed: dict[str, Any], limiters: dict[str, AsyncInterval]) -> AsyncInterval:
    kind = feed.get("type")
    if kind == "arxiv":
        key, interval = "arxiv", ARXIV_MIN_INTERVAL
    elif kind == "s2":
        key, interval = "s2", S2_MIN_INTERVAL
    else:
        key, interval = "default", DEFAULT_MIN_INTERVAL
    if key not in limiters:
        limiters[key] = AsyncInterval(interval)
    return limiters[key]


def cache_path(cache_dir: Path, feed_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in feed_id)
    return cache_dir / f"{safe}.json"


def write_cache(cache_dir: Path, feed_id: str, body: str, content_type: str, url: str) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {"url": url, "content_type": content_type, "body": body}
    cache_path(cache_dir, feed_id).write_text(json.dumps(payload), encoding="utf-8")


def read_cache(cache_dir: Path, feed_id: str) -> dict[str, Any] | None:
    path = cache_path(cache_dir, feed_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def resolve_url(feed: dict[str, Any]) -> str:
    kind = feed.get("type")
    if kind == "arxiv":
        return arxiv_src.build_query_url(feed)
    if kind == "s2":
        return s2_src.build_search_url(feed)
    if kind == "gdelt":
        return news_src.build_gdelt_url(feed)
    if kind == "google_news":
        return news_src.build_google_news_url(feed)
    return str(feed.get("url") or "")


def parse_body(body: str, feed: dict[str, Any], content_type: str = "") -> list[Item]:
    kind = feed.get("type")
    ctype = (content_type or "").lower()
    if kind == "arxiv":
        return arxiv_src.parse_atom(body, feed)
    if kind == "s2":
        return s2_src.parse(body, feed)
    if kind == "graphql":
        return forums_src.parse_graphql(body, feed)
    if kind == "gdelt":
        return news_src.parse_gdelt(body, feed)
    if kind == "google_news":
        return news_src.parse_google_news(body, feed)
    url = str(feed.get("url") or "")
    category = feed.get("category") or ""
    if "substack.com" in url or feed.get("full_text"):
        return substack_src.parse(body, feed)
    if category == "econ" or kind == "econ":
        return econ_src.parse(body, feed)
    if category in {"culture", "serendipity", "learning"}:
        return culture_src.parse(body, feed)
    if "application/json" in ctype or (isinstance(body, str) and body.lstrip().startswith("{")):
        # Unknown JSON — try GraphQL then S2 then GDELT.
        try:
            return forums_src.parse_graphql(body, feed)
        except Exception:
            try:
                return s2_src.parse(body, feed)
            except Exception:
                return news_src.parse_gdelt(body, feed)
    return substack_src.parse(body, feed)


def _headers(settings: dict[str, Any], feed: dict[str, Any]) -> dict[str, str]:
    ua = settings.get("user_agent") or "daily-audio-brief/0.1"
    headers = {"User-Agent": ua, "Accept": "*/*"}
    if feed.get("type") == "s2":
        import os

        key = os.environ.get("S2_API_KEY") or ""
        if key:
            headers["x-api-key"] = key
    if feed.get("type") == "graphql":
        headers["Content-Type"] = "application/json"
    return headers


@retry(
    retry=retry_if_exception(_should_retry),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)
async def http_get(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    timeout: float,
) -> httpx.Response:
    response = await client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
    if response.status_code == 429 or response.status_code >= 500:
        retry_after = None
        if response.headers.get("Retry-After"):
            try:
                retry_after = float(response.headers["Retry-After"])
            except ValueError:
                retry_after = None
        raise RateLimitError(response.status_code, retry_after)
    response.raise_for_status()
    return response


@retry(
    retry=retry_if_exception(_should_retry),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)
async def http_post_json(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> httpx.Response:
    response = await client.post(url, json=payload, headers=headers, timeout=timeout, follow_redirects=True)
    if response.status_code == 429 or response.status_code >= 500:
        raise RateLimitError(response.status_code)
    response.raise_for_status()
    return response


async def fetch_one(
    client: httpx.AsyncClient,
    feed: dict[str, Any],
    settings: dict[str, Any],
    limiter: AsyncInterval,
    cache_dir: Path,
) -> tuple[list[Item], FeedHealth]:
    feed_id = str(feed.get("id") or "unknown")
    url = resolve_url(feed)
    timeout = float(settings.get("http_timeout_seconds") or 30)
    max_items = int(settings.get("max_items_per_feed") or 40)
    headers = _headers(settings, feed)
    try:
        await limiter.acquire()
        if feed.get("type") == "graphql":
            payload = {
                "query": forums_src.POSTS_QUERY,
                "variables": {"limit": max_items},
            }
            response = await http_post_json(client, url, payload, headers, timeout)
        else:
            response = await http_get(client, url, headers, timeout)
        body = response.text
        ctype = response.headers.get("content-type", "")
        items = parse_body(body, feed, ctype)[:max_items]
        write_cache(cache_dir, feed_id, body, ctype, url)
        return items, FeedHealth(
            feed_id=feed_id, ok=True, status=response.status_code, n_items=len(items), url=url
        )
    except Exception as exc:
        cached = read_cache(cache_dir, feed_id)
        if cached and cached.get("body"):
            try:
                items = parse_body(cached["body"], feed, cached.get("content_type") or "")[:max_items]
                return items, FeedHealth(
                    feed_id=feed_id,
                    ok=True,
                    status=None,
                    n_items=len(items),
                    error=f"{type(exc).__name__}: {exc}",
                    cached=True,
                    url=url,
                )
            except Exception as parse_exc:
                return [], FeedHealth(
                    feed_id=feed_id,
                    ok=False,
                    n_items=0,
                    error=f"{type(exc).__name__}: {exc}; cache-parse {parse_exc}",
                    url=url,
                )
        return [], FeedHealth(
            feed_id=feed_id,
            ok=False,
            n_items=0,
            error=f"{type(exc).__name__}: {exc}",
            url=url,
        )


async def fetch_all(
    feeds: list[dict[str, Any]],
    settings: dict[str, Any],
    *,
    cache_dir: Path | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[list[Item], list[FeedHealth]]:
    """Fetch every feed concurrently. One feed's failure never aborts the run."""
    cache_dir = cache_dir or CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    limiters: dict[str, AsyncInterval] = {}
    own_client = client is None
    if client is None:
        # arXiv ToU: single connection for that host; keep a small pool overall.
        client = httpx.AsyncClient(
            headers={"User-Agent": settings.get("user_agent") or "daily-audio-brief/0.1"},
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
        )
    health: list[FeedHealth] = []
    items: list[Item] = []
    try:
        tasks = [
            fetch_one(client, feed, settings, limiter_for(feed, limiters), cache_dir) for feed in feeds
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for feed, result in zip(feeds, results, strict=False):
            if isinstance(result, BaseException):
                health.append(
                    FeedHealth(
                        feed_id=str(feed.get("id") or "unknown"),
                        ok=False,
                        error=f"{type(result).__name__}: {result}",
                    )
                )
                continue
            feed_items, feed_health = result
            items.extend(feed_items)
            health.append(feed_health)
    finally:
        if own_client:
            await client.aclose()

    failed = sum(1 for h in health if not h.ok)
    log(
        event="fetch_complete",
        n_feeds=len(feeds),
        n_ok=sum(1 for h in health if h.ok),
        n_failed=failed,
        n_items=len(items),
        fail_share=round(failed / max(len(health), 1), 3),
    )
    return items, health
