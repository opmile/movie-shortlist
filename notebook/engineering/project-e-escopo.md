# Definição do projeto e corte de escopo

**Data:** 2026-05-28

O que o projeto é (e não é), seu propósito, e o ROI do corte de escopo (4 patterns → 2).

---

## O que é

**Sistema interativo de catalogação de filmes** que:
1. Carrega filmes de uma fonte plugável (Repository pattern)
2. Classifica filmes polimorficamente conforme propriedades emergentes dos dados (herança POO)
3. Expõe busca, análise estatística e recomendação por estratégias intercambiáveis (Strategy pattern)
4. Apresenta tudo via UI Streamlit interativa

**Definição precisa:** sistema que carrega dados de uma fonte plugável, classifica filmes polimorficamente conforme propriedades emergentes dos dados, e expõe busca/análise/recomendação por estratégias intercambiáveis.

---

## O que NÃO é

| Não é | Por quê |
|---|---|
| ETL | A fase existe em `etl/aggregate.py` mas é one-shot offline. Não é o produto. |
| Recomendador puro | Recomendação é uma feature entre várias, não o foco. |
| Sistema de ML | Não treina modelo. Recomendação determinística (filter/sort + lookup de vizinhos pré-computados offline). |
| Backend / API | UI direta, sem cliente externo. |
| Aplicação de uso real | Ninguém escolhe filme real aqui. É demonstração arquitetural. |

---

## Propósito

**Produto de portfolio:** caso de estudo de engenharia onde se sai sabendo justificar escopo, aplicar 2 patterns clássicos (Strategy + Repository) com substância (não decoração) + herança/polimorfismo sobre problema real, justificar arquitetura em entrevista, e implementar TDD em domínio core. A recomendação tem critério — CF item-based + rating bayesiano — não é sort decorativo.

Critério de sucesso: clona repo, instala deps, roda app e navega telas sem erros; cada classe/abstração tem resposta clara pra "por que existe?"; testes demonstram a intercambiabilidade dos patterns.

É também a entrega de um Trabalho Final de POO, mas a doc descreve o **produto**. O racional consolidado de cada decisão vive em `../faq.md`.

---

## Nome do produto: `shortlist`

Lista curada/filtrada (o que `Recomendador` produz). Referência cinema sutil ("Oscar shortlist"). Repo: `github.com/opmile/shortlist` (público). Upstream: repo original do grupo — push final no fim do projeto.

---

## Corte de escopo — o que saiu e por quê

### Corte 1 — o pesado fica no ETL, o produto consome snapshots

O produto consome **só os snapshots estáticos do ETL** (`aggregated.csv`, `neighbors.csv`) — nunca o raw nem cálculo pesado em runtime.

**Fora do runtime (offline no `etl/`):** `KaggleDataSource` · chunked groupby · sparse matrix 200MB · cosine similarity (CF). Esse trabalho roda **uma vez** e emite tabelas; o produto só lê.

**No produto:** 59k filmes com `avg_rating`/`count`/`genres`/`year` + `weighted_rating` (bayesiano) · subclasses derivadas estatisticamente · 4 estratégias de recomendação via Strategy (gênero, nota, popularidade, **similar/CF**) · estatísticas pandas · Streamlit com 3 telas.

A separação build/runtime mantém o produto simples (sem ML, sem rede) **sem** abrir mão da feature de CF — o cosseno só não roda no request path. Detalhe: `../data/dataset-e-etl.md` · `../data/collab-filter.md`.

### Corte 2 — 2 patterns formais em vez de 4

POO fundamentals (sempre presentes, não contam como pattern): encapsulamento, herança, polimorfismo, abstração. **Patterns formais:** Strategy + Repository. **Dropped:** Factory (sem polimorfismo real de DataSource via instanciação dinâmica — detalhe em `design-patterns.md`).

---

## ROI da redução (por dimensão)

| Dimensão | Ambiciosa (4 patterns) | Enxuta (2) | Saldo |
|---|---|---|---|
| Patterns profundidade | 4 × ~1.5h | 2 × ~3h | **Ganho** — fundos > rasos |
| Patterns quantidade | 4 | 2 | Perda nominal (Factory é variação leve) |
| Engineering judgment | "implementei tudo" | "cortei X porque Y" | **Ganho** — skill de senioridade |
| Collab filtering | em runtime (caro, frágil) | offline no ETL → lookup O(1) | **Ganho** — feature entregue, custo de runtime nulo |
| Pandas / data eng | Chunked + sparse + agg | Read + filter + groupby | Perda mínima (agg já no ETL) |
| Justificativa de escopo | 4 pra explicar, risco "por que tantos" | 2 a fundo, "por que SÓ 2" vira força | **Ganho** |
| Buffer pra ir fundo | 0h | ~3-4h | **Ganho** — testes, refactor, 2ª passada |
| Risco de não entregar | Médio | Baixo | **Ganho** |

Dimensões neutras (empate): herança/POO fundamental, Python idiom, Streamlit.

---

## Veredito

ROI por hora investida **sobe** com a redução de *patterns* (4→2) — não é menos aprendizado, é aprendizado redistribuído pra coisas que multiplicam. Ambiciosa = buffet largo, prato raso. Enxuta = 2 pratos fundos que se carregam pra carreira. Strategy + Repository profundos são exatamente o que multiplica em qualquer stack (Spring, Go, Node, Python).

A redução é de **patterns**, não de produto: a recomendação ganhou substância — CF item-based (`RecomendaSimilar`) e rating bayesiano (`weighted_rating`) entram como 4ª estratégia + métrica de ranking, com o trabalho pesado **offline no `etl/`**. Runtime segue determinístico, sem ML, mas a recomendação deixa de ser sort decorativo: é "porque você gostou de X" e nota corrigida por confiança. Ver `../data/collab-filter.md` e `../data/rating-bayesiano.md`.

**Onde compensa:** saber **justificar escopo** vale 10× em entrevistas; patterns ficam internalizados, não decorados; sobra tempo pra testes (TDD = validação do core POO).

**Decisão final:** 2 patterns formais a fundo + 2 métricas de recomendação com substância (CF + bayesiano, ambas offline). Critério decisivo — aprendizado que multiplica > aprendizado que acumula superficialmente. **TDD:** imprescindível, acordado explicitamente (`tdd-e-workflow.md`).
