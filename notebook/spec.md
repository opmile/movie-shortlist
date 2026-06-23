# shortlist — Especificação

**Versão:** v1
**Última atualização:** 2026-06-22
**Repositório:** `github.com/opmile/movie-shortlist`

> Este documento é a referência consolidada do projeto: **o que** será construído.
> O **porquê** de cada decisão está nas notas vizinhas: `data/`, `engineering/`, `faq.md`.

---

## 1. Visão geral

`shortlist` é um sistema interativo de catalogação de filmes que carrega dados de uma fonte plugável (Repository pattern), classifica filmes polimorficamente conforme propriedades emergentes dos dados (herança POO), e expõe operações de busca, análise estatística e recomendação por estratégias intercambiáveis (Strategy pattern). UI via Streamlit.

Escopo enxuto, arquitetura justificada — produto de portfolio.

---

## 2. Propósito

**Produto de portfolio:** caso de estudo de engenharia — 2 design patterns formais (Strategy + Repository) + herança/polimorfismo sobre problema com substância, recomendação com critério (CF item-based + rating bayesiano), escopo enxuto e arquitetura justificada.

Detalhe: `engineering/project-e-escopo.md`.

---

## 3. Definição

### O que é
Catálogo interativo de filmes com features analíticas e de recomendação. UI Streamlit. Stack pequena, decisões justificadas.

### O que NÃO é
- ❌ ETL (a fase ETL existe em `etl/`, é one-shot, não é o produto)
- ❌ Recomendador puro (recomendação é uma feature entre várias)
- ❌ Sistema de ML (sem modelo treinado; recomendação determinística)
- ❌ Backend / API (UI direta, sem cliente externo)
- ❌ Aplicação de uso real (ninguém escolhe filme real aqui; é demonstração arquitetural)

---

## 4. Stack

- **Linguagem:** Python 3.13
- **Isolamento:** venv local (`.venv/`), **sem Docker**
- **Dependências do produto:** `streamlit`, `pandas`, `matplotlib`, `plotly`, `pytest`
- **Dependências do ETL (separadas):** `kagglehub[pandas-datasets]`

Detalhe: `engineering/stack-and-tooling.md`.

---

## 5. Dados e ETL

### Dataset
`chaitanyahivlekar/large-movie-dataset` (Kaggle) — 25M ratings, 162k users, 58.958 filmes únicos.

### ETL one-shot (etl/ → snapshots)
O ETL roda **uma vez** offline e emite dois snapshots estáticos que o produto consome:
- `etl/aggregate.py` agrega raw → `aggregated.csv` (58.958 linhas, ~3MB). Chunked groupby, ~30s, pico ~500MB RAM. Inclui a coluna derivada `weighted_rating` (rating bayesiano — ver §8).
- `etl/neighbors.py` relê o raw (matriz esparsa user×item, cosseno item-based) → `neighbors.csv` (top-10 vizinhos por filme; alimenta `RecomendaSimilar`). `scipy`/`scikit-learn` ficam **só no ETL**.

**Princípio:** build-time vs run-time. O pesado roda offline; o sistema consome os snapshots. Sem rede, sem credencial Kaggle, sem dependência de ML no produto.

### Schema do agregado (consumido pelo sistema)
| Coluna | Tipo |
|---|---|
| `Movie_Name` | str (título-com-ano — chave de join com `neighbors.csv`) |
| `title` | str (título limpo, sem `(YYYY)`) |
| `year` | Int64 (nullable) |
| `genres` | str pipe-separated (split → `list[str]` no `Filme`) |
| `sum_rating` | float (soma das notas; intermediária de `avg_rating`) |
| `count` | int |
| `avg_rating` | float |
| `weighted_rating` | float (rating bayesiano — shrinkage; ver §8) |

Detalhe: `data/dataset-e-etl.md` · `data/collab-filter.md` · `data/rating-bayesiano.md`.

---

## 6. Arquitetura

### Camadas

```
UI (Streamlit) ── 3 telas
    │
    ├──> Catalogo (coleção encapsulada)
    │       │
    │       ▼
    │     Filme + 4 subclasses (herança POO)
    │       ▲
    │       │ instancia
    │     FilmeFactory (precedência de thresholds)
    │       ▲
    │       │ consome dict
    │     DataSource ABC ────► Repository pattern
    │       ├── CSVDataSource
    │       └── JSONDataSource
    │
    ├──> Analisador (encapsula pandas)
    │
    └──> Recomendador ABC ────► Strategy pattern
          ├── RecomendaPorGenero
          ├── RecomendaPorNota          (ordena por weighted_rating)
          ├── RecomendaPorPopularidade
          └── RecomendaSimilar          (lookup item-based em neighbors.csv)
```

