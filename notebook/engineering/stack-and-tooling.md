# Stack e tooling

**Data:** 2026-05-28

---

## Linguagem e versão

- **Python 3.13.3** (instalado globalmente via Python.org)
- Sem dependência de versão específica — qualquer 3.11+ funciona

---

## Isolamento: venv local, sem Docker

**Decisão:** `.venv/` no projeto, ativado via `.venv/bin/python` direto (sem `source activate`).

**Por que não Docker:**
- Velocidade de iteração: `python script.py` (0.2s) vs `docker run` (1-3s overhead por invocação)
- REPL / `python -i` mais ergonômico nativo
- Hot reload do Streamlit é mais rápido sem camada de filesystem Docker (macOS osxfs/virtiofs é lento)
- IDE + debugger funcionam out-of-the-box com interpretador local
- Docker Desktop come 2-4GB RAM constantes no mac
- Container vale pra deploy/CI — não pra dev solo num mac

**Regra geral:** Docker pra deploy/CI, venv pra dev. Padrão em empresas grandes também.

---

## Dependências do produto

```
streamlit          # UI
pandas             # análise (encapsulada em Analisador)
plotly             # gráficos interativos da tela Estatísticas
pytest             # testes
```

`matplotlib` **fora do produto**: os 4 charts da tela Estatísticas são plotly
(interativo, combina com a demo). Dep ociosa é pior que cortada — toda dep
justifica seu lugar. matplotlib segue só no `etl/` (plots exploratórios offline).

**Não usadas no produto (intencional):**
- ❌ `scipy` / `scikit-learn` — usados **só no `etl/`** (cosseno item-based do CF, offline). Ficam fora do `requirements.txt` do produto por design: o produto só lê `neighbors.csv`, então "sem ML/dep pesada em runtime" é literal. Detalhe: `../data/collab-filter.md`.
- ❌ `tensorflow` / `pytorch` — não há modelo treinado em lugar nenhum (CF é álgebra linear, não ML).
- ❌ `numpy` direto — pandas já puxa transitivamente
- ❌ `kagglehub` — só no `etl/`, não em runtime

---

## Dependências do `etl/` (separadas)

```
kagglehub[pandas-datasets]   # download de dataset
pandas                       # agregação
scipy                        # matriz esparsa (CSR/CSC) do CF
scikit-learn                 # cosine_similarity item-based do CF
matplotlib                   # plots exploratórios
```

`scipy`/`scikit-learn` vivem **só aqui**: o cosseno do collaborative filtering roda offline e emite `neighbors.csv`. O produto não os importa. `etl/` tem ciclo de vida independente — pode ter venv próprio ou compartilhar o do produto. Decisão atual: compartilhar (`.venv/` único).

---

## Arquivos de dependência

**`requirements.txt`** — produto, mínimo necessário pra rodar app:
```
streamlit
pandas
plotly
pytest
```

**`requirements-etl.txt`** (opcional, futuro) — deps de `etl/`:
```
kagglehub[pandas-datasets]
scipy
scikit-learn
```

Manter separação evita poluir `requirements.txt` do produto com deps de ETL/CF — e é o que preserva a claim "sem ML em runtime".

---

## Estrutura de pastas (proposta)

```
shortlist/
├── src/movie_manager/      # código do produto (a definir nome do pacote)
│   ├── __init__.py
│   ├── domain.py           # Filme + subclasses
│   ├── catalogo.py
│   ├── factory.py
│   ├── datasource.py       # ABC + 2 impls
│   ├── analisador.py
│   ├── recomendador.py     # ABC + 4 estratégias (inclui RecomendaSimilar)
│   └── app.py              # entry Streamlit
├── tests/
│   ├── conftest.py
│   ├── test_filme.py
│   ├── test_catalogo.py
│   ├── test_datasource.py
│   ├── test_factory.py
│   └── test_recomendador.py
├── etl/                    # pipeline build-time — estrutura/uso em etl/README.md
├── notebook/               # documentação de raciocínio (commitado)
│   ├── faq.md
│   ├── data/
│   └── engineering/
├── .venv/                  # gitignored
├── .gitignore
├── requirements.txt
├── README.md               # instruções de execução pra avaliador
└── spec.md                 # spec final do projeto
```

**Decisões pendentes:**
- Nome do pacote interno (`movie_manager`, `shortlist`, ou direto na raiz sem `src/`?)
- Commitar `aggregated.csv` ou regenerar via ETL? (Ver `notebook/data/dataset-e-etl.md`)

---

## Git

- **Repo principal:** `github.com/opmile/shortlist` (origin, público)
- **Repo upstream:** repo original do grupo (push final no fim do projeto)
- **Branch workflow:** branch por feature/camada, PRs revisados antes do merge na `main` (histórico documenta o racional de cada mudança)
- **Convenção de commit:** sem prefixo formal — mensagem clara e descritiva (escopo solo dispensa Conventional Commits)

---

## Auth Kaggle

- **Modo:** novo formato `~/.kaggle/access_token` (KGAT_*)
- **Local:** apenas no `etl/`, nunca em runtime do produto
- **Segurança:** token gerenciado fora do repo, nunca commitado

---

## IDE / Editor

- **VSCode** assumido (gitignore inclui `.vscode/`)
- **Interpretador**: apontar pra `.venv/bin/python` no settings
- **Extensão sugerida:** Pylance (typing) + ruff (lint/format)

---

## Critério "roda em ambiente limpo"

Avaliador deve conseguir:
```bash
git clone https://github.com/opmile/shortlist
cd shortlist
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run src/movie_manager/app.py
```

4 comandos, sem credencial Kaggle, sem download de 1.66GB. Pré-requisito: `aggregated.csv` commitado (ou regeneração via `etl/build.py` — ver `etl/README.md`).
