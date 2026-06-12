# FAQ — racional das decisões

Parágrafos objetivos que explicam cada decisão do projeto, escritos pra quem **não acompanhou o processo**. Cada resposta é autossuficiente. Detalhe técnico mora nas notas linkadas em `notebook/`.

---

## Por que as subclasses de `Filme` são essas (Classico, Cult, Blockbuster, Aclamado)?

As subclasses não foram inventadas a priori — elas **emergiram da distribuição real** do dataset (58.958 filmes agregados de 25M ratings). Em vez de chutar o que é "blockbuster" ou "clássico", medimos os percentis de três métricas — `count` (popularidade), `avg_rating` (nota) e `year` (ano) — e deixamos os cortes naturais da distribuição definirem cada categoria: `Blockbuster` é o topo 5% de popularidade (p95), `FilmeCult` é a faixa do meio bem avaliada (p50–p75), `FilmeAclamado` é nota alta com votos suficientes pra média valer, e `Classico` é filme antigo **que ainda é assistido** (ano + piso de reconhecimento). Cada threshold é, portanto, justificado por um número observado, não por opinião; e cada subclasse ficou com amostra real e não-vazia. O polimorfismo — cada subclasse calculando seu `score` de um jeito — é o reflexo em código dessa estrutura que o dado já tinha: as classes existem porque a distribuição mostrou que esses grupos existem de fato. *(Detalhe: `data/thresholds.md`.)*

---

## Por que percentis e não valores fixos?

Porque a média é distorcida por outliers e um valor "redondo" escolhido a olho não se sustenta. Um único filme com 81.491 ratings puxaria qualquer média; o percentil ignora o *valor* dos extremos e olha só a *posição* na fila ordenada — é robusto. Ancorar cada threshold num percentil (`count ≥ p95`, `year ≤ 1970 ∧ count ≥ p75`) transforma "achei que era assim" em "é o corte natural dos 5% mais populares deste acervo". A régua passa a ser o próprio dado. *(Detalhe: `data/thresholds.md`.)*

---

## Por que `FilmeAclamado` exige um mínimo de votos (`count ≥ 6`), e não só nota alta?

Porque nota alta de pouquíssimos votos não é aclamação — é ruído estatístico. Sem o piso, a categoria capturava 3.514 filmes com `count ≤ 5`, dos quais 2.005 tinham um único voto (um filme que uma pessoa avaliou com 5.0 não é "aclamado"). O piso `count ≥ 6` (mediana de `count`) garante amostra mínima pra a média significar algo. *(Detalhe: `data/thresholds.md` — finding 1.)*

---

## Por que `Classico` não é só "filme antigo"?

Porque idade pura confunde *velho* com *clássico*. `year ≤ 1970` sozinho rotulava 18,5% do catálogo como clássico, metade com ≤4 votos e 2.313 com um voto só — filmes esquecidos, não canônicos. Adicionamos um piso de reconhecimento (`count ≥ 37`, p75): clássico é o filme antigo que **ainda é assistido o bastante pra ter ficado**. Cai pra 3,3%. *(Detalhe: `data/thresholds.md` — finding 3.)*

---

## Por que a ordem das guard clauses do `FilmeFactory` importa?

Porque os critérios das subclasses **se sobrepõem** (vários pedem nota alta), então um filme pode satisfazer mais de um. A precedência resolve isso atribuindo classe única, e a **ordem é o mecanismo que fatia o eixo de popularidade em faixas**: avalia-se a condição mais estreita (Cult, faixa do meio) antes da mais ampla (Aclamado), pra a larga não engolir a estreita. `Classico` vem primeiro porque o tempo é um eixo ortogonal e foi eleito identidade dominante. Reordenar mudaria a classificação — a ordem é contrato, não estética. *(Detalhe: `data/thresholds.md`.)*

---

## Como as guard clauses do `FilmeFactory` funcionam como mecanismo de engenharia para revelar os dados?

Na engenharia de software do projeto, as *guard clauses* (cláusulas de guarda) lineares com retornos precoces (`return` antecipado) não são mero capricho de estilo ou legibilidade, mas o **motor físico que materializa a distribuição dos dados**. Funcionando como uma cascata de peneiras sobrepostas (filtro de gravidade), elas eliminam o acoplamento do *Arrow Anti-pattern* (aninhamentos profundos de `if/else`) e introduzem uma **simplificação matemática implícita**: à medida que cada guarda captura e retira uma classe de filme do fluxo (como `Cult` ou `Blockbuster`), as guardas seguintes operam sobre um espaço amostral automaticamente reduzido sem precisar declarar fórmulas booleanas complexas de exclusão de intervalo. A ordem de execução é, portanto, o instrumento de engenharia que de fato *revela* e separa a estrutura latente do dataset de forma determinística, garantindo partição perfeita (exclusão mútua absoluta) e alta extensibilidade para novas subclasses (princípio Open/Closed) com baixíssimo custo de processamento. *(Detalhe: `data/thresholds.md` — guard clauses.)*

