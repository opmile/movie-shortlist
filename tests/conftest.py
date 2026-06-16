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


@pytest.fixture
def catalogo(sample_csv_path):
    from shortlist.catalogo import Catalogo
    from shortlist.datasource import CSVDataSource
    from shortlist.factory import FilmeFactory

    filmes = [FilmeFactory.criar(d) for d in CSVDataSource(sample_csv_path).carregar()]
    return Catalogo(filmes)
