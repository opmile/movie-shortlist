# Notebook — registro de raciocínio do projeto

Documentação do projeto `shortlist`: a especificação consolidada mais o registro de raciocínio — argumentos, alternativas consideradas, racional de cortes de escopo, conceitos discutidos. (Exploração técnica do pipeline fica em `etl/`.)

Lê pra: entender o que o projeto é e por que é assim · retomar contexto em sessões futuras · justificar decisões em portfolio/entrevista · reproduzir o raciocínio em projetos futuros.

---

## Referência consolidada

- [spec.md](spec.md) — a especificação do projeto: o que é construído, arquitetura, patterns, domínio, escopo. Ponto de partida quando precisa lembrar do todo.

## Porta de entrada — justificativas das decisões

- [faq.md](faq.md) — parágrafos objetivos e autossuficientes que explicam o racional de cada decisão. Destila as notas longas. Cada resposta linka pro detalhe técnico. Concentra o racional consolidado, mantendo as notas técnicas focadas no detalhe.

---

## `data/` — dados, estatística e ETL

- [dataset-e-etl.md](data/dataset-e-etl.md) — por que esse dataset, shape/schema, trade-off do schema fino, pipeline chunked groupby, build vs runtime, anomalias
- [thresholds.md](data/thresholds.md) — **fonte canônica** dos thresholds: distribuições/percentis, calibração das subclasses (pisos de count no Aclamado e Classico, Blockbuster em p95=1508) e precedência das guard clauses
- [collab-filter.md](data/collab-filter.md) — collab filter item-based (4ª estratégia `RecomendaSimilar`): matriz esparsa, cosseno, COO/CSR/CSC, dimensionamento (sparse 200MB), cosseno offline no `etl/` → `neighbors.csv`
- [rating-bayesiano.md](data/rating-bayesiano.md) — *weighted rating* (shrinkage estatístico) pra ranquear nota com confiança; conserta o ruído de poucos votos no acervo, calibrado em p75 do count

## `engineering/` — arquitetura, patterns e processo

- [project-e-escopo.md](engineering/project-e-escopo.md) — o que o projeto é (e não é), propósito (portfolio), ROI do corte de escopo (4 patterns → 2)
- [architecture.md](engineering/architecture.md) — camadas, contratos, fluxo de dados startup/runtime, encapsulamento do Analisador, código + precedência do FilmeFactory
- [design-patterns.md](engineering/design-patterns.md) — Strategy + Repository, FilmeFactory como factory-like (não GoF), DataSource dual, Repository desacopla formato mas não distribuição
- [tdd-e-workflow.md](engineering/tdd-e-workflow.md) — TDD seletivo no core POO + fluxo conceito → contrato → implementação
- [stack-and-tooling.md](engineering/stack-and-tooling.md) — Python, venv, deps, estrutura de pastas, git

---

## Convenção

- Notas datadas no topo
- Português pra prosa, termos técnicos em inglês; código em snippets quando ajuda
- Linkagem entre notas via path relativo (`[texto](../pasta/file.md)`)
- Atualizar ao invés de criar duplicata; thresholds só em `data/thresholds.md` (resto cross-referencia)
- Quando uma decisão muda, **atualizar in-place** refletindo o estado atual; reescrever a afirmação obsoleta, não anexar seção datada de histórico
