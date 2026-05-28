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
matplotlib         # gráficos básicos (Estatísticas)
plotly             # gráficos interativos no Streamlit (opcional)
pytest             # testes
```

**Não usadas (intencional):**
- ❌ `scipy` — collab filtering deferred to v2
- ❌ `scikit-learn` — content-based deferred (sem texto rico no dataset)
- ❌ `tensorflow` / `pytorch` — overkill pra POO TFD
- ❌ `numpy` direto — pandas já puxa transitivamente
- ❌ `kagglehub` — só no `lab/`, não em runtime

---

## Dependências do `lab/` (separadas)

```
kagglehub[pandas-datasets]   # download de dataset
pandas                       # agregação
matplotlib                   # plots exploratórios
```

`lab/` tem ciclo de vida independente — pode ter venv próprio ou compartilhar o do produto. Decisão atual: compartilhar (`.venv/` único).

---

## Arquivos de dependência

**`requirements.txt`** — produto, mínimo necessário pra rodar app:
```
streamlit
pandas
matplotlib
plotly
pytest
```

**`requirements-lab.txt`** (opcional, futuro) — deps de `lab/`:
```
kagglehub[pandas-datasets]
```

Manter separação evita poluir `requirements.txt` do produto com deps de ETL.

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
│   ├── recomendador.py     # ABC + 3 estratégias
│   └── app.py              # entry Streamlit
├── tests/
│   ├── conftest.py
│   ├── test_filme.py
│   ├── test_catalogo.py
│   ├── test_datasource.py
│   ├── test_factory.py
│   └── test_recomendador.py
├── lab/                    # ETL + exploração (gitignored exceto findings)
│   ├── 01_load_kaggle.py
│   ├── 02_aggregate.py
│   ├── findings.md
│   └── aggregated.csv      # commitar! avaliador roda sem Kaggle
├── notebook/               # documentação de raciocínio (commitado)
│   ├── doc/
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
- Commitar `aggregated.csv` ou regenerar via lab? (Ver `notebook/data/etl-pipeline.md`)

---

## Git

- **Repo principal:** `github.com/opmile/shortlist` (origin, público)
- **Repo upstream:** repo original do grupo (push final no fim do projeto)
- **Branch workflow:** branch por feature/camada, PRs revisados antes do merge na `main` (histórico vira material de defesa)
- **Convenção de commit:** sem prefixo formal — mensagem clara e descritiva (escopo solo dispensa Conventional Commits)

---

## Auth Kaggle

- **Modo:** novo formato `~/.kaggle/access_token` (KGAT_*)
- **Local:** apenas no `lab/`, nunca em runtime do produto
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

4 comandos, sem credencial Kaggle, sem download de 1.66GB. Pré-requisito: `aggregated.csv` commitado (ou instruções de regeneração via `lab/02_aggregate.py` no README).
