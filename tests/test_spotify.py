from __future__ import annotations

from pathlib import Path

from brief.spotify import maybe_save_to_spotify


def test_spotify_skipped_on_dry_run(tmp_path: Path, monkeypatch) -> None:
    mp3 = tmp_path / "brief.mp3"
    mp3.write_bytes(b"ID3")
    called = []

    def fake_cli(*args, **kwargs):
        called.append(args)
        return {}

    monkeypatch.setattr("brief.spotify._cli", fake_cli)
    assert maybe_save_to_spotify(mp3, episode_title="Daily Brief — 16 August 2026", settings={}, dry_run=True) is None
    assert called == []


def test_spotify_skipped_without_credentials(tmp_path: Path, monkeypatch) -> None:
    mp3 = tmp_path / "brief.mp3"
    mp3.write_bytes(b"ID3")
    monkeypatch.setattr("brief.spotify.shutil.which", lambda _name: "/usr/bin/save-to-spotify")
    monkeypatch.setattr("brief.spotify.credentials_present", lambda: False)
    called = []
    monkeypatch.setattr("brief.spotify._cli", lambda *a, **k: called.append(a) or {})
    assert maybe_save_to_spotify(mp3, episode_title="x", settings={}) is None
    assert called == []


def test_spotify_reuses_existing_show(tmp_path: Path, monkeypatch) -> None:
    mp3 = tmp_path / "brief.mp3"
    mp3.write_bytes(b"ID3")
    monkeypatch.setattr("brief.spotify.shutil.which", lambda _name: "/usr/bin/save-to-spotify")
    monkeypatch.setattr("brief.spotify.credentials_present", lambda: True)

    calls: list[tuple[str, ...]] = []

    def fake_cli(*args, **kwargs):
        calls.append(args)
        if args[:1] == ("shows",) and "create" not in args:
            return {"shows": [{"id": "show-1", "title": "Daily Brief"}]}
        if args[:1] == ("upload",):
            return {"episode_id": "ep-9", "episode_uri": "spotify:episode:ep-9"}
        if args[:1] == ("episodes",):
            return {"status": "READY"}
        raise AssertionError(args)

    monkeypatch.setattr("brief.spotify._cli", fake_cli)
    result = maybe_save_to_spotify(
        mp3, episode_title="Daily Brief — 16 August 2026", settings={"spotify_show_title": "Daily Brief"}
    )
    assert result is not None
    assert result["show_id"] == "show-1"
    assert result["episode_id"] == "ep-9"
    assert any(c[:1] == ("upload",) and "--show-id" in c and "show-1" in c for c in calls)
    assert not any("create" in c for c in calls)


def test_spotify_upload_failure_does_not_raise(tmp_path: Path, monkeypatch) -> None:
    mp3 = tmp_path / "brief.mp3"
    mp3.write_bytes(b"ID3")
    monkeypatch.setattr("brief.spotify.shutil.which", lambda _name: "/usr/bin/save-to-spotify")
    monkeypatch.setattr("brief.spotify.credentials_present", lambda: True)

    def fake_cli(*args, **kwargs):
        raise RuntimeError("401")

    monkeypatch.setattr("brief.spotify._cli", fake_cli)
    monkeypatch.setattr("brief.spotify.notify", lambda *a, **k: None)
    assert maybe_save_to_spotify(mp3, episode_title="x", settings={}) is None