`neighbors.csv` (emitido pelo ETL) é input estático de `RecomendaSimilar` — lookup O(1), zero cosseno em runtime.

Detalhe: `engineering/architecture.md`.

### Fluxo
1. **Startup:** `DataSource.carregar()` → list[dict] → `FilmeFactory.criar()` → `Filme` (subclasse apropriada) → `Catalogo(filmes)` (coleção read-only, injetada no construtor)
2. **Uso:** UI → camada (`Catalogo` / `Analisador` / `Recomendador`) → list[Filme] → render

O startup é fixado por `@st.cache_resource` em `build_catalogo()` (roda 1× e persiste entre reruns do Streamlit, que re-executa o script a cada interação); parse de `aggregated.csv`/`neighbors.csv` via `@st.cache_data`. Built-in do streamlit — nenhuma dep nova. Mecânica e os 3 sentidos de "cache" em `engineering/architecture.md` · `data/dataset-e-etl.md`.

---

## 7. Design patterns

### 7.1 Strategy — `Recomendador`

```python
class Recomendador(ABC):
    @abstractmethod
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]: ...

class RecomendaPorGenero(Recomendador):
    def __init__(self, genero_alvo: str): ...
class RecomendaPorNota(Recomendador): ...          # sort por weighted_rating
class RecomendaPorPopularidade(Recomendador): ...  # sort por count
class RecomendaSimilar(Recomendador):              # lookup item-based em neighbors.csv
    def __init__(self, titulo_alvo: str, vizinhos: dict[str, list[str]]): ...  # vizinhos injetados (carregar_vizinhos)
```

Algoritmos diferentes (filtro vs sort por chave vs lookup de vizinhos), mesmo contrato. UI escolhe estratégia em runtime (dropdown). `RecomendaSimilar` só consulta `neighbors.csv` (pré-computado no ETL) — o cosseno não roda no produto. Detalhe: `data/collab-filter.md`.

### 7.2 Repository — `DataSource`

```python
class DataSource(ABC):
    @abstractmethod
    def carregar(self) -> list[dict]: ...

class CSVDataSource(DataSource):
    def __init__(self, path: str): ...
class JSONDataSource(DataSource):
    def __init__(self, path: str): ...
```

Retorna `list[dict]` (não `list[Filme]`) — separação: DataSource não conhece subclasses; FilmeFactory decide.

**JSON = mesmos dados agregados, formato JSON** (o ETL emite `aggregated.json` junto do `.csv`), não um dataset diferente. Repository desacopla **formato/origem**, não **distribuição**: os thresholds do FilmeFactory são calibrados a *este* dataset; fonte com distribuição diferente exigiria recalibração por fonte. Detalhe: `engineering/design-patterns.md`.

### O que NÃO é pattern formal
- **Factory** — `FilmeFactory` existe como "construtor com lógica de dispatch", não trabalhado como pattern GoF
- **Singleton, Observer, Decorator, Adapter** — não emergem naturalmente
- **Singleton (nota):** `Catalogo` é singleton-*scoped* via `@st.cache_resource` (lifecycle de infra — mesma instância entre reruns), **não** Singleton GoF (classe não se policia, construtor público, testável). Mecanismo de framework, não pattern. Detalhe: `engineering/design-patterns.md`

Detalhe: `engineering/design-patterns.md`.

---

## 8. Domínio — `Filme` e subclasses

### Base
```python
@dataclass
class Filme:
    title: str
    year: int | None
    genres: list[str]
    avg_rating: float
    count: int
    def calcular_score(self) -> float: ...
    def exibir(self) -> str: ...
    def categoria(self) -> str: ...
```

### Subclasses (cada uma sobrescreve `calcular_score`)
- `FilmeAclamado` — pondera `avg_rating` alto
- `Blockbuster` — pondera `count` (popularidade)
- `FilmeCult` — pondera nicho (count médio, avg alto)
- `Classico` — bônus por antiguidade

### Thresholds calibrados (do ETL)
| Subclasse | Critério | Estimativa |
|---|---|---|
| `Classico` | `year ≤ 1970 ∧ count ≥ 37` | ~1.9k |
| `FilmeCult` | `count ∈ [6, 37] ∧ avg_rating ≥ 3.9` | ~474 |
| `Blockbuster` | `count ≥ p95 (1508)` | ~2.7k |
| `FilmeAclamado` | `avg_rating ≥ 4.0 ∧ count ≥ 6` | ~121 |
| `Filme` (base) | fallback | ~53.7k (~91%) |

> Calibração refinada em `etl/explore/calibrate.py` (2026-05-28): pisos de `count` no Aclamado (`≥6`, mata ruído de poucos votos) e no Classico (`≥37`, exige reconhecimento — idade não basta); Blockbuster em p95 real (1508, não ~250). Detalhe: `data/thresholds.md`.

