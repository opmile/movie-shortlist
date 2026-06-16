import math
from dataclasses import dataclass


@dataclass
class Filme:
    """Filme do catálogo. Campos espelham o schema do aggregated.csv.

    `movie_name` (título-com-ano) é a chave de join com neighbors.csv.
    `calcular_score` é o eixo de PERSONALIDADE (polimórfico nas subclasses);
    `weighted_rating` (do ETL) é a correção de CONFIANÇA, ortogonal — não entra aqui.
    """

    movie_name: str
    title: str
    year: int | None
    genres: list[str]
    avg_rating: float
    count: int
    weighted_rating: float

    def calcular_score(self) -> float:
        return self.avg_rating

    def categoria(self) -> str:
        return "Filme"

    def exibir(self) -> str:
        ano = self.year if self.year is not None else "?"
        return (
            f"{self.title} ({ano}) — {self.categoria()} · "
            f"{self.avg_rating:.1f} ({self.count} votos)"
        )


@dataclass
class FilmeAclamado(Filme):
    def calcular_score(self) -> float:
        return self.avg_rating * 1.5

    def categoria(self) -> str:
        return "Aclamado"


@dataclass
class Blockbuster(Filme):
    def calcular_score(self) -> float:
        return self.avg_rating + math.log10(self.count)

    def categoria(self) -> str:
        return "Blockbuster"


@dataclass
class FilmeCult(Filme):
    def calcular_score(self) -> float:
        return self.avg_rating + (37 - self.count) / 37

    def categoria(self) -> str:
        return "Cult"


@dataclass
class Classico(Filme):
    def calcular_score(self) -> float:
        return self.avg_rating + (1970 - self.year) / 100

    def categoria(self) -> str:
        return "Classico"
