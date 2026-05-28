# ETL pipeline — racional e implementação

**Data:** 2026-05-28
**Script:** `lab/02_aggregate.py`
**Output:** `lab/aggregated.csv` (58.958 linhas, ~3MB)
**Tempo de execução:** ~30s, pico ~500MB RAM

---

## Princípio: build-time vs run-time

**Build-time (ETL, one-shot):**
- Download do raw Kaggle (1.66GB)
- Chunked groupby pra agregação rating → filme
- Extração de `year` do título via regex
- Cálculo de stats (`avg_rating`, `count`)
- Escrita do snapshot agregado

**Run-time (produto):**
- App lê o snapshot direto
- Sem rede, sem credencial Kaggle, sem ETL
- Startup instantâneo

Padrão industrial: Airflow/dbt produzem dataset; aplicações consomem. ETL nunca corre em request path.

---

## Por que chunked groupby (e não load + groupby direto)

Load direto via `pd.read_csv(path)`:
- ~5-10 min de leitura
- ~10GB de RAM (CSV 1.66GB infla 4-7× em DataFrame por overhead de strings)
- Estoura em máquina com 16GB

Chunked groupby:
- Lê em chunks de 500k linhas
- Agrega incrementalmente em estrutura dict
- Pico ~500MB
- ~30s total

```python
acc = defaultdict(lambda: {"sum": 0.0, "count": 0, "genres": None, "year": None})
users_set = set()

for chunk in pd.read_csv(csv_path, chunksize=500_000):
    chunk["year"] = chunk["Movie_Name"].str.extract(r"\((\d{4})\)$").astype("Int64")
    users_set.update(chunk["User_Id"].unique())
    for movie, group in chunk.groupby("Movie_Name"):
        acc[movie]["sum"] += group["Rating"].sum()
        acc[movie]["count"] += len(group)
        if acc[movie]["genres"] is None:
            acc[movie]["genres"] = group["Genre"].iloc[0]
            acc[movie]["year"] = group["year"].iloc[0]
```

---

## Decisão de arquitetura: ETL fora do produto

**Alternativa rejeitada:** `KaggleDataSource` que faz download + agg em runtime.

**Problemas:**
1. Cold start de minutos
2. Credencial Kaggle exigida em todo ambiente
3. Dep de rede no startup
4. Não roda offline
5. Banca tentar rodar → trava esperando
6. Cada `streamlit run` repete pipeline

**Solução adotada:** ETL como artefato `lab/02_aggregate.py`, executado one-shot. `CSVDataSource` consome o output.

Banca: "por que ETL separado?" → "porque build-time data pipelines são padrão de mercado. Aplicações não fazem ETL no request path."

---

## Reprodutibilidade

Qualquer dev com:
1. Conta Kaggle + token
2. `pip install kagglehub[pandas-datasets] pandas`
3. Rodar `python lab/02_aggregate.py`

reproduz `aggregated.csv` em ~30s + tempo de download.

`aggregated.csv` está commitável (3MB) — incluir no repo evita exigir Kaggle pra rodar o app. Decisão pendente: commit ou .gitignore?

**Recomendação:** commitar. Banca clona repo + roda `streamlit run` em 1 minuto. Critério "rodar em ambiente limpo com 1 comando" depende disso.

---

## Anomalias capturadas no ETL

- **527 filmes sem ano detectado** (0.9%) — regex `\((\d{4})\)$` falha em títulos com formato exótico (ex: re-releases, títulos com parênteses internos). Ignoráveis.
- **0 ratings fora de [0.5, 5.0]** — dados limpos.
- **0 gêneros null** — dados limpos.

---

## O que NÃO foi feito (intencional)

- **Não normalizamos gêneros** — mantemos pipe-separated. Conversão pra lista vira responsabilidade do `Filme` no domínio.
- **Não persistimos a matriz user-item agregada** — collab filtering ficou fora do v1.
- **Não geramos parquet** — CSV é mais portável pra demo acadêmica. Trade-off de performance aceitável (3MB).
