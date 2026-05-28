# O que esse projeto exercita em engenharia — leitura pra quem está chegando

**Data:** 2026-05-28
**Pra quem é:** pessoa que sabe programar mas nunca trabalhou design patterns formais, POO disciplinada ou TDD direcionado a contratos. Lê esse arquivo primeiro, depois mergulha nos outros quando precisar de detalhe.

---

## TL;DR

Um catálogo de filmes em Python com Streamlit. Por baixo, dois **design patterns formais** (Strategy + Repository) + **herança polimórfica** (`Filme` → 4 subclasses) coordenados sobre um dataset agregado real. **Não é** sobre filmes nem sobre dados — é sobre **defender cada decisão arquitetural na banca**.

---

## Conceitos centrais que esse projeto exercita

### 1. POO disciplinada vs POO decorativa

POO decorativa: tudo vira classe porque "é OO". Métodos viram getters/setters. Herança aparece porque "ficou bonito ter classes-pai".

POO disciplinada: classe existe **porque encapsula um conceito do domínio**. Herança existe **porque há polimorfismo real**. Método existe **porque expressa uma operação relevante**.

Aqui, cada subclasse de `Filme` (`Aclamado`, `Blockbuster`, `Cult`, `Classico`) sobrescreve `calcular_score()` com fórmula coerente com sua identidade. **Polimorfismo aplicado, não etiqueta.**

Critério de defesa: pra cada classe/método/abstração existe **resposta clara à pergunta "por que isso existe?"**.

### 2. Por que design patterns existem

Pattern não é "código mais bonito". Pattern resolve **acoplamento**: sem ele, mudar X exige mexer em Y, Z, W. Com ele, mudar X é trocar uma linha.

Aqui:
- Sem Strategy: adicionar "recomendar por popularidade" exige `if estrategia == "popularidade": ...` espalhado.
- Com Strategy: adicionar = nova classe que respeita o contrato. Resto do código não vê diferença.

**Princípio que isso instancia:** *Open/Closed* — código aberto pra extensão, fechado pra modificação.

### 3. Strategy — algoritmo plugável

Mesmo contrato (`recomendar(catalogo, n) -> list[Filme]`), implementações diferentes.

```python
class Recomendador(ABC):
    @abstractmethod
    def recomendar(self, catalogo, n=5) -> list[Filme]: ...

class RecomendaPorGenero(Recomendador): ...
class RecomendaPorNota(Recomendador): ...
class RecomendaPorPopularidade(Recomendador): ...
```

UI escolhe estratégia em runtime via dropdown. Quem chama não sabe qual veio. **Dispatch polimórfico substitui `if/elif`.**

Em Go isso é uma `interface` com N implementações — princípio idêntico, sem o nome formal. Em Spring é `@Component` + injeção. Pattern existe em qualquer linguagem que tenha polimorfismo.

### 4. Repository — origem plugável

Mesmo contrato (`carregar() -> list[dict]`), origens diferentes.

```python
class DataSource(ABC):
    @abstractmethod
    def carregar(self) -> list[dict]: ...

class CSVDataSource(DataSource): ...
class JSONDataSource(DataSource): ...
```

`Catalogo` não sabe se dados vêm de CSV, JSON, API ou DB. Trocar fonte = trocar uma linha de instanciação. **Mock em teste = `MockDataSource` retornando dicts hardcoded.** Spring Data, Django ORM, GORM, Prisma — todos materializam esse pattern.

### 5. Herança apropriada (e quando não usar)

Herança é apropriada quando há **especialização real**: subclasse "é um(a)" mais específico da base, com comportamento próprio.

Aqui: `FilmeAclamado` *é um* `Filme` que calcula score ponderando nota. `Blockbuster` *é um* `Filme` que pondera popularidade. Cada um respeita o contrato base e adiciona comportamento.

**Quando herança seria errada:** se "Aclamado" fosse só uma flag (`if filme.is_aclamado:`) sem comportamento próprio. Aí seria atributo, não subclasse.

Regra geral moderna: **prefira composição quando a relação é "tem um"**. Herança quando é "é um" e há método polimórfico real.

### 6. TDD direcionado a contratos

TDD aqui não é "1 teste pra cada método". É **teste que valida o contrato público** das abstrações.

Exemplo: o teste paramétrico abaixo demonstra Strategy direto no código:

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

O mesmo teste roda contra todas as implementações. **Se o pattern quebra, qualquer impl falha o teste.** Validação do pattern, não do detalhe interno.

UI não tem TDD — Streamlit é consumidor, custa caro testar, rende pouco. **TDD seletivo**: aplica onde rende, ignora onde não rende.

### 7. Encapsulamento como disciplina, não enfeite

`Catalogo` guarda uma `list[Filme]`. Quem usa `Catalogo` **nunca acessa a lista direto**. Acesso vai via `buscar`, `filtrar_por_genero`, `listar`.

