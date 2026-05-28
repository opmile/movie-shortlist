# Definição do projeto

**Data:** 2026-05-28

---

## O que é

**Sistema interativo de catalogação de filmes** que:
1. Carrega filmes de uma fonte plugável (Repository pattern)
2. Classifica filmes polimorficamente conforme propriedades emergentes dos dados (herança POO)
3. Expõe operações de busca, análise estatística e recomendação por estratégias intercambiáveis (Strategy pattern)
4. Apresenta tudo via UI Streamlit interativa

---

## O que NÃO é

| Não é | Por quê |
|---|---|
| ETL | A fase ETL existe em `lab/02_aggregate.py` mas é one-shot offline. Não é o produto. |
| Recomendador puro | Recomendação é uma feature entre várias, não o foco. |
| Sistema de ML | Não treina modelo. Recomendação determinística via filter/sort. |
| Backend / API | UI direta, sem cliente externo. |
| Aplicação de uso real | Banca não vai escolher filme aqui. É demonstração arquitetural. |

---

## Propósito duplo

### 1. Acadêmico (TFD POO)
Demonstrar 2 design patterns formais (Strategy + Repository) + herança/polimorfismo trabalhando juntos sobre problema com substância. Cada decisão arquitetural defensável na banca.

**Critério de sucesso (banca):**
- Avaliador clona repo, instala deps, roda app, navega telas, sem erros
- Cada classe/abstração tem resposta clara pra "por que essa existe?"
- Testes demonstram intercambiabilidade dos patterns

### 2. Pessoal / portfolio
Caso de estudo de engenharia onde se sai sabendo:
- Defender escopo (skill de senioridade)
- Aplicar patterns clássicos com substância (não decoração)
- Justificar arquitetura em entrevista
- Implementar TDD em domínio core

---

## Nome do produto: `shortlist`

Significado funcional: lista curada/filtrada (o que `Recomendador` produz).
Referência cinema sutil: "Oscar shortlist", festival shortlists.
Tom: tech, sem arrogância, defensável em CV.

Repo: `github.com/opmile/shortlist` (público).
Upstream: repo original do grupo — push final no fim do projeto.

---

## Dataset

`chaitanyahivlekar/large-movie-dataset` (Kaggle) — 25M ratings, 162k users, 59k filmes.
Sistema consome forma **agregada** (`lab/aggregated.csv`, ~3MB), não o raw.
Ver `notebook/data/dataset-rationale.md` e `notebook/data/etl-pipeline.md`.
