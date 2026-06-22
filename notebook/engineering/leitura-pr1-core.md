# Leitura guiada — PR 1 (core POO as-built)

**Data:** 2026-06-22

Sessão de leitura linha-a-linha do core do PR 1: `domain.py`, `factory.py`,
`datasource.py`, `catalogo.py`, `recomendador.py`. Foco duplo — **semântica de
domínio** (o que cada peça significa) e **sintaxe Python** (os idiomas que tropeçam
vindo de Go/Java). Costurado na ordem didática certa (a sessão pulou de camada;
aqui segue o fluxo natural do dado).

Ordem de leitura recomendada do core:

```
DataSource → FilmeFactory → domain (Filme+subclasses) → Catalogo → Recomendador
   (lê)        (traduz)         (modela)                 (guarda)     (consome)
```

---

## 1. `domain.py` — herança + o eixo de personalidade

`Filme` base (dataclass) + 4 subclasses (`FilmeAclamado`, `Blockbuster`,
`FilmeCult`, `Classico`). Campos espelham o `aggregated.csv`.

### `calcular_score()` — o eixo de PERSONALIDADE

Polimorfismo: mesma chamada, fórmula diferente por subclasse. Cada uma pondera o
eixo que define sua identidade. Sempre `avg_rating` + um bônus:

| Classe | fórmula | premia |
|---|---|---|
| `Filme` (base) | `avg_rating` | nada — nota crua |
| `FilmeAclamado` | `avg_rating * 1.5` | NOTA (elite avaliada) |
| `Blockbuster` | `avg_rating + log10(count)` | VOLUME (massa viu) |
| `FilmeCult` | `avg_rating + (37 - count)/37` | ESCASSEZ (nicho) |
| `Classico` | `avg_rating + (1970 - year)/100` | ANTIGUIDADE (tempo) |

**Por que `log10(count)` no Blockbuster — retornos decrescentes.** `count` tem
cauda longa brutal (6 → 81.491). Soma linear (`+count`) deixaria o filme gigante
esmagar tudo. Log comprime: cada ×10 votos soma só +1 ao bônus.

```
10 → 100      bônus +1.0   (10× mais votos)
10k → 100k    bônus +1.0   (também 10×, mesmo +1)
```

Os primeiros milhares de votos contam muito; milhões extras quase nada. Filme com
1M de votos ganhando +1M a mais sobe o bônus ~0.3 — já saturou como "blockbuster".
Reflete a realidade: dobrar votos de obscuro = sinal forte; dobrar votos de gigante
= ruído.

### Personalidade ≠ Confiança (ortogonais)

`calcular_score` (personalidade da subclasse) **não** é `weighted_rating` (rating
bayesiano, correção de confiança estatística). Separados de propósito: misturar
confundiria os dois papéis. `weighted_rating` vem do ETL como coluna própria;
`calcular_score` é método polimórfico. Detalhe: `../data/rating-bayesiano.md`.

### Sintaxe Python que apareceu

- `@dataclass` — gera `__init__`/`__repr__` a partir dos campos anotados.
- **Type-narrowing com `assert`:** `Classico.calcular_score` faz
  `assert self.year is not None` antes de `1970 - self.year`. O campo é
  `int | None` na base (vale pra todas subclasses), mas o `FilmeFactory` só
  instancia `Classico` com `year` presente. O `assert` (a) estreita o tipo pro
  Pylance parar de reclamar de `1970 - None`, e (b) vigia a invariante em runtime —
  se um dia vier `None`, estoura claro em vez de `TypeError` críptico.

---

## 2. `factory.py` — construtor com dispatch (factory-like, NÃO GoF)

`FilmeFactory.criar(d)` faz dois passos: **parse** (dict cru → campos limpos) +
**dispatch** (escolhe a subclasse por precedência).

### Por que reconstruir um dict se já recebe um dict

`d` (do DataSource) e `campos` são dicts **diferentes**. Factory **traduz**, não
copia. Três diferenças:

