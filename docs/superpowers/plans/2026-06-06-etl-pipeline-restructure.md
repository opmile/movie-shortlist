# ETL Pipeline Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `etl/` from numbered scratch scripts into a versioned pipeline with an importable production path (`core` + `aggregate` + `profile` + `neighbors` + `build`) and a separate `explore/` for didactic/experiment scripts, while adding the two missing cache artifacts (`weighted_rating` column + `neighbors.csv`).

**Architecture:** Two roles. **Production** = importable modules emitting committed snapshots: `core.py` (shared contracts), `aggregate.py` (raw → `aggregated.csv` + `_raw_stats.json`), `profile.py` (those two → `findings.{md,json}`, no raw pass), `neighbors.py` (raw + `aggregated.csv` → `neighbors.csv`), `build.py` (the regen runner). **Exploration** = `explore/inspect.py` + `explore/calibrate.py`, by-hand, no committed output, never in regen. The heavy raw read stays single-pass in `aggregate.py`; `profile.py` renders from facts it persisted.

**Tech Stack:** Python 3, pandas, numpy (production); scipy + scikit-learn (neighbors only, confined to `etl/`); kagglehub (raw resolution).

**Testing note (overrides skill default):** Per `CLAUDE.md`, TDD is **none** on `etl/` scripts. Tasks are write → run → inspect output → commit. Unit-level checks are used only for the pure, raw-free function `core.classify` (cheap, deterministic). Full regen needs Kaggle creds + ~1.66GB download; offline fallbacks are given where an artifact is derivable without raw.

---

## File Structure (target)

```
etl/
  core.py          # resolve_raw_csv(), THRESHOLDS, M_CONFIANCA, classify(), iter_raw_chunks()
  aggregate.py     # run(): raw → aggregated.csv (+ _raw_stats.json)
  profile.py       # run(): aggregated.csv + _raw_stats.json → findings.{md,json}
  neighbors.py     # run(): raw + aggregated.csv → neighbors.csv
  build.py         # main(): aggregate → profile → neighbors
  explore/
    inspect.py     # was 01_load_kaggle.py — didactic REPL inspection
    calibrate.py   # was 03_calibrate_classes.py — threshold/floor experiments
  aggregated.csv   # committed — 8-col schema
  neighbors.csv    # committed — tidy 4-col
  findings.md / findings.json   # committed report
  _raw_stats.json  # gitignored intermediate (aggregate → profile)
  README.md        # how to regen
```

Name mapping: `01_load_kaggle.py`→`explore/inspect.py`; `02_aggregate.py`→ split into `aggregate.py` (data) + `profile.py` (report); `03_calibrate_classes.py`→`explore/calibrate.py`; `04_neighbors.py` (never existed)→`neighbors.py`; NEW `core.py`, `build.py`.

Import model: flat modules in `etl/`. `python etl/build.py` puts `etl/` on `sys.path[0]`, so `import aggregate, profile, neighbors` and their `import core` resolve. `explore/` scripts add the parent dir to `sys.path` (2-line shim) to reach `core`.

---

### Task 1: Canonical docs + .gitignore to new structure

**Files:**
- Modify: `spec.md` (tree at 287-289, refs at 61-62, 197)
- Modify: `notebook/engineering/stack-and-tooling.md` (tree at 105-107, refs at 164)
- Modify: `notebook/data/dataset-e-etl.md` (refs at 11, 96, 148, 158, 174)
- Modify: `notebook/data/thresholds.md` (refs at 4, 59)
- Modify: `notebook/data/collab-filter.md` (ref at 237)
- Modify: `notebook/engineering/project-e-escopo.md` (ref at 25)
- Modify: `.gitignore`

- [ ] **Step 1: Sweep script-name refs in canonical docs**

Use the proven loop (zsh does NOT word-split unquoted vars; macOS sed chokes on UTF-8 → use `while read` + `perl -CSD`):

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
printf '%s\n' spec.md notebook/engineering/stack-and-tooling.md \
  notebook/data/dataset-e-etl.md notebook/data/thresholds.md \
  notebook/data/collab-filter.md notebook/engineering/project-e-escopo.md \
| while IFS= read -r f; do
    perl -CSD -i -pe '
      s/etl\/02_aggregate\.py/etl\/aggregate.py/g;
      s/etl\/04_neighbors\.py/etl\/neighbors.py/g;
      s/`04_neighbors\.py`/`neighbors.py`/g;
      s/etl\/03_calibrate_classes\.py/etl\/explore\/calibrate.py/g;
      s/etl\/01_load_kaggle\.py/etl\/explore\/inspect.py/g;
    ' "$f"
  done
