# Collaborative Filtering — matriz esparsa, cosseno e o caso item-based/CSC

**Data:** 2026-05-29 (CF promovido a v1 em 2026-06-05)

CF item-based é a 4ª estratégia (`RecomendaSimilar`, §8): sai de *"filmes bem avaliados"* (qualquer sort) pra *"porque você gostou de Matrix"* (relacional). O trabalho pesado — cosseno sobre a matriz esparsa de co-avaliação — roda **offline no `etl/`** e emite `neighbors.csv`; o produto só faz lookup O(1). É o que dá substância de produto à recomendação, junto do [rating bayesiano](rating-bayesiano.md) (shrinkage estatístico) no ranking por nota.

Esta nota documenta o raciocínio que amarra CF ao dataset raw (grão por usuário; o agregado é só o snapshot do acervo, ver §6). Progressão didática: da ideia social do CF → matriz utilidade → por que esparsa → cosseno → formatos COO/CSR/CSC → fechamento no **item-based + CSC** pro nosso caso.

---

## Cosseno não é ML (a fronteira que mantém "recomendação determinística")

A recomendação do produto é **determinística, sem modelo treinado** — e CF não quebra isso, porque "collaborative filtering" aparecer em livro de ML não faz do cosseno um modelo.

**Cosseno é álgebra linear:**

```
cos(A, B) = (A · B) / (‖A‖ · ‖B‖)
```

Produto escalar normalizado pela magnitude — mede **ângulo** entre vetores. Sem modelo treinado, parâmetro aprendido, função de perda, otimização nem aleatoriedade. **Determinístico:** mesmos dados → mesmo resultado, sempre. Anterior a ML — vem do *vector space model* de recuperação de informação (anos 70). `sklearn` só **hospeda** a função (`sklearn.metrics.pairwise.cosine_similarity`); scipy também tem, e o cosseno em si são 5 linhas de numpy.

**CF item-based também não é "modelo treinado":** é *memory-based / instance-based* — não treina, guarda os dados e calcula similaridade (no nosso caso, **offline**). É **não-paramétrico**. Contrasta com *model-based CF* (fatoração de matriz, SVD, redes), que treina — e que **não** usamos.

**Higiene de dependência:** `sklearn`/`scipy` ficam **só no `etl/`** (não entram no `requirements.txt` do produto). O `etl/` computa cosseno → `neighbors.csv` (tabela estática) → produto lê e indexa. Assim "sem ML em runtime, recomendação determinística" é literal. *(A versão consolidada desse argumento mora em [faq](../faq.md).)*

---

## 1. A ideia central

Premissa **social**, não de conteúdo: *"gente que concordou no passado tende a concordar no futuro"*. Não olho **o que** o filme é (gênero, diretor, ano) — olho **quem gostou dele** e comparo padrões de gosto.

Duas variantes:

- **User-based:** acha usuários parecidos comigo, recomenda o que eles curtiram e eu não vi.
- **Item-based:** acha itens parecidos (parecidos = avaliados de forma parecida pelas *mesmas* pessoas), recomenda itens próximos aos que já curti.

Item-based vence na prática: itens são mais estáveis que usuários (perfil de um filme muda devagar) e a similaridade item-item pode ser **pré-computada offline**.

---

## 2. A matriz utilidade (user × item)

Tabela base: linhas = usuários, colunas = filmes, célula = nota.

```
            Matrix  Titanic  Inception  Notebook  JohnWick
Ana           5        -         5          -         4
Beto          4        -         4          -         5
Carla         -        5         -          5         -
Dida          -        4         1          5         -
```

`-` = **não avaliado** (não é zero — é *desconhecido*). Ana/Beto batem em ação/sci-fi; Carla/Dida em romance. O CF captura isso **sem saber** que são gêneros — só pelo padrão de coavaliação.

---

## 3. Por que matriz ESPARSA

100k usuários × 50k filmes = **5 bilhões** de células. Cada usuário avalia ~50 filmes → ~99.9% vazias.

- **Densa** (array 2D): guarda os 5 bi, quase tudo vazio → estoura memória.
- **Esparsa:** guarda só as células preenchidas como triplas `(linha, coluna, valor)` → ~5 milhões. Economia ~1000×.

