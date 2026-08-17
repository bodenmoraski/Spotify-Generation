# Automated Daily Audio Brief Pipeline — Research Report + Build Prompt + Studio Prompt

## TL;DR
- **Studio by Spotify Labs is real and matches the brief closely.** It launched May 21, 2026 as a macOS research-preview agent (built on Mario Zechner's open-source "Pi" framework, pi.dev); it reads local files you point it to, browses the web read-only via a separate browser profile, runs scheduled tasks in the background, and requires your Mac to be on. The recommended ingestion seam is a **local file** the pipeline writes to a Studio-permitted synced folder, with a **plain unguessable HTTPS markdown URL** as the fallback.
- **The $0.10/day ceiling is met with large headroom — the recommended config costs ~$0.07/day (≈$2.16/month), the cheapest viable config ~$0.013/day, and a free-tier-maximizing config ~$0.00/day marginal** — essentially all LLM tokens, on free hosting (GitHub Actions public repo or Cloudflare Workers). No paid data source is needed. The single hard unknown is not cost but Studio's **undocumented usage limits** (Spotify publishes no numeric credit/minute figure anywhere).
- **Biggest risks are Studio-side, not pipeline-side:** no published usage-limit numbers, no confirmed voice-input or local write-back, and research-preview instability. The architecture is therefore consumer-agnostic: it publishes a markdown + RSS + (optional MP3) artifact that works with Studio if available and with NotebookLM, a private podcast RSS feed, or Readwise Reader if not.

---

## Part 1 — Research Report

### §0. Verification of "Studio by Spotify Labs"

**Verdict: CONFIRMED real, and the user's description is substantially accurate.** Primary sources: Spotify's own Labs site (labs.spotify.com/studio and /how-it-works, © 2026 Spotify AB), the Spotify newsroom launch post (newsroom.spotify.com, dated 2026-05-21, updated 2026-07-20), and Spotify Support (support.spotify.com/us/article/studio/, /ai-usage-limits/, /personal-podcasts/). Corroborated by TechCrunch (2026-05-21), MacRumors (2026-05-08), Engadget, Hollywood Reporter, and How-To Geek.

Confirmed facts (all from Spotify primary sources unless noted):
- **What it is:** a standalone macOS desktop app — a personal agent that understands your Spotify taste and creates Personal Podcasts from your inbox, calendar, notes, files, and the web. Announced at Spotify Investor Day 2026-05-21; began gradual research-preview rollout ~2026-07-20. Invite-only, Premium users 18+, in 20+ markets. macOS only (no Windows/iOS/Android for creation; generated audio syncs to the Spotify library for playback anywhere).
- **Built on Pi**, an open-source agent framework by Mario Zechner (pi.dev), confirmed verbatim in the Labs site footer: *"Studio by Spotify Labs is built on Pi, an open source agent framework created by Mario Zechner. We're grateful to Mario and the Pi community."*
- **Distinct from "Personal Podcasts"** (a simpler prompt-based feature inside the main Spotify app) and from the earlier "Save to Spotify" CLI (May 2026, for Claude Code/Codex/OpenClaw users). Studio is the more capable standalone app; Personal Podcast is one of its outputs.
- **Discrepancy vs. brief (minor):** The user's launch month ("May 2026") is correct. The description of local-file/notes/highlights access, scheduled tasks, and read-only web browsing is all accurate. Spotify markets Studio's memory as taste/preference-oriented ("listening patterns and taste preferences… your timezone and routine"), which matches the user's observation that its memory is "designed for music taste rather than durable application state." The default in-app agent appears to be named "Kit" (the support page instructs "Type a request for Kit"), and is renameable.

### §1. The Studio ingestion seam (highest uncertainty — resolved as far as public docs allow)

**Local file reading — CONFIRMED.** How-it-works page, verbatim: *"With your permission, Studio reads files you point it to — notes, documents, highlights — and helps you act on them,"* and *"Studio can access files you point it to, but it's blocked from sensitive locations by default, including saved passwords, security keys, and system files."* Folder access is a **persisted, revocable permission** — the "Your controls → Permissions" panel lets you *"See and revoke connected accounts, folder access, and tool permissions."* The exact grant mechanism (macOS folder picker vs. per-file) and whether it survives across every scheduled run is **not documented in detail**; this is the single item to verify experimentally (see below).

**Scheduled task fetching a plain URL — PARTIALLY CONFIRMED.** Studio's web skill: *"Browses the web using a separate browser profile to research topics and gather news,"* and *"It's designed to read, not post, comment or take actions on websites."* Web browsing and scheduled tasks are both in the "acts immediately" tier: *"Playback, playlists, search, information retrieval, audio creation, web browsing, and scheduled tasks."* Spotify does **not** explicitly say whether an arbitrary static URL can be fetched on demand vs. general "browsing," and there is no statement about robots.txt or JS-rendering behavior. Because the browser profile is separate and has **no access to your logged-in accounts**, any URL you point it at must be reachable without auth — an unguessable static URL works in principle; real auth will not.

**Mac awake requirement — CONFIRMED.** Labs site, verbatim: *"Your computer must be on for scheduled tasks to run,"* and *"Your computer needs to be on and running Studio to respond — scheduled tasks and audio creation run there too."* The docs say "on" / "on and running," not "awake"; sleep/lid-closed behavior and missed-trigger behavior are **undocumented**. This is fine for the brief's use case: the pipeline runs in the cloud (Mac off overnight), and Studio only needs to be on at listening time — so the recommended pattern is to have Studio's scheduled task fire shortly before the commute when the Mac is already awake, OR to trigger episode generation manually / by message when you wake the Mac.

**Voice input — UNDOCUMENTED.** No Spotify page or credible press confirms whether Studio accepts spoken replies. The documented input channels are typed desktop requests and messaging from the Spotify mobile app. **Design assumption: text-in / audio-out only.** The spaced-repetition design therefore must not depend on voice input (see §6).

**Write-back to a local file — UNDOCUMENTED / assume NO.** Spotify describes reading local files and drafting emails/documents only; it never advertises saving to disk. (The underlying Pi framework has read/write/edit/bash tools, so write is technically possible at the framework layer, but Studio does not expose it as a feature and blocks sensitive locations by default. Unofficial community reports of a `com.apple.security.automation.apple-events` entitlement bug and "cannot write to library" errors corroborate that write paths are gated/buggy — flagged as unverified user posts, not Spotify statements.) **Design assumption: output is audio + chat only; the brief must carry all state itself.**

**Usage limits — NO NUMBERS PUBLISHED.** This is the critical finding. Spotify's AI-usage-limits support page gives only qualitative language: *"the more Studio has to think, create, or build on your behalf, the more it draws from your limit… asking Studio to research a topic, browse the web, or build a podcast from scratch uses more."* "Pro credits" are purchasable top-ups (Spotify states they are *"valid for 12 months from the date of purchase"* and non-refundable except when unused within 7 days) once you hit the included limit, but **the included monthly allowance is not quantified anywhere** — you cannot even see included usage in the account page, only purchased Pro credits. The only concrete numbers on the entire page are the 12-month validity and 7-day refund window. **Therefore whether a daily 15–20 min brief plus a paper deep-dive fits inside the preview limits cannot be verified from documentation and must be tested empirically.** Because "build a podcast from scratch" and "browse the web" are explicitly the most expensive operations, the pipeline should minimize what Studio has to do: hand it a finished, well-structured script so it only reads and voices, rather than researching.

**Prompt-length ceiling for a scheduled-task instruction — UNDOCUMENTED.** Pi (the underlying framework) supports long persistent context via AGENTS.md/system-prompt files and append-only JSONL sessions, but Studio does not expose these, and there is no published character limit for a scheduled-task instruction. **Design assumption: keep the Studio-side instruction short and stable, and push all structural complexity into the markdown artifact itself**, which Studio reads fresh each run.

**Recommended ingestion path + fallback:**
- **Primary: local file.** Publish `brief-latest.md` into a cloud-synced folder (iCloud Drive / Dropbox / Google Drive desktop client) that downloads to a real on-disk path on the Mac, and grant Studio folder access to that path once. Studio reads the freshest file each morning. This avoids the read-only browser's auth limitations entirely and is the most robust.
- **Fallback: plain HTTPS URL.** Publish the same markdown at an unguessable static URL (e.g. `https://<user>.github.io/b/<random-32-char-token>/brief-latest.md`). Studio's web skill fetches it.
- **Failure signature that triggers switching:** If, over 2–3 mornings, the episode omits the day's content or Studio says it could not read the source (local path not found because the sync client hadn't downloaded the file, or permission lapsed) → switch to the URL path. If the episode is stale/duplicated or Studio reports it couldn't fetch the URL (JS/robots/timeout) → switch to the local-file path. Publishing **both** every day costs nothing extra and lets you flip the Studio instruction in one line.

