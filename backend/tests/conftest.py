"""Shared test fixtures and configuration."""

import pytest
from pathlib import Path

# Define the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_fixture_path(fixtures_dir):
    """Return a sample fixture file path."""
    return fixtures_dir / "sample.json"
