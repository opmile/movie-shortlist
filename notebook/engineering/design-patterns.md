# Design patterns escolhidos

**Data:** 2026-05-28

---

## Decisão: 2 patterns formais + POO fundamental

Após análise de ROI (ver `notebook/doc/02-roi-reducao-complexidade.md`), reduzimos de 4 patterns iniciais pra **2 patterns profundos**.

### POO fundamentals (sempre presentes, não contam como "pattern" GoF)
- Encapsulamento
- Herança (`Filme` base + 4 subclasses)
- Polimorfismo (sobrescrita de `calcular_score()`, `exibir()`)
- Abstração via classes/ABCs

### Design patterns formalmente trabalhados
1. **Strategy** — `Recomendador` ABC + 3 implementações
2. **Repository** — `DataSource` ABC + 2 implementações

---

## Strategy — `Recomendador`

**Contrato:**
```python
class Recomendador(ABC):
    @abstractmethod
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]: ...
```

**Implementações:**
| Classe | Operação interna |
|---|---|
| `RecomendaPorGenero(genero_alvo)` | Filtro |
| `RecomendaPorNota` | Sort por `avg_rating` |
| `RecomendaPorPopularidade` | Sort por `count` |

**Por que Strategy aqui:**
- Mesmo contrato, algoritmos diferentes (filter vs sort vs sort com chave diferente)
- Substitui chain de `if/elif` por dispatch polimórfico (Open/Closed Principle)
- UI escolhe estratégia em runtime (dropdown), sem `if` em quem chama
- Pattern absorve adicionar `RecomendaCollabFiltering` em v2 sem mexer no resto

**Por que mercado-relevante:**
- Pattern mais útil em código de domínio
- Aparece em: payment gateways (Stripe/PayPal/PIX), validação de regras, formatters, retry policies, motor de regras
- Em Go = `interface` com N impls (mesmo princípio, sem o nome)

---

## Repository — `DataSource`

**Contrato:**
```python
class DataSource(ABC):
    @abstractmethod
    def carregar(self) -> list[dict]: ...
```

Retorna lista de dicts (não `Filme` direto) — separa responsabilidade: `DataSource` lê dados brutos, `FilmeFactory` decide subclasse.

**Implementações:**
| Classe | Origem |
|---|---|
| `CSVDataSource(path)` | Lê `aggregated.csv` |
| `JSONDataSource(path)` | Lê variante JSON (conversão trivial pra demonstrar plug-and-play) |

**Por que Repository aqui:**
- Catalogo não sabe se dados vêm de CSV, JSON, API, DB
- Trocar fonte = trocar 1 linha de instanciação
- Mock em teste = `MockDataSource` retornando dicts hardcoded

**Por que mercado-relevante:**
- Onipresente em backend: Spring Data, JPA, Hibernate, ActiveRecord, Django ORM, GORM, Prisma
- Toda app séria tem camada Repository
- Em Spring Boot ela usa `@Repository` — aqui implementa do zero, entendendo o porquê

---

## O que NÃO é pattern formal aqui

### Factory (rejeitado)
**Por que sai do escopo:** sem polimorfismo de `DataSource` instanciado dinamicamente em runtime, Factory pra `DataSource` vira `CSVDataSource()` direto.

**Mas existe um "Factory-like":** `FilmeFactory` decide subclasse de `Filme` baseado em stats. Isso é mais "construtor com lógica" do que pattern Factory formal. **Decisão:** documentar como ajudante de construção, não como pattern trabalhado.

### Singleton, Observer, Decorator, Adapter (não aplicáveis)
Não emergem naturalmente do problema. Forçar = decoração.

---

## Como esses 2 patterns se complementam

| Eixo | Pattern | Polimorfismo aplicado |
|---|---|---|
| **Camada de dados** (origem) | Repository | Horizontal — várias fontes, mesmo contrato |
| **Camada de uso** (algoritmo) | Strategy | Vertical — várias maneiras de processar, mesmo contrato |

Banca vê o mesmo princípio aplicado em contextos diferentes — argumento de coerência arquitetural.

---

## TDD nesses patterns

Tanto `Recomendador` quanto `DataSource` têm contratos verificáveis via teste:

**Strategy:**
```python
def test_recomendadores_sao_intercambiaveis():
    catalogo = Catalogo([...])
    for rec in [RecomendaPorGenero("Drama"), RecomendaPorNota(), RecomendaPorPopularidade()]:
        resultado = rec.recomendar(catalogo, n=3)
        assert isinstance(resultado, list)
        assert all(isinstance(f, Filme) for f in resultado)
        assert len(resultado) <= 3
```

**Repository:**
```python
def test_datasources_retornam_mesmo_schema():
    for src in [CSVDataSource("test.csv"), JSONDataSource("test.json")]:
        dados = src.carregar()
        assert isinstance(dados, list)
        assert all(set(d.keys()) >= {"title", "year", "genres", "avg_rating", "count"} for d in dados)
```

Teste = munição de banca ("aqui valido o pattern") + skill transferível direta pro Go (table-driven tests).
