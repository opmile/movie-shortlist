# Thresholds das subclasses — estatística, calibração e precedência

**Data:** 2026-05-28
**Fonte:** `etl/findings.md` + `etl/explore/calibrate.py`, distribuição real do dataset agregado (`etl/aggregated.csv`, 58.958 filmes).

Fonte **canônica** dos thresholds. Outros docs cross-referenciam isto, não repetem os números. O espelho em código é `etl/core.py` (`THRESHOLDS`) — não editar o dict sem refletir aqui.

---

## Princípio de calibração

Thresholds derivam de **percentis da distribuição real**, não de chute. Cada subclasse precisa ter amostra suficiente pra ser demonstrável (não vazia, não inflada).

**Por que percentil e não média:** a média soma tudo e divide pelo total — um único filme com 81.491 ratings distorce a média pra cima. O percentil ignora o *valor* dos extremos e olha só a *posição* na fila ordenada — robusto a outlier. Por isso threshold ancora em percentil: "p95 dos 5% mais populares" é número observado, não opinião.

**Vocabulário:** percentil = valor na posição N% da fila ordenada · mediana = p50 · distribuição = formato do espalhamento · cauda longa = poucos valores enormes + maioria pequena · outlier = extremo que distorce média.

---

## Distribuições observadas

**`avg_rating` (por filme, após agregação):**
```
min   p50    p90    p95   max
0.500 3.150  3.865  4.000 5.000
```
Notas se amontoam em 2.5–3.5; nota alta é rara (só 5% chegam a 4.0). Justifica `FilmeAclamado` exigir `avg ≥ 4.0` — a elite real.

**`count` (ratings por filme) — achado mais importante:**
```
min   p20   p50   p75   p90   p95    max
1     2     6     37    414   1508   81491
```
Distribuição **brutalmente desigual** (cauda longa): filme do meio tem 6 ratings, o mais popular tem 81.491. Molda a semântica: `Blockbuster` = topo (`count ≥ p95`), `FilmeCult` = faixa do meio (`count [6,37]`, visto mas não mainstream).

**`year`:**
```
min   p50    max          ≤1970 = 10.906 (~18%)
1874  2003   2019         ≤1980 = 15.315 (~26%)
```
Catálogo moderno (metade é 2003+). `Classico = year ≤ 1970` pega os ~18% mais antigos. Cortar na mediana (2003) esvaziaria a palavra.

**Por que a distribuição destravou o projeto:** antes dela threshold era chute; depois virou número observado — cada subclasse tem amostra real, "por que 4.0?" → "p95 do `avg_rating`", e a cauda longa define a semântica (blockbuster por extremo, cult por meio, aclamado por nota rara).

---

## Thresholds finais (após calibração)

| Subclasse | Critério | Threshold concreto | Estimativa (pós-precedência) |
|---|---|---|---|
| `Classico` | `year ≤ X ∧ count ≥ p75` | `year ≤ 1970 ∧ count ≥ 37` | ~1.926 (~3.3%) |
| `FilmeCult` | `count ∈ [p50, p75] ∧ avg ≥ p75` | `count ∈ [6, 37] ∧ avg_rating ≥ 3.9` | ~474 (~0.8%) |
| `Blockbuster` | `count ≥ p95` | `count ≥ 1508` | ~2.709 (~4.6%) |
| `FilmeAclamado` | `avg ≥ p95 ∧ count ≥ p50` | `avg_rating ≥ 4.0 ∧ count ≥ 6` | ~121 (~0.2%) |
| `Filme` (base) | fallback | — | ~53.728 (~91%) |

Base = 91% é **honesto**: a maioria dos filmes é comum (poucos votos, nota média); subclasse é a exceção interessante, não a regra. Todas não-vazias e demonstráveis. As estimativas acima são **pós-precedência** (medidas após aplicar a ordem das guard clauses), não contagens independentes por critério.

---

## Calibração — os três findings (didático)

### 1. Aclamado: piso de `count` mata o ruído de poucos votos

`Aclamado` original (`avg ≥ 4.0`, sem piso) capturava nota alta de pouquíssimos votos — ruído estatístico, não aclamação. Medido sem piso: **3.577 Aclamados**, dos quais **3.514 com `count ≤ 5`** e **2.005 com um único voto** (`Once Upon a Ladder (2016)`, count=1, avg=5.0). ~98% era ruído. Semanticamente é veneno ("aclamado por quem?").

**Finding-chave — piso 6 ≡ piso 38 (resultado idêntico):**

