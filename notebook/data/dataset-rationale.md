# Escolha do dataset — racional e shape

**Data:** 2026-05-28
**Dataset:** `chaitanyahivlekar/large-movie-dataset` (Kaggle)
**Artefato consumido pelo sistema:** `lab/aggregated.csv` (derivado via ETL one-shot)

---

## Cardinalidade real (descoberta no lab)

- **Ratings totais:** 25M
- **Users únicos:** 162k
- **Filmes únicos:** 58.958
- **Densidade da matriz user-item:** 0.26%
- **Tempo de agregação chunked:** 29.7s, pico ~500MB RAM
- **Tamanho raw:** 1.66GB CSV
- **Tamanho agregado:** ~3MB CSV (58.958 linhas)

---

## Schema do raw

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Unnamed: 0` | int | índice do export — descarta |
| `User_Id` | int | id de usuário |
| `Movie_Name` | str | título + ano embutido (`"Pulp Fiction (1994)"`) |
| `Rating` | float | nota daquele user pro filme (0.5–5.0) |
| `Genre` | str | gêneros pipe-separated (`"Comedy\|Crime\|Drama"`) |

**Descoberta crítica:** cada linha = um rating de um user, não um filme. Dataset é **rating-centric**, não catálogo. MovieLens-derived.

---

## Schema do agregado (produto do ETL)

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Movie_Name` | str | título com ano (formato original) |
| `title` | str | título limpo (sem `(YYYY)`) |
| `year` | Int64 | ano extraído por regex |
| `genres` | str | mantém pipe-separated do raw |
| `sum_rating` | float | soma das notas |
| `count` | int | número de ratings |
| `avg_rating` | float | `sum_rating / count` |

Esse é o input direto pro `CSVDataSource`.

---

## Por que esse dataset (não outro mais simples)

**Pros:**

1. **Subclasses emergentes** — `FilmeAclamado`, `Cult`, `Blockbuster`, `Classico` vêm de distribuição estatística real (percentis sobre 59k filmes). Dataset pequeno curado → subclasses viram etiquetas hardcoded.
2. **Volume "de verdade"** — 25M ratings, 162k users. Pipeline aguentou dado real → vai pro currículo.
3. **Polimorfismo defensável** — subclasse não é flag (`if genre=='Documentary'`); é decisão de threshold sobre stats. Decisão arquitetural real.

**Cons:**

- ❌ Sem `overview`/`description` → content-based via TF-IDF inviável
- ❌ Sem `country`/`language` → `FilmeNacional` inviável
- ❌ Sem `director`/`cast` → metadata pobre
- ❌ Variação de subclasses tipo `Documentario`/`Serie` (precisaria de TMDB-like)

**Veredito:** se começasse hoje do zero, TMDB top-5k (~10MB) com metadata rica teria sido escolha mais simples. Não foi erro catastrófico — escolha precedeu inspeção. Sunk cost + lab já feito favorece manter.

---

## Decisões sobre o uso do dataset

1. **Sistema consome só o agregado** (`aggregated.csv`). Raw fica fora do produto.
2. **ETL one-shot** (`lab/02_aggregate.py`) — não é re-executado em runtime.
3. **`KaggleDataSource` ficou fora do escopo v1** — `CSVDataSource` é a fonte default.
4. **Filmes sem ano (527, 0.9%)** caem em `Filme` base; não justifica parser mais elaborado.

---

## Próximos passos potenciais (v2+)

- Reativar `KaggleDataSource` se quiser demonstrar download dinâmico
- Substituir/complementar com TMDB pra recomendação content-based
- Reabilitar collab filtering usando o raw (matriz sparse já dimensionada — ver `collab-filter-deferred.md`)