**Vocabulário:** esparsa = maioria das células vazias · densa = todas as células materializadas · não-zero (nnz) = quantidade de células preenchidas.

---

## 4. Similaridade do cosseno — o coração do cálculo

Cada usuário (ou item) vira **vetor**. Mede-se a semelhança pelo **ângulo** entre vetores, não pela distância.

```
                  A · B           Σ (Aᵢ × Bᵢ)
cos(A, B) = ─────────────── = ──────────────────────
             ‖A‖ × ‖B‖        √Σ Aᵢ²  ×  √Σ Bᵢ²
```

Resultado entre **-1 e 1** (notas positivas → 0 a 1). 1 = mesma direção de gosto, 0 = sem relação.

### Por que dividir pela norma — a correção

O denominador `‖A‖ × ‖B‖` não é decoração: conserta um defeito do produto escalar cru. `A · B` sozinho mistura **duas** informações — quão **alinhados** os vetores estão (direção = gosto) e quão **grandes** são (magnitude = quanto/quão alto a pessoa vota). Pra similaridade quer-se só a direção; mas o dot cru cresce com o tamanho, mesmo direção igual.

Exemplo. Três filmes votados por 2 users: `A=[5,5]`, `B=[1,1]`, `C=[5,0]`. A e B apontam na **mesma** direção (diagonal — gosto idêntico, só intensidade diferente); C aponta noutra.

```
A·B = 5·1 + 5·1 = 10
A·C = 5·5 + 5·0 = 25
```

Cru diz "A mais parecido com C (25) que com B (10)" — **errado**. Premiou C só porque `5·5` é número grande. A divisão conserta:

```
‖A‖=√50≈7.07  ‖B‖=√2≈1.41  ‖C‖=√25=5
cos(A,B) = 10/(7.07·1.41) = 1.00   ← mesma direção (gosto igual)
cos(A,C) = 25/(7.07·5)   ≈ 0.71   ← parcialmente alinhados
```

A razão é geométrica. O produto escalar tem a forma `A·B = ‖A‖·‖B‖·cos(θ)`, onde θ = ângulo entre os vetores. Isolando: `cos(θ) = (A·B)/(‖A‖·‖B‖)`. Dividir pelas normas **cancela** o tamanho e deixa só `cos(θ)` — o ângulo, que é direção pura. Por isso o resultado mora sempre em `[-1,1]`: `1` mesma direção, `0` perpendicular (sem relação), `-1` oposto.

**Por que cosseno e não euclidiana:**
- **Mede ângulo, não distância.** É a correção acima: quem dá nota alta pra tudo (4–5) e quem é rígido (2–3) podem ter o mesmo *gosto* (mesma ordem). Euclidiana diz "longe" (magnitude diferente); cosseno cancela a magnitude e diz "parecidos".
- **Casa com esparsidade.** No produto escalar `Σ(Aᵢ×Bᵢ)`, toda parcela com um zero **some** → só sobra a interseção de filmes que **ambos** avaliaram. Numa matriz esparsa esses zeros nem estão armazenados → ignorados de graça.

**Exemplo Ana vs. Beto:**
```
Ana=[5,0,5,0,4]  Beto=[4,0,4,0,5]
A·B = 5×4 + 5×4 + 4×5 = 60
‖Ana‖=√66≈8.124  ‖Beto‖=√57≈7.550
cos = 60 / (8.124×7.550) ≈ 0.978   → quase idênticos
```
Ana vs. Carla ≈ 0 (vetores sem sobreposição).

### Por que `Xᵀ · X` cospe todas as similaridades de uma vez

Calcular par-a-par seria 59k² ≈ 3.5 bilhões de cosines na unha — inviável. O atalho: uma multiplicação de matriz já calcula todos os pares. Dois passos.

**Passo 1 — normaliza antes.** Escala cada coluna pra norma 1: `X̂[:,i] = X[:,i]/‖X[:,i]‖`. Cada filme vira vetor **unitário**. Com vetores unitários, `‖A‖=‖B‖=1`, então a fórmula do cosseno desmorona pra `cos = A·B` direto (denominador = 1). Ou seja: paga a divisão **uma vez** por coluna no começo, em vez de par-a-par 3.5 bi de vezes depois.

**Passo 2 — `S = X̂ᵀ · X̂`.** Agora um produto de matriz já É a tabela de cosines. Por que a transposta?

