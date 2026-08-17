"""Editorial and triage prompts for the news-led commute brief."""

from brief.prompts import EDITORIAL_SYSTEM_PROMPT, TRIAGE_SYSTEM_PROMPT

TRIAGE_SNIPPET = "CHANGE HOW A THOUGHTFUL READER THINKS"
EDITORIAL_SNIPPET = "Write for the ear"


def test_triage_prompt_is_verbatim() -> None:
    assert TRIAGE_SYSTEM_PROMPT.startswith("\nYou are the triage editor")
    assert TRIAGE_SNIPPET in TRIAGE_SYSTEM_PROMPT
    assert "Be harsh: most items should score below 0.4." in TRIAGE_SYSTEM_PROMPT
    assert "one idea" in TRIAGE_SYSTEM_PROMPT
    assert 'Output only the JSON.' in TRIAGE_SYSTEM_PROMPT


def test_editorial_prompt_is_commute_shaped() -> None:
    assert EDITORIAL_SYSTEM_PROMPT.startswith("\nYou are the editor-in-chief")
    assert EDITORIAL_SNIPPET in EDITORIAL_SYSTEM_PROMPT
    assert "The World" in EDITORIAL_SYSTEM_PROMPT
    assert "One Idea" in EDITORIAL_SYSTEM_PROMPT
    assert "read this" in EDITORIAL_SYSTEM_PROMPT
    assert "later" in EDITORIAL_SYSTEM_PROMPT
    assert "AI & AI Safety" not in EDITORIAL_SYSTEM_PROMPT
    assert "Read these three today:" not in EDITORIAL_SYSTEM_PROMPT
    assert "_…take a second…_" in EDITORIAL_SYSTEM_PROMPT or "…take a second…" in EDITORIAL_SYSTEM_PROMPT
    assert "Output only the markdown." in EDITORIAL_SYSTEM_PROMPT
    assert "A draft under 2,200 words" in EDITORIAL_SYSTEM_PROMPT
    assert "180-250 words" in EDITORIAL_SYSTEM_PROMPT