**The 10-minute experiment to settle the seam:** (1) Manually place a small markdown file in a candidate folder; grant Studio access; ask "read <file> and make a 2-minute podcast." Confirm it reads it. (2) Restart the Mac, wait for a scheduled task, confirm folder permission persisted across the run. (3) Publish the same file at an unguessable URL; ask Studio to "browse <url> and summarize." Confirm fetch works without login. (4) Note whether Studio will accept a spoken reply to a question it poses. Record which of the four worked; that dictates primary vs. fallback and whether the optional voice upgrade in §6 is available.

### §2. Sources and retrieval

All feeds below use official/open endpoints; none require paid access at the brief's volume.

| Source | Endpoint / method | Auth | Rate limit | Cost | ToS on automated use |
|---|---|---|---|---|---|
| arXiv (cs.AI, cs.LG, cs.CY, cs.CL) | Legacy API `export.arxiv.org/api/query` + RSS `arxiv.org/rss/<cat>`; OAI-PMH for bulk | None | **≤ 1 request every 3 seconds, single connection** (verbatim ToU) | Free | Explicitly permitted: "provide tools/services to users that help them discover or be notified about arXiv e-prints" |
| Semantic Scholar Graph API | `api.semanticscholar.org/graph/v1/...` | Optional key | **~5,000 req / 5 min unauthenticated (shared pool)**; ~1 req/s with a free key; batch endpoints available | Free | Permitted; rate-limit circumvention prohibited |
| LessWrong / Alignment Forum | RSS `lesswrong.com/feed.xml?view=frontpage&karmaThreshold=<n>`; GraphQL `/graphql` | None | Reasonable use | Free | UI-generated RSS "supported indefinitely"; query-param feeds unofficial but tolerated |
| EA Forum | GraphQL `forum.effectivealtruism.org/graphql`; RSS | None | Reasonable use | Free | Same engine as LW (ForumMagnum) |
| Substack newsletters | Per-publication `/feed` (e.g. `thezvi.substack.com/feed`) | None | Reasonable use | Free | RSS is public; **full-text** for most free posts |
| NBER working papers | RSS via `nber.org`; RePEc series `RePEc:nbr:nberwo`; New-This-Week email | None | Reasonable use | Free (metadata/abstracts) | Metadata reuse permitted; full PDFs gated (3 free/yr for non-affiliates) |
| VoxEU / IMF / Fed / BIS | Site RSS feeds | None | Reasonable use | Free | Public feeds |
| GDELT DOC 2.0 API | `api.gdeltproject.org/api/v2/doc/doc` | None | Generous, undocumented soft cap | Free | Open platform (Google Jigsaw-supported); best for non-US-centric, 65-language machine-translated coverage |
| Google News RSS | `news.google.com/rss/search?q=...` | None | Lightweight; "won't get blocked" for modest daily use | Free | Unofficial but stable; 50 items/query |
| Culture/lit (LRB, n+1, Paris Review, Public Books, LitHub, The Point, Pitchfork) | Site RSS feeds | None | Reasonable use | Free | Public feeds; mix of full-text and truncated |

**Surfacing important AI papers without citation lag:** citation velocity is too slow for a daily brief. Use a composite signal: (a) **author priors** — a maintained allowlist of ~150 researchers/labs whose first-author papers auto-shortlist; (b) **venue/announcement signal** — arXiv cross-listing to cs.LG+cs.AI, plus lab-blog corroboration (Anthropic/DeepMind/OpenAI research blogs via RSS); (c) **social/discourse signal** — a paper discussed on LessWrong/Alignment Forum above a karma threshold, or in Zvi's roundups, within 24–48h; (d) **the cheap-LLM triage pass** scoring "does this change how a practitioner thinks?" One paper/day maximum.

