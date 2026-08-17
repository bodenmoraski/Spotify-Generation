"""Two-pass ranker: DeepSeek (Gemini fallback) with a heuristic last resort."""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from brief.logutil import log
from brief.models import Item, Spend
from brief.prompts import EDITORIAL_SYSTEM_PROMPT, TRIAGE_SYSTEM_PROMPT

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

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

CATEGORIES = ("ai", "ai_safety", "ai_news", "econ", "world", "culture", "learning", "serendipity")

LAB_NEWS_FEEDS = {"openai_news", "anthropic_news", "deepmind_blog", "transformer"}
AI_NEWS_RE = re.compile(
    r"\b("
    r"export control|chip ban|ai act|white house|regulation|"
    r"safety institute|compute cluster|open.?weight|frontier lab|"
    r"deployment|national security.+model|model.+national security"
    r")\b",
    re.I,
)


def resolve_model_name(name: str, settings: dict[str, Any], today: date) -> str:
    eol = settings.get("gemini_flash_lite_eol") or "2026-10-16"
    try:
        eol_date = date.fromisoformat(str(eol)[:10])
    except ValueError:
        eol_date = date(2026, 10, 16)
    if name == "gemini-2.5-flash-lite" and today >= eol_date:
        return str(settings.get("gemini_eol_fallback") or "gemini-3.1-flash-lite")
    return name


def has_llm_keys() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def is_deepseek_model(name: str) -> bool:
    return name.startswith("deepseek")


def is_gemini_model(name: str) -> bool:
    return name.startswith("gemini")


def resolve_runtime(
    requested: str,
    settings: dict[str, Any],
    today: date,
    role: str,
) -> tuple[str, str] | None:
    """Pick (provider, model). DeepSeek wins when its key is set; Gemini is fallback."""
    model = resolve_model_name(requested, settings, today)
    deepseek_key = bool(os.environ.get("DEEPSEEK_API_KEY"))
    gemini_key = bool(os.environ.get("GEMINI_API_KEY"))
    if is_deepseek_model(model) and deepseek_key:
        return "deepseek", model
    if is_gemini_model(model) and gemini_key:
        return "gemini", model
    if is_deepseek_model(model) and gemini_key:
        key = "gemini_triage_fallback" if role == "triage" else "gemini_editorial_fallback"
        gem = resolve_model_name(str(settings.get(key) or "gemini-2.5-flash-lite"), settings, today)
        return "gemini", gem
    if is_gemini_model(model) and deepseek_key:
        ds = "deepseek-v4-flash" if role == "triage" else "deepseek-v4-pro"
        return "deepseek", ds
    if deepseek_key:
        return "deepseek", "deepseek-v4-flash" if role == "triage" else "deepseek-v4-pro"
    if gemini_key:
        return "gemini", resolve_model_name("gemini-2.5-flash-lite", settings, today)
    return None


def _last_name(full: str) -> str:
    parts = [p for p in re.split(r"\s+", full.strip()) if p and p[0].isalpha()]
    return parts[-1].lower() if parts else ""


def _lab_mentioned(lab: str, blob: str) -> bool:
    """Whole-token lab match. Short names like SSI/Mila must not hit 'possible'/'similar'."""
    token = lab.lower().strip()
    if not token:
        return False
    return re.search(rf"(?<!\w){re.escape(token)}(?!\w)", blob) is not None


def allowlist_match(authors: list[str], excerpt: str, allowlist: dict[str, Any]) -> bool:
    researchers = [str(n).strip() for n in (allowlist.get("researchers") or []) if n]
    labs = [str(n).strip() for n in (allowlist.get("labs") or []) if n]
    lower_full = {n.lower() for n in researchers}
    last_counts: dict[str, int] = {}
    for n in researchers:
        last = _last_name(n)
        last_counts[last] = last_counts.get(last, 0) + 1
    distinctive = {
        last for last, n in last_counts.items() if n == 1 and last not in COMMON_LAST and len(last) > 3
    }
    for author in authors:
        al = author.lower().strip()
        if al in lower_full:
            return True
        last = _last_name(author)
        if last in distinctive:
            return True
    blob = excerpt.lower()
    return any(_lab_mentioned(lab, blob) for lab in labs)


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
    if not item.why_this_matters:
        first = (item.excerpt or "").split(".")[0].strip()
        first = re.sub(r"^\s*Subscribe now\s*", "", first, flags=re.I).strip()
        if first and first.lower() not in {"subscribe now", "i", "ii", "iii"}:
            item.why_this_matters = first[:180].rstrip() + "."
        elif item.auto_shortlist:
            item.why_this_matters = "An allowlisted researcher or lab is on the byline — worth a look even before the editorial pass."
        else:
            item.why_this_matters = item.one_line_reason.rstrip(".") + "."
    return tag_ai_news(item)