No layout `X` = (users × filmes), **filme é coluna**. Quer comparar colunas. Mas a regra de multiplicação casa **linha da esquerda com coluna da direita** — e exige dimensões internas iguais: `(a×b)·(b×c)=(a×c)`. Quer resultado `filme×filme` (`n×n`) com a soma caindo no eixo dos `m` users:

```
   Xᵀ      ·    X     =    S
(n × m)   ·  (m × n)  =  (n × n)
       ↑ soma sobre os m users (dimensão interna casa)
```

`X` é `(m×n)`; pra ter `(n×m)` na frente, **transpõe** — `Xᵀ` põe os filmes nas linhas (eram colunas de `X`). A transposta só serve pra **alinhar a dimensão** pra soma cair no eixo certo. Não é compressão nem truque mágico.

E por que isso dá tudo: por definição, a célula `(i,j)` do produto = `linha i da esquerda · coluna j da direita` = `filme i · filme j` = o cosine do par `(i,j)`. Cada célula do resultado **já é** uma similaridade; a multiplicação calcula as `n×n` células = todos os pares simultâneos. A multiplicação de matriz **é** o loop par-a-par — só que feito em C/BLAS otimizado, não em Python.

```
S[i,j] = (linha i de Xᵀ) · (coluna j de X) = cosine(filme_i, filme_j)
```

É exatamente isso que `sklearn.metrics.pairwise.cosine_similarity` faz por baixo: normaliza + `X̂ᵀ·X̂` esparso, otimizado em C. O cosseno em si é trivial (5 linhas); o que não se reimplementa é o **produto esparso eficiente em escala** — por isso a lib.

### Três eixos que não se confundem

`Xᵀ·X` normalizado mexe em três coisas **independentes**. Conflatá-las é o erro comum:

| Eixo | O que é | Papel |
|---|---|---|
| **Normalização** | matemática (dividir pela norma) | corrige o cosseno: extrai ângulo, descarta magnitude |
| **Esparsidade** | 99.74% zeros não guardados | o que dá **escala** (cabe na RAM, ver §3) |
| **Formato CSR/CSC** | layout dos bytes (ver §5) | só decide **velocidade de acesso** (por linha vs coluna) |

Mesma matriz, mesmos números, mesmo `S` final: trocar CSC↔CSR não muda **um dígito** de `S`, só o tempo de acesso. Pode-se normalizar matriz densa; pode-se ter CSC sem normalizar. CF junta os três de propósito — esparso (cabe), normalizado (mede semelhança real), CSC (acesso por coluna = por filme, rápido pro item-based, §6).

---

## 5. Formatos de matriz esparsa — COO, CSR, CSC

Mesma matriz, arrumada na memória de jeitos diferentes, cada um rápido pra uma operação.

Matriz de exemplo:
```
        col0  col1  col2
row0     5     0     0
row1     0     0     8
row2     0     3     0
```

### COO — Coordinate (lista de coordenadas)
Três listas paralelas: pra cada valor, sua linha, sua coluna, seu valor.
```
row  = [0, 1, 2]
col  = [0, 2, 1]
data = [5, 8, 3]
```
**Bom para:** *construir* a matriz (joga tuplas conforme lê os dados). **Ruim para:** contas (somar uma linha exige varrer tudo).

### CSR — Compressed Sparse Row (comprimido por linha)
Reorganiza pra acesso rápido **por linha**.
```
data    = [5, 8, 3]      valores lidos linha a linha
indices = [0, 2, 1]      a COLUNA de cada valor
indptr  = [0, 1, 2, 3]   onde cada linha começa em data
```
`indptr` tem tamanho **nº linhas + 1**. Linha `i` = `data[indptr[i] : indptr[i+1]]` → **acesso O(1)** à fatia, sem varrer.

### CSC — Compressed Sparse Column (comprimido por coluna)
Idêntico ao CSR, **pivotado**: comprime por coluna, `indices` guarda **linha**.
```
data    = [5, 3, 8]      valores lidos coluna a coluna
indices = [0, 2, 1]      a LINHA de cada valor
indptr  = [0, 1, 2, 3]   onde cada coluna começa
```

