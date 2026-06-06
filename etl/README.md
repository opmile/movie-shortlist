# etl/ — pipeline build-time

Referência canônica do pipeline: o que cada peça faz, como os dados fluem, o que sai e como regenerar. Os docs canônicos (`spec.md`, `notebook/`) carregam o **WHAT** e o **WHY**; **a estrutura e a operação do pipeline vivem aqui** — eles cross-refam este arquivo em vez de duplicar.

## Princípio: build-time vs run-time

O trabalho pesado roda **uma vez offline** e emite snapshots estáticos (`aggregated.csv`, `neighbors.csv`). O produto só lê esses snapshots — nunca toca o raw, a rede ou o Kaggle em runtime. Por isso `scipy`/`scikit-learn`/`kagglehub` ficam **só aqui**, fora das deps do produto. Raciocínio em [`../notebook/data/dataset-e-etl.md`](../notebook/data/dataset-e-etl.md).

## Estrutura

```
etl/
  core.py          # contratos compartilhados — não tem exploração
  aggregate.py     # stage: raw → aggregated.csv (+ _raw_stats.json)
  profile.py       # stage: aggregated.csv + _raw_stats.json → findings.{md,json}
  neighbors.py     # stage: raw + aggregated.csv → neighbors.csv (CF item-based)
  build.py         # orquestra: aggregate → profile → neighbors
  explore/         # didático/experimentos — fora do regen, sem artefato commitado
    inspect.py     #   inspeção do raw via kagglehub (REPL)
    calibrate.py   #   varia piso do Aclamado sobre aggregated.csv
  aggregated.csv   # commitado — snapshot do acervo
  neighbors.csv    # commitado — vizinhos item-based
  findings.{md,json}  # commitado — profiling do dataset
  _raw_stats.json  # intermediário (aggregate → profile), gitignored
```

**Dois papéis, separados de propósito:**
- **Produção** = `core` + `aggregate` + `profile` + `neighbors`, orquestrados por `build.py`. Determinístico, emite os artefatos commitados.
- **Exploração** = `explore/`. Rodado à mão, didático, não entra no regen.

### Responsabilidade de cada módulo

| Módulo | Faz | Entrada | Saída |
|---|---|---|---|
| `core.py` | `resolve_raw_csv()` (kagglehub, path estável), `THRESHOLDS`, `M_CONFIANCA`, `classify()` (precedência), `iter_raw_chunks()` | — | — |
| `aggregate.py` | single-pass chunked: agrega 25M ratings → 58.958 filmes; deriva `title` + `weighted_rating`; captura fatos raw-only | raw CSV | `aggregated.csv`, `_raw_stats.json` |
| `profile.py` | percentis (do aggregated) + cardinalidade/anomalias (do `_raw_stats`) + dimensionamento de matriz; **não relê o raw** | `aggregated.csv`, `_raw_stats.json` | `findings.{md,json}` |
| `neighbors.py` | filtra `count ≥ 37`, monta matriz esparsa user×filme (COO→CSC), cosseno por coluna, top-10 vizinhos | raw CSV, `aggregated.csv` | `neighbors.csv` |
| `build.py` | roda os 3 stages de produção em ordem, com timing | — | os 3 artefatos |

## Fluxo de dados

```
                 ┌─────────────► aggregate.py ──┬──► aggregated.csv ──┐
   raw CSV ──────┤                              └──► _raw_stats.json ─┤
 (kagglehub,     │                                                    ├──► profile.py ──► findings.{md,json}
  1.66GB, 25M)   └─────────────► neighbors.py ◄───── aggregated.csv ──┘
                                      │  (filtro count≥37)
                                      └──► neighbors.csv
```

`profile.py` lê só os fatos que `aggregate.py` persistiu — preserva o **single-pass** sobre o raw (só `aggregate` e `neighbors` o leem; a varredura pesada da agregação é única). `neighbors.py` depende de `aggregated.csv` (pro filtro `count≥37`), por isso `build.py` roda `aggregate` antes.

## Artefatos (contratos)

### `aggregated.csv` — snapshot do acervo (58.958 filmes)

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Movie_Name` | str | título com ano (chave) |
| `title` | str | título limpo (sem `(YYYY)`) |
| `year` | Int64 | ano extraído por regex `\((\d{4})\)$` |
| `genres` | str | pipe-separated do raw |
| `sum_rating` | float | soma das notas |
| `count` | int | nº de ratings (popularidade) |
| `avg_rating` | float | `sum_rating / count` |
| `weighted_rating` | float | rating bayesiano — `(v/(v+m))·avg + (m/(v+m))·C`, `m=37`, `C`=média global. Ver [`rating-bayesiano.md`](../notebook/data/rating-bayesiano.md) |

### `neighbors.csv` — vizinhos item-based (tidy, ~147k linhas)

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Movie_Name` | str | filme-alvo (mesma chave do `aggregated.csv`) |
| `rank` | int | 1..10, ordenado por `sim` desc |
| `vizinho` | str | `Movie_Name` do filme similar |
| `sim` | float | similaridade de cosseno, `[0,1]` |

Formato **long/tidy** (não wide `vizinho_1..10`): produto carrega 1×, `groupby("Movie_Name")` → dict de `(vizinho, sim)`, lookup O(1). Decisão e trade-offs em [`collab-filter.md §8`](../notebook/data/collab-filter.md).

### `findings.{md,json}` — profiling

Cardinalidade, distribuições/percentis, anomalias, contagens por subclasse (precedência), dimensionamento da matriz CF.

## Regenerar

```bash
python etl/build.py        # aggregate → profile → neighbors
```

**Pré-requisitos** (só pra regenerar — avaliadores **não** precisam):
- Credenciais Kaggle: `~/.kaggle/kaggle.json` = `{"username","key"}` (ou env `KAGGLE_USERNAME`/`KAGGLE_KEY`).
- Deps: `pip install "kagglehub[pandas-datasets]" pandas numpy scipy scikit-learn matplotlib`.
- 1ª vez baixa ~420MB (kagglehub cacheia local depois).

Os snapshots já vêm **commitados** — `git clone` + `streamlit run` roda em 1 minuto sem Kaggle. Stages individuais: `python etl/aggregate.py`, `python etl/profile.py` (precisa do `_raw_stats.json`), `python etl/neighbors.py`.

## Thresholds

Os números (subclasses, piso bayesiano) são canônicos em [`../notebook/data/thresholds.md`](../notebook/data/thresholds.md). `core.THRESHOLDS` é o espelho em código — não editar o dict sem refletir lá.
