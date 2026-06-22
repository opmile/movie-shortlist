import math

from shortlist.analisador import Analisador
from shortlist.catalogo import Catalogo
from shortlist.domain import Blockbuster, Classico, Filme


def _filme(cls, **kw):
    base = dict(
        movie_name="m",
        title="t",
        year=2000,
        genres=[],
        avg_rating=4.0,
        count=10,
        weighted_rating=4.0,
    )
    base.update(kw)
    return cls(**base)


def test_contagem_por_categoria_conta_subclasses():
    cat = Catalogo(
        [
            _filme(Filme),
            _filme(Filme),
            _filme(Blockbuster),
            _filme(Classico, year=1960),
        ]
    )
    assert Analisador(cat).contagem_por_categoria() == {
        "Filme": 2,
        "Blockbuster": 1,
        "Classico": 1,
    }


def test_media_por_categoria_usa_avg_rating():
    cat = Catalogo(
        [
            _filme(Filme, avg_rating=3.0),
            _filme(Filme, avg_rating=5.0),
            _filme(Blockbuster, avg_rating=4.0),
        ]
    )
    assert Analisador(cat).media_por_categoria() == {"Filme": 4.0, "Blockbuster": 4.0}


def test_distribuicao_notas_retorna_todas_as_notas():
    cat = Catalogo([_filme(Filme, avg_rating=3.0), _filme(Filme, avg_rating=4.5)])
    assert sorted(Analisador(cat).distribuicao_notas().tolist()) == [3.0, 4.5]


def test_correlacao_menos_de_dois_pontos_eh_nan():
    cat = Catalogo([_filme(Filme, year=2000, avg_rating=4.0)])
    assert math.isnan(Analisador(cat).correlacao_ano_nota())


def test_catalogo_vazio_nao_estoura():
    a = Analisador(Catalogo([]))
    assert a.contagem_por_categoria() == {}
    assert a.media_por_categoria() == {}
    assert a.distribuicao_notas().tolist() == []
    assert math.isnan(a.correlacao_ano_nota())
