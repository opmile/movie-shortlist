"""Analisador — encapsula pandas. Converte list[Filme] → DataFrame uma vez e
expõe métricas como tipos de domínio (dict/float). Ninguém fora vê DataFrame
(exceção pragmática: distribuicao_notas/_popularidade devolvem pd.Series,
consumidas direto pelo plot). media_/contagem_por_categoria agrupam por
categoria() — a classificação polimórfica do core reaparece na análise.
"""

import pandas as pd

from shortlist.catalogo import Catalogo


class Analisador:
    def __init__(self, catalogo: Catalogo):
        self._df = pd.DataFrame(
            [
                {
                    "categoria": f.categoria(),
                    "avg_rating": f.avg_rating,
                    "year": f.year,
                    "count": f.count,
                }
                for f in catalogo.todos()
            ],
            columns=["categoria", "avg_rating", "year", "count"],
        )

    def distribuicao_notas(self) -> pd.Series:
        return self._df["avg_rating"]

    def distribuicao_popularidade(self) -> pd.Series:
        return self._df["count"]

    def media_por_categoria(self) -> dict[str, float]:
        return self._df.groupby("categoria")["avg_rating"].mean().to_dict()

    def contagem_por_categoria(self) -> dict[str, int]:
        return self._df.groupby("categoria").size().to_dict()

    def correlacao_ano_nota(self) -> float:
        # corr precisa de ≥2 pontos com year e avg_rating presentes; menos que isso
        # é indefinido (NaN). Guardado aqui pra não vazar RuntimeWarning do numpy.
        pares = self._df[["year", "avg_rating"]].dropna()
        if len(pares) < 2:
            return float("nan")
        return float(pares["year"].corr(pares["avg_rating"]))
