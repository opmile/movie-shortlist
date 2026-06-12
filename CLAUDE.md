# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Two states of this repo

There is a **gap between what's built and what's specified**. Do not assume the spec describes the current code.

- **Built (committed, working):** a flat CLI app at the repo root — `filme.py`, `catalogo.py`, `persistencia.py`, `main.py`, reading `filmes.csv`. Simple `Filme(titulo, ano, genero, diretor, nota)`, interactive menu loop. This is the inherited first version (forked from `juliacoit/movie-dataset-manager-poo`).
- **Specified (planned, mostly NOT built yet):** a full rewrite into a `src/shortlist/` package with Streamlit UI, a `Filme` base + 4 subclasses, Strategy + Repository patterns, and a kaggle-derived `aggregated.csv`. Defined in `spec.md`; **does not exist on disk yet**.

When asked to implement, you are almost always moving the repo **toward the spec**, replacing the flat root files — not extending them. The two data schemas are different and incompatible:

- Current `filmes.csv`: `titulo, ano, genero, diretor, nota` (hand-curated, tiny).
- Target `aggregated.csv`: `title, year, genres (pipe-list), avg_rating, count` (58,958 rows, ETL-derived).

## Running

```bash
python3 main.py          # current CLI app (no deps, stdlib csv only)
```

Planned (once the rewrite exists): `streamlit run src/shortlist/app.py` and `pytest tests/ -v`. There is **no `requirements.txt`, no `tests/`, and no `.venv/` yet** — create them when building toward the spec (deps: `streamlit, pandas, matplotlib, plotly, pytest`).

## The documentation system — read before coding

This project is documentation-heavy by design. The artifacts have **distinct, non-overlapping roles**; respect them when reading and when writing:

- **`spec.md`** — the **WHAT**. Consolidated reference for target architecture. The north star. When confused, return here.
- **`notebook/`** — the **WHY**. Justified reasoning, alternatives considered, scope-cut rationale, consolidated design rationale. `notebook/faq.md` is the distilled entry point. `notebook/data/thresholds.md` is the **canonical source** for subclass thresholds (do not duplicate threshold numbers elsewhere — cross-reference it).
- **`etl/`** — the **PIPELINE** (was `lab/`). Versioned build-time ETL: numbered scripts + the snapshots they emit (`aggregated.csv`, `neighbors.csv`) + `etl/findings.md` (raw dataset stats). Runs **once** offline to produce the snapshots the product consumes; the ETL itself is never imported at runtime — `scipy`/`scikit-learn`/`kagglehub` stay out of the product deps. Only regenerated artifacts (`*.png`) are gitignored.
- **`LEITURA.md`** — the **reading trail**. Ordered path through all the above with per-persona shortcuts. Start here when onboarding.

When a decision changes: update `spec.md` if architecture shifted, and edit the relevant `notebook/` note **in place to reflect the current source of truth** — rewrite the obsolete claim, don't append a dated "Atualização YYYY-MM-DD" section preserving old rationale. The gradual evolution of understanding is implicit; the doc carries only the current state ("it used to be X, now it's Y" history is noise). Update `LEITURA.md` only if folder structure changed.

## Conventions

- **Language:** prose and identifiers are **Portuguese** (`titulo`, `adicionar_filme`, `Catalogo`); technical terms stay English. Match this — don't anglicize the domain.
- **Notebook notes:** dated at top; link between notes via relative paths; update-in-place rather than duplicate.
- **Build-time vs run-time** is a core principle: the system consumes a static snapshot; it never hits Kaggle or the network at runtime.

## Target architecture (from spec.md, for when you build it)

Layered: Streamlit UI → `Catalogo` (encapsulated collection) / `Analisador` (encapsulates pandas) / `Recomendador`. Two formal GoF patterns:

- **Strategy** — `Recomendador` ABC with `RecomendaPorGenero/PorNota/PorPopularidade`.
- **Repository** — `DataSource` ABC with `CSVDataSource/JSONDataSource`, returning `list[dict]` (not `list[Filme]` — it must not know subclasses).

`FilmeFactory` maps dicts → the right `Filme` subclass (`Classico`, `FilmeCult`, `Blockbuster`, `FilmeAclamado`, base `Filme`) by applying threshold guard clauses in strict **precedence order**: `Classico > FilmeCult > Blockbuster > FilmeAclamado > Filme`. It is treated as a "constructor with dispatch", **not** a formal Factory pattern — don't frame it as GoF.

TDD is **selective**: required on the POO core (`Filme`+subclasses, `Catalogo`, `DataSource`, `FilmeFactory`, `Recomendador`, with `parametrize` to exercise Strategy/Repository directly); minimal on `Analisador`; none on Streamlit UI or `etl/` scripts.