### Precedência (FilmeFactory aplica em ordem)
`Classico > FilmeCult > Blockbuster > FilmeAclamado > Filme`

Detalhe: `data/thresholds.md`.

### Métricas derivadas (emitidas pelo ETL, separadas de `calcular_score`)

- **`weighted_rating` (rating bayesiano):** *weighted rating* (shrinkage) `WR = (v/(v+m))·R + (m/(v+m))·C`, com `m`=p75 do `count`=37 e `C`=média global. Puxa a média de poucos votos pro prior global, corrigindo o ruído de baixa amostra (um filme de 1 voto e nota 5.0 não lidera o ranking). Usado por `RecomendaPorNota` e na ordenação da tela Acervo. **Não** entra no `calcular_score` das subclasses (que é o eixo de *personalidade*); é uma correção de *confiança* ortogonal. Detalhe: `data/rating-bayesiano.md`.
- **`neighbors` (collaborative filtering):** top-10 vizinhos item-based por filme (cosseno sobre co-avaliação, computado offline no ETL → `neighbors.csv`). Schema **tidy** `Movie_Name, rank, vizinho, sim` (uma linha por par; chave = `Movie_Name`, mesma do `aggregated.csv`; carrega o score `sim`). Produto lê 1×, indexa por `groupby` → dict, lookup O(1). Alimenta `RecomendaSimilar`. Determinístico, sem modelo treinado, sem ML em runtime. Detalhe: `data/collab-filter.md`.

---

## 9. TDD

**Imprescindível.** Seletivo no core POO. Não cerimonial.

| Camada | TDD? |
|---|---|
| `Filme` + subclasses | ✅ |
| `Catalogo` | ✅ |
| `DataSource` + impls | ✅ (parametrizado) |
| `FilmeFactory` | ✅ |
| `Recomendador` + estratégias | ✅ (parametrizado) |
| `Analisador` | ⚠️ minimal (só boundary) |
| Streamlit UI | ❌ |
| `etl/` scripts | ❌ |

`pytest` + `parametrize` pra demonstrar Strategy/Repository diretamente no teste.

Detalhe: `engineering/tdd-e-workflow.md`.

---

## 10. Fora de escopo (v1)

- **ML / modelo treinado em runtime** — a recomendação é determinística. O collaborative filtering é álgebra linear (cosseno) computada **offline no ETL**; o produto só faz lookup. Sem treino, sem inferência no request path.
- **Content-based via TF-IDF** — dataset não tem texto rico (sem `overview`).
- **`KaggleDataSource` em runtime** — ETL é one-shot no `etl/`.
- **Factory pattern formal** — `FilmeFactory` é construtor com dispatch, não trabalhado como pattern.
- **`FilmeNacional`, `Documentario`, `Serie`** — dataset não tem `country`/`language`/tipo distinto suficiente.
- **Banco de dados, autenticação, API REST, Docker, deploy.**

---

## 11. Critério de pronto

Em ambiente limpo, deve-se conseguir:

```bash
git clone https://github.com/opmile/movie-shortlist
cd movie-shortlist
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run src/shortlist/app.py
```

E:
1. App abre sem erros
2. Tela Acervo lista filmes filtravelmente, com `weighted_rating` (nota ajustada) ao lado da média crua
3. Tela Estatísticas renderiza gráficos
4. Tela Recomendações permite trocar entre as 4 estratégias — incluindo `RecomendaSimilar` ("porque você gostou de X") — e ver resultado
5. Testes passam: `.venv/bin/pytest tests/ -v`

Tudo além disso é polimento.

---

## 12. Estrutura de pastas (proposta)

```
shortlist/
├── src/shortlist/
│   ├── __init__.py
│   ├── domain.py           # Filme + subclasses
│   ├── catalogo.py
│   ├── factory.py
│   ├── datasource.py       # ABC + CSV + JSON
│   ├── analisador.py
│   ├── recomendador.py     # ABC + 4 estratégias (inclui RecomendaSimilar)
│   └── app.py              # entry Streamlit
├── tests/
│   ├── conftest.py
│   ├── test_filme.py
│   ├── test_catalogo.py
│   ├── test_datasource.py
│   ├── test_factory.py
│   └── test_recomendador.py
├── etl/                    # pipeline build-time — estrutura/uso em etl/README.md
├── notebook/               # documentação do projeto (commitado)
│   ├── README.md
│   ├── spec.md             # este arquivo (referência consolidada)
│   ├── faq.md
│   ├── data/
│   └── engineering/
├── .venv/                  # gitignored
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 13. Próximo passo

Plan de implementação via skill `superpowers:writing-plans` — traduz spec em sequência executável de tarefas, branch por camada, ordem de entrega.