def tag_ai_news(item: Item) -> Item:
    """Move lab-news / policy-shaped AI items out of the research bucket."""
    if item.is_paper or item.category == "ai_news":
        return item
    fid = (item.feed_id or "").lower()
    blob = f"{item.title} {item.excerpt}"
    if fid in LAB_NEWS_FEEDS:
        item.category = "ai_news"
        return item
    if item.category in {"ai", "ai_safety", "world"} and AI_NEWS_RE.search(blob):
        if item.category == "world" and not re.search(
            r"\b(AI|A\.I\.|artificial intelligence|LLM|language model)\b", blob, re.I
        ):
            return item
        item.category = "ai_news"
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


class LLMHttpError(Exception):
    pass


@retry(
    retry=retry_if_exception_type((LLMHttpError, httpx.TransportError, httpx.TimeoutException)),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _deepseek_generate(
    model_name: str,
    system: str,
    user: str,
    *,
    json_mode: bool,
    thinking: bool,
) -> tuple[str, int, int]:
    api_key = os.environ.get("DEEPSEEK_API_KEY") or ""
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2 if json_mode else 0.3,
        "max_tokens": 8192 if json_mode else 32768,
        "thinking": {"type": "enabled" if thinking else "disabled"},
    }
    if thinking:
        payload["thinking"]["reasoning_effort"] = "high"
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    with httpx.Client(timeout=180.0) as client:
        response = client.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
    if response.status_code in {429, 500, 502, 503, 504}:
        raise LLMHttpError(f"DeepSeek HTTP {response.status_code}: {response.text[:300]}")
    response.raise_for_status()
    data = response.json()
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    text = (message.get("content") or "").strip()
    usage = data.get("usage") or {}
    inp = int(usage.get("prompt_tokens") or 0) or _estimate_tokens(system + user)
    out = int(usage.get("completion_tokens") or 0) or _estimate_tokens(text)
    return text, inp, out


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


def generate_llm(
    provider: str,
    model_name: str,
    system: str,
    user: str,
    *,
    json_mode: bool,
    thinking: bool = False,
) -> tuple[str, int, int]:
    if provider == "deepseek":
        return _deepseek_generate(model_name, system, user, json_mode=json_mode, thinking=thinking)
    return _gemini_generate(model_name, system, user, json_mode=json_mode)


def _triage_one(item: Item, provider: str, model_name: str) -> tuple[Item, int, int]:
    authors = ", ".join(item.authors) if item.authors else "unknown"
    user = (
        f"title: {item.title}\n"
        f"source: {item.source}\n"
        f"category_hint: {item.category}\n"
        f"author: {authors}\n"
        f"abstract_or_excerpt: {item.excerpt[:1500]}\n"
        f"serendipity: {str(item.is_serendipity).lower()}\n"
    )
    text, inp, out = generate_llm(
        provider, model_name, TRIAGE_SYSTEM_PROMPT, user, json_mode=True, thinking=False
    )
    data = _parse_json_object(text)
    score = float(data.get("score") or 0)
    item.score = max(0.0, min(1.0, score))
    cat = str(data.get("category") or item.category)
    if cat in CATEGORIES:
        item.category = cat
        item.is_serendipity = cat == "serendipity" or item.is_serendipity
    item.one_line_reason = str(data.get("one_line_reason") or item.one_line_reason)[:160]
    return tag_ai_news(item), inp, out


