from pathlib import Path

import pytest

from brief.config import load_settings

FIXTURES = Path(__file__).parent / "fixtures"


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
