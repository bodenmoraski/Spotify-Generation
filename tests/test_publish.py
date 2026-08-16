"""Silent-safe republish never writes an empty brief."""

from __future__ import annotations

from pathlib import Path

from brief.publish import republish_yesterday
from brief.render import STUB_BRIEF
from brief.run import main


def test_republish_dry_run_writes_stub_or_previous(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BRIEF_SYNC_PATH", "")
    # No previous brief → stub.
    from brief import publish as pub

    monkeypatch.setattr(pub, "previous_brief_text", lambda: None)
    monkeypatch.setattr(pub, "OUT_DIR", tmp_path)
    path = republish_yesterday(dry_run=True)
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert text.strip()
    assert "Daily Brief" in text


def test_main_dry_run_never_raises(monkeypatch) -> None:
    async def boom(**kwargs):
        raise RuntimeError("injected failure")

    monkeypatch.setattr("brief.run.pipeline", boom)
    code = main(["--dry-run"])
    assert code == 0
