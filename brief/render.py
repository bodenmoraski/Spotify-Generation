"""Markdown + RSS + optional MP3 rendering. Template lives here as the editorial schema."""

from __future__ import annotations

import html
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from brief.models import Item
from brief.sources import strip_html
from brief.srs import QueueItem

MARKDOWN_SCHEMA = """# Daily Brief — Tuesday, 16 June 2026

_Good morning. Here's your brief: five threads worth your attention, one paper, a stretch pick, and three quick reviews. About seventeen minutes._

## AI & AI Safety

### 1. A new argument that interpretability is hitting a wall
Researchers at Anthropic [an-THROP-ic] published an analysis arguing that current sparse-autoencoder methods plateau on frontier models.
**Why this matters:** If the argument holds, the field's main bet for "reading a model's mind" needs a rethink — this reframes what safety cases can rely on.

### 2. The comparative-advantage debate about AI and jobs, sharpened
Zvi [zuh-VEE] Mowshowitz responds to the claim that AI can only raise the value of human labor, and finds the "no such thing as technological unemployment" position proves too much.
**Why this matters:** It's the cleanest statement yet of where the economists' standard model and the AI-capabilities view actually disagree.

## Economics

### 3. A new NBER [N-B-E-R] working paper on behavioral policy
List and coauthors estimate the welfare value of "nudge" interventions across a large field sample.
**Why this matters:** It puts a number on something usually argued qualitatively, and the number is smaller than advocates assume.

## World & Geopolitics

### 4. Non-Anglophone coverage of Sahel [sah-HEL] realignment
Via GDELT [GEE-delt] machine-translated sources, several West African outlets frame a security pact shift very differently from the wire services.
**Why this matters:** The local framing inverts the standard Western read — a reminder of how much the "who benefits" story depends on the desk.

## Culture & Criticism

### 5. An essay on the exhaustion of the autofiction novel
The London Review of Books [L-R-B] runs a long piece arguing the mode has calcified into mannerism.
**Why this matters:** A useful lens on why so much acclaimed new fiction feels the same — and what might come next.

## Paper of the Day

### Spacing effects, revisited for the AI-tutoring era
A replication extends Cepeda [seh-PEH-dah] et al.'s optimal-spacing findings to app-based review.
**Why this matters:** The optimal gap scales with how long you want to remember — a directly usable rule, not folklore.

## One Stretch Pick

Here's something from outside your usual orbit: a piece on how medieval cathedral builders encoded structural knowledge in geometry, with no written engineering. Worth it for the analogy to tacit knowledge in modern ML teams.

## Quick Reviews

**1.** Three days ago we covered an argument about why open-weight models can't be made safe after release. _…take a second… what was the core reason?_
Because once weights are public, any safety fine-tuning can be cheaply stripped or overridden — the release is irreversible.

**2.** A week ago: what did the NBER paper on remote work find about productivity? _…think…_
Hybrid schedules showed no measurable productivity loss and a large retention gain.

**3.** Two weeks ago: what's the "desirable difficulties" idea? _…_
That making retrieval slightly harder — spacing, testing — improves long-term retention even though it feels worse in the moment.

## Read These Three Today
1. The Anthropic interpretability analysis — it may move the whole safety agenda.
2. Zvi on comparative advantage — the sharpest framing of the jobs debate.
3. The LRB autofiction essay — the one most likely to change a conversation.

_End of brief._
"""

PRONUNCIATIONS = {
    "arxiv": "arXiv [archive]",
    "gdelt": "GDELT [GEE-delt]",
    "nvidia": "Nvidia [en-VID-ee-ah]",
    "nber": "NBER [N-B-E-R]",
    "zvi": "Zvi [zuh-VEE]",
    "anthropic": "Anthropic [an-THROP-ic]",
    "cepeda": "Cepeda [seh-PEH-dah]",
    "sahel": "Sahel [sah-HEL]",
}


def brief_title(day: date) -> str:
    return f"Daily Brief — {day.day} {day.strftime('%B %Y')}"


_EPISODE_TITLE_RE = re.compile(r"<!--\s*episode_title:\s*(.+?)\s*-->", re.I)
_ITEM_HEADING_RE = re.compile(r"^### (?:\d+\.\s*)?(.+)$", re.M)


def extract_episode_title(markdown: str, day: date) -> str:
    """Magazine-style Spotify/RSS title. Falls back to the first item heading, then the dated title."""
    commented = _EPISODE_TITLE_RE.search(markdown or "")
    if commented:
        title = re.sub(r"\s+", " ", commented.group(1)).strip().strip("\"'")
        if 6 <= len(title) <= 80 and "daily brief" not in title.lower():
            return title
    skip = {"paper of the day", "quick reviews", "one stretch pick", "stretch picks"}
    heads = [
        re.sub(r"\s+", " ", h).strip()
        for h in _ITEM_HEADING_RE.findall(markdown or "")
        if re.sub(r"\s+", " ", h).strip().lower() not in skip
    ]
    if heads:
        first = heads[0]
        if len(first) > 72:
            first = first[:69].rsplit(" ", 1)[0] + "…"
        return first
    return brief_title(day)


