# shortlist — Especificação

**Trabalho Final de POO**
**Versão:** v1
**Última atualização:** 2026-05-28
**Repositório:** `github.com/opmile/shortlist`

> Este documento é a referência consolidada do projeto: **o que** será construído.
> O **porquê** de cada decisão está em `notebook/` (`doc/`, `data/`, `engineering/`).

---

## 1. Visão geral

`shortlist` é um sistema interativo de catalogação de filmes que carrega dados de uma fonte plugável (Repository pattern), classifica filmes polimorficamente conforme propriedades emergentes dos dados (herança POO), e expõe operações de busca, análise estatística e recomendação por estratégias intercambiáveis (Strategy pattern). UI via Streamlit.

Projeto solo, escopo enxuto, ~6-8h ativas distribuídas em 4 semanas como projeto secundário.

---

## 2. Propósito duplo

1. **Acadêmico (TFD POO):** demonstrar 2 design patterns formais + herança/polimorfismo trabalhando juntos sobre problema com substância. Cada decisão arquitetural defensável na banca.
2. **Pessoal / portfolio:** caso de estudo de engenharia — saber defender escopo, aplicar patterns, justificar arquitetura.

Detalhe: `notebook/engineering/project-definition.md`.

---

## 3. Definição

### O que é
Catálogo interativo de filmes com features analíticas e de recomendação. UI Streamlit. Stack pequena, decisões justificadas.

### O que NÃO é
- ❌ ETL (a fase ETL existe em `lab/`, é one-shot, não é o produto)
- ❌ Recomendador puro (recomendação é uma feature entre várias)
- ❌ Sistema de ML (sem modelo treinado; recomendação determinística)
- ❌ Backend / API (UI direta, sem cliente externo)
- ❌ Aplicação de uso real (banca não vai escolher filme; é demonstração arquitetural)

---

## 4. Stack

- **Linguagem:** Python 3.13
- **Isolamento:** venv local (`.venv/`), **sem Docker**
- **Dependências do produto:** `streamlit`, `pandas`, `matplotlib`, `plotly`, `pytest`
- **Dependências do lab (separadas):** `kagglehub[pandas-datasets]`

Detalhe: `notebook/engineering/stack-and-tooling.md`.

---

## 5. Dados e ETL

### Dataset
`chaitanyahivlekar/large-movie-dataset` (Kaggle) — 25M ratings, 162k users, 58.958 filmes únicos.

### ETL one-shot
Script `lab/02_aggregate.py` agrega raw → `aggregated.csv` (58.958 linhas, ~3MB). Chunked groupby, ~30s, pico ~500MB RAM.

**Princípio:** build-time vs run-time. ETL roda **uma vez** offline; sistema consome o snapshot. Sem rede, sem credencial Kaggle no produto.

### Schema do agregado (consumido pelo sistema)
| Coluna | Tipo |
|---|---|
| `title` | str |
| `year` | Int64 (nullable) |
| `genres` | list[str] (split de pipe-separated) |
| `avg_rating` | float |
| `count` | int |

Detalhe: `notebook/data/dataset-rationale.md`, `notebook/data/etl-pipeline.md`.

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
          ├── RecomendaPorNota
          └── RecomendaPorPopularidade
```

Detalhe: `notebook/engineering/architecture.md`.

### Fluxo
1. **Startup:** `DataSource.carregar()` → list[dict] → `FilmeFactory.criar()` → `Filme` (subclasse apropriada) → `Catalogo.adicionar()`
2. **Uso:** UI → camada (`Catalogo` / `Analisador` / `Recomendador`) → list[Filme] → render

---

## 7. Design patterns

### 7.1 Strategy — `Recomendador`

```python
class Recomendador(ABC):
    @abstractmethod
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]: ...

class RecomendaPorGenero(Recomendador):
    def __init__(self, genero_alvo: str): ...
