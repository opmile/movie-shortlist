from shortlist.domain import Filme


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
