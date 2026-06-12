# TDD e workflow — conceito → contrato → implementação

**Data:** 2026-05-27 (workflow validado), 2026-05-28 (TDD + aplicado)

Onde aplicar TDD (seletivo no core POO) e o fluxo de trabalho por camada.

---

## Premissa do workflow

Usuária vem de **Go (stack principal)** + Java/Spring (histórico). Python = sintaxe conhecida, idiom não. **Gap real = design patterns**, não linguagem. Não quer codar manualmente, mas precisa **entender e ter ownership de cada decisão** — então conceito + contrato vêm dela, implementação vem do Claude.

---

## Fluxo por camada (core POO)

1. **Conceito (5-15 min)** — Claude expõe o pattern em linguagem agnóstica: o que resolve, alternativa sem ele, quando NÃO usar, ponte com Go/Java quando ajuda. Sem palestra; corta em 15min ou quando ela perguntar diferente.
2. **Contrato** — ela esboça interface/métodos. Decisão é dela ("foi minha decisão, não geração").
3. **TDD seletivo** — ela escreve 1-2 testes que exercitam o pattern; Claude refina e implementa pra passar. Teste = ela verbalizando o contrato.
4. **Revisão** — ela lê o diff e faz **pergunta de engenharia**, não de sintaxe ("Por que parâmetro no construtor e não no método?").

### Camadas com fluxo completo

| Camada | Tempo ativo |
|---|---|
| `Filme` + subclasses | ~40min |
| `Catalogo` | ~30min |
| `DataSource` ABC + 2 impls | ~60min |
| `FilmeFactory` | ~25min |
| `Recomendador` ABC + 3 estratégias | ~50min |

Total core: ~3.5h ativas.

### Camadas com fluxo colapsado (periferia/lib-heavy/UI)

| Camada | Por que colapsa |
|---|---|
| `Analisador` (pandas) | Lib-heavy; conceito de boundary apenas |
| Streamlit UI | Consumidor, não produtor de pattern |

Claude gera, ela lê com olho crítico ("vazou abstração?"). Sem TDD.

### Regras de corte

- Conceito passa de 15min → cortar com "chega, mostra contrato".
- Python idiom → JIT, só quando travar, não preventivo.
- Periferia → pode gerar direto, pausar se ela perguntar "por quê".
- **Core POO → nunca pular conceito + contrato dela** (senão vira generate-and-defend e perde o gap).

---

## TDD — escopo e estratégia

TDD é imprescindível, adotado **seletivamente** no core POO. Testar tudo é caro; testar nada perde a validação arquitetural.

| Camada | TDD? | Razão |
|---|---|---|
| `Filme` + subclasses | ✅ | Polimorfismo é o coração da modelagem; valida cada sobrescrita |
| `Catalogo` | ✅ | Operações de coleção são contratos públicos; protege refactor |
| `DataSource` ABC + impls | ✅ | Repository: valida intercambiabilidade |
| `Recomendador` ABC + estratégias | ✅ | Strategy: valida intercambiabilidade |
| `FilmeFactory` | ✅ | Decide subclasse — comportamento crítico |
| `Analisador` (pandas) | ⚠️ minimal | Encapsulamento testado; conteúdo de DataFrame não |
| Streamlit UI | ❌ | Caro de testar, baixo retorno acadêmico |
| `etl/` scripts | ❌ | Exploração, não produto |

Não é TDD cerimonial — é teste que valida o **contrato público** das abstrações, não cada detalhe interno.

---

## O que cada teste valida

**`Filme` + subclasses** — polimorfismo (cada subclasse retorna score conforme regra), igualdade entre instâncias (mesmo título+ano), atributos preservados.

```python
def test_filme_aclamado_score_pondera_avg():
    f = FilmeAclamado(title="X", year=2000, genres=["Drama"], avg_rating=4.5, count=100)
    assert f.calcular_score() > Filme(title="X", year=2000, genres=["Drama"], avg_rating=4.5, count=100).calcular_score()
```

**`Catalogo`** — `buscar_por_titulo` case-insensitive; `filtrar_por_genero` subset correto; `adicionar` não duplica; `remover` retorna bool conforme presença.

**`DataSource` (Repository)** — teste de contrato: impls diferentes retornam mesma estrutura; cada uma carrega arquivo válido e falha graciosamente em arquivo ausente.

```python
@pytest.mark.parametrize("src", [
    CSVDataSource("fixtures/sample.csv"),
    JSONDataSource("fixtures/sample.json"),
])
def test_datasources_retornam_mesma_estrutura(src):
    dados = src.carregar()
    assert all(set(d.keys()) >= {"title", "year", "genres", "avg_rating", "count"} for d in dados)
```

**`Recomendador` (Strategy)** — teste de contrato: estratégias diferentes consumidas pelo mesmo código; `RecomendaPorGenero` só do gênero; `RecomendaPorNota` ordenado desc; `n` limita resultado.

```python
@pytest.mark.parametrize("rec", [
    RecomendaPorGenero("Drama"),
    RecomendaPorNota(),
    RecomendaPorPopularidade(),
])
def test_recomendadores_sao_intercambiaveis(rec, catalogo_fixture):
    resultado = rec.recomendar(catalogo_fixture, n=3)
    assert len(resultado) <= 3
    assert all(isinstance(f, Filme) for f in resultado)
```

O mesmo teste roda contra todas as impls — se o pattern quebra, qualquer impl falha. Validação do pattern, não do detalhe.

**`FilmeFactory`** — aplica precedência correta (`Classico > Cult > Blockbuster > Aclamado > Filme`); filme sem year vira `Filme` base; cada threshold testado na borda (limiar exato).

---

## Stack e estrutura de teste

- **`pytest`** — runner default; **fixtures** — `Catalogo` populado reutilizável; **`pytest.mark.parametrize`** — mesma asserção contra várias impls (demonstra Strategy/Repository no próprio teste, e é skill transferível direta pro Go: table-driven tests). Sem mocks elaborados; fixtures hardcoded com 5-10 filmes bastam.

```
tests/
├── conftest.py          # fixtures compartilhadas
├── test_filme.py        # Filme + subclasses
├── test_catalogo.py
├── test_datasource.py   # parametrizado em ambas impls
├── test_factory.py
└── test_recomendador.py # parametrizado nas 3 estratégias
```

Rodar: `.venv/bin/pytest tests/ -v`

---

## Por que o workflow rende ROI alto

| Etapa | Aprendizado |
|---|---|
| Conceito | Pattern em si (transferível pra Go/qualquer stack) |
| Contrato | Engineering judgment + arguibilidade da decisão |
| TDD | Validação do pattern + table-driven tests (skill Go) |
| Revisão | Internalização ativa, não passiva |

**Onde pode falhar:** Claude palestrar 25min → ela corta com "chega"; contrato ambíguo → teste falha cedo (mais barato que descobrir depois); ela pular conceito por pressa → vira generate-and-defend (compromisso: nunca pular conceito em camada core); Python idiom travar → Claude para e explica (JIT).

O racional sobre TDD ("por que TDD?", "por que não testar UI?", "por que parametrize?") mora em `../faq.md`.
