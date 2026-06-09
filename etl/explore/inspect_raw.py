"""
ETL 01 — Carregamento e inspeção do dataset Kaggle via API.

Objetivo didático:
- Entender duas formas de carregar dataset via kagglehub (adapter PANDAS vs download path)
- Inspecionar schema, shape, e distribuições básicas
- Extrair informação derivada (ano embutido no título)

Rode com:
    .venv/bin/python etl/01_load_kaggle.py

Ou interativo (recomendado pra explorar):
    .venv/bin/python -i etl/01_load_kaggle.py
"""

import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
import matplotlib.pyplot as plt

DATASET = "chaitanyahivlekar/large-movie-dataset"
FILE = "movies_dataset.csv"


# ─────────────────────────────────────────────────────────────
# MÉTODO A — kagglehub PANDAS adapter (forma "idiomática" do Kaggle)
# ─────────────────────────────────────────────────────────────
# Vantagem: 1 chamada, retorna DataFrame direto.
# Desvantagem: menos controle sobre como o CSV é lido (chunks, dtypes custom, etc).
# Bom pra: prototipagem rápida.
#
# pandas_kwargs aceita os mesmos kwargs de pd.read_csv. Aqui amostro 100k linhas
# pra não travar a máquina — o CSV tem 1.66GB.

print("[A] Carregando amostra via kagglehub PANDAS adapter...")
df_sample = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    DATASET,
    FILE,
    pandas_kwargs={"nrows": 100_000},
)
print(f"    Linhas carregadas: {len(df_sample):,}")


# ─────────────────────────────────────────────────────────────
# MÉTODO B — download_path + pandas direto (mais controle)
# ─────────────────────────────────────────────────────────────
# Vantagem: você lê o arquivo como quiser — chunks, dtypes específicos, parquet, etc.
# Desvantagem: 2 passos.
# Bom pra: quando o adapter PANDAS não basta (datasets grandes, transformação custom).
#
# Como já baixamos antes, essa chamada usa cache local (instantâneo).

print("\n[B] Resolvendo path local via dataset_download...")
local_dir = kagglehub.dataset_download(DATASET)
csv_path = f"{local_dir}/{FILE}"
print(f"    Path: {csv_path}")


# ─────────────────────────────────────────────────────────────
# Inspeção de schema
# ─────────────────────────────────────────────────────────────
# Sempre rodar isso ANTES de qualquer análise. Aprendi do jeito difícil:
# assumir colunas custa tempo de debug depois.

print("\n=== SCHEMA ===")
print(df_sample.dtypes)
print(f"\nMemory footprint da amostra: {df_sample.memory_usage(deep=True).sum() / 1e6:.1f} MB")


# ─────────────────────────────────────────────────────────────
# Sample visual — 5 linhas, todas as colunas
# ─────────────────────────────────────────────────────────────

print("\n=== HEAD ===")
print(df_sample.head().to_string(max_colwidth=50))


# ─────────────────────────────────────────────────────────────
# Cardinalidade — quantos filmes e users únicos na amostra
# ─────────────────────────────────────────────────────────────
# Importante: isso é da AMOSTRA (100k linhas). Pro número real do dataset inteiro
# precisaríamos varrer o CSV completo (próxima etapa do ETL).

n_filmes = df_sample["Movie_Name"].nunique()
n_users = df_sample["User_Id"].nunique()
print("\n=== CARDINALIDADE (amostra) ===")
print(f"Filmes únicos: {n_filmes:,}")
print(f"Users únicos:  {n_users:,}")
print(f"Ratings/filme (média): {len(df_sample) / n_filmes:.1f}")


# ─────────────────────────────────────────────────────────────
# Distribuição de ratings
# ─────────────────────────────────────────────────────────────
# Datasets MovieLens-like costumam ter notas de 0.5 a 5.0 em passos de 0.5.
# Olhar a distribuição mostra se há viés (todo mundo dá 4-5? cauda longa?).

print("\n=== DISTRIBUIÇÃO DE RATINGS ===")
print(df_sample["Rating"].describe())
print("\nContagem por valor:")
print(df_sample["Rating"].value_counts().sort_index())


# Plot — histograma das notas
df_sample["Rating"].plot.hist(bins=20, edgecolor="black", title="Distribuição de ratings (amostra 100k)")
plt.xlabel("Rating")
plt.tight_layout()
plt.savefig("etl/rating_distribution.png", dpi=100)
print("\nPlot salvo em etl/rating_distribution.png")


# ─────────────────────────────────────────────────────────────
# Extração de ano embutido no título
# ─────────────────────────────────────────────────────────────
# Movie_Name vem como "Pulp Fiction (1994)" — ano dentro de parênteses.
# Esse é exatamente o tipo de transformação que vai morar no FilmeFactory
# quando ele instanciar Filme a partir dos dados brutos da fonte.
# Praticando aqui pra entender o que o Factory vai precisar fazer.

df_sample["year"] = df_sample["Movie_Name"].str.extract(r"\((\d{4})\)$").astype("Int64")
df_sample["title_clean"] = df_sample["Movie_Name"].str.replace(r"\s*\(\d{4}\)$", "", regex=True)

print("\n=== ANO EXTRAÍDO ===")
print(df_sample[["Movie_Name", "title_clean", "year"]].head())
print(f"\nFilmes sem ano detectado: {df_sample['year'].isna().sum()}")
print(f"Range de anos: {df_sample['year'].min()} – {df_sample['year'].max()}")


# ─────────────────────────────────────────────────────────────
# Próximos passos pra explorar (no REPL com python -i)
# ─────────────────────────────────────────────────────────────
# Tente:
#   df_sample["Genre"].str.split("|").explode().value_counts()  # contagem por gênero
#   df_sample.groupby("Movie_Name")["Rating"].agg(["mean", "count"]).sort_values("count", ascending=False).head(20)
#   df_sample.groupby("year")["Rating"].mean().plot(); plt.show()  # nota média por ano
#
# Quando estiver pronta pra carregar o CSV INTEIRO (1.66GB), use:
#   df_full = pd.read_csv(csv_path)  # ~5-10 min, ~10GB RAM
# ou em chunks:
#   chunks = pd.read_csv(csv_path, chunksize=500_000)
#   for chunk in chunks: ...

print("\n✓ ETL 01 concluído. df_sample disponível no REPL se rodou com python -i.")
