"""Heuristic ranker + circuit breaker, no API keys."""

from __future__ import annotations

from datetime import date

from brief.config import load_allowlist
from brief.models import Item, Spend, item_id_from_url
from brief.rank import (
    allowlist_match,
    editorial_pass,
    editorial_word_count,
    heuristic_triage,
    resolve_runtime,
    select_shortlist,
)
from brief.render import MARKDOWN_SCHEMA


def _item(title: str, url: str, **kwargs) -> Item:
    return Item(id=item_id_from_url(url), title=title, url=url, **kwargs)


def test_allowlist_does_not_match_ssi_inside_possible() -> None:
    allow = load_allowlist()
    assert allowlist_match([], "this is possible in classification and confession", allow) is False
    assert allowlist_match([], "Researchers at Anthropic published an SAE paper", allow) is True
    assert allowlist_match(["Nelson Elhage"], "unrelated abstract", allow) is True


def test_heuristic_kills_funding_and_shortlists_allowlisted_author() -> None:
    allow = load_allowlist()
    junk = _item("Acme raises $40M Series B", "https://example.com/funding", excerpt="funding round and product launch")
    paper = _item(
        "Interpretability Hits a Wall",
        "https://arxiv.org/abs/2606.01234",
        authors=["Nelson Elhage"],
        excerpt="An argument that sparse autoencoders plateau.",
        is_paper=True,
        category="ai",
        weight=1.2,
    )
    scored = heuristic_triage([junk, paper], allow)
    by_title = {i.title: i for i in scored}
    assert by_title[junk.title].score < 0.2
    assert by_title[paper.title].auto_shortlist is True
    assert by_title[paper.title].score >= 0.35


def test_serendipity_force_included(settings: dict) -> None:
    items = [
        _item(
            f"World news {i}",
            f"https://news.example.com/{i}",
            category="world",
            score=0.8,
            excerpt="argument " * 20,
            source=f"Desk {i}",
        )
        for i in range(6)
    ]
    items += [
        _item(f"AI paper {i}", f"https://arxiv.org/abs/{i}", category="ai", score=0.9, excerpt="argument " * 20)
        for i in range(4)
    ]
    stretch = _item(
        "Cathedral geometry",
        "https://aeon.co/cathedral",
        category="serendipity",
        is_serendipity=True,
        score=0.5,
        source="Aeon",
        excerpt="Tacit knowledge in stone.",
    )
    items.append(stretch)
    shortlist, paper, serendipity = select_shortlist(items, settings)
    assert stretch.id in {s.id for s in serendipity}
    assert len(shortlist) >= settings["new_items_min"]
    assert all(i.category in {"ai_news", "world", "econ", "culture"} for i in shortlist)


def test_lab_news_tagged_ai_news() -> None:
    from brief.rank import tag_ai_news

    item = _item(
        "White House export controls on frontier compute",
        "https://openai.com/news/export",
        category="ai",
        feed_id="openai_news",
        excerpt="The administration tightened export controls on AI chips.",
    )
    tagged = tag_ai_news(item)
    assert tagged.category == "ai_news"


def test_shortlist_fills_news_not_architecture(settings: dict) -> None:
    items = [
        _item(
            f"Alignment argument {i}",
            f"https://www.lesswrong.com/posts/{i}",
            category="ai_safety",
            score=0.8,
            excerpt="A new argument about monitoring.",
            source="LessWrong",
        )
        for i in range(5)
    ]
    items.append(
        _item(
            "Export controls as industrial policy",
            "https://example.com/chips",
            category="ai_news",
            score=0.7,
            excerpt="Chip bans as industrial policy.",
            source="Firstpost",
        )
    )
    for i in range(5):
        items.append(
            _item(
                f"Sahel coverage {i}",
                f"https://news.example.com/sahel/{i}",
                category="world",
                score=0.75,
                excerpt="A security pact shift.",
                source=f"Desk {i}",
            )
        )
    for i in range(6):
        items.append(
            _item(
                f"Nice building {i}",
                f"https://www.archdaily.com/{i}",
                category="serendipity",
                is_serendipity=True,
                score=0.85,
                source="ArchDaily",
                excerpt="A pavilion.",
            )
        )
    shortlist, _paper, serendipity = select_shortlist(items, settings)
    assert sum(1 for i in shortlist if i.category in {"ai_news", "world", "econ", "culture"}) >= 4
    assert sum(1 for i in shortlist if i.category in {"ai", "ai_safety"}) == 0
    assert sum(1 for i in shortlist if "ArchDaily" in (i.source or "")) == 0
    assert sum(1 for i in serendipity if "ArchDaily" in (i.source or "")) == 0
    assert len(serendipity) <= settings["idea_slots"]


