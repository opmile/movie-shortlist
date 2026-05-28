# Collaborative filtering — deferred to v2

**Data:** 2026-05-28
**Status:** fora do escopo v1. Reativar em v2 se houver tempo após engenharia core estar pronta.

---

## Análise feita no lab

Dataset bruto entrega o sinal ideal pra collab filtering: tuplas `(user, movie, rating)` em massa.

**Dimensionamento:**

| Estratégia | RAM | Viável? |
|---|---|---|
| Dense float32 | 162k × 59k × 4 bytes = **38.3 GB** | ❌ Impossível |
| Sparse CSR float32 | ~25M × 12 bytes = **200 MB** | ✅ Trivial |
| Item-item M×M float32 | 59k × 59k × 4 = **13.9 GB** | ⚠️ Possível mas pesado |

**Densidade:** 0.26% (25M ratings em 162k × 59k células). Sparse vence claro.

**Recomendação técnica:** `scipy.sparse.csr_matrix` + `sklearn.metrics.pairwise.cosine_similarity`.

---

## Por que deferido

1. **ROI de aprendizado** — collab filter exige 2-3h dedicadas de álgebra linear + IR pra não virar cargo cult. Mistura com TFD POO dilui as duas aprendizagens.
2. **Escopo enxuto venceu** — 2 patterns profundos > 4 patterns rasos. Collab filter forçaria 3o pattern (precompute + cache) que não cabe.
3. **Engenharia core primeiro** — Strategy + Repository + herança + TDD é o foco da v1.
4. **Pode ser projeto próprio** — collab filter sozinho rende projeto de portfólio focado em recsys/IR.

---

## Como reativar (v2)

**Pré-requisitos:**
- Engenharia core (v1) pronta e estável
- Buffer de tempo disponível

**Trabalho mínimo:**
1. Reusar `lab/aggregated.csv` apenas como source de filmes
2. Carregar raw novamente ou exportar matriz sparse do raw → `lab/user_item_matrix.npz`
3. Adicionar estratégia `RecomendaCollabFiltering(Recomendador)` no produto
4. Precomputar cosine_similarity matrix (item-item, M×M) no carregamento — cacheável em disco
5. Recomendação = "filmes parecidos com X" via lookup na matriz de similaridade
6. Adicionar tela Streamlit de "Detalhe do filme" com seção "filmes parecidos"

**Estimativa:** 4-6h se v1 estável.

**Dependências extras necessárias:** `scipy`, `scikit-learn`.

---

## Defesa na banca (sobre não ter feito v1)

"Considerei implementar collab filtering, mas o eixo de aprendizado do TFD é POO. Implementar collab filter de forma defensável exige álgebra linear + métricas de recsys que dispersariam o foco. Mantive Strategy aberto pra acomodar a estratégia em v2 — o pattern não precisa mudar, só ganha mais uma implementação."

Defesa positiva: demonstra **engineering judgment** (saber cortar > saber implementar tudo).
