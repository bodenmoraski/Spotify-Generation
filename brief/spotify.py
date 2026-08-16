"""Upload the daily MP3 to a private Spotify Personal Podcast show."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from brief.logutil import log
from brief.notify import notify

CLI = "save-to-spotify"
CONFIG_DIR = Path.home() / ".config" / "save-to-spotify"
DEFAULT_SHOW_TITLE = "Daily Brief"


def credentials_present() -> bool:
    return (CONFIG_DIR / "token.json").is_file() and (CONFIG_DIR / "dpop_key.json").is_file()


def _cli(*args: str, timeout: int = 180) -> dict[str, Any]:
    binary = shutil.which(CLI)
    if not binary:
        raise FileNotFoundError(f"{CLI} is not on PATH")
    proc = subprocess.run(
        [binary, "--json", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    payload = _parse_json(proc.stdout) or _parse_json(proc.stderr)
    if proc.returncode != 0:
        err = ""
        if isinstance(payload, dict):
            err = str(payload.get("error") or "")
        raise RuntimeError(err or proc.stderr.strip() or proc.stdout.strip() or f"{CLI} exited {proc.returncode}")
    if not isinstance(payload, dict):
        return {}
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return payload


def _parse_json(text: str) -> dict[str, Any] | None:
    blob = (text or "").strip()
    if not blob:
        return None
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        start, end = blob.find("{"), blob.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(blob[start : end + 1])
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def _id_of(obj: dict[str, Any]) -> str:
    for key in ("id", "show_id", "episode_id", "show_uri", "episode_uri", "uri"):
        val = obj.get(key)
        if val:
            return str(val)
    return ""


def _ensure_show(title: str) -> str:
    listed = _cli("shows")
    shows = listed.get("shows") if isinstance(listed.get("shows"), list) else []
    if not shows and listed.get("title"):
        shows = [listed]
    want = title.strip().lower()
    for show in shows:
        if not isinstance(show, dict):
            continue
        if str(show.get("title") or "").strip().lower() == want:
            sid = _id_of(show)
            if sid:
                return sid
    created = _cli("shows", "create", "--title", title, "--summary", "Private daily audio brief.")
    sid = _id_of(created)
    if not sid:
        raise RuntimeError("save-to-spotify shows create returned no id")
    return sid


def maybe_save_to_spotify(
    mp3: Path,
    *,
    episode_title: str,
    settings: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """Upload mp3 as today's episode. Skip if CLI/credentials missing. Never raise."""
    if dry_run:
        log(event="spotify_skip", reason="dry_run")
        return None
    if not mp3.exists():
        log(event="spotify_skip", reason="no_mp3")
        return None
    if os.environ.get("SAVE_TO_SPOTIFY_DISABLED"):
        log(event="spotify_skip", reason="disabled")
        return None
    if not shutil.which(CLI):
        log(event="spotify_skip", reason="cli_missing")
        return None
    if not credentials_present():
        log(event="spotify_skip", reason="no_credentials")
        return None
    show_title = str(settings.get("spotify_show_title") or DEFAULT_SHOW_TITLE)
    show_id = (os.environ.get("SAVE_TO_SPOTIFY_SHOW_ID") or "").strip() or str(
        settings.get("spotify_show_id") or ""
    ).strip()
    try:
        if not show_id:
            show_id = _ensure_show(show_title)
        uploaded = _cli(
            "upload",
            str(mp3),
            "--title",
            episode_title,
            "--show-id",
            show_id,
            "--summary",
            episode_title,
            timeout=300,
        )
        episode_id = _id_of(uploaded) or str(uploaded.get("episode_id") or "")
        if episode_id:
            try:
                _cli("episodes", "status", episode_id, "--wait", "5m", timeout=360)
            except Exception as exc:
                log(event="spotify_wait_failed", error=str(exc), episode_id=episode_id)
        result = {
            "show_id": show_id,
            "episode_id": episode_id,
            "episode_uri": uploaded.get("episode_uri") or uploaded.get("uri"),
        }
        log(event="spotify_upload_ok", **{k: v for k, v in result.items() if v})
        return result
    except Exception as exc:
        log(event="spotify_upload_failed", error=str(exc))
        notify(f"Spotify upload failed: {exc}", title="daily-audio-brief spotify")
        return None
