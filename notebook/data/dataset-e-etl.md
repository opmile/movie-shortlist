# Dataset e ETL — escolha, shape e pipeline

**Data:** 2026-05-28

Por que esse dataset, como ele é, e como o ETL one-shot o reduz de 1.66GB para 3MB.

---

## TL;DR

CSV bruto de **25M avaliações** (1.66GB) → snapshot de **58.958 filmes** (~3MB) com stats pré-calculadas. Pipeline roda **uma vez offline** (`etl/aggregate.py`, ~30s, pico ~500MB RAM) e o app consome só o snapshot — sem rede, sem credencial Kaggle, sem ETL no startup.

---

## Conceitos de data engineering exercitados

- **Eventos vs entidades** — cada linha do raw é um evento (`user X deu nota Y ao filme Z`), não uma entidade. O domínio precisa de `Filme` como entidade com propriedades agregadas (`avg_rating`, `count`, `year`). ETL é a transformação eventos → entidades — o ponto de partida de quase todo trabalho de dados (logs, cliques, transações).
- **Por que não "só carregar o arquivo"** — CSV de 1.66GB vira ~10GB em DataFrame (overhead de strings 4-7×). Numa máquina de 16GB, mata o processo. Data engineering começa quando "carregar e processar" deixa de caber na RAM.
- **Streaming + acumulador** — lê em chunks (500k linhas, ~500MB cada), agrega parcial, combina no fim. Funciona porque agregações são **associativas**: soma total = soma das somas parciais. Mesmo princípio de Spark/MapReduce/dbt em escala maior.
- **Single-pass** — tudo que precisa do dataset inteiro (agregação, users únicos, anomalias, total de eventos) é calculado numa varredura só. Em escala industrial, single-pass é a diferença entre horas e dias.
- **Data profiling é o passo zero** — distribuições/percentis/anomalias antes de modelar. Ver `thresholds.md`: profiling expôs que "count moderado" para Cult, que parecia ser [p20,p50]=[2,6], era na verdade cauda obscura, não cult.
- **Build-time vs run-time** — pipeline pesado roda uma vez (build), produz snapshot; app consome o snapshot (run), nunca toca o raw. App não faz ETL no caminho da request.
- **Representação esparsa** — matriz user-item tem densidade 0.26%; densa = 38GB, sparse = 200MB. Detalhe e uso em `collab-filter.md`.

---

## Cardinalidade real (descoberta no ETL)

- **Ratings totais:** 25.000.095
- **Users únicos:** 162k
- **Filmes únicos:** 58.958
- **Densidade da matriz user-item:** 0.26%
- **Raw:** 1.66GB CSV — **Agregado:** ~3MB CSV
- **Agregação chunked:** ~30s, pico ~500MB RAM

**Dataset:** `chaitanyahivlekar/large-movie-dataset` (Kaggle, MovieLens-derived). Cada linha do raw é um rating de um user, não um filme — é **rating-centric**, não catálogo.

---

## Schema

**Raw:**

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Unnamed: 0` | int | índice do export — descarta |
| `User_Id` | int | id de usuário |
| `Movie_Name` | str | título + ano embutido (`"Pulp Fiction (1994)"`) |
| `Rating` | float | nota daquele user (0.5–5.0) |
| `Genre` | str | gêneros pipe-separated (`"Comedy\|Crime\|Drama"`) |

**Agregado (produto do ETL, input direto do `CSVDataSource`):**

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Movie_Name` | str | título com ano (formato original) |
| `title` | str | título limpo (sem `(YYYY)`) |
| `year` | Int64 | ano extraído por regex `\((\d{4})\)$` |
| `genres` | str | pipe-separated do raw |
| `sum_rating` | float | soma das notas |
| `count` | int | número de ratings (popularidade) |
| `avg_rating` | float | `sum_rating / count` |
| `weighted_rating` | float | rating bayesiano (shrinkage; ver `rating-bayesiano.md`) |

---

## Por que agregar (redução de granularidade, 99.8%)

O catálogo não precisa saber **quem** votou — só das propriedades e stats consolidadas de cada filme. Agrupar por `Movie_Name` reduz 25M linhas → 58.958 (uma por filme). Sem agregação: 25M rows em memória inviável, "nota média de Pulp Fiction" exige scan de 25M, subclasses por threshold de stat não podem existir.

