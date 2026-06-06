"""Stage de profiling/relatório — aggregated.csv + _raw_stats.json → findings.{md,json}.

Não relê o raw: percentis saem do aggregated.csv, cardinalidade/anomalias do
_raw_stats.json (capturados no single-pass do aggregate.py). Toda a apresentação
(tabelas, dimensionamento de matriz, contagens por precedência) mora aqui.
"""
import json

import numpy as np
import pandas as pd

from core import OUT_DIR, THRESHOLDS, classify

PERCENTILES = [0.10, 0.20, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
PCT_COLS = ["min", "p10", "p20", "p25", "p50", "p75", "p90", "p95", "p99", "max"]


def _pct(s: pd.Series) -> dict:
    q = s.quantile(PERCENTILES)
    d = {f"p{int(p*100)}": float(q.loc[p]) for p in PERCENTILES}
    d["min"], d["max"] = float(s.min()), float(s.max())
    return d


def run() -> dict:
    df = pd.read_csv(OUT_DIR / "aggregated.csv")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    raw = json.loads((OUT_DIR / "_raw_stats.json").read_text())

    U = raw["users"]
    M = len(df)
    ratings_total = raw["ratings_total"]
    density = ratings_total / (U * M)

    dist = {
        "avg_rating": _pct(df["avg_rating"]),
        "count_per_movie": _pct(df["count"]),
        "year": _pct(df["year"].dropna()),
    }

    class_counts = classify(df).value_counts().to_dict()

    dense_gb = U * M * 4 / 1e9
    sparse_mb = (ratings_total * 8 + (U + 1) * 4) / 1e6
    item_item_gb = M * M * 4 / 1e9

    findings = {
        "cardinality": {"users": U, "movies": M, "ratings_total": ratings_total,
                        "density_pct": round(density * 100, 4)},
        "anomalies": {**raw["anomalies"],
                      "movies_no_year": int(df["year"].isna().sum()),
                      "movies_no_genre": int(df["genres"].isna().sum())},
        "distributions": dist,
        "thresholds": THRESHOLDS,
        "global_mean_C": raw["global_mean_C"],
        "class_counts_final": class_counts,
        "matrix_sizing": {"dense_float32_gb": round(dense_gb, 3),
                          "sparse_csr_float32_mb": round(sparse_mb, 1),
                          "item_item_float32_gb": round(item_item_gb, 3)},
        "versions": {"pandas": pd.__version__, "numpy": np.__version__},
    }
    (OUT_DIR / "findings.json").write_text(json.dumps(findings, indent=2))
    (OUT_DIR / "findings.md").write_text(_render_md(findings))
    print(f"[profile] findings.{{md,json}} ; U={U:,} M={M:,} density={findings['cardinality']['density_pct']}%")
    return findings


def _row(d: dict) -> str:
    return " | ".join(f"{d[k]:.3f}" if isinstance(d[k], float) else str(d[k]) for k in PCT_COLS)


def _render_md(f: dict) -> str:
    c, an = f["cardinality"], f["anomalies"]
    d, th, cc, ms = f["distributions"], f["thresholds"], f["class_counts_final"], f["matrix_sizing"]
    order = ["Classico", "Cult", "Blockbuster", "Aclamado", "Filme"]
    return f"""# Findings — ETL data exploration

Dataset: `movies_dataset.csv` (chaitanyahivlekar/large-movie-dataset)
pandas {f["versions"]["pandas"]} / numpy {f["versions"]["numpy"]}

## 1. Cardinalidade

- Ratings total: **{c["ratings_total"]:,}**
- Users únicos: **{c["users"]:,}**
- Filmes únicos: **{c["movies"]:,}**
- Densidade da matriz user×movie: **{c["density_pct"]}%**

## 2. Distribuições agregadas

| Métrica | {" | ".join(PCT_COLS)} |
|---|{"---|" * len(PCT_COLS)}
| avg_rating | {_row(d["avg_rating"])} |
| count por filme | {_row(d["count_per_movie"])} |
| year | {_row(d["year"])} |

## 3. Anomalias

- Ratings fora de [0.5, 5.0]: **{an["rating_out_of_range"]:,}**
- Linhas com título sem ano: **{an["title_no_year_rows"]:,}**
- Linhas com gênero null: **{an["genre_null_rows"]:,}**
- Filmes únicos sem ano: **{an["movies_no_year"]:,}**
- Filmes únicos sem gênero: **{an["movies_no_genre"]:,}**

## 4. Thresholds finais aplicados (precedência Classico > Cult > Blockbuster > Aclamado > Filme)

Prior do rating bayesiano: C (média global) = **{f["global_mean_C"]:.3f}**.

| Subclasse | Filmes (pós-precedência) |
|---|---|
{chr(10).join(f"| {k} | {cc.get(k, 0):,} |" for k in order)}

Thresholds (fonte canônica: `../notebook/data/thresholds.md`): `{th}`

## 5. Matriz collaborative filtering — dimensionamento

U × M = {c["users"]:,} × {c["movies"]:,} = {c["users"] * c["movies"]:,} células

| Estratégia | RAM |
|---|---|
| Dense float32 | **{ms["dense_float32_gb"]} GB** |
| Sparse CSR float32 | **{ms["sparse_csr_float32_mb"]} MB** |
| Item-item M×M float32 | **{ms["item_item_float32_gb"]} GB** |

Densidade {c["density_pct"]}% → sparse CSR. Item-based + filtro `count ≥ 37` deixa o item×item caber. Ver `../notebook/data/collab-filter.md`.
"""


if __name__ == "__main__":
    run()
