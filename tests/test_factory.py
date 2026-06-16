import pytest

from shortlist.domain import Blockbuster, Classico, Filme, FilmeAclamado, FilmeCult
from shortlist.factory import FilmeFactory


def _d(**kw):
    base = dict(Movie_Name="X (2000)", title="X", year="2000.0", genres="Drama",
                sum_rating="0", count="10", avg_rating="3.0", weighted_rating="3.0")
    base.update({k: str(v) for k, v in kw.items()})
    return base


@pytest.mark.parametrize("dados,esperado", [
    (_d(year=1965, count=50, avg_rating=4.2), Classico),
    (_d(year=2001, count=20, avg_rating=4.1), FilmeCult),
    (_d(year=2009, count=2000, avg_rating=3.8), Blockbuster),
    (_d(year=2015, count=100, avg_rating=4.3), FilmeAclamado),
    (_d(year=2018, count=40, avg_rating=3.2), Filme),
    (_d(year=2020, count=2, avg_rating=3.5), Filme),
])
def test_factory_dispatch_por_threshold(dados, esperado):
    assert type(FilmeFactory.criar(dados)) is esperado


def test_precedencia_classico_vence_aclamado():
    f = FilmeFactory.criar(_d(year=1960, count=80, avg_rating=4.5))
    assert type(f) is Classico


def test_precedencia_cult_vence_aclamado():
    f = FilmeFactory.criar(_d(year=2005, count=20, avg_rating=4.4))
    assert type(f) is FilmeCult


def test_precedencia_classico_vence_blockbuster():
    # year≤1970 ∧ count≥1508 → Classico (decisão de design: velho+popular = clássico)
    f = FilmeFactory.criar(_d(year=1965, count=2000, avg_rating=3.8))
    assert type(f) is Classico


def test_factory_parseia_campos():
    f = FilmeFactory.criar(_d(genres="Action|Thriller", count=1600, year=2011, avg_rating=3.9))
    assert f.genres == ["Action", "Thriller"]
    assert f.year == 2011 and isinstance(f.year, int)
    assert f.count == 1600 and isinstance(f.count, int)
    assert f.weighted_rating == 3.0


def test_factory_year_vazio_vira_none():
    f = FilmeFactory.criar(_d(year=""))
    assert f.year is None
