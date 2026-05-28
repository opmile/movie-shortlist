# Conversa — natureza do projeto, ETL e dataset

**Data:** 2026-05-28
**Contexto:** discussão pra dar passo atrás antes de escrever spec. Pergunta central: que projeto é esse, de fato? Por que esse dataset? A agregação enriquece ou foi overengineering?

---

## Pergunta 1 — Que projeto é esse, de fato?

**Definição precisa:** sistema interativo de catalogação de filmes que carrega dados de uma fonte plugável (Repository), classifica filmes polimorficamente conforme propriedades emergentes dos dados (herança POO), e expõe operações de busca, análise estatística e recomendação por estratégias intercambiáveis (Strategy).

**Não é:**
- ❌ ETL — a fase ETL existe (`lab/02_aggregate.py`), mas é one-shot offline, não é o produto.
- ❌ Recomendador puro — recomendação é uma das features, não o foco.
- ❌ Sistema de ML — não treina modelo; recomendação é determinística.
- ❌ Backend / API — UI Streamlit é direta, sem cliente externo.

**Propósito duplo:**

1. **Acadêmico (TFD POO):** demonstrar 2 patterns formais (Strategy + Repository) + herança/polimorfismo trabalhando juntos sobre problema com substância. Defender cada decisão arquitetural na banca.

2. **Pessoal/portfólio:** caso de estudo de engenharia onde se sai sabendo defender escopo, aplicar patterns e justificar arquitetura — não só "fiz CRUD em Python".

---

## Pergunta 2 — Agregação, dataset e overengineering

### a) Por que a agregação foi necessária?

Dataset bruto = 25M linhas de `(user, movie, rating)`. Cada linha é evento, não entidade.

Mas o domínio do projeto trata `Filme` como **entidade** com propriedades agregadas (`avg_rating`, `count`, `year`, `genres`). Precisa transformar eventos → entidades.

Sem agregação: 25M rows em memória inviável, "qual nota média de Pulp Fiction" exige scan de 25M, subclasses por threshold de stat não podem existir.

Com agregação: 59k entidades com stats pré-calculadas, subclasses atribuídas no load, queries O(1) ou O(n=59k).

Data engineering 101. Sem agregação, o domínio não fecha.

### b) Por que ETL separado e não consumir Kaggle direto no app?

Hipótese alternativa: app baixa 1.66GB do Kaggle no startup, agrega na hora, usa.

Problemas:
- Cold start de minutos
- Credencial Kaggle exigida em todo ambiente
- Dependência de rede no startup
- Não roda offline
- Banca tentar rodar → trava esperando
- Cada `streamlit run` repete pipeline pesado

Solução adotada:
- ETL roda **uma vez** offline → produz `aggregated.csv` (3MB)
- App consome o artefato direto
- Startup instantâneo, sem rede, sem credencial

Padrão industrial: build-time pipelines (Airflow/dbt) produzem snapshots; aplicações consomem snapshots. Mesmo princípio.

### c) Por que esse dataset e não um mais simples?

**Sinceridade:** se começasse hoje, um TMDB top-5k com metadata rica (~10MB) seria mais simples e habilitaria content-based recommendation. Não foi erro catastrófico — escolha foi feita antes de saber o shape real.

**O que justifica manter:**

1. **Subclasses emergentes** — `FilmeAclamado`, `Cult`, `Blockbuster`, `Classico` derivam de distribuição estatística real (percentis de 59k filmes). Com dataset pequeno curado, subclasses virariam etiquetas hardcoded. Aqui são emergência de dados — defensável.

2. **Volume "de verdade"** — 25M ratings, 162k users. Pipeline aguentou dado real. "Processei 1.66GB com chunked groupby" entra no currículo.

3. **Polimorfismo defensável** — subclasse não é flag (`if genre=='Documentary'`). É decisão de threshold sobre stats agregadas. Decisão arquitetural real.

**O que perdemos:**
- Content-based via TF-IDF (precisa de texto rico tipo `overview`)
- `FilmeNacional` (precisa de `country`/`language`)
- Variação de subclasses tipo `Documentario`, `Serie`

### d) ETL enriqueceu ou foi overengineering?

**Foi os dois, saldo positivo:**

**Enriqueceu:**
- `lab/02_aggregate.py` ficou como aprendizado em chunked groupby + percentis. Vai pro currículo.
- `aggregated.csv` é artefato real, não mock.
- Subclasses só fazem sentido com agregação. Sem ela = etiquetas hardcoded, polimorfismo decorativo.
- Defesa na banca ganha substância arquitetural: separação build/runtime.

**Foi overengineering parcial:**
- Pra só passar no TFD POO, 200 filmes hardcoded teriam bastado.
- Complexidade do pipeline (1.66GB, chunks, percentis) era desnecessária pro critério mínimo.
- 1-2h gastas no lab que não viram código de produto.

**Saldo líquido positivo. Razões:**

1. Lab foi sessão separada — não consumiu tempo do projeto principal.
2. Substância pra defesa cresceu desproporcionalmente ao tempo investido.
3. ETL é skill multiplicador — vai aparecer em qualquer trabalho de dados/backend.
4. Eliminar hoje exigiria trocar dataset → re-rodar lab inteiro. Custo > benefício marginal.

**Onde foi de fato overengineering:** sistema original que tinha `KaggleDataSource` rodando pipeline em runtime. Cortado. ETL ficou em `lab/`, fora do produto.

**Regra pra projetos futuros:** se ETL > 30% do projeto principal, trocar dataset. Aqui ficou ~10% (lab paralelo). Aceitável.
