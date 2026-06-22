"""Entry Streamlit — 3 telas (Acervo, Estatísticas, Recomendações).

Consome só as interfaces de domínio (Catalogo/Analisador/Recomendador). O startup
(disco→objetos) roda 1× via @st.cache_resource e persiste entre reruns. Gráficos
via plotly. Sem ML em runtime — RecomendaSimilar só faz lookup em neighbors.csv.
"""

from pathlib import Path

import plotly.express as px
import streamlit as st

from shortlist.analisador import Analisador
from shortlist.catalogo import Catalogo
from shortlist.datasource import CSVDataSource
from shortlist.factory import FilmeFactory
from shortlist.recomendador import (
    RecomendaPorGenero,
    RecomendaPorNota,
    RecomendaPorPopularidade,
    RecomendaSimilar,
    carregar_vizinhos,
)

ETL = Path(__file__).resolve().parents[2] / "etl"
AGGREGATED = str(ETL / "aggregated.csv")
NEIGHBORS = str(ETL / "neighbors.csv")


@st.cache_resource
def build_catalogo() -> Catalogo:
    filmes = [FilmeFactory.criar(d) for d in CSVDataSource(AGGREGATED).carregar()]
    return Catalogo(filmes)


@st.cache_data
def load_vizinhos() -> dict[str, list[str]]:
    return carregar_vizinhos(NEIGHBORS)


def _linhas(filmes):
    return [
        {
            "Título": f.title,
            "Ano": f.year,
            "Categoria": f.categoria(),
            "Nota": round(f.avg_rating, 2),
            "Nota ajustada": round(f.weighted_rating, 2),
            "Votos": f.count,
        }
        for f in filmes
    ]


def tela_acervo(catalogo: Catalogo):
    st.header("Acervo")
    generos = sorted({g for f in catalogo.todos() for g in f.genres})
    categorias = sorted({f.categoria() for f in catalogo.todos()})

    col1, col2, col3 = st.columns(3)
    genero = col1.selectbox("Gênero", ["(todos)"] + generos)
    categoria = col2.selectbox("Categoria", ["(todas)"] + categorias)
    termo = col3.text_input("Buscar título")

    filmes = catalogo.todos()
    if genero != "(todos)":
        filmes = [f for f in filmes if genero in f.genres]
    if categoria != "(todas)":
        filmes = [f for f in filmes if f.categoria() == categoria]
    if termo:
        t = termo.lower()
        filmes = [f for f in filmes if t in f.title.lower()]

    st.caption(f"{len(filmes)} filme(s)")
    st.dataframe(_linhas(filmes[:500]), use_container_width=True, hide_index=True)


def tela_estatisticas(catalogo: Catalogo):
    st.header("Estatísticas")
    a = Analisador(catalogo)

    st.subheader("Distribuição de notas")
    st.plotly_chart(
        px.histogram(a.distribuicao_notas(), nbins=30, labels={"value": "Nota"}),
        use_container_width=True,
    )

    col1, col2 = st.columns(2)
    media = a.media_por_categoria()
    col1.subheader("Nota média por categoria")
    col1.plotly_chart(
        px.bar(
            x=list(media.keys()),
            y=list(media.values()),
            labels={"x": "Categoria", "y": "Nota média"},
        ),
        use_container_width=True,
    )
    contagem = a.contagem_por_categoria()
    col2.subheader("Filmes por categoria")
    col2.plotly_chart(
        px.bar(
            x=list(contagem.keys()),
            y=list(contagem.values()),
            labels={"x": "Categoria", "y": "Qtd"},
        ),
        use_container_width=True,
    )

    st.subheader("Ano × Nota")
    pontos = [(f.year, f.avg_rating) for f in catalogo.todos() if f.year is not None]
    corr = a.correlacao_ano_nota()
    st.metric("Correlação ano × nota", f"{corr:.3f}" if corr == corr else "—")
    st.plotly_chart(
        px.scatter(
            x=[p[0] for p in pontos],
            y=[p[1] for p in pontos],
            labels={"x": "Ano", "y": "Nota"},
            opacity=0.4,
        ),
        use_container_width=True,
    )


def tela_recomendacoes(catalogo: Catalogo):
    st.header("Recomendações")
    estrategia = st.selectbox(
        "Estratégia",
        ["Por nota", "Por popularidade", "Por gênero", "Similar (porque você gostou de X)"],
    )
    n = st.slider("Quantos", 1, 20, 5)

    if estrategia == "Por nota":
        rec = RecomendaPorNota()
    elif estrategia == "Por popularidade":
        rec = RecomendaPorPopularidade()
    elif estrategia == "Por gênero":
        generos = sorted({g for f in catalogo.todos() for g in f.genres})
        rec = RecomendaPorGenero(st.selectbox("Gênero", generos))
    else:
        titulos = sorted(f.movie_name for f in catalogo.todos())
        alvo = st.selectbox("Filme base", titulos)
        rec = RecomendaSimilar(alvo, load_vizinhos())

    resultado = rec.recomendar(catalogo, n=n)
    if resultado:
        st.dataframe(_linhas(resultado), use_container_width=True, hide_index=True)
    else:
        st.info("Sem recomendações para esse critério.")


def main():
    st.set_page_config(page_title="shortlist", layout="wide")
    st.title("shortlist 🎬")
    catalogo = build_catalogo()
    st.sidebar.caption(f"{len(catalogo)} filmes no acervo")
    tela = st.sidebar.radio("Tela", ["Acervo", "Estatísticas", "Recomendações"])

    if tela == "Acervo":
        tela_acervo(catalogo)
    elif tela == "Estatísticas":
        tela_estatisticas(catalogo)
    else:
        tela_recomendacoes(catalogo)


main()