1. **Chaves:** CSV usa `Movie_Name` (casing do arquivo, chave de join com
   neighbors); `Filme` espera `movie_name`. Renomeação.
2. **Tipos:** CSV entrega tudo string (`count="1508"`); `Filme` quer `int`/`float`.
   Daí os casts (`int(float(...))` — float primeiro porque `int("1508.0")` estoura).
3. **Derivados:** `genres` `"Ação|Drama"` (str) → `["Ação","Drama"]` (list);
   `year` `""` → `None`.

`d` cru não serve pra `Filme(**d)` — chaves erradas dão `TypeError`, tipos errados
quebram comparações. `campos` é a ponte arquivo→domínio.

### Precedência = guard clauses

```
Classico > FilmeCult > Blockbuster > FilmeAclamado > Filme(base)
```

Sequência de `if`-com-`return`-precoce. Primeiro que bate vence (first-wins), resto
nem roda. **Ordem é contrato, não estética:** os critérios se sobrepõem na nota, e a
ordem fatia o eixo `count` em faixas limpas (Cult nicho → Aclamado médio →
Blockbuster massa), com Classico cortando por cima pelo tempo. Reordenar muda a
classificação. Números canônicos e a lógica completa: `../data/thresholds.md`.

### Sintaxe Python que apareceu

- `@staticmethod` — método sem `self`; chama `FilmeFactory.criar(d)` sem instanciar.
- `d["x"]` (crasha se faltar, "exijo") vs `d.get("x")` (devolve `None`, tolerante).
- `dict(a=1, b=2)` == `{"a":1,"b":2}` — forma com keyword args.
- `**campos` — **desempacota** o dict em argumentos nomeados:
  `Classico(**campos)` ≡ `Classico(movie_name=..., title=..., ...)`. Monta uma vez,
  espalha nos 5 returns.
- Comparação encadeada: `6 <= count <= 37` ≡ `count >= 6 and count <= 37`.
- **`dict[str, Any]` pra calar o Pylance:** o dict mistura tipos nos valores
  (`str|int|float|list`); sem anotar, o Pylance infere a união-monstro e reclama no
  `**campos` ("float não é str"). `Any` = "não cheque o tipo aqui". Caso oposto ao
  `assert` do domain: lá o Pylance estava certo (bug latente), aqui exagerava (era
  seguro). `Any` silencia ruído; `assert` prova segurança.

---

## 3. `datasource.py` — Repository pattern

```
DataSource (ABC) ── CSVDataSource / JSONDataSource
   carregar() -> list[dict]
```

ABC + `@abstractmethod` → contrato não-instanciável; subclasse obrigada a
implementar `carregar`. Cada impl lê de uma origem diferente, **devolve o mesmo
formato** (`list[dict]`). Trocar CSV→JSON = trocar 1 linha na borda; o resto fala
com o tipo abstrato e nem sabe qual é (injeção de dependência + polimorfismo).

**Decisão load-bearing — `list[dict]`, NÃO `list[Filme]`:** a fonte não pode
conhecer subclasses. Decidir Classico/Cult/etc é regra de domínio (thresholds), não
de leitura de arquivo. Cada camada com um trabalho:

```
DataSource (I/O) → list[dict] → FilmeFactory (domínio) → list[Filme] → Catalogo
```

### Sintaxe

- `with open(...) as f` — context manager; fecha o arquivo sozinho no fim do bloco.
- `csv.DictReader(f)` — cada linha vira dict usando o header como chaves.

---

## 4. `catalogo.py` — encapsulamento (POO fundamental, não pattern)

`Catalogo` embrulha uma `list[Filme]` e controla todo acesso. **Read-only após
construído.**

- `self._filmes = list(filmes)` — underscore = "privado" (convenção); `list(...)` =
  **cópia defensiva na entrada** (não guarda a referência recebida, senão quem
  passou poderia mutar por fora).
- `todos()` devolve `list(self._filmes)` — cópia defensiva **na saída** também;
  mexer no resultado não corrompe a interna.
