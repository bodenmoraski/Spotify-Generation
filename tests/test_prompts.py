"""Verbatim system prompts from brief_n_build.md."""

from brief.prompts import EDITORIAL_SYSTEM_PROMPT, TRIAGE_SYSTEM_PROMPT

TRIAGE_SNIPPET = "CHANGE HOW A THOUGHTFUL READER THINKS"
EDITORIAL_SNIPPET = "Write for the ear, not the eye."


def test_triage_prompt_is_verbatim() -> None:
    assert TRIAGE_SYSTEM_PROMPT.startswith("\nYou are the triage editor")
    assert TRIAGE_SNIPPET in TRIAGE_SYSTEM_PROMPT
    assert "Be harsh: most items should score below 0.4." in TRIAGE_SYSTEM_PROMPT
    assert 'Output only the JSON.' in TRIAGE_SYSTEM_PROMPT


def test_editorial_prompt_is_verbatim() -> None:
    assert EDITORIAL_SYSTEM_PROMPT.startswith("\nYou are the editor-in-chief")
    assert EDITORIAL_SNIPPET in EDITORIAL_SYSTEM_PROMPT
    assert "Read these three today:" in EDITORIAL_SYSTEM_PROMPT
    assert "_…take a second…_" in EDITORIAL_SYSTEM_PROMPT or "…take a second…" in EDITORIAL_SYSTEM_PROMPT
    assert "Output only the markdown." in EDITORIAL_SYSTEM_PROMPT
