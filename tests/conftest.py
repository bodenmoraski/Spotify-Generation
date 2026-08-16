from pathlib import Path

import pytest

from brief.config import load_settings

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _blank_llm_keys(monkeypatch) -> None:
    """Keep pytest off the real .env keys so dry-run never hits the network."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def settings() -> dict:
    return load_settings()


@pytest.fixture
def sample_feed() -> dict:
    return {
        "id": "test",
        "type": "rss",
        "category": "ai",
        "weight": 1.0,
        "source": "Test",
    }
