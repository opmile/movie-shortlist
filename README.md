# shortlist

Catálogo de filmes como caso de estudo de engenharia: herança polimórfica **data-driven** (subclasses de `Filme` que emergem da distribuição real de um dataset de 25M ratings), dois design patterns formais (**Strategy** + **Repository**) e recomendação com critério (**CF item-based** + **rating bayesiano**). A UI é Streamlit.

## Estado atual

Repo em transição de uma primeira versão (CLI plana, herdada de um fork) para o produto descrito em `spec.md`.

- **Pronto:** o pipeline ETL (`etl/`) e seus snapshots — `aggregated.csv` (58.958 filmes agregados) e `neighbors.csv` (vizinhos do CF, pré-computados offline). O trabalho pesado (chunked groupby, matriz esparsa, cosseno) roda **uma vez**, fora do produto.
- **Em construção:** o pacote POO `src/shortlist/` (domínio, patterns, UI Streamlit) rumo ao `spec.md`.

O princípio central é **build-time vs run-time**: o produto consome só os snapshots estáticos; nunca toca o raw, a rede ou credencial Kaggle em runtime.

## Rodar

Regenerar os snapshots do ETL (offline, requer as deps de ETL):

```bash
python3 etl/build.py
```

A app Streamlit (`streamlit run src/shortlist/app.py`) e os testes (`pytest tests/ -v`) entram conforme o pacote `src/shortlist/` for construído.

## Por onde começar

- **`LEITURA.md`** — trilha de leitura ordenada por persona; comece aqui.
- **`spec.md`** — o **quê**: arquitetura-alvo consolidada.
- **`notebook/`** — o **porquê**: racional das decisões, alternativas, cortes de escopo (`notebook/faq.md` é a porta de entrada).
- **`CONTRIBUTING.md`** — como colaborar: branch, PR, CI.
