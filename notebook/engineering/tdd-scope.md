# TDD — escopo e estratégia

**Data:** 2026-05-28
**Decisão:** TDD é imprescindível nesse projeto. Adotado seletivamente no core POO.

---

## Princípio: TDD seletivo, não cerimonial

Testar tudo é caro e diminui retorno. Testar nada perde munição arquitetural. Equilíbrio:

| Camada | TDD? | Razão |
|---|---|---|
| `Filme` + subclasses | ✅ | Polimorfismo é exigência da banca; teste valida cada sobrescrita |
| `Catalogo` | ✅ | Operações de coleção são contratos públicos; teste protege refactor |
| `DataSource` ABC + impls | ✅ | Pattern Repository: teste valida intercambiabilidade |
| `Recomendador` ABC + estratégias | ✅ | Pattern Strategy: teste valida intercambiabilidade |
| `FilmeFactory` | ✅ | Decide subclasse — comportamento crítico |
| `Analisador` (pandas) | ⚠️ minimal | Encapsulamento testado; conteúdo de DataFrame não |
| Streamlit UI | ❌ | Caro de testar, baixo retorno acadêmico |
| `lab/` scripts | ❌ | Exploração, não produto |

---

## O que cada teste valida

### `Filme` + subclasses
- Polimorfismo: cada subclasse retorna score conforme regra
- Igualdade entre instâncias (mesmo título+ano)
- Atributos preservados após construção

```python
def test_filme_aclamado_score_pondera_avg():
    f = FilmeAclamado(title="X", year=2000, genres=["Drama"], avg_rating=4.5, count=100)
    assert f.calcular_score() > Filme(title="X", year=2000, genres=["Drama"], avg_rating=4.5, count=100).calcular_score()
```

### `Catalogo`
- `buscar_por_titulo` case-insensitive
- `filtrar_por_genero` retorna subset correto
- `adicionar` não duplica
- `remover` retorna bool conforme presença

### `DataSource` (Repository)
- **Teste de contrato:** dois DataSources diferentes retornam mesma estrutura
- Cada impl carrega arquivo válido
- Cada impl falha graciosamente em arquivo ausente

```python
@pytest.mark.parametrize("src", [
    CSVDataSource("fixtures/sample.csv"),
    JSONDataSource("fixtures/sample.json"),
])
def test_datasources_retornam_mesma_estrutura(src):
    dados = src.carregar()
    assert all(set(d.keys()) >= {"title", "year", "genres", "avg_rating", "count"} for d in dados)
```

### `Recomendador` (Strategy)
- **Teste de contrato:** estratégias diferentes consumidas pelo mesmo código
- `RecomendaPorGenero` retorna só filmes do gênero
- `RecomendaPorNota` retorna ordenado desc
- `n` limita resultado

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

### `FilmeFactory`
- Aplica precedência correta (Classico > Cult > Blockbuster > Aclamado > Filme)
- Filme sem year detectado vira `Filme` base
- Cada threshold testado em borda (limiar exato)

---

## Workflow: TDD-light no fluxo conceito → contrato → implementação

Conforme `workflow.md`:

1. Conceito (Claude expõe pattern, 5-15min)
2. Contrato (você esboça interface)
3. **Você escreve 1-2 testes** que exercitam o pattern
4. Claude refina os testes (se necessário) e implementa pra passar
5. Você revisa diff com pergunta de engenharia

Não é TDD cerimonial. É TDD direcionado a validar **o contrato**, não cada detalhe interno.

---

## Stack de teste

- **`pytest`** — runner default; descobre testes automaticamente
- **`pytest fixtures`** — pra criar `Catalogo` populado reutilizável
- **`pytest.mark.parametrize`** — pra testar mesma asserção com várias estratégias/fontes (demonstra Strategy/Repository diretamente no teste)

Sem mocks elaborados. Fixtures hardcoded com 5-10 filmes bastam pra cobrir contratos.

---

## Estrutura de pastas

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

## Defesa na banca

"Por que TDD nesse projeto?"
→ "Porque os patterns só fazem sentido se o contrato for estável. Teste é o contrato verificável. Sem teste, intercambiabilidade vira promessa; com teste, vira fato demonstrável."

"Por que não testar UI?"
→ "Streamlit é camada de consumo. Testes UI rendem pouco — o que importa é se o que UI consome está correto. Teste o núcleo, demo a UI."

"Por que parametrize?"
→ "Demonstra Strategy/Repository diretamente no teste — o mesmo teste roda contra todas as implementações. Se o pattern quebra, qualquer impl falha o mesmo teste."
