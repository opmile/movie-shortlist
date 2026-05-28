# O que foi esse ETL — leitura pra quem está chegando em data engineering

**Data:** 2026-05-28
**Pra quem é:** pessoa que sabe programar mas nunca trabalhou com pipelines de dados. Lê esse arquivo primeiro, depois mergulha nos outros quando precisar de detalhe.

---

## TL;DR

Pegamos um CSV de **25 milhões de avaliações de filmes** (1.5GB) e produzimos um CSV de **59 mil filmes** (3MB) com estatísticas pré-calculadas. O pipeline rodou em **30 segundos** sem estourar memória, e o resultado alimenta o app sem nunca tocar no arquivão original. Esse é o trabalho.

---

## Conceitos centrais que essa sessão exercita

### 1. Eventos vs entidades

O CSV bruto guarda **eventos**: cada linha é "user X deu nota Y pro filme Z". É um registro de coisas que aconteceram, não uma descrição de coisas que existem.

O sistema precisa de **entidades**: um objeto `Filme` por filme, com `avg_rating`, `count`, `year`. Coisas que existem, com propriedades.

**ETL é a transformação eventos → entidades.** Quase todo trabalho de dados começa aí: rolagem de cliques, logs, transações, mensagens — eventos em massa que precisam virar visões de entidades pra serem úteis.

### 2. Por que não dá pra "só carregar o arquivo"

A primeira tentação de quem está aprendendo é `pd.read_csv("dataset.csv")`. Funciona até o dia em que não funciona — porque o arquivo é maior que a RAM.

Aqui: CSV de 1.5GB → DataFrame de ~10GB em memória (strings, índices, overhead). Numa máquina de 16GB, isso mata o processo.

**Data engineering começa quando "carregar e processar" deixa de ser viável.** Você precisa pensar em pedaços (chunks), em uma passada (single-pass), em estruturas que cabem.

### 3. Streaming + acumulador

Padrão usado:

```
[arquivão] → [chunk 1] → agrega → guarda parcial
            [chunk 2] → agrega → guarda parcial
            [chunk 3] → agrega → guarda parcial
            ...
                       → combina parciais → resultado
```

Cada chunk cabe (500k linhas, ~500MB). Os parciais são pequenos (~MB). A combinação final opera sobre uma fração do input.

**Por que isso funciona:** agregações são *associativas*. A soma de tudo é a soma das somas parciais. Contagem total é soma das contagens. Isso permite quebrar o trabalho em pedaços e juntar no fim sem perder informação. Spark, MapReduce, dbt — todos vivem desse princípio em escalas maiores.

### 4. Single-pass

Cada varredura do arquivão custa caro (I/O + parsing). Tudo que precisa do dataset inteiro deve ser calculado **na mesma passada**:

- Agregação por filme ✅
- Contagem de users únicos ✅
- Detecção de anomalias (notas fora de range, formatos exóticos) ✅
- Total de eventos ✅

Aqui: 1 varredura, 30 segundos. Se você fizer "uma passada pra cada coisa", o pipeline vira minutos.

Em escala industrial (terabytes), single-pass é diferença entre **horas e dias**.

### 5. Data profiling — sempre o passo zero

Antes de qualquer modelagem, você roda *profiling*: distribuições, percentis, anomalias, cardinalidades. Sem isso você está modelando no escuro.

Aqui isso resolveu um problema concreto: a definição de "Filme Cult" foi calibrada como "count moderado". O que é "moderado"? Sem ver os dados, parecia razoável dizer "entre p20 e p50" (cauda do meio). Olhando a distribuição real: `p20 = 2`, `p50 = 6`. Ou seja, "moderado" virou "filme com 2 a 6 avaliações no total" — **cauda obscura, não cult**.

Profiling expõe esse tipo de armadilha. **Sempre. Antes de modelar.**

### 6. Build-time vs run-time

Pipeline pesado → roda uma vez (build-time), produz um *snapshot*. App consome o snapshot (run-time), não toca no arquivo bruto.

Aqui:
- **Build-time:** `lab/02_aggregate.py` rodou uma vez, gerou `lab/aggregated.csv` (3MB).
- **Run-time:** app carrega 3MB instantaneamente, sem rede, sem credenciais Kaggle, sem ETL.

Em escala industrial, "build-time" vira Airflow, dbt, Spark jobs. O princípio é igual: **app nunca faz ETL no caminho da request**.

### 7. Representação esparsa

Quando você tem uma matriz onde quase tudo é zero (aqui: 0.26% de células preenchidas), representar densamente é desperdício absurdo. Existe `scipy.sparse` exatamente pra isso.

Densa: 162k × 59k × 4 bytes = **38 GB** (impossível).
Esparsa: armazena só os valores não-zero = **200 MB** (trivial).

A diferença é puramente de representação — a matriz "lógica" é a mesma. Saber escolher representação certa é metade do trabalho com dados grandes.

---

## Como ler os outros arquivos dessa pasta

Em ordem de mergulho:

1. **`dataset-rationale.md`** — por que esse dataset, como ele é (schema, cardinalidade). Comece aqui pra contexto.
2. **`etl-pipeline.md`** — como o pipeline foi construído, decisão de não rodar em runtime. O coração técnico.
3. **`thresholds.md`** — exemplo concreto de profiling guiando decisões de domínio (subclasses). Mostra como dados informam código.
4. **`collab-filter-deferred.md`** — análise feita mas trabalho cortado. Exemplo de **engineering judgment**: saber não fazer algo é tão importante quanto saber fazer.

---

## Vocabulário pra fixar

| Termo | O que é | Aparece em |
|---|---|---|
| ETL | Extract, Transform, Load. O pipeline raw → snapshot. | `etl-pipeline.md` |
| Chunk | Lote do arquivo lido por vez, cabendo na memória. | `etl-pipeline.md` |
| Single-pass | Calcular tudo em uma varredura. | `etl-pipeline.md` |
| Snapshot | Output materializado do pipeline, consumido pelo app. | `etl-pipeline.md` |
| Profiling | Inspeção exploratória — distribuições, anomalias, cardinalidade. | `thresholds.md` |
| Percentil | Posição relativa na distribuição (p90 = "90% dos valores estão abaixo"). | `thresholds.md` |
| Cardinalidade | Quantos valores únicos uma coluna tem. | `dataset-rationale.md` |
| Densidade | Fração de células preenchidas numa matriz esparsa. | `collab-filter-deferred.md` |
| Sparse representation | Estrutura que guarda só valores não-zero. | `collab-filter-deferred.md` |
| Build-time vs run-time | Separação entre processamento pesado offline e consumo online. | `etl-pipeline.md` |

---

## O que esse mini-projeto ensina em currículo

1. Processou 1.5GB / 25M linhas em laptop com chunked groupby.
2. Single-pass aggregation com extração de schema implícito (ano embedado em string).
3. Profiling guiou modelagem (thresholds emergem dos dados, não chutados).
4. Separação build vs runtime (snapshot consumível).
5. Dimensionamento explícito de representação (sparse vs dense, com matemática).
6. Decisão deliberada de cortar escopo (collab filter analisado e deferido).

Cinco linhas no currículo. O código vive em `lab/02_aggregate.py`.