def weekday_name(day: date) -> str:
    return day.strftime("%A")


def _hint_title(title: str) -> str:
    low = title.lower()
    for key, hinted in PRONUNCIATIONS.items():
        if key in low and hinted.split()[0].lower() in low:
            # Don't rewrite the whole title; render uses these at first mention in body.
            return title
    return title


def _why(item: Item) -> str:
    if item.why_this_matters:
        return item.why_this_matters
    if item.one_line_reason and "auto-shortlist" not in item.one_line_reason.lower() and not item.one_line_reason.startswith("Heuristic:"):
        return item.one_line_reason.rstrip(".") + "."
    if item.excerpt:
        first = item.excerpt.split(".")[0].strip()
        if first:
            return first[:180].rstrip() + "."
    return "It changes how a careful reader would frame the question."


def _body(item: Item) -> str:
    authors = ""
    if item.authors:
        authors = f"{item.authors[0]}"
        if len(item.authors) > 1:
            authors += " and coauthors"
        authors += " — "
    src = f"Via {item.source}. " if item.source else ""
    excerpt = item.excerpt[:400].rstrip()
    if excerpt and not excerpt.endswith("."):
        excerpt += "."
    return f"{authors}{src}{excerpt}".strip() or item.title


def _section_items(items: list[Item], cats: set[str]) -> list[Item]:
    return [i for i in items if i.category in cats]


def render_markdown(
    *,
    day: date,
    new_items: list[Item],
    paper: Item | None,
    serendipity: list[Item],
    reviews: list[QueueItem],
    editorial_markdown: str | None = None,
    triage_only: bool = False,
    note: str | None = None,
) -> str:
    """Never returns empty. Prefer the editorial model output when it looks like a brief."""
    if editorial_markdown and "# Daily Brief" in editorial_markdown:
        text = editorial_markdown.strip()
        if note:
            text = text.replace(
                "_Good morning.",
                f"_{note} Good morning.",
                1,
            )
        return text + ("\n" if not text.endswith("\n") else "")

    weekday = weekday_name(day)
    title = brief_title(day)
    n_reviews = len(reviews)
    n_stretch = len(serendipity)
    intro_bits = [
        f"{len(new_items)} thread{'s' if len(new_items) != 1 else ''} worth your attention",
        "one paper" if paper else None,
        f"{n_stretch} stretch pick{'s' if n_stretch != 1 else ''}" if n_stretch else None,
        f"{n_reviews} quick review{'s' if n_reviews != 1 else ''}" if n_reviews else None,
    ]
    intro = ", ".join(b for b in intro_bits if b) or "a quiet day"
    lines: list[str] = [
        f"# {title}",
        "",
        f"_Good morning. Here's your brief: {intro}. About fifteen to twenty minutes._",
        "",
    ]
    if note:
        lines += [f"_{note}_", ""]
    if triage_only:
        lines += [
            "_Editorial pass skipped (budget circuit breaker or no LLM keys). This is the triage-only brief._",
            "",
        ]

    numbered = 1

    def emit_group(heading: str, group: list[Item]) -> None:
        nonlocal numbered
        if not group:
            return
        lines.append(f"## {heading}")
        lines.append("")
        for item in group:
            lines.append(f"### {numbered}. {_hint_title(item.title)}")
            lines.append(_body(item))
            lines.append(f"**Why this matters:** {_why(item)}")
            if item.url:
                lines.append(f"Link: {item.url}")
            lines.append("")
            numbered += 1

    emit_group("AI & AI Safety", _section_items(new_items, {"ai", "ai_safety"}))
    emit_group("Economics", _section_items(new_items, {"econ"}))
    emit_group("World & Geopolitics", _section_items(new_items, {"world"}))
    emit_group("Culture & Criticism", _section_items(new_items, {"culture"}))
    learning = _section_items(new_items, {"learning"})
    if learning:
        emit_group("Learning", learning)
    leftover = [
        i
        for i in new_items
        if i.category not in {"ai", "ai_safety", "econ", "world", "culture", "learning", "serendipity"}
    ]
    emit_group("Also", leftover)

    lines.append("## Paper of the Day")
    lines.append("")
    if paper:
        lines.append(f"### {paper.title}")
        lines.append(_body(paper))
        lines.append(f"**Why this matters:** {_why(paper)}")
        if paper.url:
            lines.append(f"Link: {paper.url}")
    else:
        lines.append("No paper cleared the bar today. The queue will try again tomorrow.")
    lines.append("")

    heading = "One Stretch Pick" if len(serendipity) <= 1 else "Stretch Picks"
    lines.append(f"## {heading}")
    lines.append("")
    if serendipity:
        for item in serendipity:
            lines.append(
                f"Here's something from outside your usual orbit: **{item.title}**"
                + (f" ({item.source})" if item.source else "")
                + "."
            )
            lines.append(_body(item))
            lines.append(f"**Why this matters:** {_why(item)}")
            if item.url:
                lines.append(f"Link: {item.url}")
            lines.append("")
    else:
        lines.append("No stretch pick survived triage today.")
        lines.append("")

    lines.append("## Quick Reviews")
    lines.append("")
    if reviews:
        for idx, rev in enumerate(reviews, start=1):
            ingested = rev.ingested_date
            lines.append(
                f"**{idx}.** On {ingested} we covered: {rev.title}. "
                f"_…take a second…_ what was the core idea?"
            )
            lines.append(rev.one_line or "See the original item.")
            lines.append("")
    else:
        lines.append("No reviews due today.")
        lines.append("")

    lines.append("## Read These Three Today")
    top = list(new_items[:3])
    if paper and paper.id not in {t.id for t in top}:
        top = [paper] + top
        top = top[:3]
    if not top and paper:
        top = [paper]
    if not top:
        lines.append("1. Nothing cleared the keep line — treat this as a rest day.")
    else:
        for i, item in enumerate(top, start=1):
            lines.append(f"{i}. {item.title} — {_why(item)}")
    lines.append("")
    lines.append("_End of brief._")
    lines.append("")
    return "\n".join(lines)