**Newsletter feeds — verification status.** Confirmed resolving and full-text via search: **Zvi's *Don't Worry About the Vase*** (`thezvi.substack.com/feed`, plus a separate podcast RSS at `api.substack.com/feed/podcast/2809465.rss`). Substack free posts are generally full-text in RSS. **Astral Codex Ten** (`astralcodexten.substack.com/feed`), **Import AI** (Jack Clark, `jack-clark.net`/Substack), **Transformer**, **Hyperdimensional**, **ChinaTalk** (`chinatalk.media`), **Marginal Revolution** (`marginalrevolution.com/feed`, confirmed active) — all publish standard RSS; treat any not directly fetched here as **unconfirmed until the pipeline's feed-validation test runs on first deploy** (the build prompt includes this test). Marginal Revolution RSS is truncated to post excerpts for some posts; fetch the linked page if full text is needed.

**Learning science / self-improvement (anti-slop):** pull from academic sources (e.g. *Psychological Science*, *Trends in Cognitive Sciences*, *Applied Cognitive Psychology*) and a short allowlist of credible writers, not the productivity-content ecosystem. One idea/day, drawn from a rotating queue rather than the daily firehose.

### §3. The X/Twitter problem

**Honest assessment: skip the official X API.** As of February 2026 X eliminated the free tier and moved new developers to **pay-per-use: ~$0.005 per post read ($0.20 if a post contains a link on the write side), capped at 2M reads/month**; legacy Basic ($200/mo) was retired and force-migrated June 1, 2026; Pro ($5,000/mo) is closed to new signups; Enterprise starts ~$42,000/mo (multiple 2026 sources: postproxy.dev, socialcrawl.dev, xpoz.ai, sorsa.io). Even modest read volume blows the $0.10/day ceiling and carries ToS risk.

(a) Official API: rejected on cost. (b) Third-party RSS-from-list / scraper services (twitterapi.io ~$0.15/1k tweets, SocialData ~$0.20/1k, others $0.02–0.20/1k): cheaper but **ToS-violating and unreliable** — not recommended for a zero-maintenance build. (c) **Recommended: treat X as skippable.** The substantive AI-safety/econ discourse reliably crossposts to Substack, LessWrong, and personal blogs within 24–48h, which the pipeline already ingests for free. **Recommendation: no X ingestion.** If a specific must-have account doesn't crosspost, add its Nitter/RSS-bridge feed as a single best-effort feed that degrades silently if it breaks — never on the critical path.

### §4. Curation and ranking

**Model choice.** Two-pass architecture. Verified current pricing (per 1M tokens, input/output, dated Aug 2026):
- **Google Gemini 2.5 Flash-Lite: $0.10 / $0.40** (the absolute floor among capable models; 1M-token context; **but Google has set retirement for 2026-10-16** — migrate to Gemini 3.1 Flash-Lite at $0.25/$1.50 thereafter). Google AI Studio also offers a **free tier** with daily request/token caps suitable for a hobby pipeline.
- **OpenAI GPT-5 mini: $0.25 / $2.00** (200K context).
- **Anthropic Claude Haiku 4.5: $1.00 / $5.00** (200K context; strongest instruction-following of the three, per multiple 2026 comparisons; prompt caching at 10% of input, batch at 50%).
- Cheaper still for the triage pass: DeepSeek V4 Flash (~$0.14/$0.28) and GPT-5.4 nano (~$0.20/$1.25).

**Recommendation:** **triage pass on Gemini 2.5 Flash-Lite (or its free tier)** over all ~100–200 candidates (cheap, huge context, good enough for a 0–1 relevance score); **editorial/summarization pass on Claude Haiku 4.5** over the ~15-item shortlist (best taste/instruction-following). This "cheap-triage → strong-shortlist" split keeps quality high where it matters and cost negligible.

**Realistic token estimate.** Triage: ~200 items × ~500 tokens each ≈ 100K input + ~2K output/day on Flash-Lite ≈ **$0.011 + $0.001 ≈ $0.012/day** (and **$0 on the AI Studio free tier**). Editorial: ~15 items × ~1,500 tokens context + a ~4K-token system prompt ≈ 30K input + ~6K output/day on Haiku 4.5 ≈ **$0.03 input + $0.03 output ≈ $0.06/day**. **All-in LLM ≈ $0.07/day worst case; ≈ $0.013/day if the editorial pass also uses Flash-Lite; ≈ $0 using free tiers.** (See §7.)

**Ranking prompt with taste** — see the full literal system prompt in Part 2. Core principles: reward ideas that *change how a reader thinks* over things that merely happened; kill funding rounds, product launches, PR, and horse-race coverage; reward a strong argument over a strong headline; enforce a serendipity budget.

