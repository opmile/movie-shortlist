from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_csv_path() -> str:
    return str(FIXTURES / "sample.csv")


@pytest.fixture
def sample_json_path() -> str:
    return str(FIXTURES / "sample.json")


@pytest.fixture
def neighbors_csv_path() -> str:
    return str(FIXTURES / "neighbors.csv")
