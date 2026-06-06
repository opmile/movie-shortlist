"""Núcleo compartilhado do pipeline ETL — contratos estáveis que vários stages usam.

Sem exploração: só o que é perigoso duplicar — resolução do raw, thresholds
finais, classificação por precedência, leitura chunked.
"""
from pathlib import Path

import kagglehub
import pandas as pd

DATASET = "chaitanyahivlekar/large-movie-dataset"
FILE = "movies_dataset.csv"

OUT_DIR = Path(__file__).parent
CHUNK_SIZE = 500_000

# Thresholds FINAIS. Fonte canônica: notebook/data/thresholds.md.
# Não editar números aqui sem refletir lá.
THRESHOLDS = {
    "aclamado_avg": 4.0,
    "aclamado_floor": 38,      # piso de count pro Aclamado (mata ruído de poucos votos)
    "blockbuster_count": 250,
    "cult_count_lo": 6,
    "cult_count_hi": 37,
    "cult_avg": 3.9,
    "classico_year": 1970,
}

# Piso de votos do rating bayesiano (p75 do count). Ver notebook/data/rating-bayesiano.md.
M_CONFIANCA = 37


def resolve_raw_csv() -> Path:
    """Resolve o CSV bruto via kagglehub (usa cache local se já baixado).
    Estável entre máquinas — não hardcodar ~/.cache/...."""
    local_dir = kagglehub.dataset_download(DATASET)
    return Path(local_dir) / FILE


def iter_raw_chunks(chunksize: int = CHUNK_SIZE):
    """Itera o CSV bruto em chunks. Single-pass: o chamador agrega incremental."""
    yield from pd.read_csv(resolve_raw_csv(), chunksize=chunksize)


def classify(df: pd.DataFrame, aclamado_floor: int | None = None) -> pd.Series:
    """Subclasse por precedência Classico > Cult > Blockbuster > Aclamado > Filme.
    Sobrescreve em ordem crescente de precedência (maior prioridade por último vence).
    Espera colunas: avg_rating, count, year.
    aclamado_floor: piso de count pro Aclamado; None usa THRESHOLDS['aclamado_floor']."""
    th = THRESHOLDS
    floor = th["aclamado_floor"] if aclamado_floor is None else aclamado_floor
    cls = pd.Series(["Filme"] * len(df), index=df.index)

    mask_aclamado = df["avg_rating"] >= th["aclamado_avg"]
    if floor is not None:
        mask_aclamado &= df["count"] >= floor
    cls[mask_aclamado] = "Aclamado"

    cls[df["count"] >= th["blockbuster_count"]] = "Blockbuster"

    mask_cult = (
        (df["count"] >= th["cult_count_lo"])
        & (df["count"] <= th["cult_count_hi"])
        & (df["avg_rating"] >= th["cult_avg"])
    )
    cls[mask_cult] = "Cult"

    cls[df["year"].notna() & (df["year"] <= th["classico_year"])] = "Classico"
    return cls