**Serendipity budget (first-class requirement).** Reserve 1–2 slots/day. Mechanism: maintain a set of "adjacent but off-profile" domains (e.g. architecture, biology, music theory, history of science, poetry) with their own feeds; each day the triage pass scores items in these domains on *intrinsic interestingness to a curious generalist* (not relevance to the reader's core profile), and one high-scorer is force-included and clearly framed as a stretch pick. This is real range (curated from genuinely different domains), not random noise.

**Dedup & suppression.** (a) Near-duplicate detection across feeds via title/URL normalization + embedding or MinHash similarity; (b) a rolling 14-day store of covered item hashes; a story recurs only if the LLM judges a *material development* vs. prior coverage.

**Markdown structure for good audio** — see the schema and worked example in Part 2. Key elements: fixed section order; a one-line "why this matters" per item; pronunciation hints for names/acronyms; and an explicit "read these three today" closer.

### §5. Hosting and orchestration

| Host | Cron reliability | Free tier | Secrets | Static output | Maintenance | Verdict |
|---|---|---|---|---|---|---|
| **GitHub Actions (public repo)** | Best-effort; **10–30 min delays common at peak, occasionally 1h+**; **auto-disables after 60 days inactivity** (public repos) | **Unlimited minutes for public repos**; 2,000 min/mo private | Encrypted repo secrets | GitHub Pages / commit to repo | Low; needs keep-alive commit | **Recommended primary** (early cron time + keep-alive) |
| **Cloudflare Workers + Cron Triggers** | Reliable; 1-min minimum; **no built-in retry**; ~5 cron triggers/acct free | 100K req/day; KV 1GB/100K reads/1K writes-day; **R2 10GB/1M Class-A ops-mo**; D1 5GB | Wrangler secrets | R2 (static) or Workers response | Low | **Recommended fallback / co-primary** (better for state in R2/KV/D1) |
| Val Town | Good | Generous hobby | Env vars | Val HTTP endpoint | Very low | Good lightweight option |
| Deno Deploy | Good | Generous | Env vars | Edge static | Low | Viable |
| Vercel Cron | **Hobby tier limited to daily-minimum cron** | Hobby free | Env vars | Static hosting | Low | OK if once-daily suffices |
| Fly.io / Render | Reliable | Small always-on | Secrets | Volume/static | Medium | Overkill |
| $5 VPS | Most reliable (real cron) | **$5/mo — exceeds cost target** | .env / systemd | nginx | Highest | Not recommended (cost + maintenance) |

**Recommendation: GitHub Actions on a *public* repo as primary** (unlimited free minutes, simplest secrets, trivial static publishing via Pages), scheduled ~30–40 min before the earliest possible commute to absorb cron delay, with a weekly keep-alive commit to defeat the 60-day auto-disable. **State (spaced-repetition queue) lives in the repo as JSON** committed back by the workflow. **Fallback: Cloudflare Workers + Cron Triggers with state in R2/KV** — more reliable timing and cleaner state, at the cost of slightly more setup. Because GH Actions cron can silently skip, add a **heartbeat**: the workflow pings a free dead-man's-switch (e.g. healthchecks.io) on success; a missed ping alerts you.

**Unguessable-but-fetchable URL:** publish under a path containing a 32-char random token; no directory listing. This is security-through-obscurity, adequate for a personal brief and required because Studio's browser has no auth. **Secrets:** GitHub encrypted secrets / Wrangler secrets, never in code; `.env.example` documents names only. **Failure notification:** on any exception, the pipeline (a) republishes yesterday's brief unchanged (silent-safe) and (b) sends a notification (ntfy.sh/Telegram/email via a webhook) — never crashes to an empty brief.

### §6. Spaced repetition (grounded in the literature)

**Evidence base:** Cepeda, Vul, Rohrer, Wixted & Pashler (2008), *Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention*, *Psychological Science* 19(11):1095–1102. Per the abstract: *"over 1350 individuals were taught a set of facts… The optimum gap value was about 20% of the test delay for delays of a few weeks, falling to about 5% when delay was one year"* — i.e. the **optimal inter-study gap scales with the retention interval**, so a longer retention goal warrants longer, expanding gaps. Retrieval practice / testing effect: Karpicke & Roediger (2008), *The Critical Importance of Retrieval for Learning*, *Science*; Roediger & Butler (2011). Desirable difficulties: Bjork. Takeaway for a **low-stakes, audio-only, no-input** context: use **expanding intervals** and prioritize *retrieval attempts* (ask the question, pause, then answer) over passive re-exposure.

**Recommended schedule (expanding, tuned for a ~months-long retention goal):** review an item at **days 1, 3, 7, 16, 35** after ingestion (each gap ≈ prior interval × ~2.2; consistent with the Cepeda ridgeline for a multi-week/~2-month retention target, where the optimal gap is ~10–20% of the retention interval), then retire it. This is grounded in the spacing literature rather than SM-2 folklore, and is deliberately coarse because there is no grading signal.

**No-input state machine.** Because Studio can't write back, **the pipeline owns all state** and **no user input is required for correct scheduling.** Each ingested item is enqueued with its five future review dates computed at ingestion. Every day the pipeline emits the items due that day as **self-scored retrieval prompts**: the brief poses the question, leaves a spoken pause ("…think about it…"), then gives the answer. Scheduling advances purely by calendar date, independent of whether the listener answered. **Minimal optional upgrade if input turns out possible:** if the §1 experiment shows Studio can accept a spoken/typed reply, add a lightweight "got it / missed it" capture that, if "missed," reinserts the item one interval back — strictly optional; the default works without it.

**Dosage.** Cap at **3–4 review questions/day** to avoid tedium; ratio of **~8–12 new items : 3–4 reviews** (roughly 3:1 new:review). More than ~4 reviews in an audio brief becomes a slog.

**Good vs. bad spoken recall prompts.** Good: a single specific question answerable in a sentence or two, cued to the *idea* not the headline ("Why did X argue that Y fails?"), forcing generation before the answer. Bad: yes/no questions, multi-part questions, questions requiring visual recall, or questions that leak the answer. The model is instructed (Part 2) to write open, generative, single-fact prompts with a natural pause before the answer.

### §7. Cost model (itemized)

| Component | Free-tier limit | Marginal cost at steady state | Daily | Monthly |
|---|---|---|---|---|
| Compute/orchestration (GitHub Actions, public repo) | Unlimited minutes (public) | $0 | $0 | $0 |
| Static hosting (GitHub Pages / Cloudflare R2) | Pages free; R2 10GB free | $0 | $0 | $0 |
| State storage (JSON in repo / KV) | Free | $0 | $0 | $0 |
| Feeds (arXiv, S2, LW/EA, Substack, NBER, VoxEU, GDELT, Google News RSS, culture RSS) | All free | $0 | $0 | $0 |
| LLM triage pass (Gemini 2.5 Flash-Lite; ~100K in/2K out) | AI Studio free tier | ~$0.012/day (or $0 free tier) | $0.012 | $0.36 |
| LLM editorial pass (Claude Haiku 4.5; ~30K in/6K out) | none | ~$0.06/day | $0.06 | $1.80 |
| Heartbeat/alerts (healthchecks.io, ntfy) | Free | $0 | $0 | $0 |
| X/Twitter | — | $0 (excluded by design) | $0 | $0 |
| **TOTAL (recommended)** | | | **~$0.072/day** | **~$2.16/mo** |
| **TOTAL (cheapest: Flash-Lite for both passes)** | | | **~$0.013/day** | **~$0.39/mo** |
| **TOTAL (free-tier-maximizing)** | | | **~$0.00/day** | **~$0.00/mo** |

**Is the $0.10/day ceiling met? YES.** The **recommended** config (Haiku editorial pass) is **~$0.072/day**, under the ceiling. The **cheapest viable** config (Gemini Flash-Lite for both passes) is **~$0.013/day**. The **free-tier-maximizing** config (AI Studio free tier + public-repo Actions) is effectively **$0.00/day** marginal. The only driver that could push you toward or over the ceiling is upgrading the editorial model to a mid-tier model (e.g. Gemini 3.6 Flash at $1.50/$7.50, or Claude Sonnet 5 at $2/$10) or a large jump in shortlist size — both avoidable. **Minimum achievable all-in marginal cost: ~$0.00–0.013/day.** The Spotify Premium subscription (excluded per brief; ~$12.99/mo individual, US) is the only unavoidable real cost, and it buys the Studio consumption layer.

**Caveat driving cost up over time:** Gemini 2.5 Flash-Lite retires 2026-10-16; its cheapest successor (Gemini 3.1 Flash-Lite, $0.25/$1.50) is ~2.5× the input price and 3.75× output. Even so, the recommended config stays under $0.10/day.

### §8. Failure modes and monitoring

| Failure | Detection | Response (graceful degradation) |
|---|---|---|
| Feed outage / 404 | Per-feed fetch wrapped in try/except; feed-health log | Skip that feed; continue; note in log; alert if >30% of feeds fail |
| API change (arXiv/S2/GraphQL schema) | Parse-validation test on each run | Fall back to cached items; alert |
| Model deprecation (e.g. Flash-Lite EOL 2026-10-16) | Hard-coded model IDs + a pre-EOL calendar reminder | Config flag to swap model in one line |
| LLM cost spike / runaway | Daily token budget cap (circuit breaker, e.g. $0.20/day) | Abort editorial pass, publish triage-only brief; alert |
| Studio preview changes/discontinued | Consumer-agnostic output already published (md/RSS/MP3) | Switch consumption to NotebookLM / private podcast feed / Readwise Reader |
| Studio can't read source | The 2–3-morning failure signature (§1) | Flip local-file ↔ URL; both are always published |
| Ranker quality decay (silent) | Weekly self-audit: log the kill/keep rationale; spot-check | Adjust system prompt; the prompt is versioned in-repo |
| Cron skipped/delayed (GH Actions) | Heartbeat dead-man's-switch | Alert; manual re-run; keep-alive commit prevents 60-day disable |
| Pipeline crash | Global exception handler | Republish yesterday's brief; alert |

**Consumer-agnostic fallbacks with cost (if Studio is unavailable/insufficient):**
- **Google NotebookLM Audio Overviews:** best NotebookLM-style audio, but **no self-serve consumer API** as of Aug 2026; the consumer product is manual, and only *Gemini Notebook Enterprise* has a preview audio-overview API (not free/consumer), while a standalone Podcast API is documented but **deprecated and not allowlisting new customers**. No official scheduling. Community tools (e.g. `notebooklm-podcast-automator` via Playwright) automate the UI unofficially. **Cost: $0 (manual), but no automation on the critical path.**
- **Private podcast RSS + TTS:** generate an MP3 with **OpenAI TTS ($15/1M chars for tts-1, $30/1M for tts-1-hd — ~$0.02–0.03 per 15-min brief)**, or **ElevenLabs (free tier 10,000 credits/month ≈ 10 min audio, non-commercial with attribution; Starter $5/mo for 30,000 characters with commercial rights)**, or **self-hosted open models (Kokoro/F5-TTS, ~$0 marginal on your own compute)**; publish a private RSS feed consumed by any podcast app (Apple Podcasts, Overcast, Snipd, Pocket Casts). **Cost: ~$0–5/mo.** This is the most robust Studio-independent path and should be built as a first-class optional output.
- **Readwise Reader TTS:** if you already pay for Readwise (~$8–10/mo), its text-to-speech reads the markdown; no extra build. **Cost: subscription only.**
- **Snipd:** great for podcast highlights but not a generator; use as a player for the private RSS feed.

Because the pipeline publishes markdown + an RSS item + (optionally) an MP3 every day, switching consumers is a configuration change, not a rebuild.

---

## Part 2 — The Build Prompt (paste into Cursor / Claude Code)

> **Paste everything in this block into Cursor or Claude Code. Build it in one shot. Do not ask follow-up questions; make reasonable choices where unspecified and document them in the README.**

---

**PROJECT: `daily-audio-brief` — a cloud-cron pipeline that assembles a curated daily markdown digest (plus RSS and optional MP3) for consumption by Studio by Spotify Labs or any podcast app.**

**Goals & constraints.** Single developer, one-time setup, near-zero maintenance. Runs entirely in the cloud on a schedule (laptop off). All-in marginal cost < $0.10/day; prefer free tiers. Silent-safe: on any failure, republish yesterday's brief and send a notification; never crash to empty. Secrets only via environment variables; provide `.env.example`. Include a `--dry-run` mode that produces a brief locally without publishing.

**Language & dependencies.** Python 3.12. Use: `httpx` (async HTTP + rate limiting), `feedparser` (RSS/Atom), `pydantic` (schemas), `anthropic` and `google-generativeai` (LLM SDKs), `tenacity` (retries), `rapidfuzz` or `datasketch` (dedup), `pyyaml`, `python-dotenv`, `pytest`. Justification: Python has the best feed/LLM ecosystem; these libs are stable and light. Keep everything in one repo runnable by `python -m brief.run`.

**Repo file tree (create all of these):**
```
daily-audio-brief/
├── README.md
├── .env.example
├── pyproject.toml
├── config/
│   ├── feeds.yaml             # every feed URL, category, weight, full_text flag
│   ├── authors_allowlist.yaml # ~150 researchers/labs whose papers auto-shortlist
│   ├── serendipity.yaml       # off-profile domains + their feeds
│   └── settings.yaml          # models, thresholds, counts, budget cap, timezone
├── brief/
│   ├── __init__.py
│   ├── run.py                 # entrypoint; orchestrates; handles --dry-run; global try/except
│   ├── fetch.py               # async feed fetching w/ per-source rate limits + caching
│   ├── sources/
│   │   ├── arxiv.py           # export.arxiv.org/api/query; ≤1 req/3s; cs.AI,cs.LG,cs.CY,cs.CL
│   │   ├── semantic_scholar.py# graph/v1; optional key; batch endpoints
│   │   ├── forums.py          # LessWrong/EA GraphQL + karma-thresholded RSS
│   │   ├── substack.py        # per-publication /feed
│   │   ├── econ.py            # NBER RSS/RePEc, VoxEU, IMF/Fed/BIS
│   │   ├── news.py            # GDELT DOC 2.0 + Google News RSS (non-US-centric)
│   │   └── culture.py         # LRB, n+1, Paris Review, Public Books, LitHub, Pitchfork...
│   ├── dedup.py               # normalize + near-dup detection + 14-day covered-store
│   ├── rank.py                # two-pass: Gemini triage -> Haiku editorial
│   ├── prompts.py             # THE literal system prompts (below)
│   ├── srs.py                 # spaced-repetition queue schema + scheduling
│   ├── render.py              # markdown + RSS + (optional) MP3
│   ├── publish.py             # write local file + push static URL + RSS; heartbeat; alerts
│   ├── notify.py              # ntfy/Telegram/email webhook
│   └── state/
│       ├── queue.json         # SRS queue (committed back each run)
│       └── covered.json       # rolling 14-day dedup store
├── tests/
│   ├── test_fetch.py          # feed parsing (fixtures for arXiv Atom, RSS, GraphQL)
│   ├── test_dedup.py          # near-dup + suppression
│   └── test_srs.py            # queue scheduling at days 1,3,7,16,35
└── .github/workflows/
    ├── brief.yml              # scheduled cron + keep-alive + commit state back
    └── keepalive.yml          # weekly trivial commit to defeat 60-day auto-disable
```

**Module responsibilities.** `run.py`: load config, fetch all feeds concurrently (respecting per-source rate limits), dedup, triage-rank, editorial-rank+summarize the shortlist, pull due SRS reviews, render markdown/RSS/MP3, publish, update state, heartbeat, notify on failure. `fetch.py`: async with a token-bucket per source (arXiv ≤1/3s; S2 ~1/s with key; others polite). Everything wrapped so one feed's failure never aborts the run.

**Exact endpoints, auth, rate limits.**
- arXiv: `http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CY+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=100`. **≤ 1 request every 3 seconds, single connection** (hard ToU). No auth.
- Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,abstract,authors,year,url`. No key = ~5,000 req/5 min (shared unauthenticated pool); with a free key = ~1 req/s. Put key in `S2_API_KEY` if present.
- LessWrong RSS: `https://www.lesswrong.com/feed.xml?view=frontpage&karmaThreshold=30`. EA Forum GraphQL: `POST https://forum.effectivealtruism.org/graphql`. No auth.
- Substack: `https://<pub>.substack.com/feed`. No auth. Mark `full_text: true` for confirmed full-text feeds.
- GDELT: `https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=ArtList&format=json&timespan=24h`. No auth.
- Google News RSS: `https://news.google.com/rss/search?q=<topic>&hl=en&gl=US&ceid=US:en` (also fetch non-US `ceid` for breadth). No auth.
- Handle 429/5xx with `tenacity` exponential backoff + jitter; cache last-good response per feed to disk.

**Config-driven counts/thresholds (settings.yaml defaults):** `news_slots: 6`; `idea_slots: 2`; `paper_of_day: 1`; `reviews_per_day: 4`; `triage_model: deepseek-v4-flash`; `editorial_model: deepseek-v4-pro`; `daily_budget_usd: 0.30` (circuit breaker); `timezone`; `review_intervals_days: [1,3,7,16,35]`. Commute shape: ~8 min news (including AI-as-news), ~3 min one paper, ~4 min one applicable idea, ~3 min assigned SRS only. No "read these later" list.

**THE COMPLETE RANKING/SUMMARIZATION SYSTEM PROMPTS (literal — write these verbatim into `prompts.py`):**

```
TRIAGE_SYSTEM_PROMPT = """
You are the triage editor for a daily audio brief made for one reader: a technically
capable generalist who is comfortable with machine-learning papers and economics, and
who is deliberately trying to WIDEN their range rather than narrow it. You will be given
one candidate item (title, source, abstract or excerpt, author if known). Output a single
JSON object: {"score": <float 0.0-1.0>, "category": "<one of: ai, ai_safety, econ, world,
culture, learning, serendipity>", "one_line_reason": "<=15 words"}.

Score for how much this item would CHANGE HOW A THOUGHTFUL READER THINKS, not for how
much happened or how big the headline is. Reward: a genuinely new argument, a result that
overturns a prior, a piece of analysis that reframes a question, writing with a real point
of view. Punish toward 0.0: funding rounds, product launches, company announcements, press
releases, executive hires, horse-race coverage, listicles, engagement bait, and anything
whose only claim to attention is recency or celebrity. A strong argument beats a strong
headline every time. For 'serendipity' items (from off-profile domains), score on intrinsic
interestingness to a curious generalist, NOT on relevance to the reader's usual interests.
Be harsh: most items should score below 0.4. Output only the JSON.
"""

EDITORIAL_SYSTEM_PROMPT = """
You are the editor-in-chief of an ~18 minute commute brief. The listener already does
plenty of research sitting down. This show is for things that benefit from timely audio:
news they will not otherwise read, one paper as a story, one portable idea, and retrieval
practice. Produce MARKDOWN following the schema in the user message.

TIME BUDGET (~150 words/min; ~2,700 words). If a section is thin, say so in one sentence
and give leftover words to The World or One Idea — never pad with building slideshows,
and never add a "read this later" list (their backlog is long enough).
- The World: ~8 minutes (~1,200 words). 4-7 timely developments, mixed: geopolitics,
  econ-as-news, culture being argued NOW, and AI as news (policy, labs, compute
  geopolitics, deployments). Kill funding/launch/PR. This is the spine.
- Paper of the Day: ~3 minutes (~450 words). Exactly one paper (AI, econ, or social
  science). Tell it as a story: the question, the result, the so-what. Not a methods dump.
- One Idea: ~4 minutes (~600 words). 1-2 items. A theory, mechanism, or mental model
  they can apply — in conversation, self-improvement, or their own research. Learning
  science, a sharp conceptual argument, a quote with teeth. Not a third news item.
- Quick Reviews: ~3 minutes (~450 words). ONLY the assigned spaced-repetition cards in
  DUE_REVIEWS. Do not quiz today's episode.

TASTE. Prefer items that change how the listener thinks or what they can say at lunch.
Favor non-US-centric world coverage. One idea should be useful, not merely cute.

VOICE. Write for the ear, in a car. Short sentences. Every item gets a one-sentence
"Why this matters:" line that states the stakes — not a recap.

PRONUNCIATION. First use of a non-obvious name, foreign word, or acronym gets a
bracketed hint, e.g. "Nvidia [en-VID-ee-ah]", "arXiv [archive]", "Zvi [zuh-VEE]".

REVIEWS. For each assigned card: ONE specific open question; then "…take a second…";
then a crisp answer. Never yes/no, never multi-part, never visual. If DUE_REVIEWS is
empty, say no reviews are due.

TITLE. On the line immediately after the H1:
<!-- episode_title: <5-9 word magazine-style title> -->
No date, no "Daily Brief". End with "_End of brief._" Output only the markdown.
"""
```

**MARKDOWN OUTPUT SCHEMA + FULL WORKED EXAMPLE DAY** (also embedded in `render.py` as the template the editorial model must follow):

```markdown
# Daily Brief — Tuesday, 16 June 2026

<!-- episode_title: When the map stops matching the territory -->

_Good morning. About eighteen minutes: the news you would miss, one paper as a story, one idea you can use, and reviews._

## The World

### 1. Non-Anglophone coverage of Sahel [sah-HEL] realignment
Via GDELT [GEE-delt] machine-translated sources, several West African outlets frame a security pact shift very differently from the wire services. Spend time on the local "who benefits" story, not the wire lede.
**Why this matters:** The local framing inverts the standard Western read — a reminder of how much the story depends on the desk.

### 2. Export controls as industrial policy, not just national security
Non-US coverage of a compute-control change that US wires treated as a Pentagon story.
**Why this matters:** The local frame is about who gets to train the next wave of models, not about a press conference.

### 3. An essay on the exhaustion of the autofiction novel
The London Review of Books [L-R-B] runs a long piece arguing the mode has calcified into mannerism.
**Why this matters:** A useful lens on why so much acclaimed new fiction feels the same — and what might come next.

## Paper of the Day

### Spacing effects, revisited for the AI-tutoring era
A replication extends Cepeda [seh-PEH-dah] et al.'s optimal-spacing findings to app-based review. Tell it as a story: the question they asked, the result, and the so-what. Not a methods dump.
**Why this matters:** The optimal gap scales with how long you want to remember — a directly usable rule, not folklore.

## One Idea

### Desirable difficulties, applied
A learning-science note on why slightly harder retrieval beats fluent rereading. Walk the mechanism, then how to use it: in a conversation, in your own research, or in how you study. Give this section real airtime — about four minutes — not a one-liner.
**Why this matters:** The feeling of ease is a trap: the work that feels worse in the moment is often the work that sticks.

## Quick Reviews

**Assigned.** Three days ago we covered an argument about why open-weight models can't be made safe after release. _…take a second…_ what was the core reason?
Because once weights are public, any safety fine-tuning can be cheaply stripped — the release is irreversible.

_End of brief._
```

**SPACED-REPETITION QUEUE SCHEMA + SCHEDULING (`srs.py`):**
```json
// state/queue.json — a list of item records
{
  "items": [
    {
      "id": "sha1-of-canonical-url",
      "title": "…",
      "one_line": "…",                 // the fact to be tested
      "ingested_date": "2026-06-13",
      "review_dates": ["2026-06-14","2026-06-16","2026-06-20","2026-06-29","2026-07-18"],
      "reviews_done": 0,
      "retired": false
    }
  ]
}
```
Scheduling logic: on ingestion, compute `review_dates` = ingested_date + [1,3,7,16,35] days (from settings). Each run, `due = [i for i in items if today in i.review_dates and not i.retired]`; cap at `reviews_per_day` (oldest-due first); after the last interval, set `retired=true`. Scheduling is purely date-driven and requires no user input. If input becomes available later (per the §1 experiment), add an optional `missed` flag that reinserts one interval back. Persist `queue.json` back to the repo each run.

**Deployment (`.github/workflows/brief.yml`, recommended host = GitHub Actions on a PUBLIC repo):**
```yaml
name: daily-brief
on:
  schedule:
    - cron: "20 5 * * *"    # 05:20 UTC ≈ 30-40 min before an ~06:00 local commute; ADJUST to your timezone. GH cron is best-effort (10-30+ min late); schedule early.
  workflow_dispatch: {}
permissions:
  contents: write            # to commit state back + publish to Pages
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e .
      - name: Build & publish brief
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          S2_API_KEY: ${{ secrets.S2_API_KEY }}
          PUBLISH_TOKEN: ${{ secrets.PUBLISH_TOKEN }}   # the 32-char URL path token
          NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
          HEALTHCHECK_URL: ${{ secrets.HEALTHCHECK_URL }}
        run: python -m brief.run
      - name: Commit state
        run: |
          git config user.name "brief-bot"; git config user.email "bot@local"
          git add brief/state/*.json docs/ && git commit -m "brief $(date -u +%F)" || echo "no changes"
          git push
      - name: Keep-alive heartbeat
        if: success()
        run: curl -fsS "$HEALTHCHECK_URL" || true
```
Add `keepalive.yml` (a weekly trivial commit) to defeat the 60-day auto-disable of scheduled workflows on public repos. Publish markdown to `docs/b/<PUBLISH_TOKEN>/brief-latest.md` served by GitHub Pages, and also write it to the synced-folder path if running locally.

**`--dry-run`:** `python -m brief.run --dry-run` fetches, ranks, and renders to `./out/brief-<date>.md` and prints the estimated cost, but does NOT publish, notify, or mutate `state/`.

**Tests (pytest):** `test_fetch.py` parses fixture arXiv Atom, a Substack RSS, and a GraphQL JSON response into normalized items. `test_dedup.py` asserts two near-identical titles collapse to one and a story in `covered.json` is suppressed unless flagged as a development. `test_srs.py` asserts an item ingested on D0 is due exactly on D+1,3,7,16,35, capped at `reviews_per_day`, and retires after the last.

**Structured logging & failure path:** log JSON lines (feed health, counts, token spend, cost). Global handler in `run.py`: on any unhandled exception → republish the previous `brief-latest.md` unchanged, POST to `NTFY_TOPIC`, exit 0 (so the workflow isn't marked failed but you're still alerted). Enforce `daily_budget_usd` as a circuit breaker: if projected spend exceeds it, skip the editorial pass and publish a triage-only brief with a note.

**README (setup order):** (1) fork/create a public repo; (2) `pip install -e .`; (3) copy `.env.example`→`.env`, fill keys; (4) get free keys: Gemini (AI Studio), Anthropic, optional Semantic Scholar; set a random 32-char `PUBLISH_TOKEN`; create an ntfy topic and a healthchecks.io check; (5) add all as GitHub Actions secrets; (6) enable GitHub Pages on `/docs`; (7) run `python -m brief.run --dry-run` to preview; (8) push; (9) edit `config/feeds.yaml` to taste; (10) grant Studio access to the synced folder OR point it at the Pages URL; (11) paste the Part 3 instruction into Studio.

**`.env.example`:**
```
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
S2_API_KEY=
PUBLISH_TOKEN=
NTFY_TOPIC=
HEALTHCHECK_URL=
BRIEF_TIMEZONE=Europe/Zurich
```

---

## Part 3 — The Studio-side scheduled-task prompt

Give Studio this instruction once, as a scheduled task. Keep it short and stable (Studio reads the fresh markdown each morning; all structure lives in the file). Use the **local-file** variant if you've granted folder access, or the **URL** variant otherwise. Because Studio's usage limits are undocumented and "building from scratch" / "browsing" are the most expensive operations, this instruction tells Studio to **read and voice, not research** — minimizing credit draw.

**Local-file variant:**
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
Warm, intelligent, unhurried commute-radio voice. Target 15-20 minutes.
If the file is missing or unchanged from yesterday, still produce the
episode from whatever is there and add one sentence at the start telling
me the brief may be stale.
```

**URL variant (fallback):** replace the first sentence with:
```
Every day at 6:40 AM, browse to
https://<user>.github.io/b/<PUBLISH_TOKEN>/brief-latest.md and read that
page as a finished script …
```
(Everything else identical.) Switch between variants using the failure signature in §1: if episodes go missing/stale on the local path, use the URL; if the URL won't fetch, use the local path. Both files are published daily, so switching is a one-line edit.

---

## Recommendations (staged, with thresholds)

1. **Before writing any pipeline code, run the 10-minute §1 experiment.** It settles the three undocumented unknowns (folder-permission persistence, plain-URL fetch, voice input) that determine your ingestion path. **Threshold:** if the local file reads reliably across a restart, make it primary; if not, use the URL. If voice input works, plan the optional SRS upgrade; if not (the default assumption), ship the no-input design.
2. **Build the pipeline in the free-tier-maximizing config first** (Gemini AI Studio free tier for triage, and initially for the editorial pass too), verify quality for a week, then **upgrade only the editorial pass to Claude Haiku 4.5** if editorial judgment on the shortlist disappoints. **Threshold to upgrade:** if you're manually re-editing the brief more than ~twice a week, switch the editorial model to Haiku (still ~$0.07/day, under ceiling).
3. **Ship the private-podcast-RSS + TTS output from day one, even if Studio is your primary consumer.** It is your insurance against the biggest risk (Studio preview changes or is discontinued) and costs ~$0–5/mo. **Threshold to make it primary:** if Studio's usage limits throttle a daily 15–20 min episode, or the preview ends, flip to the RSS feed in any podcast app.
4. **Do not integrate X/Twitter.** Re-evaluate only if a specific must-follow account demonstrably fails to crosspost within 48h — and then only via a single silent-fail bridge feed, never the official API.
5. **Calendar a model-migration reminder for early October 2026** (Gemini 2.5 Flash-Lite EOL 2026-10-16) and set the config fallback to `gemini-3.1-flash-lite`.
6. **Add the heartbeat and keep-alive from the start.** GitHub Actions cron silently skips and auto-disables after 60 days; these two cheap safeguards prevent the most likely "brief just stopped appearing" failure.

## Caveats
- **Studio's numeric usage limits are unverifiable** — Spotify publishes none. Whether a daily 15–20 min brief + paper deep-dive fits the research-preview allowance must be tested empirically; if it doesn't, the private-podcast-RSS fallback is unaffected.
- **Voice input and local write-back to Studio are undocumented; treated as unavailable.** The design is correct without them.
- **Studio is an invite-only research preview** (macOS, Premium 18+, 20+ markets); access is not guaranteed, and preview behavior can change without notice.
- **Several newsletter feed URLs are asserted from search results, not all individually fetched here** (Astral Codex Ten, Import AI, Transformer, Hyperdimensional, ChinaTalk). Confirmed-active: Zvi's *Don't Worry About the Vase*, Marginal Revolution, and the arXiv/Semantic Scholar/LessWrong/GDELT/NBER endpoints. The build prompt's feed-validation test flags any that don't resolve on first deploy — treat unconfirmed feeds as unverified until then.
- **LLM pricing and API terms move fast.** All prices are dated Aug 2026 from vendor/aggregator pages; re-verify against official pricing pages before deploying, especially around the Oct 2026 Gemini transition.
- **The "Pi" framework internals** (AGENTS.md persistence, JSONL sessions, four built-in tools) are drawn from Pi's own docs/community analyses and explain Studio's observed behavior, but Spotify has not documented exactly how much of Pi it exposes — treat the Pi-to-Studio mapping as informed inference, not official spec.
- **Unofficial community bug reports** about Studio (osascript entitlement, "cannot write to library") are unverified user posts, included only as weak corroboration that write paths are gated.