grep -rn "01_load_kaggle\|02_aggregate\|03_calibrate\|04_neighbors" --include="*.md" \
  spec.md notebook/ | grep -v "^\.claude"
```
Expected: last grep prints nothing (0 stale script-name refs).

- [ ] **Step 2: Shrink the two duplicated ASCII trees to a cross-ref**

`etl/README.md` is now the canonical home for the pipeline structure (already written — the structure-of-record). So the full `etl/` tree currently duplicated in `spec.md` (lines ~287-289) and `notebook/engineering/stack-and-tooling.md` (lines ~105-107) should **collapse** to a one-line pointer, not be re-expanded. In each, replace the multi-line `etl/` tree block with a single node:

```
├── etl/                    # pipeline build-time — estrutura/uso em etl/README.md
```

Keep the surrounding tree (notebook/, src/, etc.) intact. This removes the duplication (one canonical tree, in the README) — the project's anti-sprawl discipline.

- [ ] **Step 3: Fix the regen-command prose**

`notebook/data/dataset-e-etl.md:158` — change `python etl/aggregate.py reproduz aggregated.csv` to `python etl/build.py regenera aggregated.csv + neighbors.csv`. `notebook/engineering/stack-and-tooling.md:164` — change `regeneração via etl/aggregate.py` to `regeneração via etl/build.py`.

- [ ] **Step 4: Note the code-home for thresholds**

In `notebook/data/thresholds.md`, after the canonical table, add one line: `Os mesmos números vivem em código em \`etl/core.py\` (\`THRESHOLDS\`); esta nota é a fonte canônica — não editar o dict sem refletir aqui.`

- [ ] **Step 5: gitignore the intermediate**

Add to `.gitignore` under the etl block:
```
etl/_raw_stats.json
```

- [ ] **Step 6: Commit**

`git add -A` also picks up `etl/README.md` (the canonical pipeline reference, written early as the structure-of-record).

```bash
git add -A
git commit -m "docs: add etl/README.md (canonical pipeline ref); cross-ref it from spec/notebook

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: etl/core.py — shared contracts

**Files:**
- Create: `etl/core.py`

- [ ] **Step 1: Write the module**

```python
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
```

- [ ] **Step 2: Sanity-check `classify` offline (no raw)**

The existing committed `etl/aggregated.csv` has `avg_rating, count, year`. Verify precedence runs and produces all 5 labels:

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager/etl
python3 -c "
import pandas as pd, core
df = pd.read_csv('aggregated.csv')
df['year'] = pd.to_numeric(df['year'], errors='coerce')
vc = core.classify(df).value_counts()
print(vc)
assert set(vc.index) == {'Classico','Cult','Blockbuster','Aclamado','Filme'}, vc
print('OK: 5 labels present')
"
```
Expected: a value_counts table with all 5 classes, then `OK: 5 labels present`.

- [ ] **Step 3: Commit**

```bash
git add etl/core.py
git commit -m "feat(etl): add core.py — shared raw resolution, thresholds, classify

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: etl/aggregate.py — raw → aggregated.csv (+ derived columns)

**Files:**
- Create: `etl/aggregate.py`
- Delete (after extract): `etl/02_aggregate.py` (its profiling half moves to Task 4)

- [ ] **Step 1: Write the module**

```python
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
```

- [ ] **Step 2: Remove the old script**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
rm etl/02_aggregate.py
```

- [ ] **Step 3: Offline schema verification (no raw needed)**

`title` and `weighted_rating` are 100% derivable from the existing committed `aggregated.csv` (old 6-col schema). Backfill the new 8-col schema offline so the committed snapshot matches the new contract even without Kaggle:

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager/etl
python3 -c "
import pandas as pd
from core import M_CONFIANCA
df = pd.read_csv('aggregated.csv')
df['title'] = df['Movie_Name'].str.replace(r'\s*\(\d{4}\)\$', '', regex=True)
C = float(df['avg_rating'].mean())
v, m = df['count'], M_CONFIANCA
df['weighted_rating'] = (v/(v+m))*df['avg_rating'] + (m/(v+m))*C
df = df[['Movie_Name','title','year','genres','sum_rating','count','avg_rating','weighted_rating']]
df.to_csv('aggregated.csv', index=False)
# sanity: a 1-vote 5.0 film must be pulled toward C
hi = df[(df['count']==1) & (df['avg_rating']==5.0)]
assert (hi['weighted_rating'] < 3.5).all(), 'bayesian shrinkage not applied'
print('OK schema:', list(df.columns)); print('C=%.3f' % C)
print(df[['title','count','avg_rating','weighted_rating']].head())
"
```
Expected: prints the 8 columns, `C≈3.07`, and a head sample where low-count 5.0 films show `weighted_rating` near C, not 5.0.

- [ ] **Step 4: Commit**

```bash
git add etl/aggregate.py etl/aggregated.csv
git rm etl/02_aggregate.py 2>/dev/null; git add -A etl/
git commit -m "feat(etl): aggregate.py with title + weighted_rating; 8-col aggregated.csv

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: etl/profile.py — findings from facts (no raw pass)

