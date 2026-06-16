import pytest

from shortlist.recomendador import (
    Recomendador,
    RecomendaPorGenero,
    RecomendaPorNota,
    RecomendaPorPopularidade,
    RecomendaSimilar,
    carregar_vizinhos,
)


def test_recomendador_eh_abstrato():
    with pytest.raises(TypeError):
        Recomendador()


def test_por_nota_ordena_por_weighted_rating(catalogo):
    top = RecomendaPorNota().recomendar(catalogo, n=3)
    notas = [f.weighted_rating for f in top]
    assert notas == sorted(notas, reverse=True)
    assert top[0].title == "Quiet Gem"


def test_por_popularidade_ordena_por_count(catalogo):
    top = RecomendaPorPopularidade().recomendar(catalogo, n=2)
    assert [f.title for f in top] == ["Big Hit", "Action Two"]


def test_por_genero_filtra_e_ordena(catalogo):
    top = RecomendaPorGenero("Drama").recomendar(catalogo, n=5)
    assert all("Drama" in f.genres for f in top)
    notas = [f.weighted_rating for f in top]
    assert notas == sorted(notas, reverse=True)


def test_similar_usa_vizinhos_em_ordem(catalogo, neighbors_csv_path):
    vizinhos = carregar_vizinhos(neighbors_csv_path)
    rec = RecomendaSimilar("Big Hit (2009)", vizinhos).recomendar(catalogo, n=5)
    assert [f.title for f in rec] == ["Action Two", "Quiet Gem"]


def test_similar_alvo_desconhecido_devolve_vazio(catalogo, neighbors_csv_path):
    vizinhos = carregar_vizinhos(neighbors_csv_path)
    assert RecomendaSimilar("Inexistente (1900)", vizinhos).recomendar(catalogo) == []


def test_carregar_vizinhos_agrupa_por_movie_name(neighbors_csv_path):
    v = carregar_vizinhos(neighbors_csv_path)
    assert v["Big Hit (2009)"] == ["Action Two (2011)", "Quiet Gem (2015)"]


@pytest.mark.parametrize("estrategia", [
    RecomendaPorNota(), RecomendaPorPopularidade(), RecomendaPorGenero("Drama"),
])
def test_estrategias_respeitam_contrato_n(catalogo, estrategia):
    assert len(estrategia.recomendar(catalogo, n=2)) <= 2