def llm_triage(
    items: list[Item],
    settings: dict[str, Any],
    spend: Spend,
    today: date,
    allowlist: dict[str, Any],
) -> list[Item]:
    runtime = resolve_runtime(
        str(settings.get("triage_model") or "deepseek-v4-flash"), settings, today, "triage"
    )
    if runtime is None:
        log(event="triage_heuristic", reason="no DEEPSEEK_API_KEY or GEMINI_API_KEY")
        return heuristic_triage(items, allowlist)
    provider, model = runtime
    log(event="triage_backend", provider=provider, model=model)
    prices = settings.get("model_prices") or {}
    workers = max(1, int(settings.get("triage_concurrency") or 6))

    def score_one(item: Item) -> tuple[Item, int, int]:
        try:
            return _triage_one(item, provider, model)
        except Exception as exc:
            log(event="triage_item_fallback", feed_id=item.feed_id, error=str(exc))
            return heuristic_score(item, allowlist), 0, 0

    scored: list[Item] = []
    if workers == 1 or len(items) < 2:
        results = [score_one(item) for item in items]
    else:
        results = [(items[0], 0, 0)] * len(items)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(score_one, item): idx for idx, item in enumerate(items)}
            for fut in as_completed(futures):
                results[futures[fut]] = fut.result()
    for item, inp, out in results:
        if inp or out:
            spend.add(model, inp, out, prices)
        scored.append(item)
    return scored


NEWS_CATEGORIES = {"ai_news", "world", "econ", "culture"}
FILLER_SOURCE_MARKERS = ("archdaily",)


def _bucket(item: Item) -> str:
    """News is the commute spine. Papers and portable ideas are separate slots."""
    if item.is_paper:
        return "paper"
    if item.category in NEWS_CATEGORIES:
        return "news"
    return "idea"


def _is_filler_source(item: Item) -> bool:
    blob = f"{item.source or ''} {item.feed_id or ''} {item.url or ''}".lower()
    return any(marker in blob for marker in FILLER_SOURCE_MARKERS)


def _idea_sort_key(item: Item) -> tuple:
    """Prefer portable ideas over dumping leftover research posts."""
    if item.category == "learning":
        pri = 0
    elif item.is_serendipity or item.category == "serendipity":
        pri = 1
    else:
        pri = 2
    return (pri, -float(item.score or 0), -float(item.weight or 0))


def select_shortlist(
    items: list[Item],
    settings: dict[str, Any],
) -> tuple[list[Item], Item | None, list[Item]]:
    """Fill news first, then one paper and 1-2 idea slots. No architecture filler."""
    min_score = float(settings.get("shortlist_min_score") or 0.35)
    n_max = int(settings.get("new_items_max") or 8)
    news_n = int(settings.get("news_slots") or 6)
    idea_n = int(settings.get("idea_slots") or settings.get("serendipity_slots_max") or 2)

    ranked = sorted(items, key=lambda i: (i.score, i.weight), reverse=True)
    papers = [i for i in ranked if i.is_paper]
    paper = papers[0] if papers else next(
        (i for i in ranked if i.auto_shortlist and i.category in {"ai", "ai_safety"}),
        None,
    )

    used_ids = {paper.id} if paper else set()

    def source_key(it: Item) -> str:
        return (it.source or it.feed_id or it.id).lower()

    source_counts: dict[str, int] = {}
    if paper:
        source_counts[source_key(paper)] = 1

    def eligible(it: Item, *, relax: bool = False) -> bool:
        if it.id in used_ids:
            return False
        if _is_filler_source(it):
            return False
        if not relax and it.score < min_score and not it.auto_shortlist:
            return False
        cap = 4 if it.is_paper else 1
        return source_counts.get(source_key(it), 0) < cap

    def take(it: Item, dest: list[Item]) -> None:
        dest.append(it)
        used_ids.add(it.id)
        key = source_key(it)
        source_counts[key] = source_counts.get(key, 0) + 1

    def fill_news(n: int) -> list[Item]:
        out: list[Item] = []
        for it in ranked:
            if len(out) >= n:
                break
            if _bucket(it) != "news" or not eligible(it):
                continue
            take(it, out)
        if len(out) < n:
            for it in ranked:
                if len(out) >= n:
                    break
                if _bucket(it) != "news" or not eligible(it, relax=True):
                    continue
                take(it, out)
        return out

    def fill_idea(n: int) -> list[Item]:
        out: list[Item] = []
        pool = [i for i in ranked if _bucket(i) == "idea"]
        pool.sort(key=_idea_sort_key)
        for it in pool:
            if len(out) >= n:
                break
            if not eligible(it):
                continue
            take(it, out)
        if len(out) < n:
            for it in pool:
                if len(out) >= n:
                    break
                if not eligible(it, relax=True):
                    continue
                take(it, out)
        return out

    news = fill_news(news_n)
    ideas = fill_idea(idea_n)
    n_min = int(settings.get("new_items_min") or 4)
    if len(news) < n_min:
        for it in ranked:
            if len(news) >= n_min:
                break
            if _bucket(it) != "news" or not eligible(it, relax=True):
                continue
            take(it, news)
    return news[:n_max], paper, ideas