**Files:**
- Create: `etl/profile.py`

- [ ] **Step 1: Write the module**

Reads `aggregated.csv` + `_raw_stats.json` and renders the same `findings.{md,json}` the old `02` produced, but percentiles come from `aggregated.csv` and cardinality/anomalies from `_raw_stats.json`. Uses `core.classify` for the post-precedence counts.

```python
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

    cls = classify(df)
    class_counts = cls.value_counts().to_dict()

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

Thresholds (fonte canônica: `notebook/data/thresholds.md`): `{th}`

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
```

- [ ] **Step 2: Run offline (uses existing aggregated.csv; needs _raw_stats.json)**

`_raw_stats.json` won't exist until `aggregate.run()` does a real raw pass. For offline verification, write a stub from the known committed numbers (`findings.json` history): users=162541, ratings_total=25000095, anomalies as documented.

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager/etl
python3 -c "
import json, pandas as pd
df = pd.read_csv('aggregated.csv')
C = float(df['avg_rating'].mean())
json.dump({'users':162541,'ratings_total':25000095,
  'anomalies':{'rating_out_of_range':0,'title_no_year_rows':13495,'genre_null_rows':0},
  'global_mean_C':C,'elapsed_seconds':0.0}, open('_raw_stats.json','w'), indent=2)
"
python3 profile.py
head -20 findings.md
```
Expected: prints `[profile] findings.{md,json} ; U=162,541 M=58,958 density=0.2609%` and a findings.md head with the cardinality + distribution sections.

- [ ] **Step 3: Commit**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
git add etl/profile.py etl/findings.md etl/findings.json
git commit -m "feat(etl): profile.py renders findings from aggregated.csv + _raw_stats.json

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: etl/neighbors.py — CF → neighbors.csv

**Files:**
- Create: `etl/neighbors.py`

- [ ] **Step 1: Write the module**

```python
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
        for j in np.argsort(-sim):
            if idx[j] == i:                # pula auto-similaridade
                continue
            out.append((name, len(out) % TOP_N + 1, keep[idx[j]], float(sim[j])))
            if (len([o for o in out if o[0] == name])) >= TOP_N:
                break

    df = pd.DataFrame(out, columns=["Movie_Name", "rank", "vizinho", "sim"])
    df = df.sort_values(["Movie_Name", "rank"]).reset_index(drop=True)
    df.to_csv(OUT_DIR / "neighbors.csv", index=False)
    print(f"[neighbors] {len(df):,} linhas → neighbors.csv ; {time.time()-t0:.1f}s")
    return df


if __name__ == "__main__":
    run()
```

Note on the rank loop: the inline rank computation above is fragile. Replace the `for i, name` body with this clearer per-movie version:

```python
    out = []
    for i, name in enumerate(keep):
        rr = S.getrow(i)
        idx, sim = rr.indices, rr.data
        order = [j for j in np.argsort(-sim) if idx[j] != i][:TOP_N]
        for rank, j in enumerate(order, start=1):
            out.append((name, rank, keep[idx[j]], float(sim[j])))
```

Use this second version in the file.

- [ ] **Step 2: Offline logic smoke-test (tiny synthetic matrix, no raw)**

Verify the cosine + top-N + tidy-output shape on a 4-movie toy case:

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager/etl
python3 -c "
import numpy as np
from scipy.sparse import coo_matrix
from sklearn.metrics.pairwise import cosine_similarity
# 3 users x 4 movies; movies 0,1 co-rated alike, 2 alike-ish, 3 alone
X = coo_matrix(np.array([[5,5,0,0],[4,4,0,1],[0,0,5,0]], dtype='float32')).tocsc()
S = cosine_similarity(X.T, dense_output=False).tocsr()
rr = S.getrow(0); idx, sim = rr.indices, rr.data
order = [j for j in np.argsort(-sim) if idx[j] != 0][:2]
top = [(int(idx[j]), round(float(sim[j]),3)) for j in order]
print('top neighbors of movie 0:', top)
assert top[0][0] == 1, 'movie 1 should be most similar to movie 0'
print('OK cosine/top-N logic')
"
```
Expected: `top neighbors of movie 0: [(1, ...), ...]` then `OK cosine/top-N logic`.