| piso | Aclamado |
|---|---|
| sem piso | 3.577 |
| 6 | 63 |
| 38 | 63 |
| 100 | 37 |

Por quê: não existe Aclamado na faixa `count [6,37]` — o `Cult` (que vem **antes** na precedência) já pega todo `count [6,37] ∧ avg ≥ 3.9`, e `avg ≥ 4.0 ⊂ ≥ 3.9`. A faixa [6,37] do Aclamado é **vazia por construção da precedência**, não pelo piso. Logo o piso tem **um único trabalho**: matar o ruído de `count ≤ 5`. A separação do Cult já é feita pela ordem das guard clauses.

**Decisão: piso = 6** (= p50, "mínimo de votos pra a média ser confiável"). Escrever 38 seria enganoso — sugeriria que o piso separa o Cult, quando a precedência já faz isso. 6 é o número honesto que descreve o trabalho real do piso.

### 2. Blockbuster: corrigido de ~250 para 1508 (p95 real)

`~250` contradizia o rótulo "p95"; o p95 real de `count` é **1508**. O threshold de Blockbuster controla o tamanho do Aclamado (Blockbuster come os bem avaliados muito populares):

| Blockbuster | nº | % catálogo | Aclamado |
|---|---|---|---|
| `count ≥ 250` | 6.531 | ~11% | 63 |
| `count ≥ 1508` (p95 real) | 2.709 | ~5% | 121 |

**Decisão: `count ≥ 1508`** — top 5% verdadeiro, casa com o rótulo "p95", e dá ao Aclamado tamanho saudável (121) em vez de raquítico (63).

### 3. Classico: velho ≠ clássico (mesma doença do Aclamado)

`year ≤ 1970` puro conflava *velho* com *clássico*. Entre os 10.906 filmes ≤1970: p50 de `count` = 4 (metade tem ≤4 votos), 2.313 com 1 voto, mediana de `avg` = 3.16 (medíocre). `$100,000 for Ringo (1965)`, 1 voto, avg 2.5, entrava como "Classico".

**Conserto: piso de `count`, mas com bar mais alto** — "clássico" carrega **reconhecimento**, não só validade estatística:

| piso count | Classicos | % catálogo |
|---|---|---|
| sem (atual) | 10.906 | 18.5% |
| ≥ 6 | 4.736 | 8.0% |
| **≥ 37 (escolhido)** | **1.926** | **3.3%** |
| ≥ 100 | 1.237 | 2.1% |

**Decisão: `year ≤ 1970 ∧ count ≥ 37`** (p75). Mais alto que o piso 6 do Aclamado de propósito: "clássico" pede mais que "a média vale" — pede que o filme antigo ainda seja assistido o bastante pra ter ficado. Efeito: 56 filmes velhos com `count [6,37] ∧ avg ≥ 3.9` que antes eram `Classico` (idade pura) migram pro `Cult` (velho + nicho devoto). Cult foi 418 → 474. Ninguém some, só remapeia.

---

## Outras decisões de calibração

1. **Aclamado em p95 (4.0) e não p90 (3.865):** nota < 4 quebra o senso comum de "aclamado"; p95=4.0 casa com o senso comum.
2. **Cult em count [p50, p75] e não [p20, p50]:** o range [2, 6] capturava filmes obscuros (2-6 ratings totais) — semântica de "cult" errada. [6, 37] = visto mas não mainstream + bem avaliado = cult de verdade.
3. **Classico em 1970 e não 1980:** 1980 cobriria 26% do catálogo; 1970 cobre 18% — divisor mais justificado (pré/pós nova Hollywood).

---

## Precedência (resolve overlap entre subclasses)

Os critérios das subclasses **se sobrepõem na nota** (várias pedem avg alto), então um filme pode satisfazer mais de um. A precedência atribui classe única, e a **ordem é o mecanismo que fatia o eixo de `count` em faixas** — avalia-se a condição mais estreita antes da mais ampla, pra a larga não engolir a estreita.

```
Classico  >  FilmeCult  >  Blockbuster  >  FilmeAclamado  >  Filme (base)
```

`FilmeFactory` percorre essa ordem e instancia a primeira classe cujo critério bate (first-wins). Reordenar muda a classificação — **ordem é contrato, não estética**.

