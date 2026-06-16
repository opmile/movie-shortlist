"""FilmeFactory — construtor com dispatch por precedência de thresholds.

NÃO é Factory GoF: é parse de dict + escolha de subclasse em ordem estrita.
Thresholds espelhados de etl/core.py (que não é importável em runtime — puxa
kagglehub). Fonte canônica dos números: notebook/data/thresholds.md.
"""

from shortlist.domain import Blockbuster, Classico, Filme, FilmeAclamado, FilmeCult

THRESHOLDS = {
    "aclamado_avg": 4.0,
    "aclamado_floor": 6,
    "blockbuster_count": 1508,
    "cult_count_lo": 6,
    "cult_count_hi": 37,
    "cult_avg": 3.9,
    "classico_year": 1970,
    "classico_count": 37,
}


def _parse_year(v) -> int | None:
    if v is None or v == "":
        return None
    return int(float(v))


def _parse_genres(v) -> list[str]:
    if not v:
        return []
    return str(v).split("|")


class FilmeFactory:
    @staticmethod
    def criar(d: dict) -> Filme:
        th = THRESHOLDS
        year = _parse_year(d.get("year"))
        count = int(float(d["count"]))
        avg = float(d["avg_rating"])
        campos = dict(
            # Movie_Name: casing exata da coluna do aggregated.csv (chave de join c/ neighbors)
            movie_name=d["Movie_Name"],
            title=d["title"],
            year=year,
            genres=_parse_genres(d.get("genres")),
            avg_rating=avg,
            count=count,
            weighted_rating=float(d["weighted_rating"]),
        )

        # Precedência: Classico > Cult > Blockbuster > Aclamado > Filme.
        if year is not None and year <= th["classico_year"] and count >= th["classico_count"]:
            return Classico(**campos)
        if th["cult_count_lo"] <= count <= th["cult_count_hi"] and avg >= th["cult_avg"]:
            return FilmeCult(**campos)
        if count >= th["blockbuster_count"]:
            return Blockbuster(**campos)
        if avg >= th["aclamado_avg"] and count >= th["aclamado_floor"]:
            return FilmeAclamado(**campos)
        return Filme(**campos)
