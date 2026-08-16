"""Two-pass ranker: Gemini triage → editorial, with a heuristic fallback."""

from __future__ import annotations

import json
import os
import re
from datetime import date
from typing import Any

from brief.logutil import log
from brief.models import Item, Spend
from brief.prompts import EDITORIAL_SYSTEM_PROMPT, TRIAGE_SYSTEM_PROMPT

KILL_RE = re.compile(
    r"\b("
    r"funding round|series [a-d]\b|raises? \$?\d|seed round|"
    r"product launch|launches? (a|its|new)|now available|"
    r"press release|executive (hire|appointment)|appointed (ceo|cto|cfo)|"
    r"\bhired as\b|\bipo\b|horse[- ]race|listicle|"
    r"top \d+ (things|tools|startups)"
    r")\b",
    re.I,
)
BOOST_RE = re.compile(
    r"\b("
    r"argument|working paper|replication|interpretab|alignment|"
    r"causal|welfare|mechanism|theorem|proof|failure mode|"
    r"spaced repetition|retrieval practice|desirable difficult"
    r")\b",
    re.I,
)
COMMON_LAST = {
    "smith",
    "lee",
    "wang",
    "zhang",
    "li",
    "kim",
    "park",
    "singh",
    "kumar",
    "chen",
    "lin",
    "yang",
    "choi",
    "liu",
    "wu",
    "zhao",
    "john",
    "brown",
    "jones",
    "davis",
    "miller",
    "wilson",
    "martin",
    "taylor",
}

CATEGORIES = ("ai", "ai_safety", "econ", "world", "culture", "learning", "serendipity")


def resolve_model_name(name: str, settings: dict[str, Any], today: date) -> str:
    eol = settings.get("gemini_flash_lite_eol") or "2026-10-16"
    try:
        eol_date = date.fromisoformat(str(eol)[:10])
    except ValueError:
        eol_date = date(2026, 10, 16)
    if name == "gemini-2.5-flash-lite" and today >= eol_date:
        return str(settings.get("triage_model_fallback") or "gemini-3.1-flash-lite")
    return name


def _last_name(full: str) -> str:
    parts = [p for p in re.split(r"\s+", full.strip()) if p and p[0].isalpha()]
    return parts[-1].lower() if parts else ""


def allowlist_match(authors: list[str], excerpt: str, allowlist: dict[str, Any]) -> bool:
    researchers = [str(n).strip() for n in (allowlist.get("researchers") or []) if n]
    labs = [str(n).strip() for n in (allowlist.get("labs") or []) if n]
    lower_full = {n.lower() for n in researchers}
    last_counts: dict[str, int] = {}
    for n in researchers:
        last = _last_name(n)
        last_counts[last] = last_counts.get(last, 0) + 1
    distinctive = {last for last, n in last_counts.items() if n == 1 and last not in COMMON_LAST and len(last) > 3}
    for author in authors:
        al = author.lower().strip()
        if al in lower_full:
            return True
        last = _last_name(author)
        if last in distinctive:
            return True
    blob = excerpt.lower()
    for lab in labs:
        if lab.lower() in blob:
            return True
    return False


def heuristic_score(item: Item, allowlist: dict[str, Any]) -> Item:
    blob = f"{item.title} {item.excerpt}"
    score = 0.22 * min(item.weight, 1.5)
    if KILL_RE.search(blob):
        score = min(score, 0.12)
    if BOOST_RE.search(blob):
        score += 0.22
    if allowlist_match(item.authors, blob, allowlist):
        score += 0.28
        item.auto_shortlist = True
    if item.is_paper:
        score += 0.08
    if item.karma and item.karma >= 40:
        score += 0.08
    if item.is_serendipity:
        # Intrinsic interestingness proxy: longer excerpt + non-clickbait title.
        score = 0.25 + 0.15 * min(item.weight, 1.4)
        if BOOST_RE.search(blob):
            score += 0.2
        if len(item.excerpt) > 400:
            score += 0.08
    score = max(0.0, min(1.0, score))
    # Harsh: most items stay below 0.4 unless boosted.
    if score < 0.45 and not item.auto_shortlist:
        score = min(score, 0.39)
    item.score = round(score, 3)
    if not item.one_line_reason:
        if item.auto_shortlist:
            item.one_line_reason = "Allowlisted author or lab; auto-shortlist."
        elif item.is_serendipity:
            item.one_line_reason = "Off-profile candidate for the stretch slot."
        elif score >= 0.35:
            item.one_line_reason = "Heuristic: argument-shaped, not mere news."
        else:
            item.one_line_reason = "Heuristic: below the keep line."
    return item


