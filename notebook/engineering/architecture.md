# Arquitetura — camadas, responsabilidades e fluxo de dados

**Data:** 2026-05-28

Camadas, contratos de cada uma, e o fluxo de dados (startup e runtime).

---

## Visão geral

```
┌─────────────────────────────────────────────────────┐
│  UI (Streamlit)                                     │
│  3 telas: Acervo, Estatísticas, Recomendações       │
└──────┬──────────────────┬─────────────────┬────────┘
       │                  │                 │
       ▼                  ▼                 ▼
┌─────────────┐  ┌────────────────┐  ┌──────────────┐
│  Catalogo   │  │  Analisador    │  │ Recomendador │
│  (coleção)  │  │  (pandas API)  │  │  (Strategy)  │
└──────┬──────┘  └────────┬───────┘  └──────────────┘
       │                  │
       ▼                  │
┌─────────────────┐       │
│  Filme + sub    │◄──────┘
│  (herança POO)  │
└──────▲──────────┘
       │
┌──────┴───────────┐
│  FilmeFactory    │
│  (constrói sub)  │
└──────▲───────────┘
       │
┌──────┴───────────┐
│  DataSource ABC  │  ← Repository pattern
│  + CSV / JSON    │
└──────────────────┘
```

---

## Camadas

### 1. Domínio — `Filme` e subclasses

**Base `Filme`** — atributos `title`, `year`, `genres` (list[str]), `avg_rating`, `count`; métodos polimórficos `calcular_score() -> float`, `exibir() -> str`, `categoria() -> str`.

**Subclasses** (cada uma sobrescreve `calcular_score()` com fórmula coerente com sua identidade — polimorfismo aplicado, não decorativo):
- `FilmeAclamado` — pondera `avg_rating`
- `Blockbuster` — pondera `count` (popularidade)
- `FilmeCult` — pondera nicho (count médio, avg alto)
- `Classico` — bônus por antiguidade (decay temporal invertido)

### 2. Construção — `FilmeFactory`

Recebe dict cru do DataSource, aplica precedência de thresholds, instancia a subclasse correta. **Não é Factory GoF formal** — é construtor com lógica de dispatch (detalhe em `design-patterns.md`). Critérios em `../data/thresholds.md`.

### 3. Coleção — `Catalogo`

Encapsula `list[Filme]`. Expõe `buscar`, `filtrar_por_genero`, `filtrar_por_categoria`, `listar`, `adicionar`, `remover`. Quem usa nunca toca a lista interna — encapsulamento POO 101.

### 4. Persistência — `DataSource` ABC + impls (Repository)

`carregar() -> list[dict]` (contrato) · `CSVDataSource(path)` lê `aggregated.csv` · `JSONDataSource(path)` lê variante JSON. Retorna `list[dict]`, não `list[Filme]` — DataSource não conhece subclasses; FilmeFactory decide. Detalhe em `design-patterns.md`.

### 5. Análise — `Analisador` (encapsula pandas)

```python
class Analisador:
    def __init__(self, catalogo: Catalogo): ...
    def distribuicao_notas(self) -> pd.Series
    def media_por_categoria(self) -> dict[str, float]
    def contagem_por_categoria(self) -> dict[str, int]
    def correlacao_ano_nota(self) -> float
```

`contagem_por_categoria` (quantos filmes por subclasse) é a estrela da tela
Estatísticas: visualiza o dispatch de threshold do `FilmeFactory` funcionando.
Substituiu `top_por_genero` (tabular e sobreposto a `RecomendaPorGenero` — virava
tabela, não gráfico).

**Princípio:** pandas é detalhe interno. Ninguém fora vê `DataFrame`. Fluxo: construtor converte `list[Filme]` → `DataFrame` uma vez (guarda em `self._df` privado); cada método roda pandas no `_df`; converte resultado de volta a domínio antes de retornar. Trocar pandas → polars = reescrever só o interior.

**Exceção pragmática:** métodos de plot podem vazar `pd.Series` porque plotly consome direto — converter só pra reconverter seria cerimônia. A fronteira fica nos métodos de **dado de domínio**, não nos de **render**.

### 6. Recomendação — `Recomendador` ABC + estratégias (Strategy)

`recomendar(catalogo, n) -> list[Filme]` (contrato) · `RecomendaPorGenero(genero)` filtra · `RecomendaPorNota` ordena por `weighted_rating` (rating bayesiano) · `RecomendaPorPopularidade` ordena por `count` · `RecomendaSimilar(titulo)` faz lookup item-based em `neighbors.csv` (CF pré-computado no ETL). Detalhe em `design-patterns.md` · `../data/collab-filter.md`.

### 7. UI — Streamlit (3 telas)

1. **Acervo** → `Catalogo`: lista filtrável por gênero/categoria, search por título.
2. **Estatísticas** → `Analisador`: top N, distribuição, correlação.
3. **Recomendações** → `Recomendador`: dropdown escolhe estratégia, mostra resultado.

UI consome interfaces (`Catalogo`, `Analisador`, `Recomendador`) — não conhece pandas nem `DataSource` concreto.

---

## Fluxo de dados

### Startup (1×)

```
CSV/JSON → DataSource.carregar() → list[dict] → FilmeFactory.criar() → Filme(subclasse) → Catalogo.adicionar()
```