---

## Por que dois `DataSource` (CSV e JSON) se o sistema usa um dataset só?

Pra demonstrar o padrão Repository com fontes que leem bytes reais — não com uma fonte fantasma. O JSON carrega **os mesmos dados agregados em outro formato** (não um dataset diferente): assim os dois impls produzem o mesmo `Catalogo`, provando que o resto do sistema não se acopla ao formato. Importante: o Repository desacopla **formato/origem**, não **distribuição** — os thresholds são calibrados a este dataset, então uma fonte com distribuição diferente exigiria recalibração. *(Detalhe: `engineering/design-patterns.md`.)*

---

## Por que o ETL fica fora do produto?

Princípio build-time vs run-time. A agregação dos 25M ratings (1,5GB) roda **uma vez**, offline, no `etl/`, e produz um snapshot de 58.958 linhas (~3MB) que o sistema consome. O produto nunca toca o dado bruto, não precisa de rede nem credencial Kaggle, e o avaliador roda em ambiente limpo sem reprocessar nada. ETL é fase, não produto. *(Detalhe: `data/dataset-e-etl.md`.)*

---

## Por que só dois patterns formais (Repository + Strategy) e o `FilmeFactory` é "factory-like"?

Porque os dois patterns formais emergem por necessidade real — fonte de dados plugável (Repository) e algoritmos de recomendação intercambiáveis (Strategy) —, não pra preencher checklist. O `FilmeFactory` é uma classe concreta com um método de fabricação (`criar(dado: dict) -> Filme`) que encapsula a lógica de decidir qual subclasse instanciar. Não o rotulamos como *Factory Method* GoF porque não há polimorfismo entre fábricas (não existe `FilmeFactoryA`/`FilmeFactoryB` com herança própria) — forçar isso seria overengineering pro tamanho do projeto. Por isso ele entra como **utilitário de domínio honesto** (factory-like), e os patterns formais ficam no Repository e no Strategy. Dois patterns com substância valem mais que cinco forçados. *(Detalhe: `engineering/design-patterns.md`.)*

---

## Por que a classificação fica numa fábrica separada, e não no `Filme` ou no `DataSource`?

Por responsabilidade única (SRP). A classificação não pode morar na entidade `Filme`: o `__init__` de uma classe de domínio recebe atributos, não decide qual de suas próprias subclasses instanciar. Também não pode morar no `DataSource`: a camada de persistência só lê bytes (CSV/JSON) e devolve `dict` — se conhecesse as subclasses, ficaria acoplada a regras estatísticas de negócio que não são da sua conta. O `FilmeFactory` é a fronteira ideal: recebe o `dict` cru do repositório, aplica os thresholds e a ordem de precedência, e devolve a subclasse correta. Efeito colateral valioso: todas as regras de classificação ficam **centralizadas** em `factory.py` — se um threshold mudar, UI, domínio e persistência não sofrem alteração. *(Detalhe: `engineering/design-patterns.md`.)*

---

## Por que esse dataset (e qual o trade-off)?

Escolhi um dataset **massivo de ratings** (25M ratings, 58.958 filmes) de propósito: a tese do projeto é que as subclasses **emergem de distribuição medida**, não de etiqueta arbitrária. Só com essa escala os percentis significam algo — "Blockbuster = topo 5% de popularidade" é estatística real, não rótulo hardcoded como `if genre == 'Documentary'`. Isso torna o polimorfismo uma decisão arquitetural justificada e dá substância de engenharia ao ETL (1,5GB agregados offline). **O trade-off, assumido conscientemente:** é um dataset *rating-centric*, de schema fino — só título, gênero, nota, contagem e ano (este enfiado no título, parseado por regex). Isso encurralou a modelagem num eixo só: `Cult`, `Blockbuster` e `Aclamado` vivem todos no plano `count × avg_rating`, diferindo por *onde sentam na popularidade*, não por tipos de dado distintos. O schema fino também não comporta subclasses por atributo (`FilmeNacional`/`Documentario`, sem `country`/`language`) nem recomendação content-based (sem sinopse) — ficam fora do escopo. Um TMDB/IMDb com metadata rica daria subclasses mais variadas e menos sobrepostas, mas custaria a narrativa de emergência estatística. Para *este* enquadramento (demonstrar POO + decisão data-driven), a troca compensa; a pobreza de schema foi justamente o que forçou a história limpa. *(Detalhe: `data/dataset-e-etl.md`.)*

