# Conversa — ROI da redução de complexidade

**Data:** 2026-05-28
**Contexto:** decisão de cortar escopo. De 4 patterns → 2. Remover collab filtering. Avaliar ROI de aprendizado por hora investida.

---

## Cortes propostos e aceitos

### Corte 1 — usar dataset, mas só forma agregada

Sistema consome **só `lab/aggregated.csv`** (59k linhas, ~3MB). Pipeline pesado fica fora do escopo.

**Removido:**
- ❌ `KaggleDataSource` em runtime
- ❌ Chunked groupby em runtime
- ❌ Sparse matrix 200MB
- ❌ Cosine similarity precompute
- ❌ Collaborative filtering (precisaria de matriz user-item)
- ❌ `RecomendaCollabFiltering`

**Mantido:**
- ✅ 59k filmes únicos com `avg_rating`, `count`, `genres`, `year`
- ✅ Subclasses derivadas estatisticamente (thresholds calibrados pelo lab)
- ✅ Recomendação simples via Strategy: gênero, nota, popularidade
- ✅ Estatísticas pandas
- ✅ Streamlit com 3 telas

Sistema fica ~70% mais simples sem perder fundamento POO.

### Corte 2 — 2 patterns ao invés de 4

**POO fundamentals (sempre presentes, não contam como "pattern"):**
- Encapsulamento, herança, polimorfismo, abstração via classes

**Design patterns formalmente trabalhados:** Strategy + Repository

**Dropped:**
- Factory (sem polimorfismo real de DataSource via instanciação dinâmica)

---

## ROI por dimensão

| Dimensão | Ambiciosa | Enxuta | Ganho/Perda |
|---|---|---|---|
| Patterns profundidade | 4 × ~1.5h cada | 2 × ~3h cada | **GANHO grande** — fundos > rasos |
| Patterns quantidade | 4 | 2 | Perda nominal. Factory que sai é variação leve. |
| Polimorfismo aplicado | 4 sub + 5 strat + 2 src | 4 sub + 3 strat + 2 src | Empate marginal |
| Herança / POO fundamental | idêntico | idêntico | Empate |
| Engineering judgment | "implementei tudo" | "cortei X porque Y" | **GANHO grande** — skill de senioridade |
| Collab filtering | Implementaria | Não | Perda real, mitigada — vale como projeto próprio depois |
| Pandas / data eng | Chunked + sparse + agg | Read + filter + groupby | Perda nominal, real mínima — agg já feito no lab |
| scipy.sparse + sklearn | Exposição | Sem | Perda real mas fora do eixo declarado (engenharia, não ML) |
| Python idiom | idêntico | idêntico | Empate |
| Streamlit | idêntico | idêntico | Empate |
| Defesa de banca | 4 pra explicar, risco "por que tantos" | 2 a fundo, "por que SÓ 2" vira força | **GANHO** |
| Buffer pra ir fundo | 0h | ~3-4h | **GANHO** — permite testes, refactor, segunda passada |
| Risco de não entregar | Médio | Baixo | **GANHO** |

## Veredito

ROI por hora investida sobe com a redução. Não é menos aprendizado — é aprendizado redistribuído pra coisas que multiplicam.

- **Ambiciosa** = buffet largo, prato raso de cada. Bom pra ver cardápio, ruim pra internalizar sabor.
- **Enxuta** = 2 pratos fundos. Bom pra dominar. Carrega pro resto da carreira.

Strategy + Repository profundos = exatamente o que multiplica em qualquer stack (Spring, Go, Node, Python). Collab filter é divertido, não casa com perfil "backend engineer que entende patterns".

**Onde a enxuta é inferior:**
- Não implementa recomendação "de verdade" (collab filter)
- Currículo "projetos com ML" não cresce

**Onde compensa:**
- Saber **defender escopo** vale 10× em entrevistas técnicas
- Patterns ficam internalizados, não decorados
- Tempo sobra pra escrever testes (TDD = munição de defesa POO)

**Decisão final:** versão enxuta. Critério decisivo — aprendizado que multiplica > aprendizado que acumula superficialmente.

**Collab filter:** vai pra v2, depois da engenharia de verdade estar pronta, se sobrar tempo. `lab/aggregated.csv` fica salvo pra retomar.

**TDD:** imprescindível. Núcleo dos patterns escolhidos. Foi acordado explicitamente.
