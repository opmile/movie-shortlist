# Como colaborar no `shortlist`

Trabalho colaborativo é novo pra todo mundo do grupo. Este guia é o passo-a-passo:
como contribuir sem pisar no código dos outros, e o porquê de cada etapa. Leia uma vez
inteiro antes do primeiro PR — depois vira só consulta.

---

## Por que a gente trabalha assim

Regra única: **ninguém commita direto na `main`.**

A `main` não é uma branch qualquer — é a fonte que o **Streamlit Community Cloud** publica.
Todo merge na `main` redeploya o app automaticamente. Se código quebrado entra na `main`,
o app no ar quebra junto.

Então o fluxo protege a `main`: cada um trabalha **isolado na própria branch**, abre um
**Pull Request (PR)**, o **CI** valida, alguém revisa, e só então funde. Assim a `main`
está sempre verde e deployável.

```
sua branch  →  código + commit  →  push  →  abrir PR  →  CI roda  →  review  →  merge  →  deploy automático
```

---

## 1. Crie sua branch

**Por quê:** sua branch é seu espaço isolado. Você experimenta, erra, refaz — sem afetar a
`main` nem o trabalho dos outros. Duas pessoas podem mexer no projeto ao mesmo tempo sem
colisão, porque cada uma está na sua branch.

**Como:** sempre parta da `main` atualizada.

```bash
git checkout main
git pull                              # pega o estado mais recente
git checkout -b tipo/descricao-curta  # cria E entra na branch nova
```

Convenção de nome — `tipo/descricao` (o tipo casa com o estilo de commit do repo):

| Tipo     | Quando                          | Exemplo                     |
|----------|---------------------------------|-----------------------------|
| `feat/`  | funcionalidade nova             | `feat/filme-subclasses`     |
| `test/`  | testes                          | `test/catalogo`             |
| `refactor/` | refatoração sem mudar comportamento | `refactor/repository`   |
| `docs/`  | documentação                    | `docs/spec-recomendador`    |
| `fix/`   | correção de bug                 | `fix/threshold-precedencia` |

Descrição curta, em minúsculas, com hífen. Domínio em português (como o resto do projeto).

---

## 2. Trabalhe, commite e pushe a branch

Faça seu trabalho e commits normalmente. Quando quiser subir pro GitHub:

```bash
git push -u origin tipo/descricao-curta
```

O `-u` liga sua branch local à do GitHub na primeira vez; depois é só `git push`.

**Nunca** rode `git push` apontando pra `main`. Sua branch, sempre.

---

## 3. Abra um Pull Request (PR)

Depois do push, o GitHub mostra um botão pra abrir PR a partir da sua branch.

**O que é:** um pedido pra fundir sua branch na `main`.

**Por que existe:** o PR é o ponto onde o trabalho é **visto antes de entrar**. Ele dá:
- **revisão** — outra pessoa lê seu código, pergunta, sugere;
- **discussão** — fica registrado o porquê das decisões;
- **gate automático** — o CI roda sozinho e mostra se algo quebrou.

Sem PR, código entra na `main` sem ninguém olhar e sem validação. Com PR, nada entra cru.

Escreva no PR o **o quê** e o **porquê** da mudança (não só o "o quê" — isso o diff já mostra).

---

## 4. O CI no GitHub Actions

Assim que o PR abre (e a cada novo push na branch), o **CI** roda automático. É o workflow
em `.github/workflows/ci.yml`.

**O que ele roda:**
- **`ruff`** — checa estilo e erros de código (imports não usados, variável indefinida, formatação).
- **`pytest`** — roda os testes.

**Por que existe:** pega problema **antes do merge**, não depois. Estilo inconsistente e
teste quebrado são barrados no PR — a `main` (que vira deploy) fica protegida. É o que
torna seguro várias pessoas mexerem no mesmo projeto.

**Como ler:** no PR aparece um check `quality`:
- ✔ **verde** — passou, pode seguir pra review/merge.
- ✘ **vermelho** — algo falhou. Clique em "Details" pra ver qual passo (ruff? pytest?) e o erro. Corrija na sua branch, commite, pushe — o CI roda de novo sozinho.

> **Nota da fase atual:** ainda estamos em discovery/spec, sem testes. O CI está configurado
> pra ficar **verde mesmo sem nenhum teste** (trata "zero testes" como sucesso). Assim que o
> primeiro teste do core POO for commitado, o CI passa a barrar testes quebrados de verdade —
> sem precisar mexer no workflow.

**Regra:** PR só funde com **CI verde + ao menos uma aprovação na review.**

---

## 5. Merge → deploy automático

Com o CI verde e a review aprovada, faça o merge do PR na `main` (botão no GitHub).

A partir daí o **Streamlit Community Cloud detecta o push na `main` e redeploya o app sozinho**
— não precisa fazer mais nada. O ciclo fechou.

Depois do merge, apague a branch (o GitHub oferece o botão) e, localmente:

```bash
git checkout main
git pull
```

para começar o próximo trabalho a partir da `main` já atualizada.

---

## Setup inicial do repositório (uma vez, pelo dono)

Pra que a regra "ninguém commita na `main`" seja **garantida** (não só combinada), ligue a
proteção de branch no GitHub — isso não dá pra configurar por arquivo no repo:

**Settings → Branches → Add branch ruleset (ou Add rule) para `main`:**
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging → selecionar o check **`quality`**

Sem isso, o `push` direto na `main` continua tecnicamente possível e o PR vira só convenção.

---

## Setup local de cada pessoa (uma vez)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Antes de pushar, rode o mesmo que o CI roda — pega o erro localmente, evita PR vermelho:

```bash
ruff check .
ruff format .       # aplica a formatação (o CI checa com --check)
pytest
```