---

## Por que chunked groupby (e não load + groupby direto)

`pd.read_csv(path)` direto: ~5-10 min, ~10GB RAM, estoura em 16GB. Chunked: lê em blocos de 500k, agrega incremental, pico ~500MB, ~30s.

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

Mecânica que importa:
- **Acumula `sum` e `count` separados, não a média por bloco.** Tirar média de cada chunk distorceria: blocos têm pesos diferentes (um filme pode ter 10 ratings no chunk A e 1.000 no B). Média ponderada global só no fim: `avg = sum/count`.
- **Regex de ano** — `\((\d{4})\)$` extrai 4 dígitos entre parênteses no fim do título; ano não existe como coluna.
- **`first` em strings repetidas** — gênero/ano são constantes por filme; `first` basta, sem concatenação.

Código de referência: `etl/aggregate.py`.

---

## Build-time vs run-time

| Aspecto | Runtime (startup UI) | Build-time (ETL) |
|---|---|---|
| Tempo de carga | < 0.2s | ~30s |
| Memória | ~15MB (dados) | ~500MB |
| Dependências | `aggregated.csv` local | Kaggle + Python (etl/) |

**Alternativa rejeitada:** `KaggleDataSource` que baixa + agrega em runtime. Problemas: cold start de minutos, credencial Kaggle exigida em todo ambiente, dependência de rede, não roda offline, app trava esperando, cada `streamlit run` repete o pipeline. Padrão industrial (Airflow/dbt): pipelines de build-time produzem snapshots; aplicações consomem. ETL nunca corre no request path.

Resultado: o app roda em < 1 minuto em qualquer máquina, sem internet nem chave Kaggle, exibindo dados derivados de massa de escala real.

### Cache vs precompute vs memoização de rerun

"Computar caro uma vez e reusar" tem **três** mecanismos distintos que a palavra "cache" embola. Separá-los é o que evita o doc parecer se contradizer:

| | **Precompute (build-time)** | **Cache de domínio (runtime)** | **Memoização de rerun (Streamlit)** |
|---|---|---|---|
| Quando | offline, uma vez, antes do app subir | 1ª query guarda resultado, reusa | 1º rerun constrói, reusa entre reruns |
| Onde | disco (`.csv`) | RAM (TTL/eviction) | store no processo do servidor Streamlit |
| Cacheia | stats agregadas (`aggregated.csv`, `neighbors.csv`) | resultados de busca/filtro/sort | objeto `Catalogo` + DataFrame carregado |
| Veredito | **é a estratégia central** | **dispensado** (overkill) | **necessário** (imposto pelo framework) |

**Precompute — os CSVs do ETL já são a camada de "cache" sob outro nome.** O sistema escala adicionando CSV, não camada de cache de domínio. ETL roda uma vez offline; o produto só lê o snapshot.

**Cache de domínio — dispensado.** Filtrar/ordenar 59k filmes em memória é milissegundos; memoizar query não compra nada. Um `DataSource` com cache (Decorator sobre `carregar()`) seria pattern inútil — `carregar()` roda uma vez. Esse cache só importaria em web/multiusuário com queries caras (v3+).

**Memoização de rerun — necessária, e não contradiz o ponto acima.** É eixo diferente: lifecycle de *framework*, não camada de *domínio*. O Streamlit re-executa o script **inteiro** a cada interação (clique/dropdown); sem memoização, o load do CSV + build de 59k re-roda a cada clique — o "carrega uma vez no startup" deixa de ser verdade. `@st.cache_resource` fixa o `Catalogo` (singleton-scoped — mesma ref entre reruns, ver `../engineering/design-patterns.md`) e `@st.cache_data` fixa o parse de `aggregated.csv`/`neighbors.csv`. Não é cache de domínio reabilitado: é o que torna o startup-1× literal sob o modelo de execução do Streamlit. Mecânica e alvos em `../engineering/architecture.md`.

---

## Por que esse dataset (e o trade-off assumido)