def test_resolve_runtime_prefers_deepseek(settings: dict, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    today = date(2026, 8, 16)
    assert resolve_runtime(settings["triage_model"], settings, today, "triage") == (
        "deepseek",
        "deepseek-v4-flash",
    )
    assert resolve_runtime(settings["editorial_model"], settings, today, "editorial") == (
        "deepseek",
        "deepseek-v4-pro",
    )


def test_resolve_runtime_falls_back_to_gemini(settings: dict, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    today = date(2026, 8, 16)
    assert resolve_runtime("deepseek-v4-flash", settings, today, "triage") == (
        "gemini",
        "gemini-2.5-flash-lite",
    )
    assert resolve_runtime("deepseek-v4-pro", settings, today, "editorial") == (
        "gemini",
        "gemini-2.5-flash-lite",
    )


def test_resolve_runtime_heuristic_without_keys(settings: dict, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert resolve_runtime("deepseek-v4-pro", settings, date(2026, 8, 16), "editorial") is None


def test_circuit_breaker_skips_editorial(settings: dict, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    spend = Spend(cost_usd=0.29)
    settings = {**settings, "daily_budget_usd": 0.30}
    md = editorial_pass(
        [],
        None,
        [],
        [],
        settings,
        spend,
        date(2026, 6, 16),
        MARKDOWN_SCHEMA,
        "Tuesday",
    )
    assert md is None


def test_deepseek_generate_json_mode_disables_thinking(monkeypatch) -> None:
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [{"message": {"content": '{"score": 0.7, "category": "ai", "one_line_reason": "ok"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }

    class FakeClient:
        def __init__(self, timeout=None):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr("brief.rank.httpx.Client", FakeClient)
    from brief.rank import _deepseek_generate

    text, inp, out = _deepseek_generate(
        "deepseek-v4-flash", "sys", "user", json_mode=True, thinking=False
    )
    assert text.startswith("{")
    assert inp == 10 and out == 5
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["json"]["model"] == "deepseek-v4-flash"
    assert captured["json"]["thinking"] == {"type": "disabled"}
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert captured["headers"]["Authorization"] == "Bearer sk-test"


def test_deepseek_editorial_enables_thinking(monkeypatch) -> None:
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [{"message": {"content": "# Daily Brief\n\n## Quick Reviews\n\n_End of brief._"}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200},
            }

    class FakeClient:
        def __init__(self, timeout=None):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr("brief.rank.httpx.Client", FakeClient)
    from brief.rank import _deepseek_generate

    _deepseek_generate("deepseek-v4-pro", "sys", "user", json_mode=False, thinking=True)
    assert captured["json"]["model"] == "deepseek-v4-pro"
    assert captured["json"]["thinking"]["type"] == "enabled"
    assert captured["json"]["thinking"]["reasoning_effort"] == "high"
    assert "response_format" not in captured["json"]


def test_editorial_retries_when_too_short(settings: dict, monkeypatch) -> None:
    calls: list[str] = []
    short = "# Daily Brief\n\n## The World\n\nx\n\n## Quick Reviews\n\nnone\n\n_End of brief._\n"
    long = short + " extra " * 2300

    def fake_generate(provider, model, system, user, *, json_mode, thinking=False):
        calls.append(user)
        text = short if len(calls) == 1 else long
        return text, 10, 20

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr("brief.rank.generate_llm", fake_generate)
    settings = {**settings, "editorial_min_words": 2200, "daily_budget_usd": 5.0}
    md = editorial_pass(
        [],
        None,
        [],
        [],
        settings,
        Spend(),
        date(2026, 8, 17),
        MARKDOWN_SCHEMA,
        "Monday",
    )
    assert len(calls) == 2
    assert "too short" in calls[1]
    assert md is not None
    assert editorial_word_count(md) >= 2200