1. **DataSource lê fonte → `list[dict]`** (`{title, year, genres, avg_rating, count, weighted_rating}`). Não conhece `Filme`. Fronteira do Repository.
2. **FilmeFactory recebe cada dict → decide subclasse** por thresholds em ordem de precedência (first-wins).
3. **Instancia subclasse** (cada uma com `calcular_score` próprio = polimorfismo).
4. **Catalogo.adicionar()** acumula numa coleção encapsulada — fonte única pra UI/Analisador/Recomendador.
5. **`neighbors.csv` carregado à parte** (tabela estática emitida pelo ETL, schema tidy `Movie_Name, rank, vizinho, sim`) — `RecomendaSimilar` indexa via `groupby("Movie_Name")` → dict de `(vizinho, sim)` no load (`@st.cache_data`), depois lookup O(1). Não passa pela Factory: é dado de relação entre filmes, não atributo de um filme. Detalhe: `../data/collab-filter.md`.

`weighted_rating` (rating bayesiano) já vem pronto na coluna do `aggregated.csv` (pré-computado no ETL) — `RecomendaPorNota` e a tela Acervo só leem. É métrica de **confiança** ortogonal ao `calcular_score` da subclasse (que é o eixo de *personalidade*), por isso vive como coluna/atributo, não dentro do score. Detalhe: `../data/rating-bayesiano.md`.

**Separação chave:** DataSource conhece **formato** (CSV vs JSON), ignora domínio; Factory conhece **domínio** (regras de classificação), ignora formato. Por isso `carregar()` devolve `dict`, não `Filme`: trocar CSV→JSON não toca a Factory; mudar threshold não toca o DataSource.

### Runtime (cada interação UI)

```
UI → Catalogo | Analisador | Recomendador → list[Filme] → render
```

3 telas, cada uma bate numa camada; todas leem o **mesmo** `Catalogo` em memória, sem reler disco. Polimorfismo reaparece no ranking: `calcular_score()` difere por subclasse — mesma chamada, comportamento por tipo. Startup = disco→objetos (1×); uso = objetos→view (N×, barato).

**Pré-requisito sob Streamlit:** "startup 1×" e "mesmo `Catalogo` em memória" só valem porque o build é **fixado por memoização de rerun**. O Streamlit re-executa o script inteiro a cada interação; sem pin, o load+build de 59k re-rodaria por clique. Alvos:

| Alvo | Decorator | Por quê |
|---|---|---|
| `build_catalogo() -> Catalogo` | `@st.cache_resource` | objeto singleton-scoped; devolve **mesma ref** entre reruns (sem copiar) |
| parse de `aggregated.csv` / DataFrame | `@st.cache_data` | dado serializável; devolve **cópia** isolada |
| `neighbors.csv` (lookup do `RecomendaSimilar`) | `@st.cache_data` | tabela estática lida 1×, reusada |

`cache_resource` (não `cache_data`) no `Catalogo` porque é objeto vivo compartilhado — quer a mesma ref, não cópia. Corolário: `Catalogo` fica **read-only pós-build** (filtro/busca devolve `list[Filme]` nova, não muta a coleção interna), senão a ref compartilhada vaza entre sessões. Não é Singleton GoF — é escopo de lifecycle gerido pela infra (`design-patterns.md`). Distinção dos 3 sentidos de "cache" em `../data/dataset-e-etl.md`.

---

## FilmeFactory — código e precedência

```python
class FilmeFactory:
    @staticmethod
    def criar(dado: dict) -> Filme:
        year, count, avg = dado["year"], dado["count"], dado["avg_rating"]
        if year is not None and year <= 1970 and count >= 37:
            return Classico(**dado)
        if 6 <= count <= 37 and avg >= 3.9:
            return FilmeCult(**dado)
        if count >= 1508:
            return Blockbuster(**dado)
        if avg >= 4.0 and count >= 6:
            return FilmeAclamado(**dado)
        return Filme(**dado)
```

`if` sequencial com `return` (não `elif`, não score): o `return` no primeiro match embute precedência na ordem de leitura. A ordem dos blocos **é** a regra `Classico > FilmeCult > Blockbuster > FilmeAclamado > Filme`. Reordenar muda a classificação — ordem é contrato. Justificativa completa dos thresholds e da ordem em `../data/thresholds.md`.

Anomalia: `year is None` (527 filmes, 0.9%) — guarda `year is not None` evita crash no `<=`, cai no fallback.

---

## Princípios respeitados

1. **Encapsulamento** — coleções nunca expostas cruas.
2. **Open/Closed** — adicionar subclasse/estratégia/fonte não exige mexer no existente.
3. **Single responsibility** — cada classe responde a uma pergunta clara.
4. **Dependency inversion** — UI depende de abstrações, não de concretos.
5. **Separation of concerns** — ETL fora do produto; pandas isolado no `Analisador`.

---

## O que NÃO está nessa arquitetura

- ❌ Cache **de domínio** runtime (memoizar query/filtro) — overkill: 59k em memória, filtro/sort em ms. Os CSVs do ETL são a camada de "cache" via precompute. ⚠️ Distinto da **memoização de rerun do Streamlit** (`@st.cache_resource`/`@st.cache_data`), que **é** usada — não por perf de domínio, mas porque o Streamlit re-executa o script a cada interação (ver Fluxo runtime abaixo e `../data/dataset-e-etl.md`)
- ❌ Banco de dados (CSV agregado basta)
- ❌ Autenticação (sem usuários)
- ❌ API REST (UI direta)
- ❌ Logging estruturado (acadêmico; print serve)
- ❌ Configuração externa (.env/YAML) — paths hardcoded em `config.py` se necessário