- Filtros (`filtrar_por_genero`, `buscar_por_titulo`, `por_categoria`) sempre
  produzem lista **nova** via list comprehension. Zero mutação.
- `por_categoria` usa `f.categoria()` — polimorfismo do domain ligando as camadas.

**Por que read-only:** a instância é compartilhada entre reruns do Streamlit (via
`@st.cache_resource`); mutação vazaria entre sessões. Catálogo = snapshot estático,
sem `adicionar`/`remover` (build-time vs runtime).

### Sintaxe

- `__len__` (dunder) — liga o objeto ao `len()` nativo: `len(cat)`.
- List comprehension: `[f for f in self._filmes if cond]`.

---

## 5. `recomendador.py` — Strategy pattern

```
Recomendador (ABC) ── RecomendaPorNota / PorPopularidade / PorGenero / Similar
   recomendar(catalogo, n=5) -> list[Filme]
```

Mesma mecânica do Repository (ABC + polimorfismo), eixo diferente: pluga
**algoritmo**, não origem. Cada estratégia implementa `recomendar` com um critério.
UI escolhe em runtime sem `if` em quem chama.

| Estratégia | algoritmo |
|---|---|
| `RecomendaPorNota` | `sorted` por `weighted_rating` desc, top-n |
| `RecomendaPorPopularidade` | `sorted` por `count` desc |
| `RecomendaPorGenero(genero)` | filtra por gênero, depois ordena (estratégia com estado no `__init__`) |
| `RecomendaSimilar(titulo, vizinhos)` | lookup no mapa pré-computado, zero cálculo em runtime |

### `RecomendaSimilar` (resumo)

Recebe um filme-alvo e um mapa de vizinhança pré-computado no ETL
(`{filme: [parecidos em ordem]}`), pega os `n` mais parecidos, traduz esses nomes
nos objetos `Filme` do catálogo (pulando os ausentes) e devolve a lista. Puro
lookup — o cosseno (CF) rodou offline no ETL, runtime só consulta dict.

### `carregar_vizinhos` (resumo)

Lê o `neighbors.csv` (uma linha por par filme-vizinho, com `rank`), agrupa as linhas
por filme acumulando tuplas `(rank, vizinho)`, ordena cada grupo por rank e descarta
o rank — devolvendo o dict `{filme: [vizinhos em ordem de proximidade]}` que
`RecomendaSimilar` consome. Duas etapas porque o CSV vem espalhado: a tupla carrega
o rank só o tempo necessário pra ordenar, depois some.

### Sintaxe que apareceu (a mais densa da sessão)

- `sorted(lista, key=lambda f: f.campo, reverse=True)` — `key` diz por qual campo;
  `lambda` = função anônima (Java `f -> f.campo`); `reverse=True` = decrescente.
- `[:n]` — slice, top-n; seguro com lista curta (não estoura).
- `.get(chave, [])` / `.setdefault(chave, [])` — acesso a dict tolerante; `get` lê
  com default, `setdefault` cria-se-ausente (idioma de agrupamento).
- Dict comprehension: `{f.movie_name: f for f in ...}` — índice nome→Filme pra
  lookup O(1) (sem ele, busca linear por nome).
- List comprehension com guarda: `[por_nome[n] for n in nomes if n in por_nome]` —
  o `if` pula vizinhos ausentes do catálogo (senão `KeyError`).
- `for _, v in sorted(pares)` — **desempacotamento de tupla**; `_` = "descarto" (o
  rank, já usado pra ordenar). `sorted(tuplas)` ordena pelo 1º elemento.

---

## Fechamento — os 2 patterns formais

```
Repository (DataSource):   troca ORIGEM    → CSV / JSON
Strategy   (Recomendador): troca ALGORITMO → Nota / Popularidade / Genero / Similar
```

Mesma receita (ABC + impls + polimorfismo), eixos ortogonais. `FilmeFactory` é a
ponte entre eles — factory-like, não GoF. Conceito completo dos patterns:
`design-patterns.md`.