def projected_editorial_cost(settings: dict[str, Any], model: str) -> float:
    prices = (settings.get("model_prices") or {}).get(model) or {"input": 0.0, "output": 0.0}
    # Spec estimate: ~30K in + 6K out. Thinking tokens on Pro can exceed this; breaker still has headroom.
    return (30_000 / 1_000_000) * float(prices.get("input") or 0) + (6_000 / 1_000_000) * float(
        prices.get("output") or 0
    )


def editorial_word_count(markdown: str) -> int:
    text = re.sub(r"<!--.*?-->", " ", markdown or "", flags=re.S)
    text = re.sub(r"[#*_`\[\]()>-]", " ", text)
    return len(text.split())


def _looks_like_brief(text: str) -> bool:
    return "# Daily Brief" in text and "## Quick Reviews" in text and "_End of brief._" in text


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
    runtime = resolve_runtime(
        str(settings.get("editorial_model") or "deepseek-v4-pro"), settings, today, "editorial"
    )
    if runtime is None:
        log(event="editorial_heuristic", reason="no DEEPSEEK_API_KEY or GEMINI_API_KEY")
        return None
    provider, editorial_model = runtime
    budget = float(settings.get("daily_budget_usd") or 0.20)
    min_words = int(settings.get("editorial_min_words") or 2200)
    projected = spend.cost_usd + projected_editorial_cost(settings, editorial_model)
    if projected > budget:
        log(event="circuit_breaker", projected_usd=round(projected, 4), budget_usd=budget)
        return None
    log(event="editorial_backend", provider=provider, model=editorial_model)

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
        f"THE_NEWS:\n{json.dumps([pack(i) for i in shortlist], ensure_ascii=False, indent=2)}\n\n"
        f"PAPER:\n{json.dumps(pack(paper), ensure_ascii=False, indent=2) if paper else 'null'}\n\n"
        f"ONE_IDEA:\n{json.dumps([pack(i) for i in serendipity], ensure_ascii=False, indent=2)}\n\n"
        f"DUE_REVIEWS:\n{json.dumps(reviews_blob, ensure_ascii=False, indent=2)}\n"
        "Do not quiz today's episode. Do not add a read-later / 'Read these three today' list.\n"
        f"Write about {min_words + 500} words. The schema is a skeleton, not a length target.\n"
    )
    prices = settings.get("model_prices") or {}

    def generate(prompt: str) -> str | None:
        text, inp, out = generate_llm(
            provider,
            editorial_model,
            EDITORIAL_SYSTEM_PROMPT,
            prompt,
            json_mode=False,
            thinking=provider == "deepseek",
        )
        spend.add(editorial_model, inp, out, prices)
        return text.strip() or None

    try:
        text = generate(user)
        if not text:
            return None
        if not _looks_like_brief(text):
            log(event="editorial_schema_mismatch")
            return text
        n_words = editorial_word_count(text)
        if n_words >= min_words:
            log(event="editorial_length_ok", words=n_words, min_words=min_words)
            return text
        retry_projected = spend.cost_usd + projected_editorial_cost(settings, editorial_model)
        if retry_projected > budget:
            log(event="editorial_too_short", words=n_words, min_words=min_words, retry=False)
            return text
        log(event="editorial_too_short", words=n_words, min_words=min_words, retry=True)
        expand = (
            user
            + f"\n\nYour previous draft was {n_words} words. That is too short for an 18-minute "
            f"radio brief (minimum {min_words}). Expand The World and One Idea in place. "
            "Do not add sections. Do not add a read-later list. Output only the markdown.\n"
        )
        retry = generate(expand)
        if retry and _looks_like_brief(retry) and editorial_word_count(retry) >= n_words:
            log(event="editorial_retry_ok", words=editorial_word_count(retry))
            return retry
        log(event="editorial_retry_kept_first", words=n_words)
        return text
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
        editorial_words=editorial_word_count(markdown) if markdown else 0,
        cost_usd=round(spend.cost_usd, 5),
        tokens_in=spend.input_tokens,
        tokens_out=spend.output_tokens,
    )
    return shortlist, paper, serendipity, markdown, spend
