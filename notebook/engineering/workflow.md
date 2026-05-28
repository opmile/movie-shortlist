# Workflow — conceito → contrato → implementação

**Data:** 2026-05-27 (validado), 2026-05-28 (aplicado)

---

## Premissa

Usuária vem de **Go (stack principal)** + Java/Spring (histórico). Python = sintaxe conhecida, idiom não. **Gap real = design patterns**, não linguagem.

Não quer codar manualmente. Mas precisa **defender na banca** — então conceito + contrato vêm dela, implementação vem do Claude.

---

## Fluxo por camada (core POO)

### 1. Conceito (5-15 min)
Claude expõe o pattern em linguagem agnóstica:
- O que resolve
- Alternativa sem ele
- Quando NÃO usar
- Ponte mental com Go/Java quando ajuda

Sem palestra. Corta em 15min ou quando ela perguntar diferente.

### 2. Contrato
Ela esboça interface/métodos com base no conceito. Decisão é dela — vira munição de banca ("foi minha decisão, não geração").

### 3. TDD seletivo (core POO apenas)
Ela escreve 1-2 testes que exercitam o pattern. Claude refina, depois implementa pra passar. Teste = ela verbalizando o contrato.

### 4. Revisão
Ela lê o diff e faz **pergunta de engenharia**, não de sintaxe. ("Por que parâmetro no construtor e não no método?")

---

## Camadas com fluxo completo

| Camada | Tempo ativo estimado |
|---|---|
| `Filme` + subclasses | ~40min |
| `Catalogo` | ~30min |
| `DataSource` ABC + 2 impls | ~60min |
| `FilmeFactory` | ~25min |
| `Recomendador` ABC + 3 estratégias | ~50min |

Total core: ~3.5h ativas.

---

## Camadas com fluxo colapsado

Periferia / lib-heavy / UI consumidora — sem etapa de conceito ou TDD detalhado.

| Camada | Por que colapsa |
|---|---|
| `Analisador` (pandas) | Lib-heavy; conceito de boundary apenas |
| Streamlit UI | Consumidor, não produtor de pattern |

Claude gera, ela lê com olho crítico ("vazou abstração?"). Sem TDD.

---

## Regras de corte

- **Conceito passa de 15min:** cortar com "chega, mostra contrato"
- **Python idiom**: JIT — só quando travar, não preventivo
- **Periferia**: pode gerar direto, pausar se ela perguntar "por quê"
- **Core POO**: nunca pular conceito + contrato dela

---

## Por que esse workflow rende ROI alto

| Etapa | Aprendizado |
|---|---|
| Conceito | Pattern em si, não sintaxe (transferível pra Go/qualquer stack) |
| Contrato | Engineering judgment + arguibilidade de banca |
| TDD | Validação do pattern + skill transferível direta pro Go (table-driven tests) |
| Revisão | Internalização ativa, não passiva |

---

## Onde pode falhar

- Claude palestrar 25min em conceito → ela corta com "chega"
- Contrato ambíguo → teste falha cedo, ajusta (mais barato que descobrir depois)
- Ela pular conceito por pressa → vira generate-and-defend, perde gap. **Compromisso:** nunca pula conceito em camada core
- Python idiom emergir e travar — Claude para e explica (JIT)