- [ ] **Step 3: Commit (code only; neighbors.csv comes from regen in Task 8)**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
git add etl/neighbors.py
git commit -m "feat(etl): neighbors.py — item-based CF → tidy neighbors.csv

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: etl/build.py — regen runner

**Files:**
- Create: `etl/build.py`

- [ ] **Step 1: Write the module**

```python
"""Regenera todos os snapshots do ETL, em ordem.

    python etl/build.py

Precisa de credenciais Kaggle + ~1.66GB de download (1ª vez; depois usa cache
local do kagglehub). Avaliadores NÃO precisam rodar isto — aggregated.csv e
neighbors.csv já vêm commitados.
"""
import time

import aggregate
import neighbors
import profile


def main():
    t0 = time.time()
    for name, stage in [("aggregate", aggregate), ("profile", profile), ("neighbors", neighbors)]:
        print(f"\n=== {name} ===")
        ts = time.time()
        stage.run()
        print(f"[{name}] {time.time() - ts:.1f}s")
    print(f"\n✓ build completo em {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Import-wiring check (no run)**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
python3 -c "import ast; ast.parse(open('etl/build.py').read())" && echo "parse OK"
python3 -c "
import sys; sys.path.insert(0, 'etl')
import importlib
for mod in ['core','aggregate','profile','neighbors','build']:
    importlib.import_module(mod)
print('OK: all etl modules import')
"
```
Expected: `parse OK` then `OK: all etl modules import` (scipy/sklearn/kagglehub must be installed in the venv).

- [ ] **Step 3: Commit**

