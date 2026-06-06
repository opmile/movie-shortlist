# Findings — ETL data exploration

Dataset: `movies_dataset.csv` (chaitanyahivlekar/large-movie-dataset)
pandas 3.0.3 / numpy 2.4.6

## 1. Cardinalidade

- Ratings total: **25,000,095**
- Users únicos: **162,541**
- Filmes únicos: **58,958**
- Densidade da matriz user×movie: **0.2609%**

## 2. Distribuições agregadas

| Métrica | min | p10 | p20 | p25 | p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| avg_rating | 0.500 | 2.091 | 2.500 | 2.688 | 3.150 | 3.500 | 3.865 | 4.000 | 5.000 | 5.000 |
| count por filme | 1.000 | 1.000 | 2.000 | 2.000 | 6.000 | 36.750 | 414.000 | 1508.000 | 9943.000 | 81491.000 |
| year | 1874.000 | 1954.000 | 1972.000 | 1979.000 | 2003.000 | 2013.000 | 2016.000 | 2018.000 | 2019.000 | 2019.000 |

## 3. Anomalias

- Ratings fora de [0.5, 5.0]: **0**
- Linhas com título sem ano: **13,495**
- Linhas com gênero null: **0**
- Filmes únicos sem ano: **527**
- Filmes únicos sem gênero: **0**

## 4. Thresholds finais aplicados (precedência Classico > Cult > Blockbuster > Aclamado > Filme)

Prior do rating bayesiano: C (média global) = **3.071**.

| Subclasse | Filmes (pós-precedência) |
|---|---|
| Classico | 10,906 |
| Cult | 418 |
| Blockbuster | 6,531 |
| Aclamado | 63 |
| Filme | 41,040 |

Thresholds (fonte canônica: `../notebook/data/thresholds.md`): `{'aclamado_avg': 4.0, 'aclamado_floor': 38, 'blockbuster_count': 250, 'cult_count_lo': 6, 'cult_count_hi': 37, 'cult_avg': 3.9, 'classico_year': 1970}`

## 5. Matriz collaborative filtering — dimensionamento

U × M = 162,541 × 58,958 = 9,583,092,278 células

| Estratégia | RAM |
|---|---|
| Dense float32 | **38.332 GB** |
| Sparse CSR float32 | **200.7 MB** |
| Item-item M×M float32 | **13.904 GB** |

Densidade 0.2609% → sparse CSR. Item-based + filtro `count ≥ 37` deixa o item×item caber. Ver `../notebook/data/collab-filter.md`.
