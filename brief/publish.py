"""Write local file + GitHub Pages path + RSS. Never empty. Dry-run is a no-op here."""

from __future__ import annotations

import os
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from brief.config import DOCS_DIR, OUT_DIR, ROOT
from brief.logutil import log
from brief.notify import heartbeat
from brief.render import STUB_BRIEF, brief_title, maybe_tts, render_rss


def publish_token() -> str:
    return (os.environ.get("PUBLISH_TOKEN") or "").strip()


def pages_dir(token: str | None = None) -> Path:
    tok = token or publish_token() or "local"
    return DOCS_DIR / "b" / tok


def public_url(filename: str = "brief-latest.md") -> str:
    host = (os.environ.get("GITHUB_PAGES_HOST") or "").strip().rstrip("/")
    token = publish_token()
    if host and token:
        return f"{host}/b/{token}/{filename}"
    if token:
        return f"/b/{token}/{filename}"
    return ""


def write_outputs(
    *,
    markdown: str,
    rss: str,
    day: date,
    dest_dir: Path,
    mp3: Path | None = None,
) -> dict[str, Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    latest = dest_dir / "brief-latest.md"
    dated = dest_dir / f"brief-{day.isoformat()}.md"
    feed = dest_dir / "feed.xml"
    latest.write_text(markdown if markdown.strip() else STUB_BRIEF, encoding="utf-8")
    dated.write_text(latest.read_text(encoding="utf-8"), encoding="utf-8")
    feed.write_text(rss, encoding="utf-8")
    written = {"latest": latest, "dated": dated, "rss": feed}
    if mp3 and mp3.exists():
        target = dest_dir / "brief-latest.mp3"
        shutil.copyfile(mp3, target)
        shutil.copyfile(mp3, dest_dir / f"brief-{day.isoformat()}.mp3")
        written["mp3"] = target
    return written


def previous_brief_text() -> str | None:
    token = publish_token()
    candidates = [
        pages_dir(token) / "brief-latest.md" if token else None,
        pages_dir("local") / "brief-latest.md",
        OUT_DIR / "brief-latest.md",
    ]
    sync = (os.environ.get("BRIEF_SYNC_PATH") or "").strip()
    if sync:
        candidates.insert(0, Path(sync).expanduser() / "brief-latest.md")
    for path in candidates:
        if path and path.exists():
            text = path.read_text(encoding="utf-8")
            if text.strip():
                return text
    return None


def republish_yesterday(*, dry_run: bool = False) -> Path | None:
    """Silent-safe: republish the previous brief unchanged. Never write empty."""
    text = previous_brief_text() or STUB_BRIEF
    if dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / "brief-latest.md"
        path.write_text(text, encoding="utf-8")
        log(event="republish_dry_run", path=str(path))
        return path
    token = publish_token()
    dest = pages_dir(token)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "brief-latest.md"
    path.write_text(text, encoding="utf-8")
    sync = (os.environ.get("BRIEF_SYNC_PATH") or "").strip()
    if sync:
        sdir = Path(sync).expanduser()
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "brief-latest.md").write_text(text, encoding="utf-8")
    log(event="republish_previous", path=str(path))
    return path


def publish(
    *,
    markdown: str,
    day: date,
    settings: dict[str, Any],
    dry_run: bool,
    want_tts: bool = False,
    success_heartbeat: bool = True,
) -> dict[str, Any]:
    body = markdown.strip() or STUB_BRIEF
    title = brief_title(day)
    page = public_url()
    mp3_path: Path | None = None
    if want_tts and not dry_run:
        mp3_path = maybe_tts(body, settings, OUT_DIR / f"brief-{day.isoformat()}.mp3")
    mp3_url = public_url("brief-latest.mp3") if mp3_path else None
    rss = render_rss(
        title=title,
        markdown=body,
        day=day,
        page_url=page or f"brief-{day.isoformat()}",
        mp3_url=mp3_url,
        mp3_bytes=mp3_path.stat().st_size if mp3_path else None,
    )

    if dry_run:
        written = write_outputs(markdown=body, rss=rss, day=day, dest_dir=OUT_DIR, mp3=None)
        log(event="publish_skipped", reason="dry_run", out=str(written["latest"]))
        return {"written": {k: str(v) for k, v in written.items()}, "url": "", "dry_run": True}

    ensure_docs_root()
    token = publish_token()
    dest = pages_dir(token)
    written = write_outputs(markdown=body, rss=rss, day=day, dest_dir=dest, mp3=mp3_path)
    sync = (os.environ.get("BRIEF_SYNC_PATH") or "").strip()
    if sync:
        sdir = Path(sync).expanduser()
        write_outputs(markdown=body, rss=rss, day=day, dest_dir=sdir, mp3=mp3_path)
    if success_heartbeat:
        heartbeat(dry_run=False)
    log(event="publish_ok", path=str(written["latest"]), url=page)
    return {"written": {k: str(v) for k, v in written.items()}, "url": page, "dry_run": False}


def ensure_docs_root() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    index = DOCS_DIR / "index.md"
    if not index.exists():
        index.write_text("# Daily Audio Brief\n\nNothing listed here.\n", encoding="utf-8")
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")