### `indptr` com linhas de tamanhos diferentes
A peça que mais confunde. Matriz com linha vazia e contagens variadas:
```
        col0  col1  col2  col3
row0     5     0     7     2     ← 3 valores
row1     0     0     0     0     ← 0 valores
row2     0     4     0     9     ← 2 valores
row3     1     0     0     0     ← 1 valor
```
`indptr` = **soma acumulada** das contagens por linha, começando em 0:
```
início 0 → +3 (row0)=3 → +0 (row1)=3 → +2 (row2)=5 → +1 (row3)=6
indptr = [0, 3, 3, 5, 6]
data    = [5, 7, 2, 4, 9, 1]
indices = [0, 2, 3, 1, 3, 0]
```
Leitura: `row0=data[0:3]`, `row1=data[3:3]` (**vazia** → dois números iguais), `row2=data[3:5]`, `row3=data[5:6]`. Último valor do `indptr` = nnz total (sempre confere).

**Insight:** linhas têm tamanhos diferentes → posição não dá pra calcular por `linha×largura`; o `indptr` **grava** as fronteiras. Linha vazia = par repetido, custo ~zero.

| Formato | Comprime | Rápido em | Uso |
|---------|----------|-----------|-----|
| **COO** | nada | montar | construir a matriz |
| **CSR** | linhas | uma linha | matriz×vetor, user-based |
| **CSC** | colunas | uma coluna | **item-based** |

Fluxo: monta em **COO** → converte (`.tocsr()` / `.tocsc()`) pra calcular.

---

## 6. Fechamento — item-based + CSC pro nosso caso

Por que essa combinação é a escolha natural aqui:

1. **Item-based** porque o catálogo de filmes é estável e a matriz item-item de similaridade pode ser **pré-computada** — recomendar fica barato em runtime (só consulta vizinhos).
2. No layout user×item, **cada filme é uma coluna**. Comparar dois filmes = acessar duas colunas inteiras. **CSC** dá esse acesso por coluna em O(1) na fatia — exatamente a operação dominante do item-based.
3. CSC alimenta direto o `cosine_similarity` por coluna → matriz `filme × filme`. Recomendação = nota prevista ponderada pela similaridade:
```
                Σ_j  sim(c, j) × nota_U(j)
pred(U, c) = ──────────────────────────────     (j = filmes que U já avaliou)
                  Σ_j  |sim(c, j)|
```

### O grão existe — CF reusa o raw, offline
O **raw existe**: 1.66GB, 25M ratings, tuplas `(user, movie, rating)` (ver [dataset-e-etl](dataset-e-etl.md)). O `aggregated.csv` (58.958 filmes, `avg_rating` + `count`) é só o **snapshot do acervo** — não "o dataset". O grão por usuário **não foi descartado**; segue no raw. Logo CF **não** precisa de fonte secundária nem de "reintroduzir" nada: o passo de `etl/` (`neighbors.py`) relê o raw direto.

Memória também não é obstáculo (ver §7): filtro de `count` + output esparso deixam o item×item caber folgado em 16GB. CF é **mais uma estratégia** do Strategy (§8) — o pattern não muda, ganha uma implementação; o raw já basta.

---

## 7. Custo de memória — input barato, output é o gargalo

Dois custos distintos. O de formato de armazenamento (input) é pequeno; o que de fato pode estourar RAM é a **matriz de similaridade resultante** (output).

### Input: COO vs CSC (a parte barata)

| Formato | Bytes | Total (nnz=25M) |
|---|---|---|
| COO | `3 × 4B × nnz` (row, col, data) | ~300 MB |
| CSR/CSC | `2 × 4B × nnz + indptr` | ~200 MB |

CSR/CSC economiza ~100MB matando o array de índice redundante (COO guarda `col[]` de 25M; CSC troca por `indptr[]` de 59k). Conversão `COO → CSC` tem **pico transiente ~500MB** (os dois coexistem enquanto scipy ordena por coluna), depois cai pra 200MB. Em laptop 16GB, **irrelevante** — escolher COO ou CSC no input não salva nem quebra.

### Output: o item×item é o que estoura

```
item×item DENSO = 59k × 59k × 4B = 13.9 GB   ⚠️ estoura 16GB
```

Formato do input **não muda isso**. Duas medidas resolvem:

