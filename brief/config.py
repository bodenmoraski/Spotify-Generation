"""Load YAML config and environment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
STATE_DIR = ROOT / "brief" / "state"
CACHE_DIR = ROOT / ".cache" / "feeds"
OUT_DIR = ROOT / "out"
DOCS_DIR = ROOT / "docs"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_settings() -> dict[str, Any]:
    load_dotenv(ROOT / ".env")
    settings = load_yaml(CONFIG_DIR / "settings.yaml")
    tz = os.environ.get("BRIEF_TIMEZONE") or settings.get("timezone") or "Europe/Zurich"
    settings["timezone"] = tz
    return settings


def load_feeds() -> list[dict[str, Any]]:
    main = load_yaml(CONFIG_DIR / "feeds.yaml")
    serendipity = load_yaml(CONFIG_DIR / "serendipity.yaml")
    feeds = list(main.get("feeds") or [])
    for feed in serendipity.get("feeds") or []:
        feed = dict(feed)
        feed.setdefault("category", "serendipity")
        feeds.append(feed)
    return feeds


def load_allowlist() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "authors_allowlist.yaml")


def load_serendipity() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "serendipity.yaml")
