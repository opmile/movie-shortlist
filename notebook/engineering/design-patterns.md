# Design patterns — Strategy, Repository e o FilmeFactory "factory-like"

**Data:** 2026-05-28

Os 2 patterns formais (Strategy + Repository), por que o `FilmeFactory` é factory-like e não GoF, e por que o Repository desacopla formato mas não distribuição.

---

## Decisão: 2 patterns formais + POO fundamental

Após análise de ROI (`project-e-escopo.md`), reduzimos de 4 patterns iniciais pra **2 profundos**.

**POO fundamentals** (sempre presentes, não contam como pattern GoF): encapsulamento, herança (`Filme` base + 4 subclasses), polimorfismo (sobrescrita de `calcular_score()`), abstração via ABCs.

**Patterns formalmente trabalhados:** Strategy (`Recomendador`) + Repository (`DataSource`).

Dois patterns bem defendidos valem mais que cinco forçados.

---

## Strategy — `Recomendador`

```python
class Recomendador(ABC):
    @abstractmethod
    def recomendar(self, catalogo: Catalogo, n: int = 5) -> list[Filme]: ...
```

| Implementação | Operação interna |
|---|---|
| `RecomendaPorGenero(genero_alvo)` | Filtro |
| `RecomendaPorNota` | Sort por `weighted_rating` (rating bayesiano) |
| `RecomendaPorPopularidade` | Sort por `count` |
| `RecomendaSimilar(titulo_alvo)` | Lookup item-based em `neighbors.csv` (CF, ver `../data/collab-filter.md`) |

**Por que Strategy:** mesmo contrato, algoritmos diferentes; substitui chain de `if/elif` por dispatch polimórfico (Open/Closed); UI escolhe estratégia em runtime (dropdown) sem `if` em quem chama. O `RecomendaSimilar` (CF) é a prova viva da extensibilidade: entrou como 4ª implementação sem tocar o contrato nem as outras três.

**Mercado:** payment gateways (Stripe/PayPal/PIX), validação de regras, formatters, retry policies. Em Go = `interface` com N impls (mesmo princípio, sem o nome); em Spring = `@Component` + injeção.

---

## Repository — `DataSource`

```python
class DataSource(ABC):
    @abstractmethod
    def carregar(self) -> list[dict]: ...
```

| Implementação | Origem |
|---|---|
| `CSVDataSource(path)` | Lê `aggregated.csv` |
| `JSONDataSource(path)` | Lê variante JSON (mesmos dados agregados, outro formato) |

Retorna `list[dict]` (não `Filme`) — separa responsabilidade: `DataSource` lê dados brutos, `FilmeFactory` decide subclasse.

**Por que Repository:** `Catalogo` não sabe se dados vêm de CSV/JSON/API/DB; trocar fonte = 1 linha de instanciação; mock em teste = `MockDataSource` com dicts hardcoded.

**Mercado:** onipresente em backend (Spring Data, JPA, Hibernate, Django ORM, GORM, Prisma). Aqui implementa do zero, entendendo o porquê.

---

## Por que dois DataSources se o sistema usa um dataset só

O ruído real **não** seria "dois datasources" — seria "um datasource que não lê nada". O sistema consome **um** arquivo (`aggregated.csv`); um `JSONDataSource` fantasma (sem JSON real pra ler) cheira a teatro ("cadê o JSON que ele lê?").

**Decisão (Alternativa A):** o JSON carrega **os mesmos dados agregados em outro formato** (o ETL emite `aggregated.json` junto do `.csv`, ~1 linha `df.to_json`; `JSONDataSource.carregar()` ~3 linhas). Os dois impls produzem `Catalogo` idêntico — essa é a prova de swappability, com bytes reais, não fantasma.

Por que não as outras: **(B) CSV-only** — abstração de um filho só parece YAGNI, Repository fica afirmado e não demonstrado. **(C) 2 fontes + `DataSourceFactory`** — mais forte academicamente (3º pattern formal), mas re-infla o escopo enxugado; guardado como upgrade opcional de reta final (e A é pré-requisito dele).

---

## Insight central — Repository desacopla formato, NÃO distribuição

Por que o JSON precisa ser do **mesmo** dataset?

Os thresholds do `FilmeFactory` são **calibrados a este dataset**: `count ≥ 1508` é o p95 *destas* 58.958 linhas; `Classico count ≥ 37` é o p75 *delas* (ver `../data/thresholds.md`). Se o `JSONDataSource` lesse um dataset **diferente** (ex: lista curada com `count=1` por filme), o `FilmeFactory` quebraria — nenhum blockbuster possível, tudo cairia em base/Classico. Estaríamos demonstrando o swap do Repository com uma fonte que produz lixo, **minando** a demo.