**Pros:**
1. **Subclasses emergentes** — `FilmeAclamado`, `Cult`, `Blockbuster`, `Classico` vêm de distribuição estatística real (percentis sobre 59k filmes). Dataset pequeno curado → subclasses viram etiquetas hardcoded (`if genre=='Documentary'`). Aqui são emergência de dados — polimorfismo justificado, não decorativo.
2. **Volume "de verdade"** — 25M ratings, 162k users; pipeline aguentou dado real → entra no currículo.
3. **Substância de engenharia** — separação build/runtime, chunked groupby, profiling.

**Trade-off (schema fino, rating-centric):** só título, gênero, nota, count e ano (este enfiado no título). Isso:
- Encurralou a modelagem num eixo só — `Cult`, `Blockbuster`, `Aclamado` vivem todos no plano `count × avg_rating`, diferindo por *onde sentam na popularidade*, não por tipo de dado.
- Não comporta subclasses por atributo (`FilmeNacional`/`Documentario` — sem `country`/`language`) nem recomendação content-based (sem `overview` pra TF-IDF). Ambas ficam fora do escopo.

**Veredito:** um TMDB/IMDb top-5k (~10MB) com metadata rica seria mais simples e habilitaria content-based, mas custaria a narrativa de emergência estatística. Para *este* enquadramento (POO + decisão data-driven), a pobreza de schema foi justamente o que forçou a história limpa. Escolha precedeu a inspeção do shape; sunk cost + ETL já feito favorece manter.

---

## ETL

**Enriqueceu:** `etl/aggregate.py` virou aprendizado real em chunked groupby + percentis; `aggregated.csv` é artefato real, não mock; subclasses só fazem sentido com a agregação; ganha substância arquitetural (build/runtime).

**Saldo positivo porque:** o ETL foi sessão separada (~10% do projeto, não consumiu o tempo do core); substância de engenharia cresceu desproporcional ao tempo; ETL é skill multiplicador; eliminar hoje exigiria trocar dataset e re-rodar o ETL. **Onde foi de fato overengineering e foi cortado:** o `KaggleDataSource` rodando pipeline em runtime — ETL ficou em `etl/`, fora do produto.

**Regra pra projetos futuros:** se ETL > 30% do projeto principal, trocar dataset. Aqui ficou ~10%.

---

## Reprodutibilidade

Qualquer dev com conta Kaggle + token, `pip install "kagglehub[pandas-datasets]" pandas numpy scipy scikit-learn`, e `python etl/build.py` regenera `aggregated.csv` + `neighbors.csv` (agregação ~30s + download; CF alguns min). Detalhe em `etl/README.md`.

**Decisão: commitar `aggregated.csv`** (3MB; idem `neighbors.csv`). Clona o repo e roda `streamlit run` em 1 minuto — o critério "rodar em ambiente limpo com 1 comando" depende disso.

---

## Anomalias capturadas no ETL

- **527 filmes (0.9%) sem ano detectado** — regex falha em formatos exóticos (re-releases, parênteses internos). Caem em `Filme` base via guarda `year is not None` do `FilmeFactory`. Não justifica refinar o parser. Nota: contar anomalia na granularidade da decisão (filme, 0.9%), não na de linha — eram 13.495 *linhas* sem ano, mas só 527 filmes únicos.
- **0 ratings fora de [0.5, 5.0]** e **0 gêneros null** → dado limpo, sem validação extra no código.

---

## O que NÃO foi feito (intencional)

- **Gêneros não normalizados** — mantém pipe-separated; conversão pra lista é responsabilidade do `Filme` no domínio.
- **Matriz user-item não persistida** — o passo de `etl/` do CF (`neighbors.py`) reconstrói a matriz do raw em build-time pra emitir `neighbors.csv`; o produto não guarda a matriz (ver `collab-filter.md`).
- **Sem parquet** — CSV é mais portável pra demo; 3MB torna o trade-off de performance irrelevante.

---

## O que esse mini-projeto ensina 

1. Processou 1.66GB / 25M linhas em laptop com chunked groupby.
2. Single-pass aggregation com extração de schema implícito (ano embutido em string).
3. Profiling guiou modelagem (thresholds emergem dos dados — ver `thresholds.md`).
4. Separação build vs runtime (snapshot consumível).
5. Dimensionamento explícito de representação (sparse vs dense, com matemática).
6. Dimensionamento de collab filtering (sparse vs dense) feito no ETL; CF entregue no v1 via `neighbors.csv` (cosseno offline). Ver `collab-filter.md`.