def heuristic_triage(items: list[Item], allowlist: dict[str, Any]) -> list[Item]:
    return [heuristic_score(item, allowlist) for item in items]


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _gemini_generate(model_name: str, system: str, user: str, *, json_mode: bool) -> tuple[str, int, int]:
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY") or ""
    genai.configure(api_key=api_key)
    kwargs: dict[str, Any] = {"system_instruction": system}
    model = genai.GenerativeModel(model_name, **kwargs)
    config: dict[str, Any] = {"temperature": 0.2}
    if json_mode:
        config["response_mime_type"] = "application/json"
    response = model.generate_content(user, generation_config=config)
    text = (getattr(response, "text", None) or "").strip()
    usage = getattr(response, "usage_metadata", None)
    inp = int(getattr(usage, "prompt_token_count", 0) or 0) or _estimate_tokens(system + user)
    out = int(getattr(usage, "candidates_token_count", 0) or getattr(usage, "output_token_count", 0) or 0) or _estimate_tokens(
        text
    )
    return text, inp, out


def _anthropic_generate(model_name: str, system: str, user: str) -> tuple[str, int, int]:
    import anthropic

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model_name,
        max_tokens=8192,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(getattr(b, "text", "") for b in message.content).strip()
    inp = int(getattr(message.usage, "input_tokens", 0) or 0) or _estimate_tokens(system + user)
    out = int(getattr(message.usage, "output_tokens", 0) or 0) or _estimate_tokens(text)
    return text, inp, out


def _triage_one_gemini(item: Item, model_name: str, spend: Spend, prices: dict[str, Any]) -> Item:
    authors = ", ".join(item.authors) if item.authors else "unknown"
    user = (
        f"title: {item.title}\n"
        f"source: {item.source}\n"
        f"category_hint: {item.category}\n"
        f"author: {authors}\n"
        f"abstract_or_excerpt: {item.excerpt[:1500]}\n"
        f"serendipity: {str(item.is_serendipity).lower()}\n"
    )
    text, inp, out = _gemini_generate(model_name, TRIAGE_SYSTEM_PROMPT, user, json_mode=True)
    spend.add(model_name, inp, out, prices)
    data = _parse_json_object(text)
    score = float(data.get("score") or 0)
    item.score = max(0.0, min(1.0, score))
    cat = str(data.get("category") or item.category)
    if cat in CATEGORIES:
        item.category = cat
        item.is_serendipity = cat == "serendipity" or item.is_serendipity
    item.one_line_reason = str(data.get("one_line_reason") or item.one_line_reason)[:160]
    return item


def llm_triage(
    items: list[Item],
    settings: dict[str, Any],
    spend: Spend,
    today: date,
    allowlist: dict[str, Any],
) -> list[Item]:
    if not os.environ.get("GEMINI_API_KEY"):
        log(event="triage_heuristic", reason="no GEMINI_API_KEY")
        return heuristic_triage(items, allowlist)
    model = resolve_model_name(str(settings.get("triage_model") or "gemini-2.5-flash-lite"), settings, today)
    prices = settings.get("model_prices") or {}
    scored: list[Item] = []
    for item in items:
        try:
            scored.append(_triage_one_gemini(item, model, spend, prices))
        except Exception as exc:
            log(event="triage_item_fallback", feed_id=item.feed_id, error=str(exc))
            scored.append(heuristic_score(item, allowlist))
    return scored


def select_shortlist(
    items: list[Item],
    settings: dict[str, Any],
) -> tuple[list[Item], Item | None, list[Item]]:
    """Return (new items, paper of the day, serendipity picks)."""
    min_score = float(settings.get("shortlist_min_score") or 0.35)
    n_min = int(settings.get("new_items_min") or 8)
    n_max = int(settings.get("new_items_max") or 12)
    s_min = int(settings.get("serendipity_slots_min") or 1)
    s_max = int(settings.get("serendipity_slots_max") or 2)

    ranked = sorted(items, key=lambda i: (i.score, i.weight), reverse=True)
    papers = [i for i in ranked if i.is_paper or i.auto_shortlist]
    paper = papers[0] if papers else next((i for i in ranked if i.category in {"ai", "ai_safety"}), None)

    serendipity_pool = [i for i in ranked if i.is_serendipity or i.category == "serendipity"]
    serendipity = serendipity_pool[:s_max]
    if len(serendipity) < s_min and serendipity_pool:
        serendipity = serendipity_pool[:s_min]

    used_ids = {p.id for p in serendipity}
    if paper:
        used_ids.add(paper.id)

    # Diversity pass: take the best remaining per category, then fill.
    by_cat: dict[str, list[Item]] = {}
    for item in ranked:
        if item.id in used_ids:
            continue
        if item.score < min_score and not item.auto_shortlist:
            continue
        by_cat.setdefault(item.category, []).append(item)

    picks: list[Item] = []
    for cat in ("ai", "ai_safety", "econ", "world", "culture", "learning"):
        bucket = by_cat.get(cat) or []
        if bucket:
            picks.append(bucket[0])
            used_ids.add(bucket[0].id)
        if len(picks) >= n_max:
            break

    for item in ranked:
        if len(picks) >= n_max:
            break
        if item.id in used_ids:
            continue
        if item.score < min_score and not item.auto_shortlist:
            continue
        picks.append(item)
        used_ids.add(item.id)

    if len(picks) < n_min:
        for item in ranked:
            if len(picks) >= n_min:
                break
            if item.id in used_ids:
                continue
            picks.append(item)
            used_ids.add(item.id)

    return picks[:n_max], paper, serendipity


