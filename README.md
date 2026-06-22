# shortlist 🎬

Catálogo interativo de filmes com análise estatística e recomendação por
estratégias intercambiáveis. Produto de portfolio: 2 design patterns formais
(Strategy + Repository) + herança/polimorfismo, sobre um dataset real de 25M
ratings reduzido a snapshots no build-time (ETL one-shot).

## Arquitetura

UI Streamlit → `Catalogo` (coleção encapsulada) / `Analisador` (encapsula pandas)
/ `Recomendador` (Strategy). `DataSource` (Repository) carrega `list[dict]`;
`FilmeFactory` despacha pra subclasse de `Filme` por precedência de thresholds.
O collaborative filtering (cosseno item-based) roda **offline no ETL** → o produto
só faz lookup. Sem ML em runtime.

## Rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/shortlist/app.py
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

TDD seletivo no core POO (domínio, factory, datasource, catalogo, recomendador,
analisador). UI sem teste.

## Documentação

Trilha de leitura ordenada em [`LEITURA.md`](LEITURA.md). Spec em
[`spec.md`](spec.md); raciocínio justificado em [`notebook/`](notebook/); ETL
build-time em [`etl/`](etl/).