1. **`dense_output=False`** → resultado fica esparso (maioria dos pares tem similaridade 0 — filmes sem user em comum).
2. **Filtrar `count ≥ 37` (p75) ANTES** → de 59k filmes pra ~14.7k → output encolhe quadraticamente.

**Dimensionamento (filtro → nº filmes → item×item denso):**

| Filtro | Filmes | denso | Cabe 16GB? |
|---|---|---|---|
| nenhum | 58.958 | 13.9 GB | ✗ |
| `count ≥ 37` (p75) | ~14.700 | ~870 MB | ✓ folgado |
| `count ≥ 414` (p90) | ~5.900 | ~140 MB | ✓ |
| `count ≥ 1508` (p95) | ~2.950 | ~35 MB | ✓ |

No p75 **já cabe denso** (870MB); com `dense_output=False` sobra ainda mais. O filtro é o **controle dominante** (limita o lado do quadrado); o sparse-output é margem extra grátis. Sparse sozinho não basta — filme popular é parecido com dezenas de milhares → linha quase densa.

**Bônus semântico:** filme com `count < 37` tem sinal fraco — poucos users, vizinhança não-confiável. Cortar a cauda **alinha qualidade e memória**: cosine só significa algo com massa de votos. (p75 = 37, ver [thresholds](thresholds.md).)

**Veredito:** memória **não é obstáculo** — vira escolha de threshold. CF é viável e está no v1 (§6).

---

## 8. Como entra no produto (Strategy)

CF é **mais uma estratégia** do Strategy, sem tocar o contrato `recomendar(catalogo, n) -> list[Filme]`:

```
RecomendaPorGenero        filtro por gênero
RecomendaPorNota          sort por weighted_rating (rating bayesiano)
RecomendaPorPopularidade  sort por count
RecomendaSimilar          CF: lookup item-based em neighbors.csv
```

Split build-time / run-time (coerente com [dataset-e-etl](dataset-e-etl.md) e [architecture](../engineering/architecture.md)):

- **ETL (offline):** raw → filtra `count ≥ 37` → `COO → CSC` → `cosine_similarity(Xᵀ, dense_output=False)` → top-10 por filme → emite `neighbors.csv`.
- **Produto (runtime):** lê `neighbors.csv`, lookup **O(1)**. Zero cosseno no app. `sklearn`/`scipy` ficam **só no `etl/`**, fora do `requirements.txt` do produto.

### Schema do `neighbors.csv` — long/tidy com `sim`

Formato **tidy**: uma linha por par (filme, vizinho), **não** uma linha por filme com colunas `vizinho_1..10`.

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `Movie_Name` | str | filme-alvo (título-com-ano — **mesma chave** do `aggregated.csv`, não um `movie_id` novo) |
| `rank` | int | 1..10, posição do vizinho (ordenado por `sim` desc) |
| `vizinho` | str | `Movie_Name` do filme similar |
| `sim` | float | similaridade de cosseno do par, em `[0,1]` |

~14.7k filmes × 10 = **~147k linhas, poucos MB**. Por que long+sim (vs wide `vizinho_1..10`):

- **Leitura O(1) no produto.** Carrega 1× (memoizado `@st.cache_data`), um `groupby` → dict: `{nome: list(zip(g.vizinho, g.sim))}`. `RecomendaSimilar` vira lookup em dict — wide forçaria iterar colunas, sem ganho.
- **Carrega o `sim`, e ele é necessário.** O pred ponderado (§6) é `Σ sim·nota / Σ|sim|`; recomendar a partir de **vários** filmes curtidos soma `sim` por candidato. Lista crua de vizinhos jogaria fora o peso. Bônus de UI: "92% similar" sai de graça.
- **Schema estável.** top-10 → top-N, ou cortar por `sim ≥ x`, é mudança de *dado*, não de *colunas*. Wide assa o N no schema.
- **Chave `Movie_Name`** (não `movie_id`): chave que `aggregated.csv` e o `Catalogo` já usam — junta sem introduzir id + join. Strings repetem nas 147k linhas; custa MBs, não GB — portabilidade do CSV ganha da micro-otimização de bytes.

Efeito de produto: recomendação passa de *"filmes bem avaliados"* (impessoal) pra *"porque você gostou de Matrix"* (relacional). Salto de percepção grande, custo de runtime nulo.