---

## Por que rating bayesiano?

Ordenar o acervo por média crua deixa o ruído de baixa amostra dominar — um filme de 1 voto e nota 5.0 ficaria acima de um de 10 mil votos e 4.5. O piso de `count` das subclasses resolve a **classificação** (binário: dentro/fora), mas **ranquear** pede correção **contínua**. Apliquei *weighted rating* — shrinkage bayesiano que puxa a média de poucos votos rumo à média global, proporcional à quantidade de evidência. Os dois parâmetros saem da distribuição real: o prior é a média do catálogo, o piso é p75 do `count` — o mesmo já usado no Classico.

Sinaliza domínio de **estatística**, não só `sort()`. Mostra que você reconheceu um problema (baixa amostra), conhece a técnica nomeada (shrinkage / *empirical Bayes*) e a calibrou nos próprios dados. É a contraparte estatística do que o collaborative filtering é em álgebra linear — as duas métricas que sobem o produto de "catálogo com sort" pra "catálogo com critério". *(Detalhe: `data/rating-bayesiano.md`.)*

---

## Por que collaborative filtering não é "sistema de ML"?

A recomendação por similaridade (`RecomendaSimilar`) usa **similaridade de cosseno** sobre co-avaliações — `cos(A,B) = (A·B)/(‖A‖·‖B‖)`, produto escalar normalizado pela magnitude, que mede o **ângulo** entre dois vetores. Não há modelo treinado, parâmetro aprendido, função de perda nem otimização: é **determinística** (mesmos dados → mesmo resultado, sempre) e anterior a ML — vem do *vector space model* de recuperação de informação (anos 70). CF item-based é classificado como *memory-based / instance-based* (**não-paramétrico**): guarda os dados e calcula similaridade, sem treinar nada — contrasta com *model-based CF* (fatoração de matriz, SVD), que não usamos. O `sklearn` só **hospeda** a função; importá-lo não torna o projeto "sistema de ML" mais que `import math` torna alguém matemático. Por higiene, `sklearn`/`scipy` ficam **só no `etl/`**: o trabalho pesado (cosseno sobre matriz esparsa) roda offline uma vez e emite `neighbors.csv`; o produto só faz lookup O(1). A claim "sem ML em runtime, recomendação determinística" fica intacta — e mais forte, porque mostra domínio da fronteira. *(Detalhe: `data/collab-filter.md`.)*

---

## Por que TDD?

Os patterns só fazem sentido se o contrato for estável. O teste **é** o contrato verificável: sem teste, a intercambiabilidade de Strategy/Repository vira promessa; com teste, vira fato demonstrável. Por isso TDD é seletivo no core POO (`Filme`+subclasses, `Catalogo`, `DataSource`, `FilmeFactory`, `Recomendador`) e ausente na periferia. *(Detalhe: `engineering/tdd-e-workflow.md`.)*

---

## Por que não testar a UI Streamlit?

Streamlit é camada de **consumo**, não produtora de pattern — o que importa é se o que ela consome está correto. Testa-se o núcleo, demonstra-se a UI. Cobrir Streamlit teria custo alto e retorno baixo: nenhuma abstração nova vive lá. *(Detalhe: `engineering/tdd-e-workflow.md`.)*

---

## Por que `pytest.mark.parametrize`?

Porque demonstra Strategy/Repository **no próprio teste**: o mesmo teste roda contra todas as impls (3 estratégias, 2 DataSources) — se o pattern quebra, qualquer impl falha. É também *table-driven testing*, skill transferível direta pro Go. *(Detalhe: `engineering/tdd-e-workflow.md`.)*

---

## Se cache foi descartado como overkill, por que `st.cache_resource`?

São coisas diferentes — "cache" embola três mecanismos. Descartamos **cache de domínio runtime** (memoizar busca/filtro): 59k filmes em memória, filtro em milissegundos, não há o que cachear. O que **usamos** é **memoização de rerun do Streamlit**, que não é camada de domínio e sim lifecycle de framework: o Streamlit re-executa o script inteiro a cada clique/dropdown, então sem `@st.cache_resource` o build de 59k re-rodaria por interação. `cache_resource` fixa o `Catalogo` (mesma instância entre reruns) e `cache_data` o parse dos CSVs. E não — isso **não** é Singleton GoF: a unicidade é da infra, não da classe (construtor público, testável). Os patterns formais continuam só Strategy + Repository. *(Detalhe: `engineering/architecture.md` · `data/dataset-e-etl.md` · `engineering/design-patterns.md`.)*