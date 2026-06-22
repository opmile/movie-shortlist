"""Strategy pattern — recomendação por estratégias intercambiáveis.

Mesmo contrato (recomendar), algoritmos diferentes: filtro, sort por chave, lookup
de vizinhos. RecomendaSimilar só consulta neighbors.csv (pré-computado no ETL) —
zero cosseno em runtime.
"""

import csv
from abc import ABC, abstractmethod

from shortlist.catalogo import Catalogo
from shortlist.domain import Filme


class Recomendador(ABC):
    @abstractmethod
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]: ...


class RecomendaPorNota(Recomendador):
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]:
        return sorted(catalogo.todos(), key=lambda f: f.weighted_rating, reverse=True)[:n]


class RecomendaPorPopularidade(Recomendador):
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]:
        return sorted(catalogo.todos(), key=lambda f: f.count, reverse=True)[:n]


class RecomendaPorGenero(Recomendador):
    def __init__(self, genero_alvo: str):
        self.genero_alvo = genero_alvo

    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]:
        cands = catalogo.filtrar_por_genero(self.genero_alvo)
        return sorted(cands, key=lambda f: f.weighted_rating, reverse=True)[:n]


class RecomendaSimilar(Recomendador):
    """
    RecomendaSimilar recebe um filme-alvo e um mapa de vizinhança pré-computado no ETL ({filme: 
    [parecidos em ordem]}), pega os n filmes mais parecidos com o alvo nesse mapa, traduz esses
    nomes nos objetos Filme do catálogo (pulando os que não existirem) e devolve a lista — puro
    lookup, zero cálculo de similaridade em runtime.
    """
    def __init__(self, titulo_alvo: str, vizinhos: dict[str, list[str]]):
        self.titulo_alvo = titulo_alvo
        self.vizinhos = vizinhos

    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]:
        nomes = self.vizinhos.get(self.titulo_alvo, [])[:n]
        por_nome = {f.movie_name: f for f in catalogo.todos()}
        return [por_nome[nome] for nome in nomes if nome in por_nome]


def carregar_vizinhos(path: str) -> dict[str, list[str]]:
    """Lê neighbors.csv (tidy: Movie_Name, rank, vizinho, sim) → dict ordenado por rank.
        Agrupa as linhas por filme acumulando tuplas (rank, vizinho), depois ordena cada grupo por rank e
        descarta o rank — devolvendo o dict {filme: [vizinhos em ordem de proximidade]} que RecomendaSimilar consome.
    """
    linhas: dict[str, list[tuple[int, str]]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            linhas.setdefault(row["Movie_Name"], []).append((int(row["rank"]), row["vizinho"]))
    return {k: [v for _, v in sorted(pares)] for k, pares in linhas.items()}
