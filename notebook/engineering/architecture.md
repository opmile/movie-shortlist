# Arquitetura — camadas e responsabilidades

**Data:** 2026-05-28

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

**Base:** `Filme`
**Atributos:** `title`, `year`, `genres` (list[str]), `avg_rating`, `count`
**Métodos polimórficos:** `calcular_score() -> float`, `exibir() -> str`, `categoria() -> str`

**Subclasses:**
- `FilmeAclamado` — score pondera `avg_rating` mais
- `Blockbuster` — score pondera `count` mais (popularidade)
- `FilmeCult` — score pondera nicho (count médio, avg alto)
- `Classico` — score aplica bônus por antiguidade (decay temporal invertido)

Cada subclasse sobrescreve `calcular_score()` com fórmula coerente com sua identidade. Polimorfismo aplicado, não decorativo.

### 2. Construção — `FilmeFactory`

Recebe dict cru (do DataSource), aplica precedência de thresholds (`Classico > Cult > Blockbuster > Aclamado > Filme`), instancia subclasse correta.

**Status:** não é pattern Factory GoF formal — é "construtor com lógica de dispatch". Documentado como ajudante, não trabalhado como pattern.

Ver `notebook/data/thresholds.md` pra critérios.

### 3. Coleção — `Catalogo`

Encapsula `list[Filme]`. Expõe operações de alto nível: `buscar`, `filtrar_por_genero`, `filtrar_por_categoria`, `listar`, `adicionar`, `remover`.

**Princípio:** quem usa Catalogo nunca toca lista interna. Encapsulamento POO 101.

### 4. Persistência — `DataSource` ABC + impls

Repository pattern.

- `DataSource.carregar() -> list[dict]` — contrato abstrato
- `CSVDataSource(path)` — lê `aggregated.csv`
- `JSONDataSource(path)` — lê variante JSON

Retorna `list[dict]`, não `list[Filme]` — separação de concerns: DataSource não conhece subclasses; FilmeFactory decide.

### 5. Análise — `Analisador`

Encapsula pandas. Recebe `Catalogo`, expõe operações analíticas:
- `top_por_genero(n: int) -> dict[str, list[Filme]]`
- `distribuicao_notas() -> pd.Series`
- `media_por_categoria() -> dict[str, float]`
- `correlacao_ano_nota() -> float`

**Por que encapsular:** quem chama Analisador não vê DataFrame. Disciplina POO sobre lib data-oriented. Permite trocar pandas por polars no futuro sem mexer no resto.

### 6. Recomendação — `Recomendador` ABC + estratégias

Strategy pattern.

- `Recomendador.recomendar(catalogo, n) -> list[Filme]` — contrato
- `RecomendaPorGenero(genero)` — filtra
- `RecomendaPorNota` — ordena por `avg_rating`
- `RecomendaPorPopularidade` — ordena por `count`

### 7. UI — Streamlit

3 telas:
1. **Acervo** — lista filtrável por gênero/categoria, search por título
2. **Estatísticas** — gráficos do `Analisador` (top N, distribuição, correlação)
3. **Recomendações** — dropdown escolhe estratégia, mostra resultado

UI consome as camadas — não conhece pandas, não conhece `DataSource` concreto, só conhece interfaces de `Catalogo`, `Analisador`, `Recomendador`.

---

## Fluxo de dados

**Carga (1x no startup):**
```
DataSource.carregar() → list[dict]
        ↓
FilmeFactory.criar(dict) → Filme | Aclamado | Blockbuster | Cult | Classico
        ↓
Catalogo.adicionar(filme)
```

**Uso (em cada interação UI):**
```
UI → Catalogo / Analisador / Recomendador → list[Filme] → UI render
```

---

## Princípios respeitados

1. **Encapsulamento** — coleções nunca expostas cruas.
2. **Open/Closed** — adicionar nova subclasse/estratégia/fonte não exige mexer no código existente.
3. **Single responsibility** — cada classe responde a uma pergunta clara.
4. **Dependency inversion** — UI depende de abstrações (`Recomendador`, `Catalogo`), não de concretos.
5. **Separation of concerns** — ETL fora do produto; pandas isolado em `Analisador`.

---

## O que NÃO está nessa arquitetura

- ❌ Camada de cache (overkill pra 59k filmes em memória)
- ❌ Banco de dados (CSV agregado basta)
- ❌ Autenticação (sem usuários)
- ❌ API REST (UI direta)
- ❌ Logging estruturado (acadêmico; print serve)
- ❌ Configuração externa (.env, YAML) — paths hardcoded em `config.py` se necessário