Posição por posição:
1. **Classico — 1º.** Eixo *tempo* (`year`), ortogonal aos outros. Vem primeiro **não por ser raro**, mas porque "ser antigo" foi eleito **identidade dominante**: filme de 1965 com 60 mil votos e avg 4.6 vira `Classico`, não `Blockbuster`. Perda consciente de sinal, não bug.
2. **Cult — 2º (antes de Aclamado): load-bearing.** A faixa `count [6,37] ∧ avg` alto é exatamente onde Cult e Aclamado se sobrepõem. Cult-antes é o que mantém esses filmes como Cult — por isso o Aclamado tem **zero** filmes em [6,37]. Se Aclamado viesse antes, roubaria a faixa.
3. **Cult vs Blockbuster — inerte.** `[6,37]` e `≥1508` são disjuntos; trocar a ordem entre eles não muda nada.
4. **Blockbuster antes de Aclamado: load-bearing.** Popular+bom → `Blockbuster`. Isso define o `Aclamado` como a faixa do meio: `count [38, 1507] ∧ avg ≥ 4.0`. Popularidade come aclamação — quem todo mundo viu é rotulado pelo alcance.
5. **Aclamado antes de Filme; Filme base = fallback puro.**

**A régua de `count`:**
```
count:   1───5 │ 6─────37 │ 38──────1507 │ 1508──────►
              p50         p75           p95
ruído    │  CULT    │   ACLAMADO   │  BLOCKBUSTER
(→base)  │ (nicho)  │   (médio)    │  (massa)
              └── todos exigem avg alto ──┘

   CLASSICO (year ≤ 1970 ∧ count ≥ 37) corta por cima — eixo tempo + reconhecimento, vence sempre
```

Resumo: a precedência transforma critérios sobrepostos numa **partição limpa do eixo de `count`** — Cult (nicho) → Aclamado (médio) → Blockbuster (massa), com Classico cortando transversalmente pelo tempo e Filme recolhendo o resto.

### Por que guard clauses (engenharia)

Na `FilmeFactory`, a precedência se materializa como uma sequência de **guard clauses** (retornos precoces): cada `if` testa um critério e, se bater, retorna a subclasse imediatamente — o resto do código nem executa.

```
             [ dict cru do DataSource ]
                        │
  Guard 1 ──► year ≤ 1970 ∧ count ≥ 37?  ─── Sim → return Classico(...)
                        │ Não
  Guard 2 ──► count ∈ [6,37] ∧ avg ≥ 3.9? ── Sim → return FilmeCult(...)
                        │ Não
  Guard 3 ──► count ≥ 1508?  ─────────────── Sim → return Blockbuster(...)
                        │ Não
  Guard 4 ──► avg ≥ 4.0 ∧ count ≥ 6?  ────── Sim → return FilmeAclamado(...)
                        │ Não
  Fallback ─────────────────────────────────── return Filme(...)
```

**Simplificação implícita.** A guard 4 (`Aclamado`) testa apenas `avg ≥ 4.0 ∧ count ≥ 6` — sem mencionar limites de faixa. Mas quando a execução chega até ela, as guards 2 e 3 **já removeram** todo `count [6,37]` (→ Cult) e todo `count ≥ 1508` (→ Blockbuster). O `Aclamado` atua *implicitamente* na faixa [38, 1507] sem precisar escrevê-la. Cada guard estreita o espaço de dados restante; a última vê apenas o que sobrou — as faixas de `count` se separam **pela ordem de execução**, não por fórmulas booleanas compostas.

**Alternativa rejeitada (ninhos de `if/else`).** Sem retorno precoce, cada condição teria que negar explicitamente todas as anteriores (`if avg ≥ 4.0 and count ≥ 6 and not (count ∈ [6,37] and ...) and count < 1508`). Isso é o *Arrow Anti-pattern* (pirâmide de indentação): frágil, difícil de ler, propenso a bugs de borda e hostil a extensão.

**Vantagens concretas:**
1. **Partição perfeita.** Retorno precoce garante que cada filme pertence a **uma e apenas uma** subclasse — sem ambiguidade.
2. **Extensibilidade (Open/Closed).** Adicionar uma subclasse futura (ex: `BlockbusterFlop`) = inserir uma guard na posição certa. As demais não mudam.
3. **Legibilidade.** Cada guard é uma frase legível isolada; a lógica de exclusão mútua é consequência da ordem, não de expressões complexas.

---

## Anomalias tratadas

- **527 filmes sem ano (0.9%):** caem em `Filme` base via guarda `year is not None`. Taxa ignorável; não justifica refinar parser.
- **0 ratings fora de [0.5, 5.0]** e **0 gêneros null:** dado limpo, sem validação extra.