Custo: mais código. Benefício: refactor da estrutura interna (trocar lista por dict pra busca O(1)) não exige mexer no resto. **Acoplamento controlado.**

Mesma lógica em `Analisador`: encapsula pandas. Quem chama vê `top_por_genero(n) -> dict`, não DataFrame. **Pandas isolado.** Se quiser trocar pra polars depois, só `Analisador` muda.

### 8. Separation of concerns

Cada classe responde a **uma pergunta clara**:

| Classe | Pergunta |
|---|---|
| `Filme` (+ sub) | "O que é esse filme? Quanto vale?" |
| `Catalogo` | "Onde está a coleção? Como buscar?" |
| `FilmeFactory` | "Qual subclasse instanciar a partir dos dados?" |
| `DataSource` | "De onde vêm os dados?" |
| `Analisador` | "Que estatísticas sobre o catálogo?" |
| `Recomendador` | "Que filmes sugerir?" |

Cada uma faz uma coisa. Mudar uma coisa muda uma classe. **Princípio de SRP (Single Responsibility) em prática.**

### 9. Build-time vs run-time (cross-disciplinar com data/)

ETL pesado roda **uma vez** offline (em `lab/`). App carrega só o snapshot agregado. App nunca toca CSV bruto, Kaggle ou pipeline.

**Princípio:** aplicação não faz trabalho pesado no caminho do usuário. Em escala industrial, "build" vira Airflow/dbt; "run" vira API/app. Mesmo princípio.

### 10. Defesa na banca = engineering judgment

Critério final do TFD: **explicar por que cada decisão foi tomada**.

- Por que Strategy aqui? → "Recomendação tem várias formas, mesmo contrato. Strategy substitui if/elif por dispatch."
- Por que herança em Filme? → "Subclasses têm cálculo de score diferente — polimorfismo aplicado."
- Por que não cache? → "59k filmes em memória, overkill."
- Por que cortar collab filtering? → "Eixo de aprendizado é POO. Recsys dispersa foco."

**Saber cortar > saber implementar tudo.** Decisão deliberada de escopo é tão arguível quanto pattern bem aplicado.

---

## Como ler os outros arquivos dessa pasta

Em ordem de mergulho:

1. **`project-definition.md`** — o que o projeto é/não é, propósito duplo (banca + portfólio). Comece aqui pra contexto.
2. **`architecture.md`** — diagrama de camadas, fluxo de dados, princípios respeitados. O mapa visual.
3. **`design-patterns.md`** — Strategy + Repository em profundidade, com comparação Go/Java/Spring. O coração técnico.
4. **`tdd-scope.md`** — onde aplicar TDD, exemplos paramétricos, justificativa de cortes. Como validar os patterns.
5. **`workflow.md`** — fluxo "conceito → contrato → implementação" pra aprender enquanto coda. O processo de trabalho.
6. **`stack-and-tooling.md`** — Python, venv, deps, estrutura de pastas, git. A mecânica de execução.

---

## Vocabulário pra fixar

| Termo | O que é | Aparece em |
|---|---|---|
| ABC | Abstract Base Class — interface formal em Python. | `design-patterns.md` |
| Strategy | Algoritmo plugável atrás de um mesmo contrato. | `design-patterns.md` |
| Repository | Origem de dados plugável atrás de um mesmo contrato. | `design-patterns.md` |
| Polimorfismo | Mesmo método, comportamento diferente por subclasse. | `architecture.md` |
| Encapsulamento | Esconder estrutura interna; expor operações. | `architecture.md` |
| Open/Closed | Aberto pra extensão, fechado pra modificação. | `architecture.md` |
| SRP | Single Responsibility — cada classe faz uma coisa. | `architecture.md` |
| TDD seletivo | Testar contratos públicos no core; não testar UI. | `tdd-scope.md` |
| `pytest.parametrize` | Mesmo teste roda contra várias impls — demonstra pattern. | `tdd-scope.md` |
| Engineering judgment | Saber cortar escopo é skill arguível. | `project-definition.md` |

---

## O que esse mini-projeto ensina em currículo

1. Strategy + Repository aplicados com substância (não decoração).
2. Herança polimórfica defendida com método sobrescrito real.
3. TDD direcionado a contratos via `pytest.parametrize`.
4. Encapsulamento de lib externa (pandas) atrás de classe própria.
5. Build vs run-time bem separados (ETL fora do produto).
6. Escopo cortado deliberadamente com justificativa (collab filtering deferred).

Seis linhas em conversa de entrevista. Cada uma tem código pra mostrar e decisão pra defender.

---

## Relação com a pasta `data/`

Engenharia aqui = **como o sistema é construído**.
Data lá = **como o input do sistema foi preparado**.

Os dois se encontram em `aggregated.csv`: output do pipeline (data) = input do `CSVDataSource` (engineering).

Ler `notebook/data/00-introducao-data-eng.md` em paralelo dá o quadro completo: pipeline produz snapshot, sistema consome snapshot, banca defende as duas pontas.