def markdown_to_speech(markdown: str) -> str:
    text = markdown
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]", r"\1", text)  # pronunciation hints become spoken
    text = re.sub(r"^#+\\s*", "", text, flags=re.M)
    text = re.sub(r"^#+ ", "", text, flags=re.M)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^_+|_+$", "", text, flags=re.M)
    text = re.sub(r"^Link:.*$", "", text, flags=re.M)
    text = strip_html(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def render_rss(
    *,
    title: str,
    markdown: str,
    day: date,
    page_url: str,
    mp3_url: str | None = None,
    mp3_bytes: int | None = None,
    previous_items: list[dict[str, Any]] | None = None,
) -> str:
    desc = html.escape(markdown[:8000])
    guid = escape(page_url or f"brief-{day.isoformat()}")
    pub = datetime(day.year, day.month, day.day, 5, 20, tzinfo=timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    enclosure = ""
    if mp3_url:
        length = int(mp3_bytes or 0)
        enclosure = f'\n      <enclosure url="{escape(mp3_url)}" type="audio/mpeg" length="{length}" />'
    item_xml = f"""    <item>
      <title>{escape(title)}</title>
      <link>{escape(page_url)}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub}</pubDate>
      <description>{desc}</description>{enclosure}
    </item>"""
    extras = []
    for prev in (previous_items or [])[:13]:
        extras.append(
            f"""    <item>
      <title>{escape(str(prev.get('title') or ''))}</title>
      <link>{escape(str(prev.get('link') or ''))}</link>
      <guid isPermaLink="false">{escape(str(prev.get('guid') or prev.get('link') or ''))}</guid>
      <pubDate>{escape(str(prev.get('pubDate') or ''))}</pubDate>
      <description>{html.escape(str(prev.get('description') or '')[:4000])}</description>
    </item>"""
        )
    items_joined = "\n".join([item_xml, *extras])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Daily Audio Brief</title>
    <link>{escape(page_url)}</link>
    <description>Curated daily markdown brief (Studio / any podcast app).</description>
    <language>en</language>
    <lastBuildDate>{pub}</lastBuildDate>
{items_joined}
  </channel>
</rss>
"""


def maybe_tts(markdown: str, settings: dict[str, Any], dest: Path) -> Path | None:
    """Generate an MP3 if OPENAI_API_KEY is set. Returns the path or None."""
    import os

    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI()
    speech = markdown_to_speech(markdown)
    # tts-1 cap is 4096 chars; chunk if needed, concatenate via raw bytes (best-effort).
    chunks = [speech[i : i + 4000] for i in range(0, len(speech), 4000)] or [speech]
    audio = b""
    model = str(settings.get("tts_model") or "tts-1")
    voice = str(settings.get("tts_voice") or "alloy")
    for chunk in chunks:
        resp = client.audio.speech.create(model=model, voice=voice, input=chunk)
        audio += resp.content
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(audio)
    return dest


STUB_BRIEF = """# Daily Brief — unavailable

_Good morning. Today's pipeline could not assemble a new brief. This stub exists so the feed is never empty._

## Quick Reviews

No reviews available.

## Read These Three Today
1. Wait for the next successful run.

_End of brief._
"""
