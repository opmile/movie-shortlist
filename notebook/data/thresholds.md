# Thresholds das subclasses — calibração final

**Data:** 2026-05-28
**Fonte:** `lab/findings.md` (sessão data-project), distribuição real do dataset agregado (`lab/aggregated.csv`, 58.958 filmes).

---

## Princípio de calibração

Thresholds derivam de **percentis da distribuição real**, não de chute. Cada subclasse precisa ter amostra suficiente pra demo na banca (não vazia, não inflada).

---

## Distribuições observadas (referência)

**`avg_rating` (por filme, após agregação):**
- p90 = 3.865
- p95 = 4.000

**`count` (ratings por filme):**
- p20 = p25 = 2 (cauda extrema)
- p50 = 6
- p75 = 37
- p90 = 414
- p95 = ~250+ (referência)
- max = 81.491

**`year` (extraído do título):**
- 527 filmes (0.9%) sem ano detectado
- `≤ 1970` = 10.906 filmes (~18%)
- `≤ 1972` = 11.872
- `≤ 1980` = 15.315 (~26%)

---

## Thresholds finais (após calibração)

| Subclasse | Critério | Threshold concreto | Estimativa |
|---|---|---|---|
| `FilmeAclamado` | `avg_rating ≥ p95` | `avg_rating ≥ 4.0` | ~2.9k filmes (~5%) |
| `Blockbuster` | `count ≥ p95` | `count ≥ ~250` | ~3k (~5%) |
| `FilmeCult` | `count ∈ [p50, p75] ∧ avg_rating ≥ p75` | `count ∈ [6, 37] ∧ avg_rating ≥ 3.9` | ~subset, calcular após precedência |
| `Classico` | `year ≤ X` | `year ≤ 1970` | ~10.9k (~18%) |
| `Filme` (base) | fallback | — | resto |

### Decisões de calibração

1. **Aclamado em p95 e não p90:** p90=3.865 ficou abaixo de 4.0, semanticamente fraco pra "aclamado" (nota <4 quebra senso comum). p95=4.0 é defensável intuitivamente.

2. **Cult em count [p50, p75]:** range original p20-p50 = [2, 6] capturava filmes obscuros (2-6 ratings totais), semântica de "cult" errada. p50-p75 = [6, 37] = filme visto mas não mainstream + bem avaliado = cult de verdade.

3. **Classico em 1970:** 1980 cobriria 26% do catálogo (inflação). 1970 cobre 18% — divisor mais defensável (pré/pós nova Hollywood).

---

## Precedência (resolve overlap entre subclasses)

Filme pode satisfazer múltiplos critérios. Subclasse única exige regra de precedência.

```
Classico  >  FilmeCult  >  Blockbuster  >  FilmeAclamado  >  Filme (base)
```

**Razão da ordem:** mais específico/raro primeiro.
- `Classico` é determinístico (year), vence empate
- `FilmeCult` exige 2 thresholds (count + avg) — categoria mais nichada
- `Blockbuster` exige popularidade extrema (top 5%)
- `FilmeAclamado` é o "premium genérico", aplica quando nada mais coube
- `Filme` base = fallback

**Aplicação:** `FilmeFactory` percorre essa ordem e instancia a primeira classe cujo critério bate.

---

## Anomalias tratadas

- **527 filmes sem ano detectado (0.9%):** caem em `Filme` base (não classificam como Classico, fallback). Não justifica refinar parser — taxa é ignorável.
- **0 ratings fora de [0.5, 5.0]:** dados limpos, sem validação extra.
- **0 gêneros null:** dados limpos.
