"""Stage de collaborative filtering — raw + aggregated.csv → neighbors.csv.

Item-based: filtra filmes com count >= 37, monta matriz esparsa user×filme
(COO → CSC), cosseno por coluna (filme), top-10 vizinhos por filme. Emite
long/tidy + sim. scipy/scikit-learn vivem SÓ aqui (fora das deps do produto).
Ver notebook/data/collab-filter.md.
"""
import time

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from sklearn.metrics.pairwise import cosine_similarity

from core import OUT_DIR, THRESHOLDS, iter_raw_chunks

TOP_N = 10
MIN_COUNT = THRESHOLDS["cult_count_hi"]  # 37 (p75) — piso de sinal confiável


def run() -> pd.DataFrame:
    t0 = time.time()
    agg = pd.read_csv(OUT_DIR / "aggregated.csv")
    keep = agg.loc[agg["count"] >= MIN_COUNT, "Movie_Name"].tolist()
    movie_idx = {name: i for i, name in enumerate(keep)}
    n_movies = len(movie_idx)
    print(f"[neighbors] {n_movies:,} filmes com count>={MIN_COUNT}")

    # Single pass: acumula arrays vetorizados; fatora users no fim (sem dict por linha).
    uids, mcols, vals = [], [], []
    for c, chunk in enumerate(iter_raw_chunks()):
        m = chunk[chunk["Movie_Name"].isin(movie_idx)]
        uids.append(m["User_Id"].to_numpy())
        mcols.append(m["Movie_Name"].map(movie_idx).to_numpy())
        vals.append(m["Rating"].to_numpy(dtype=np.float32))
        print(f"  chunk {c+1:>3}: nnz={sum(len(a) for a in vals):>12,} t={time.time()-t0:>6.1f}s")

    row_idx, _ = pd.factorize(np.concatenate(uids))
    col_idx = np.concatenate(mcols)
    data = np.concatenate(vals)
    n_users = int(row_idx.max()) + 1
    X = coo_matrix((data, (row_idx, col_idx)), shape=(n_users, n_movies)).tocsc()
    print(f"[neighbors] matriz {X.shape} nnz={X.nnz:,} — cosseno...")

    S = cosine_similarity(X.T, dense_output=False).tocsr()  # filme×filme esparso

    out = []
    for i, name in enumerate(keep):
        rr = S.getrow(i)
        idx, sim = rr.indices, rr.data
        order = [j for j in np.argsort(-sim) if idx[j] != i][:TOP_N]
        for rank, j in enumerate(order, start=1):
            out.append((name, rank, keep[idx[j]], float(sim[j])))

    df = pd.DataFrame(out, columns=["Movie_Name", "rank", "vizinho", "sim"])
    df = df.sort_values(["Movie_Name", "rank"]).reset_index(drop=True)
    df.to_csv(OUT_DIR / "neighbors.csv", index=False)
    print(f"[neighbors] {len(df):,} linhas → neighbors.csv ; {time.time()-t0:.1f}s")
    return df


if __name__ == "__main__":
    run()
