# Rating bayesiano — shrinkage estatístico pra ranquear nota com confiança

**Data:** 2026-06-04
**Origem:** sessão de design de produto (mais dente de portfolio). Documenta o raciocínio que amarra "ordenar por nota" à confiança estatística do nosso dataset agregado.

Progressão didática: o problema (média de poucos votos mente) → a ideia do shrinkage → a fórmula do *weighted rating* → calibração dos dois parâmetros no nosso dataset → onde entra no produto.

---

## 1. O problema — média crua mente quando há poucos votos

O acervo tem `avg_rating` por filme. Ordenar por ele cru **ressuscita um bug que já documentamos** em [thresholds](thresholds.md): `Once Upon a Ladder (2016)`, `count=1`, `avg=5.0`. Uma nota 5.0 de **um voto** não é "o melhor filme do catálogo" — é acidente estatístico. Ordenado por `avg_rating` cru, esse filme senta **acima** de um com `avg=4.5` e 10.000 votos.

A cauda longa do `count` ([thresholds](thresholds.md): p50=6, mas max=81.491) garante que isso não é caso raro — **metade** do catálogo tem ≤6 votos. Ranquear por média crua = x.

**Como as subclasses já lidam com isso (e por que não basta):** o `FilmeFactory` resolve com **piso duro** de `count` (Aclamado exige `count ≥ 6`, Classico `≥ 37`). Piso é binário — corta quem está abaixo, trata todos acima como iguais. Serve pra **classificar** (dentro/fora da subclasse). Mas **ranquear** (ordenar o acervo inteiro, do melhor pro pior) pede algo **contínuo**: um filme de 8 votos é mais confiável que um de 1, e menos que um de 5.000 — o piso não enxerga essa gradação. É aí que entra o rating bayesiano.

---

## 2. A ideia — shrinkage: puxar a estimativa ruidosa pra um prior

**Shrinkage** = encolher uma estimativa de baixa confiança em direção a um valor de referência (o *prior*). Quanto menos dado, mais a estimativa cede ao prior; quanto mais dado, mais ela se sustenta sozinha.

Aplicado aqui: o prior é a **média global do catálogo** (~3.15). A intuição:

- Filme com **1 voto** e nota 5.0: quase nenhuma evidência própria → shrinkage o puxa quase todo pro prior → nota ajustada cai pra perto de 3.15.
- Filme com **10.000 votos** e nota 4.5: evidência massiva → shrinkage quase não age → nota ajustada fica ~4.5.

É **bayesiano** no sentido próprio: começa de uma crença a priori (o filme é mediano, como a maioria) e a atualiza conforme os votos chegam. Poucos votos → a crença a priori domina. Muitos votos → os dados dominam.

**Vocabulário:** prior = crença inicial antes da evidência · shrinkage = encolher estimativa rumo ao prior · estimador de baixa variância = troca um pouco de viés por muito menos ruído.

---

## 3. A fórmula — *weighted rating* (a do IMDb Top 250)

```
                v                m
   WR = ───────────── · R  +  ───────────── · C
            v + m                 v + m

   v = count do filme (nº de votos)
   R = avg_rating do filme (sua média crua)
   m = piso de votos (parâmetro: "quantos votos pra confiar na média própria")
   C = média global do catálogo (o prior)
```

É uma **média ponderada** entre a nota do filme (`R`) e o prior (`C`), com peso `v/(v+m)`:

- `v` pequeno (poucos votos) → `v/(v+m)` ≈ 0 → resultado ≈ `C` (puxado pro prior).
- `v` grande (muitos votos) → `v/(v+m)` ≈ 1 → resultado ≈ `R` (a própria nota manda).
- `v = m` → peso 50/50 entre nota própria e prior.

Verificação no nosso ruído (`v=1, R=5.0`, supondo `m=37, C=3.15`):
```
WR = (1/38)·5.0 + (37/38)·3.15 = 0.132 + 3.067 = 3.20
```
A nota 5.0 de 1 voto desaba pra **3.20** — sai do topo. Já `v=10000, R=4.5`:
```
WR = (10000/10037)·4.5 + (37/10037)·3.15 = 4.485 + 0.012 = 4.50
```
Praticamente intacto. Exatamente o comportamento desejado.

---

## 4. Calibração dos dois parâmetros (no nosso dataset)

Ambos saem do `aggregated.csv` que **já existe** — custo de cálculo ~zero, sem tocar o raw.

**`C` — média global (o prior):** média dos `avg_rating` do catálogo. Da distribuição em [thresholds](thresholds.md), p50 = 3.15; o valor exato (média, não mediana) sai de uma linha no ETL. Ancora "o filme mediano".

**`m` — piso de confiança (o botão):** quantos votos antes de confiar mais na nota própria que no prior. **Não há valor "certo"** — é decisão de quão conservador ser. Ancorar em percentil de `count` (coerente com a disciplina de [thresholds](thresholds.md)):

| `m` | Âncora | Efeito |
|---|---|---|
| 6 | p50 | brando — média própria assume cedo |
| **37** | **p75** | **recomendado** — casa com o piso do Classico; "reconhecido o bastante" |
| 414 | p90 | agressivo — só filme muito votado escapa do prior |

**Recomendado `m = 37` (p75):** mesmo número que já justifica o piso do `Classico` em [thresholds](thresholds.md) — reaproveita uma âncora já calibrada, não inventa parâmetro novo. Racional: "p75 é onde a média começa a ser confiável; abaixo disso, o prior carrega mais peso."

---

## 5. Onde entra no produto

**Métrica derivada, computada uma vez no startup** (ou pré-computada no ETL como coluna extra de `aggregated.csv` — escolha de onde, ambos build-time barato). Não é runtime pesado: é uma conta aritmética sobre 59k linhas, milissegundos.

Dois usos diretos:

1. **`RecomendaPorNota` (Strategy existente):** ordena por `WR` em vez de `avg_rating` cru. **Mesmo contrato `recomendar(catalogo, n) -> list[Filme]`** — o pattern não muda, só a chave de ordenação fica honesta. Um filme entra no top porque é *consistentemente* bem avaliado, não porque teve sorte com 1 voto.
2. **Tela Acervo (ordenação):** coluna "nota ajustada" ao lado da crua. Mostrar as duas lado a lado **é argumento visual** — o avaliador vê `5.0 (1 voto) → 3.20` e entende na hora por que a correção existe.

Encaixa no `calcular_score()` das subclasses? Possível, mas **separado de propósito:** `calcular_score` é o eixo de *personalidade* da subclasse (Blockbuster pondera `count`, Aclamado pondera `avg`); `WR` é uma correção de *confiança* ortogonal, que serve a ranking geral. Misturar confundiria os dois papéis. `WR` vive como método/coluna própria.

**Build vs run (default):** pré-computado como coluna `weighted_rating` no ETL (coerente com [dataset-e-etl](dataset-e-etl.md)), mantendo o produto burro (só lê) — embora calcular no startup seja igualmente barato em 59k linhas.

---

## 6. Custo e escopo

Uma média global + uma fórmula aritmética sobre `aggregated.csv`. Sem raw, sem dependência nova, sem ML. Não toca subclasses, não toca precedência, não toca DataSource: adiciona uma métrica derivada e troca a chave de ordenação de um Strategy. Risco baixo, custo ~zero.