**Regra:** classificação é **calibrada**, não universal. Fonte com distribuição diferente exigiria recalibração por fonte.

**Corolário de design:** a fronteira do Repository é o formato/origem dos bytes. A semântica da classificação vive **depois**, no `FilmeFactory`, amarrada à distribuição do agregado. São responsabilidades separadas — e é exatamente isso que o `list[dict]` (em vez de `list[Filme]`) na saída do `DataSource` materializa. Repository e Factory são **eixos ortogonais**: Repository = *de onde* vem o dado; Factory = *qual objeto* instanciar.

---

## FilmeFactory — factory-like, não GoF

GoF clássico costuma ter fábrica polimórfica (herança na própria fábrica): **Factory Method** define interface e deixa subclasses decidirem a classe a instanciar; **Abstract Factory** cria famílias de objetos. O nosso `FilmeFactory` é uma **classe concreta** com um método de fabricação (`criar(dado: dict) -> Filme`) que encapsula a lógica de dispatch a partir de dados brutos. Não há `FilmeFactoryA`/`FilmeFactoryB` com herança própria.

Por isso é rotulado **Factory-like** (utilitário de domínio honesto), não um dos patterns GoF formais do projeto. Forçar polimorfismo entre fábricas seria overengineering pro tamanho do projeto.

### Por que a classificação mora numa fábrica separada (SRP)

- **Não pode morar em `Filme`:** o `__init__` de uma classe de domínio recebe atributos, não decide qual de suas próprias subclasses instanciar.
- **Não pode morar no `DataSource`:** a persistência só lê bytes (CSV/JSON) e devolve `dict`; se conhecesse as subclasses, ficaria acoplada a regras estatísticas de negócio que não são da sua conta.
- **`FilmeFactory` é a fronteira ideal:** recebe o `dict` cru, aplica thresholds + precedência, devolve a subclasse correta.

**Efeito colateral valioso — centralização:** todas as regras de classificação ficam em `factory.py`. Se um threshold mudar, UI/domínio/persistência não sofrem alteração.

---

## O que NÃO é pattern formal aqui

- **Factory (rejeitado):** sem polimorfismo de `DataSource` instanciado dinamicamente, Factory pra `DataSource` vira `CSVDataSource()` direto. O `FilmeFactory` existe mas é factory-like, não pattern trabalhado.
- **Singleton, Observer, Decorator, Adapter:** não emergem do problema. Forçar = decoração.

### Singleton-scope ≠ Singleton GoF (cuidado de framing)

O `Catalogo` é instanciado **uma vez** e compartilhado entre todos os reruns/sessões do Streamlit, via `@st.cache_resource` no `build_catalogo()`. Isso **parece** Singleton, mas **não é o pattern GoF** — e a distinção é exatamente o que separa entender pattern de decorar:

| | Singleton GoF | `Catalogo` + `cache_resource` |
|---|---|---|
| Quem garante unicidade | a **própria classe** (`__new__`/`getInstance`, construtor privado) | a **infra** (store no processo do servidor Streamlit) |
| A classe se policia? | sim | **não** — construtor público, instanciável N× em teste |
| Acoplamento | estado global embutido no domínio (anti-padrão clássico: atrapalha teste) | domínio limpo; unicidade é escopo de *lifecycle*, externo |

É **singleton-scope** (ciclo de vida gerido por fora), não Singleton pattern. Justamente por isso o `Catalogo` continua testável (cada teste instancia o seu). **Não reivindicar como pattern formal** — os patterns do projeto seguem só Strategy + Repository. O `cache_resource` é mecanismo de framework, não design pattern. Mecânica/alvos em `architecture.md` (Fluxo runtime); os 3 sentidos de "cache" em `../data/dataset-e-etl.md`.

Caveat operacional: ref compartilhada ⇒ `Catalogo` read-only pós-build (filtro devolve `list[Filme]` nova, nunca muta a coleção interna), senão estado vaza entre sessões.

---

## Como os 2 patterns se complementam

| Eixo | Pattern | Polimorfismo |
|---|---|---|
| Camada de dados (origem) | Repository | Horizontal — várias fontes, mesmo contrato |
| Camada de uso (algoritmo) | Strategy | Vertical — várias maneiras de processar, mesmo contrato |

Mesmo princípio em contextos diferentes — argumento de coerência arquitetural. Os dois têm contratos verificáveis via teste (ver `tdd-e-workflow.md`).
