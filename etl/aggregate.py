"""Stage de agregação — raw (25M ratings) → aggregated.csv (58.958 filmes).

Single-pass chunked sobre o CSV bruto. Emite o snapshot do acervo + estatísticas
raw-only (users únicos, anomalias, média global) em _raw_stats.json, pro profile.py
renderizar findings sem reler o raw. Ver notebook/data/dataset-e-etl.md.
"""
import json
import time

import pandas as pd

from core import OUT_DIR, M_CONFIANCA, iter_raw_chunks


def run() -> pd.DataFrame:
    partials = []
    users = set()
    anomalies = {"rating_out_of_range": 0, "title_no_year_rows": 0, "genre_null_rows": 0}
    total_rows = 0
    t0 = time.time()

    for i, chunk in enumerate(iter_raw_chunks()):
        total_rows += len(chunk)
        users.update(chunk["User_Id"].unique())
        anomalies["rating_out_of_range"] += int(
            ((chunk["Rating"] < 0.5) | (chunk["Rating"] > 5.0)).sum()
        )
        anomalies["genre_null_rows"] += int(chunk["Genre"].isna().sum())

        year_raw = chunk["Movie_Name"].str.extract(r"\((\d{4})\)$", expand=False)
        anomalies["title_no_year_rows"] += int(year_raw.isna().sum())
        chunk = chunk.assign(_year=pd.to_numeric(year_raw, errors="coerce"))

        agg = chunk.groupby("Movie_Name", observed=True).agg(
            sum_rating=("Rating", "sum"),
            count=("Rating", "count"),
            genres=("Genre", "first"),
            year=("_year", "first"),
        ).reset_index()
        partials.append(agg)
        print(f"  chunk {i+1:>3}: rows={total_rows:>12,} users={len(users):>9,} t={time.time()-t0:>6.1f}s")

    final = pd.concat(partials, ignore_index=True).groupby("Movie_Name", observed=True).agg(
        sum_rating=("sum_rating", "sum"),
        count=("count", "sum"),
        genres=("genres", "first"),
        year=("year", "first"),
    ).reset_index()

    final["avg_rating"] = final["sum_rating"] / final["count"]
    final["title"] = final["Movie_Name"].str.replace(r"\s*\(\d{4}\)$", "", regex=True)

    # rating bayesiano: puxa média de poucos votos pro prior global C.
    C = float(final["avg_rating"].mean())
    v, m = final["count"], M_CONFIANCA
    final["weighted_rating"] = (v / (v + m)) * final["avg_rating"] + (m / (v + m)) * C

    cols = ["Movie_Name", "title", "year", "genres",
            "sum_rating", "count", "avg_rating", "weighted_rating"]
    final = final[cols]
    final.to_csv(OUT_DIR / "aggregated.csv", index=False)

    (OUT_DIR / "_raw_stats.json").write_text(json.dumps({
        "users": len(users),
        "ratings_total": total_rows,
        "anomalies": anomalies,
        "global_mean_C": C,
        "elapsed_seconds": round(time.time() - t0, 1),
    }, indent=2))

    print(f"[aggregate] {len(final):,} filmes → aggregated.csv ; C={C:.3f} ; {time.time()-t0:.1f}s")
    return final


if __name__ == "__main__":
    run()