class RecomendaPorNota(Recomendador): ...
class RecomendaPorPopularidade(Recomendador): ...
```

Algoritmos diferentes (filter vs sort por chave A vs sort por chave B), mesmo contrato. UI escolhe estratégia em runtime (dropdown).

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

### O que NÃO é pattern formal
- **Factory** — `FilmeFactory` existe como "construtor com lógica de dispatch", não trabalhado como pattern GoF
- **Singleton, Observer, Decorator, Adapter** — não emergem naturalmente

Detalhe: `notebook/engineering/design-patterns.md`.

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

### Thresholds calibrados (do lab)
| Subclasse | Critério |
|---|---|
| `Classico` | `year ≤ 1970` |
| `FilmeCult` | `count ∈ [6, 37] ∧ avg_rating ≥ 3.9` |
| `Blockbuster` | `count ≥ p95 (~250)` |
| `FilmeAclamado` | `avg_rating ≥ 4.0` |
| `Filme` (base) | fallback |

### Precedência (FilmeFactory aplica em ordem)
`Classico > FilmeCult > Blockbuster > FilmeAclamado > Filme`

Detalhe: `notebook/data/thresholds.md`.

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
| `lab/` scripts | ❌ |

`pytest` + `parametrize` pra demonstrar Strategy/Repository diretamente no teste.

Detalhe: `notebook/engineering/tdd-scope.md`.

---

## 10. Fora de escopo (v1)

- **Collaborative filtering** — análise feita no lab, dimensionamento OK (sparse 200MB). Deferred to v2. Ver `notebook/data/collab-filter-deferred.md`.
- **Content-based via TF-IDF** — dataset não tem texto rico (sem `overview`).
- **`KaggleDataSource` em runtime** — ETL é one-shot no `lab/`.
- **Factory pattern formal** — `FilmeFactory` é construtor com dispatch, não trabalhado como pattern.
- **`FilmeNacional`, `Documentario`, `Serie`** — dataset não tem `country`/`language`/tipo distinto suficiente.
- **Banco de dados, autenticação, API REST, ML, Docker, deploy.**

---

## 11. Cronograma — 4 semanas

| Semana | Janela | Entregas | Marco |
|---|---|---|---|
| **S1** | 26/05–01/06 | Setup repo, `Filme` + subclasses, `Catalogo` | Catalogo polimórfico funcional via script |
| **S2** | 02/06–08/06 | `DataSource` ABC + CSV + JSON, `FilmeFactory` | Troca de fonte sem mexer no resto |
| **S3** | 09/06–15/06 | `Analisador`, `Recomendador` + 3 estratégias | Análise + recomendação rodando no REPL |
| **S4** | 16/06–22/06 | Streamlit 3 telas + polimento + slides | App end-to-end + ensaio |
| **Buffer** | 23–26/06 | Bugfix, polimento extra | — |

Workflow por camada: conceito → contrato → TDD → implementação Claude → revisão. Detalhe: `notebook/engineering/workflow.md`.

---

## 12. Critério de pronto

Avaliador deve conseguir, em ambiente limpo:

```bash
git clone https://github.com/opmile/shortlist
cd shortlist
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run src/shortlist/app.py
```

E:
1. App abre sem erros
2. Tela Acervo lista filmes filtravelmente
3. Tela Estatísticas renderiza gráficos
4. Tela Recomendações permite trocar estratégia e ver resultado
5. Testes passam: `.venv/bin/pytest tests/ -v`

Tudo além disso é polimento.

---

## 13. Estrutura de pastas (proposta)

```
shortlist/
├── src/shortlist/
│   ├── __init__.py
│   ├── domain.py           # Filme + subclasses
│   ├── catalogo.py
│   ├── factory.py
│   ├── datasource.py       # ABC + CSV + JSON
│   ├── analisador.py
│   ├── recomendador.py     # ABC + 3 estratégias
│   └── app.py              # entry Streamlit
├── tests/
│   ├── conftest.py
│   ├── test_filme.py
│   ├── test_catalogo.py
│   ├── test_datasource.py
│   ├── test_factory.py
│   └── test_recomendador.py
├── lab/                    # exploração + ETL (gitignored exceto findings + aggregated)
│   ├── 01_load_kaggle.py
│   ├── 02_aggregate.py
│   ├── findings.md
│   └── aggregated.csv      # commitado pro avaliador rodar sem Kaggle
├── notebook/               # raciocínio do projeto (commitado)
│   ├── README.md
│   ├── doc/
│   ├── data/
│   └── engineering/
├── .venv/                  # gitignored
├── .gitignore
├── requirements.txt
├── README.md
└── spec.md                 # este arquivo
```

---

## 14. Próximo passo

Plan de implementação via skill `superpowers:writing-plans` — traduz spec em sequência executável de tarefas, branch por camada, ordem de entrega.
