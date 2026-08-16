# daily-audio-brief

Cloud-cron pipeline that assembles a curated daily markdown digest (plus RSS and optional MP3) for [Studio by Spotify Labs](https://labs.spotify.com/studio) or any podcast app.

It fetches papers, forums, newsletters, econ/policy, world news, and culture feeds; deduplicates; ranks; writes a 15–20 minute audio-ready markdown brief; publishes an unguessable GitHub Pages URL and a local synced copy; and keeps a no-input spaced-repetition queue in-repo.

The research report, build spec, and Studio-side prompt live in [`brief_n_build.md`](brief_n_build.md). This README is the operator manual.

## Setup order

1. Fork or create a **public** GitHub repo (public = unlimited Actions minutes).
2. `python3.12 -m pip install -e ".[dev]"` (add `.[tts]` if you want the OpenAI MP3 fallback).
3. Copy `.env.example` → `.env` and fill keys locally. **Do not commit `.env`.**
4. Get keys and endpoints:
   - **DeepSeek** — primary ranker (`DEEPSEEK_API_KEY`). [platform.deepseek.com](https://platform.deepseek.com). Triage uses `deepseek-v4-flash`; editorial (the audio script) uses `deepseek-v4-pro` with thinking on.
   - **Gemini** (AI Studio) — fallback if the DeepSeek key is missing (`GEMINI_API_KEY`)
   - Optional **Semantic Scholar** (`S2_API_KEY`) to leave the shared unauthenticated pool
   - Random 32-char `PUBLISH_TOKEN`: `python -c "import secrets; print(secrets.token_urlsafe(24))"`
   - An [ntfy.sh](https://ntfy.sh) topic name (`NTFY_TOPIC`)
   - A [healthchecks.io](https://healthchecks.io) ping URL (`HEALTHCHECK_URL`)
5. Add the same names as **GitHub Actions secrets** (and in the Cloud Agents Secrets tab if you use Cursor Cloud).
6. Enable **GitHub Pages** on the `/docs` folder of this repo.
7. Preview: `python -m brief.run --dry-run` (writes `./out/brief-<date>.md`, prints estimated cost; does **not** publish, notify, or mutate `brief/state/`).
8. Push `main`. The `daily-brief` workflow runs on `workflow_dispatch` and at 11:20 UTC (≈07:20 America/New_York in EDT).
9. Edit `config/feeds.yaml` / `config/serendipity.yaml` / `config/authors_allowlist.yaml` to taste.
10. Grant Studio folder access to the synced path (`BRIEF_SYNC_PATH`, e.g. `~/BriefSync`) **or** point it at the Pages URL.
11. Paste the Part 3 Studio instruction below as a scheduled task.

## What you still must supply

These are **not** in the repo. The pipeline is silent-safe without them (heuristic ranker + stub/previous brief), but a real daily brief needs:

| Secret | Required? | What it does |
|---|---|---|
| `DEEPSEEK_API_KEY` | Yes for LLM ranking | DeepSeek V4 Flash triage + V4 Pro editorial (~$0.05/day off-peak) |
| `GEMINI_API_KEY` | Fallback | Used only if DeepSeek key is unset |
| `PUBLISH_TOKEN` | Yes to publish | 32-char unguessable `/docs/b/<token>/` path |
| `NTFY_TOPIC` | Yes for alerts | Failure / >30% feed-loss notifications |
| `HEALTHCHECK_URL` | Yes for cron watch | Dead-man's-switch; pinged only on a **fresh** brief |
| `S2_API_KEY` | Optional | Semantic Scholar ~1 req/s instead of the shared pool |
| `OPENAI_API_KEY` | Optional | Private-podcast MP3 via `tts-1` (~$0.02–0.03/brief) |
| `BRIEF_SYNC_PATH` | Optional | Local/synced folder Studio reads (`brief-latest.md`) |
| `GITHUB_PAGES_HOST` | Optional | e.g. `https://<user>.github.io/<repo>` so logs print the public URL |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` / `WEBHOOK_URL` | Optional | Extra alert channels |

**Do not implement X/Twitter.** Substack / LessWrong / lab blogs cover that discourse within 24–48h.

## Run

```bash
python -m brief.run --dry-run    # local preview → ./out/
python -m brief.run              # fetch, rank, publish, update state, heartbeat
python -m brief.run --tts        # also generate MP3 if OPENAI_API_KEY is set
python -m pytest -q              # no network, no API keys
```

`--dry-run` fetches (per-feed failures are skipped), ranks, and renders. It does **not** write `docs/`, `BRIEF_SYNC_PATH`, `brief/state/`, ntfy, healthchecks, or MP3.

## Studio scheduled-task prompts

Keep this short and stable. Studio should **read and voice, not research**. Switch local-file ↔ URL using the failure signature in `brief_n_build.md` §1 (both artifacts are published every successful run).

### Local-file variant (primary)

```
Every day at 6:40 AM, read the markdown file at
~/BriefSync/brief-latest.md and turn it into a single spoken podcast
episode saved to my Spotify library, titled "Daily Brief — <today's date>".

Read the file as a finished script — do not research or add outside
information, and do not summarize it further; the file is already edited
to length. Preserve the section order exactly. Read every "Why this
matters" line. Honor any bracketed pronunciation hints, e.g. "[zuh-VEE]",
and then drop the brackets. In the "Quick Reviews" section, read each
question, then genuinely pause for about three seconds where it says
"…take a second…", then read the answer in a slightly warmer tone.
Warm, intelligent, unhurried commute-radio voice. Target 15–20 minutes.
If the file is missing or unchanged from yesterday, still produce the
episode from whatever is there and add one sentence at the start telling
me the brief may be stale.
```

### URL variant (fallback)

Replace the first sentence with:

```
Every day at 6:40 AM, browse to
https://<user>.github.io/<repo>/b/<PUBLISH_TOKEN>/brief-latest.md and read that
page as a finished script …
```

(Everything else identical.) If the repo is user-site Pages (`<user>.github.io`), drop `/<repo>`.

Private podcast RSS (Studio-independent): `https://<user>.github.io/<repo>/b/<PUBLISH_TOKEN>/feed.xml`.

## Architecture

```
feeds → fetch.py → dedup.py → rank.py (triage + editorial) → srs.py
                         ↓
              render.py (md + RSS + optional MP3)
                         ↓
              publish.py (Pages + BRIEF_SYNC_PATH) + notify.py
```

Config: `config/settings.yaml` (counts, models, budget), `config/feeds.yaml`, `config/serendipity.yaml`, `config/authors_allowlist.yaml`.

State committed back by Actions: `brief/state/queue.json` (SRS), `brief/state/covered.json` (14-day dedup).

## Choices made (where the spec left room)

- **DeepSeek is the default stack.** Triage: `deepseek-v4-flash` (JSON, thinking off). Editorial: `deepseek-v4-pro` with thinking on — this is the 15–20 minute script you listen to. Haiku is not used. Gemini Flash-Lite is the fallback when `DEEPSEEK_API_KEY` is missing. Add `DEEPSEEK_API_KEY` as a GitHub Actions secret (and in `.env` locally).
- **Heuristic ranker** when neither DeepSeek nor Gemini keys are set, so dry-run and pytest work without keys or network. It kills funding/launch/PR patterns, boosts allowlisted authors (auto-shortlist), and force-includes 1–2 serendipity slots.
- **Triage is one item per LLM call** (faithful to the literal prompt). Editorial is one call over the shortlist. If a call fails, that item/pass falls back to the heuristic / template renderer.
- **Gemini 2.5 Flash-Lite EOL 2026-10-16** only matters on the Gemini fallback path; the runner then swaps in `gemini_eol_fallback` (`gemini-3.1-flash-lite`).
- **Circuit breaker** `daily_budget_usd: 0.20`: skip editorial and publish a triage-only brief with a note.
- **Silent-safe.** Unhandled exceptions republish yesterday's `brief-latest.md` (or a non-empty stub), ntfy, and **exit 0**. Healthchecks are pinged only after a fresh brief so a recover does not look like success. `--dry-run` failures still do not notify or mutate `brief/state/`.
- **Dedup** uses URL canonicalization + RapidFuzz `token_set_ratio` (threshold 88), not embeddings/MinHash. A covered story returns only if the title/excerpt looks like a material development (`update:`, `follow-up`, `new evidence`, …) or the ranker set `material_development`.
- **SRS** expanding intervals `[1, 3, 7, 16, 35]`, cap `reviews_per_day` (oldest ingested first), retire after the last interval. Optional `missed` reinsert exists in `brief/srs.py` but is unused until Studio can take a reply.
- **No TTS on `--dry-run`.** Pass `--tts` on a real run if `OPENAI_API_KEY` is set. RSS is always written.
- **Last-good cache** per feed in `.cache/feeds/` (gitignored). One feed's 4xx/5xx/timeout never aborts the run; >30% failures ntfy.
- **arXiv** hard ToU: ≤1 request / 3 seconds, shared limiter. S2: 1/s. GraphQL (ForumMagnum) posts are filtered client-side by `karma_threshold`.
- **Extra modules** not in the Part 2 tree: `brief/models.py`, `brief/config.py`, `brief/logutil.py` — shared schemas, YAML loading, JSON-line logs.
- **GitHub Pages** publishes to `docs/b/<PUBLISH_TOKEN>/brief-latest.md` plus `feed.xml`. Root `docs/index.md` does not list the token.
- **Keep-alive.** `.github/workflows/keepalive.yml` weekly-touches `.keepalive` so public-repo scheduled workflows are not disabled after 60 days of “inactivity.”
- **Timezone** default `America/New_York` (`BRIEF_TIMEZONE` overrides). Cron is 11:20 UTC; adjust in `.github/workflows/brief.yml`.

## Tests

Deterministic, no network, no API keys:

```bash
python3 -m pytest -q
```

Fixtures under `tests/fixtures/` cover arXiv Atom, Substack RSS, ForumMagnum GraphQL, Semantic Scholar JSON, GDELT JSON, and Google News RSS.

## License

Personal research aggregator. Respect each source's terms of use (especially arXiv's 1 req / 3s rule).
