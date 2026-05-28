# Notebook — registro de raciocínio do projeto

Pasta dedicada ao histórico de decisões, conversas e fundamentos do projeto `shortlist`. Diferente de `lab/` (exploração técnica) e de `spec.md` (especificação consolidada), aqui mora o **porquê** — argumentos, alternativas consideradas, racional de cortes de escopo, conceitos discutidos.

Lê pra:
- Entender por que o projeto é como é
- Retomar contexto em sessões futuras com Claude
- Defender decisões na banca
- Reproduzir o raciocínio em projetos futuros

---

## Estrutura

### `doc/` — conversas e explicações
Diálogos densos, didáticos, com argumentação completa. Salva o **raciocínio** do Claude em respostas relevantes.

- [01-natureza-do-projeto-e-etl.md](doc/01-natureza-do-projeto-e-etl.md) — o que é o projeto, por que ETL, por que esse dataset
- [02-roi-reducao-complexidade.md](doc/02-roi-reducao-complexidade.md) — análise de ROI do corte de escopo

### `data/` — decisões sobre dados, estatística e ETL
- [thresholds.md](data/thresholds.md) — thresholds calibrados das subclasses + precedência
- [dataset-rationale.md](data/dataset-rationale.md) — por que esse dataset, shape descoberto
- [etl-pipeline.md](data/etl-pipeline.md) — chunked groupby, build vs runtime
- [collab-filter-deferred.md](data/collab-filter-deferred.md) — collab filter analisado e adiado pra v2

### `engineering/` — decisões de arquitetura e engenharia
- [project-definition.md](engineering/project-definition.md) — o que o projeto é (e o que não é)
- [design-patterns.md](engineering/design-patterns.md) — Strategy + Repository escolhidos, Factory rejeitado
- [architecture.md](engineering/architecture.md) — camadas, fluxo de dados, princípios
- [tdd-scope.md](engineering/tdd-scope.md) — TDD seletivo no core POO
- [workflow.md](engineering/workflow.md) — conceito → contrato → implementação
- [stack-and-tooling.md](engineering/stack-and-tooling.md) — venv, Python, deps, estrutura de pastas

---

## Convenção

- Notas datadas no topo
- Português pra prosa, código em snippets quando ajuda
- Linkagem entre notas via path relativo (`[texto](../pasta/file.md)`)
- Atualizar ao invés de criar duplicata
- Quando uma decisão muda, **manter histórico** (riscar ou adicionar seção "atualização YYYY-MM-DD")
