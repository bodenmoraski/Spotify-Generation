# daily-audio-brief

Cloud-cron pipeline that assembles a curated daily markdown digest (plus RSS and optional MP3) for Studio by Spotify Labs or any podcast app.

The full research report, build spec, and Studio-side prompt live in `brief_n_build.md`. Follow Part 2 of that file when implementing.

## Cursor Cloud specific instructions

- Environment is defined in `.cursor/environment.json`. Install is `pip install -e ".[dev]"` (pytest included).
- Python 3.12+ is required. Verify with `python3 --version` before running tests.
- Deterministic tests need no API keys and no network: `python3 -m pytest -q`.
- Dry-run (after the pipeline exists): `python3 -m brief.run --dry-run`. This must not publish, notify, or mutate `brief/state/`.
- Do not commit `.env`. Secrets belong in GitHub Actions secrets and in the Cloud Agents Secrets tab, never in the repo.
- Do not implement X/Twitter ingestion.

## Current implementation status

Scaffold is on `main` (`config/`, `.env.example`, empty `brief/state/*.json`). Core modules, tests, GitHub Actions, and README still need to be built from `brief_n_build.md` Part 2.
