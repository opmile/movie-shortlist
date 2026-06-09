# Guia de leitura — como absorver o projeto `shortlist`

Esse projeto tem muitos artefatos: spec, notebook (9 arquivos), etl, código. Sem ordem, vira labirinto. Esse arquivo é a **trilha pedagógica** pra ler com retorno máximo, sem perder tempo conectando peças.

---

## Princípio

Cada artefato tem **função distinta**:

| Artefato | Função | Quando ler |
|---|---|---|
| `spec.md` | O QUÊ — referência consolidada | Primeira leitura, ou quando precisa lembrar do escopo |
| `notebook/` | POR QUÊ — raciocínio justificado | Quando vai mexer numa decisão / defender na banca |
| `etl/` | PIPELINE — ETL build-time + snapshots | Quando vai mexer em dados / ETL / retomar collab filter |
| `src/` | IMPLEMENTAÇÃO — código vivo | Quando vai codar |
| `tests/` | CONTRATO VERIFICÁVEL | Quando muda comportamento |
| `CONTRIBUTING.md` | COMO COLABORAR — branch, PR, CI | Antes do primeiro PR / ao entrar no grupo |

Regra de ouro: **nunca pula spec.md.** É o mapa.

---

## Trilha principal (60 min total, leitura concentrada)

Sequência otimizada pra construir o modelo mental do projeto sem retrocessos.

### Fase 1 — Orientação (5 min)
1. **`README.md`** (raiz) — o que é o projeto, como rodar
2. **`spec.md`** seções 1-3 (visão geral, propósito, definição)

Saída: você sabe o que `shortlist` é e o que não é.

### Fase 2 — Arquitetura (15 min)
3. **`notebook/engineering/project-e-escopo.md`** — definição precisa, propósito duplo, ROI do corte de escopo
4. **`notebook/engineering/architecture.md`** — camadas, contratos, fluxo startup/runtime, encapsulamento do Analisador
5. **`notebook/engineering/design-patterns.md`** — Strategy + Repository, FilmeFactory factory-like, snippets de contrato

Saída: você sabe quais patterns existem e onde aplicam.

### Fase 3 — Dados (15 min)
6. **`notebook/data/dataset-e-etl.md`** — por que esse dataset, shape/schema, trade-off, pipeline chunked, build vs runtime, anomalias
7. **`notebook/data/thresholds.md`** — fonte canônica: distribuições/percentis, calibração das subclasses + precedência
8. **`etl/findings.md`** — números brutos do dataset

Saída: você sabe de onde vem `aggregated.csv` e o que está nele.

### Fase 4 — Disciplina de processo (10 min)
9. **`notebook/engineering/tdd-e-workflow.md`** — conceito → contrato → implementação + TDD seletivo no core
10. **`notebook/engineering/stack-and-tooling.md`** — venv, deps, estrutura de pastas

Saída: você sabe **como** vai trabalhar no projeto.

### Fase 5 — Munição de banca (10 min, opcional)
11. **`notebook/faq.md`** — parágrafos objetivos que justificam cada decisão, prontos pra defender
12. **`notebook/data/collab-filter-deferred.md`** — análise do que foi adiado pra v2

Saída: você tem munição de banca pra perguntas tipo "por que essa escolha?"

---

## Atalhos por persona

### Voltando ao projeto após pausa (10 min)
Foco em retomar contexto sem ler tudo de novo.

1. `spec.md` (skim)
2. `notebook/engineering/project-e-escopo.md`
3. `notebook/data/thresholds.md`
4. Último commit (`git log -5`)

### Avaliador / banca (20 min)
Foco em entender e ter pra perguntar.

1. `README.md`
2. `spec.md` (completo)
3. `notebook/engineering/architecture.md`
4. `notebook/engineering/design-patterns.md`

### Antes de codar uma camada nova (15 min)
Foco em ter contrato + conceito frescos.

1. `spec.md` seção da camada
2. `notebook/engineering/tdd-e-workflow.md`
3. `notebook/engineering/design-patterns.md` (se for camada com pattern)

### Pra estudar profundidade / aprender (60+ min)
Foco em internalizar raciocínio.

Trilha principal completa, no ritmo. `faq.md` no fim consolida o "porquê" de cada decisão.

### Pra retomar collab filter (v2, futuro) (20 min)
1. `notebook/data/collab-filter-deferred.md`
2. `etl/findings.md` (dimensionamento da matriz)
3. `etl/aggregated.csv` (input pra reusar)

---

## Mapa visual

```
                    ┌────────────────────┐
                    │  README.md (raiz)  │ ← entrada
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     spec.md        │ ← referência (sempre volta aqui)
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│  notebook/    │    │     etl/       │    │    src/      │
│  faq.md       │    │  findings.md   │    │   código     │
│  engineering/ │    │  aggregated    │    │              │
│  data/        │    │  scripts ETL   │    │  tests/      │
└───────────────┘    └────────────────┘    └──────────────┘
   POR QUÊ              PIPELINE (ETL)        COMO
```

---

## Como manter esse fio vivo

Toda vez que algo novo for criado no projeto:

1. **Atualizar `spec.md`** se a decisão arquitetural mudou
2. **Criar/atualizar nota em `notebook/`** se há raciocínio novo a preservar
3. **Atualizar este `LEITURA.md`** apenas se a estrutura de pastas mudou ou nova categoria de artefato foi adicionada
4. **Atualizar `notebook/README.md`** se nota nova for criada
5. **Atualizar `CONTRIBUTING.md`** se o fluxo de colaboração (branch, PR, CI) mudar

Sem rituals desnecessários. Notebook é vivo, não bibliografia.

---

## Anti-pattern: leitura em rabbit hole

Não fazer:
- Abrir `notebook/engineering/design-patterns.md` sem antes ter lido `architecture.md` (contexto)
- Tentar entender thresholds sem ter lido `dataset-e-etl.md`
- Reler tudo a cada sessão — usar os atalhos por persona

Fazer:
- Seguir trilha principal **uma vez** na primeira leitura
- Depois usar atalhos conforme tarefa
- `spec.md` é o farol — quando perdida, volta pra ele

---

## Tempo médio por sessão de trabalho

| Atividade | Tempo de leitura prep | Tempo de trabalho |
|---|---|---|
| Codar uma camada nova | ~15min | ~45-60min |
| Defender camada na banca | ~30min | — |
| Retomar projeto após 1 semana | ~10min | depende |
| Refatorar uma decisão | ~20min | ~30-60min |

Leitura preparatória SEMPRE rende mais que improvisar.
