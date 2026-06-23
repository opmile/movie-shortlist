# shortlist 🎬

Catálogo interativo de filmes com análise estatística e recomendação por
estratégias intercambiáveis. Caso de estudo de engenharia: **2 design patterns
formais** (Strategy + Repository) + herança/polimorfismo, sobre um dataset real
de **25M ratings** reduzido a snapshots no build-time. Sem ML e sem rede em
runtime — o produto consome só os snapshots.

UI em Streamlit, 3 telas: **Acervo**, **Estatísticas**, **Recomendações**.

🔗 **Demo ao vivo:** [movie-shortlist.streamlit.app](https://movie-shortlist.streamlit.app/)

## A tese

As subclasses de `Filme` não foram inventadas a priori — **emergem da
distribuição real** dos 58.958 filmes agregados. Mediram-se os percentis de
`count` (popularidade), `avg_rating` (nota) e `year`; os cortes naturais da
distribuição definem cada categoria. Cada threshold é justificado por um número
observado, não por opinião:

| Subclasse | Critério | ~Filmes |
|---|---|---|
| `Classico` | `year ≤ 1970 ∧ count ≥ 37` (antigo **e** ainda assistido) | 1.9k |
| `FilmeCult` | `count ∈ [6, 37] ∧ avg_rating ≥ 3.9` (nicho bem avaliado) | 474 |
| `Blockbuster` | `count ≥ p95 (1508)` (topo 5% de popularidade) | 2.7k |
| `FilmeAclamado` | `avg_rating ≥ 4.0 ∧ count ≥ 6` (nota alta com votos) | 121 |
| `Filme` (base) | fallback | 53.7k |

O polimorfismo — cada subclasse calculando seu `score` de um jeito — é o reflexo
em código de uma estrutura que o dado já tinha.

## Arquitetura

```
UI (Streamlit) ── 3 telas
    ├──> Catalogo        coleção encapsulada read-only
    ├──> Analisador      encapsula pandas (4 métricas)
    └──> Recomendador    Strategy (4 estratégias)

DataSource (Repository) ──► list[dict] ──► FilmeFactory ──► Filme + 4 subclasses
```

- **Strategy** — `Recomendador` ABC com `RecomendaPorGenero`, `RecomendaPorNota`,
  `RecomendaPorPopularidade`, `RecomendaSimilar`. Algoritmos diferentes (filtro /
  sort / lookup de vizinhos), mesmo contrato; a UI escolhe em runtime.
- **Repository** — `DataSource` ABC com `CSVDataSource`/`JSONDataSource`,
  devolvendo `list[dict]` (não `list[Filme]` — não conhece subclasses).
- **`FilmeFactory`** — despacha cada dict pra subclasse certa por precedência de
  guard clauses (`Classico > Cult > Blockbuster > Aclamado > Filme`). A ordem é
  contrato: peneiras sobrepostas que particionam o eixo de popularidade. Tratado
  como construtor com dispatch, não como Factory GoF.

## Recomendação com critério

Duas métricas pré-computadas no ETL sobem o produto de "catálogo com `sort()`"
pra "catálogo com critério":

- **Rating bayesiano** (`weighted_rating`) — *shrinkage* que puxa a média de
  poucos votos rumo ao prior global, proporcional à evidência. Um filme de 1
  voto e nota 5.0 não lidera o ranking. Calibrado na distribuição real (prior =
  média do catálogo; piso = p75 do `count`).
- **Collaborative filtering item-based** (`RecomendaSimilar`) — similaridade de
  cosseno sobre co-avaliações, computada **offline no ETL** → `neighbors.csv`. O
  produto só faz lookup O(1). Determinístico, sem modelo treinado: cosseno é
  álgebra linear, não ML. `scipy`/`scikit-learn` ficam só no ETL.

## Dados — build-time vs runtime

A agregação dos 25M ratings (~1,5GB) roda **uma vez**, offline, em `etl/`, e
emite dois snapshots estáticos: `aggregated.csv` (58.958 linhas) e
`neighbors.csv` (top-10 vizinhos por filme). O produto nunca toca o dado bruto,
não precisa de rede nem credencial Kaggle. ETL é fase, não produto.

## Rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/shortlist/app.py
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

TDD seletivo no core POO (domínio, factory, datasource, catalogo, recomendador,
analisador), com `parametrize` exercitando Strategy/Repository direto. UI e ETL
sem teste — são consumo/fase, não produtores de pattern.

## Documentação

`notebook/` concentra o raciocínio do projeto:
[`spec.md`](notebook/spec.md) (referência consolidada),
[`faq.md`](notebook/faq.md) (racional de cada decisão), e as notas em `data/`
(dataset, thresholds, bayesiano, CF) e `engineering/` (arquitetura, patterns,
TDD). Pipeline build-time em [`etl/`](etl/).