```bash
git add etl/build.py
git commit -m "feat(etl): build.py — one-command regen (aggregate → profile → neighbors)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Move explore scripts + wire to core

**Files:**
- Create: `etl/explore/inspect.py` (from `etl/01_load_kaggle.py`)
- Create: `etl/explore/calibrate.py` (from `etl/03_calibrate_classes.py`)
- Delete: `etl/01_load_kaggle.py`, `etl/03_calibrate_classes.py`

- [ ] **Step 1: Create explore/ and move inspect.py**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
mkdir -p etl/explore
git mv etl/01_load_kaggle.py etl/explore/inspect.py 2>/dev/null || mv etl/01_load_kaggle.py etl/explore/inspect.py
```
Then prepend a path shim so `import core` resolves when run as `python etl/explore/inspect.py`. Add at the very top of `etl/explore/inspect.py` (after the docstring):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # etl/ on path → import core
```
(`inspect.py` keeps its didactic kagglehub demo as-is; it does not have to use `core`.)

- [ ] **Step 2: Move calibrate.py and dedup against core**

```bash
git mv etl/03_calibrate_classes.py etl/explore/calibrate.py 2>/dev/null || mv etl/03_calibrate_classes.py etl/explore/calibrate.py
```
Replace its top (the local `TH` dict + local `classify`) with the shim + imports from `core`. The new top of `etl/explore/calibrate.py`:

```python
"""Experimento de calibração — varia o piso de count do Aclamado.

Lê etl/aggregated.csv (instantâneo, sem raw). Usa core.classify (precedência e
thresholds canônicos). Output é console — não emite artefato commitado.
Rode: python etl/explore/calibrate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # etl/ on path

import pandas as pd

from core import OUT_DIR, classify

ACLAMADO_FLOOR_CANDIDATES = [None, 6, 38, 100]


def main():
    df = pd.read_csv(OUT_DIR / "aggregated.csv")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    order = ["Classico", "Cult", "Blockbuster", "Aclamado", "Filme"]
    print(f"Total filmes: {len(df):,}\n")
    print("piso".ljust(8) + "".join(c.ljust(13) for c in order))
    for floor in ACLAMADO_FLOOR_CANDIDATES:
        vc = classify(df, aclamado_floor=floor).value_counts().to_dict()
        label = "sem" if floor is None else str(floor)
        print(label.ljust(8) + "".join(f"{vc.get(c, 0):,}".ljust(13) for c in order))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run calibrate offline (no raw)**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
python3 etl/explore/calibrate.py
```
Expected: the "piso" table with 4 rows (sem/6/38/100) and 5 class columns, counts shifting as the floor rises.

- [ ] **Step 4: Commit**

```bash
git add -A etl/
git commit -m "refactor(etl): move inspect/calibrate to explore/; calibrate uses core

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Full regen + final verification (Kaggle-gated)

**Files:**
- Modify (regenerated): `etl/aggregated.csv`, `etl/neighbors.csv`, `etl/findings.{md,json}`
- Verify (already written in Task 1): `etl/README.md`

- [ ] **Step 1: Confirm Kaggle availability**

```bash
python3 -c "import kagglehub; print(kagglehub.dataset_download('chaitanyahivlekar/large-movie-dataset'))"
```
Expected: prints a local cache path. If it errors (no creds/network), STOP the regen here — the offline backfills from Tasks 3-4 already give a valid `aggregated.csv` + `findings`; `neighbors.csv` then needs a machine with Kaggle access. Note this in the handoff and skip Steps 2-3.

- [ ] **Step 2: Run full regen**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
python3 etl/build.py
```
Expected: three `=== stage ===` blocks; aggregate ~30s, profile <1s, neighbors a few minutes; final `✓ build completo`.

- [ ] **Step 3: Verify the two contracts**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager/etl
python3 -c "
import pandas as pd
a = pd.read_csv('aggregated.csv')
assert list(a.columns) == ['Movie_Name','title','year','genres','sum_rating','count','avg_rating','weighted_rating'], a.columns
assert len(a) == 58958, len(a)
n = pd.read_csv('neighbors.csv')
assert list(n.columns) == ['Movie_Name','rank','vizinho','sim'], n.columns
assert n['rank'].between(1,10).all()
assert n['sim'].between(0,1.0001).all()
assert (n.groupby('Movie_Name')['rank'].max() <= 10).all()
print('OK contracts: aggregated', a.shape, '| neighbors', n.shape)
print(n.head())
"
```
Expected: `OK contracts: aggregated (58958, 8) | neighbors (~147000, 4)` and a tidy head sample.

- [ ] **Step 4: Verify regenerated artifacts match the README contracts**

`etl/README.md` already documents both schemas (written early, as the structure-of-record). Confirm the regen output matches what the README claims — if anything drifted, fix the README (it's canonical):

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
grep -q "Movie_Name, rank, vizinho, sim\|Movie_Name\`, \`rank\`" etl/README.md && echo "README documents neighbors schema"
# Cross-check the column lists in README's tables against Step 3's asserted columns.
# (Step 3 already asserts aggregated=8 cols and neighbors=4 cols; README must agree.)
echo "If Step 3 passed, README contracts hold. Edit etl/README.md only if a number drifted."
```
Expected: README confirmed as matching; no edit unless a documented number changed.

- [ ] **Step 5: Commit**

```bash
cd /Users/milenaoliveirapenhalves/code/python/movie-manager
git add etl/aggregated.csv etl/neighbors.csv etl/findings.md etl/findings.json
git commit -m "feat(etl): regenerate snapshots (aggregated 8-col + neighbors.csv)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- 5 items from the design: (1) `neighbors.py` → Task 5; (2) `weighted_rating` → Task 3; (3) `title` → Task 3; (4) shared module (`core.py`) → Task 2; (5) one-command regen (`build.py`) → Task 6. ✓
- Structure split (production vs explore) → Tasks 2-7. ✓
- Canonical-doc updates → Task 1 (script-name sweep + **both duplicated trees collapsed to a cross-ref**; `etl/README.md` is the single canonical pipeline reference, written early). ✓
- neighbors schema (long+sim, `Movie_Name` key) → Task 5 output + Task 8 contract check. ✓
- Single-pass tension (aggregate captures `_raw_stats.json`, profile renders) → Tasks 3-4. ✓

**Placeholder scan:** No TBD/TODO. The one fragile snippet (rank loop in Task 5 Step 1) is explicitly replaced with a clear version in the same step. ✓

**Type consistency:** `classify(df, aclamado_floor=None)` signature identical in core (Task 2), profile (Task 4), calibrate (Task 7). `run()` returns: aggregate→DataFrame, profile→dict, neighbors→DataFrame; `build.py` ignores returns. Column names `Movie_Name/title/year/genres/sum_rating/count/avg_rating/weighted_rating` and `Movie_Name/rank/vizinho/sim` consistent across Tasks 3, 5, 8. ✓

**Known constraint:** Tasks 5/8 (neighbors.csv) require Kaggle access; offline path delivers aggregated.csv + findings + all code, with neighbors.csv produced on a Kaggle-enabled machine (Task 8 Step 1 gate).
