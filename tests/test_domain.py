import math

import pytest

from shortlist.domain import Blockbuster, Classico, Filme, FilmeAclamado, FilmeCult


def _filme(**kw):
    base = dict(
        movie_name="Quiet Gem (2015)", title="Quiet Gem", year=2015,
        genres=["Drama"], avg_rating=4.3, count=100, weighted_rating=4.1,
    )
    base.update(kw)
    return Filme(**base)


def test_filme_base_score_eh_avg_rating():
    assert _filme(avg_rating=4.3).calcular_score() == 4.3


def test_filme_base_categoria():
    assert _filme().categoria() == "Filme"


def test_filme_exibir_inclui_titulo_e_categoria():
    txt = _filme().exibir()
    assert "Quiet Gem" in txt and "Filme" in txt


def test_filme_exibir_ano_desconhecido():
    assert "?" in _filme(year=None).exibir()


def test_aclamado_score_amplifica_qualidade():
    f = FilmeAclamado(movie_name="Quiet Gem (2015)", title="Quiet Gem", year=2015,
                       genres=["Drama"], avg_rating=4.2, count=100, weighted_rating=4.1)
    assert f.calcular_score() == pytest.approx(4.2 * 1.5)
    assert f.categoria() == "Aclamado"


def test_blockbuster_score_bonus_popularidade():
    f = Blockbuster(movie_name="Big Hit (2009)", title="Big Hit", year=2009,
                    genres=["Action"], avg_rating=3.8, count=2000, weighted_rating=3.8)
    assert f.calcular_score() == pytest.approx(3.8 + math.log10(2000))
    assert f.categoria() == "Blockbuster"


def test_cult_score_bonus_nicho():
    f = FilmeCult(movie_name="Niche Cult (2001)", title="Niche Cult", year=2001,
                  genres=["Horror"], avg_rating=4.1, count=20, weighted_rating=3.7)
    assert f.calcular_score() == pytest.approx(4.1 + (37 - 20) / 37)
    assert f.categoria() == "Cult"


def test_classico_score_bonus_antiguidade():
    f = Classico(movie_name="Old Classic (1965)", title="Old Classic", year=1965,
                 genres=["Drama"], avg_rating=4.2, count=50, weighted_rating=4.0)
    assert f.calcular_score() == pytest.approx(4.2 + (1970 - 1965) / 100)
    assert f.categoria() == "Classico"


@pytest.mark.parametrize("cls,esperado", [
    (FilmeAclamado, "Aclamado"), (Blockbuster, "Blockbuster"),
    (FilmeCult, "Cult"), (Classico, "Classico"),
])
def test_subclasses_sao_filme_e_polimorficas(cls, esperado):
    from shortlist.domain import Filme
    f = cls(movie_name="X (1960)", title="X", year=1960, genres=["Drama"],
            avg_rating=4.0, count=40, weighted_rating=4.0)
    assert isinstance(f, Filme)
    assert f.categoria() == esperado