def projected_editorial_cost(settings: dict[str, Any], model: str) -> float:
    prices = (settings.get("model_prices") or {}).get(model) or {"input": 0.0, "output": 0.0}
    # Spec estimate: ~30K in + 6K out.
    return (30_000 / 1_000_000) * float(prices.get("input") or 0) + (6_000 / 1_000_000) * float(
        prices.get("output") or 0
    )


def editorial_pass(
    shortlist: list[Item],
    paper: Item | None,
    serendipity: list[Item],
    reviews: list[Any],
    settings: dict[str, Any],
    spend: Spend,
    today: date,
    schema_markdown: str,
    weekday: str,
) -> str | None:
    """Return editorial markdown, or None to fall back to the template renderer."""
    editorial_model = resolve_model_name(
        str(settings.get("editorial_model") or "gemini-2.5-flash-lite"), settings, today
    )
    budget = float(settings.get("daily_budget_usd") or 0.20)
    projected = spend.cost_usd + projected_editorial_cost(settings, editorial_model)
    if projected > budget:
        log(event="circuit_breaker", projected_usd=round(projected, 4), budget_usd=budget)
        return None

    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    use_anthropic = editorial_model.startswith("claude") and bool(anthropic_key)
    use_gemini = (not use_anthropic) and bool(gemini_key)
    if not use_anthropic and not use_gemini:
        log(event="editorial_heuristic", reason="no LLM keys")
        return None

    def pack(it: Item) -> dict[str, Any]:
        return {
            "id": it.id,
            "title": it.title,
            "url": it.url,
            "source": it.source,
            "category": it.category,
            "authors": it.authors,
            "score": it.score,
            "reason": it.one_line_reason,
            "excerpt": it.excerpt[:1200],
            "is_paper": it.is_paper,
        }

    reviews_blob = [
        {"title": getattr(r, "title", ""), "one_line": getattr(r, "one_line", ""), "ingested_date": getattr(r, "ingested_date", "")}
        for r in reviews
    ]
    user = (
        f"Today is {weekday}, {today.isoformat()}.\n\n"
        f"Follow this markdown schema exactly:\n\n{schema_markdown}\n\n"
        f"SHORTLIST:\n{json.dumps([pack(i) for i in shortlist], ensure_ascii=False, indent=2)}\n\n"
        f"PAPER_OF_THE_DAY:\n{json.dumps(pack(paper), ensure_ascii=False, indent=2) if paper else 'null'}\n\n"
        f"SERENDIPITY:\n{json.dumps([pack(i) for i in serendipity], ensure_ascii=False, indent=2)}\n\n"
        f"DUE_REVIEWS:\n{json.dumps(reviews_blob, ensure_ascii=False, indent=2)}\n"
    )
    prices = settings.get("model_prices") or {}
    try:
        if use_anthropic:
            text, inp, out = _anthropic_generate(editorial_model, EDITORIAL_SYSTEM_PROMPT, user)
        else:
            text, inp, out = _gemini_generate(editorial_model, EDITORIAL_SYSTEM_PROMPT, user, json_mode=False)
        spend.add(editorial_model, inp, out, prices)
        if "# Daily Brief" in text and "Read These Three Today" in text:
            return text.strip()
        log(event="editorial_schema_mismatch")
        return text.strip() or None
    except Exception as exc:
        log(event="editorial_failed", error=str(exc))
        return None


def rank(
    items: list[Item],
    settings: dict[str, Any],
    allowlist: dict[str, Any],
    reviews: list[Any],
    today: date,
    schema_markdown: str,
    weekday: str,
    spend: Spend | None = None,
) -> tuple[list[Item], Item | None, list[Item], str | None, Spend]:
    spend = spend or Spend()
    scored = llm_triage(items, settings, spend, today, allowlist)
    shortlist, paper, serendipity = select_shortlist(scored, settings)
    markdown = editorial_pass(
        shortlist, paper, serendipity, reviews, settings, spend, today, schema_markdown, weekday
    )
    log(
        event="rank_complete",
        n_in=len(items),
        n_shortlist=len(shortlist),
        n_serendipity=len(serendipity),
        has_paper=paper is not None,
        editorial=markdown is not None,
        cost_usd=round(spend.cost_usd, 5),
        tokens_in=spend.input_tokens,
        tokens_out=spend.output_tokens,
    )
    return shortlist, paper, serendipity, markdown, spend
