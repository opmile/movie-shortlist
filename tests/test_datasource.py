import pytest

from shortlist.datasource import CSVDataSource, DataSource, JSONDataSource


def test_datasource_eh_abstrato():
    with pytest.raises(TypeError):
        DataSource()


@pytest.fixture
def fonte(request, sample_csv_path, sample_json_path):
    if request.param == "csv":
        return CSVDataSource(sample_csv_path)
    return JSONDataSource(sample_json_path)


@pytest.mark.parametrize("fonte", ["csv", "json"], indirect=True)
def test_carregar_retorna_list_dict(fonte):
    dados = fonte.carregar()
    assert isinstance(dados, list)
    assert len(dados) == 8
    assert all(isinstance(d, dict) for d in dados)


@pytest.mark.parametrize("fonte", ["csv", "json"], indirect=True)
def test_carregar_tem_chaves_do_schema(fonte):
    d = fonte.carregar()[0]
    chaves = ("Movie_Name", "title", "year", "genres", "avg_rating", "count", "weighted_rating")
    for chave in chaves:
        assert chave in d


@pytest.mark.parametrize("fonte", ["csv", "json"], indirect=True)
def test_carregar_nao_conhece_filme(fonte):
    assert all(type(d) is dict for d in fonte.carregar())
