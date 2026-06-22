"""Entry Streamlit — 3 telas (Acervo, Estatísticas, Recomendações).

Consome só as interfaces de domínio (Catalogo/Analisador/Recomendador). O startup
(disco→objetos) roda 1× via @st.cache_resource e persiste entre reruns. Gráficos
via plotly. Sem ML em runtime — RecomendaSimilar só faz lookup em neighbors.csv.

Visual "Daylight Editorial" (caderno de cultura), com par dark. As cores de chrome
vêm de .streamlit/config.toml (dois modos nativos); este módulo casa o CSS custom
(header/sprocket/badges) e o template do plotly ao modo ativo lido de
st.context.theme. Seletores `data-testid=...` acoplam ao Streamlit 1.58 (pinado).
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# src-layout: torna o pacote `shortlist` importável quando o script roda direto
# (streamlit run src/shortlist/app.py — local e no Streamlit Cloud). pytest já
# resolve via pythonpath=["src"] no pyproject; streamlit não lê essa config.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

# Paleta dark única — "caderno de cinema" noturno: fundo near-black quente
# (espresso), texto off-white com tinta de papel, crimson levantado. `cat` mapeia
# categoria()→(fundo, texto) do badge.
PAL = {
    "surface": "#211E16",
    "text": "#EDE7DA",
    "muted": "#9A917D",
    "primary": "#E8654F",
    "border": "#322D22",
    "grid": "rgba(237,231,218,.08)",
    "chart": ["#E8654F", "#E7DFCC", "#D89A5B", "#8FB39E", "#A39A86"],
    "cat": {
        "Aclamado": ("#E7DFCC", "#16140F"),
        "Cult": ("#E8654F", "#16140F"),
        "Blockbuster": ("#D89A5B", "#16140F"),
        "Classico": ("#8FB39E", "#16140F"),
        "Filme": ("#2C2820", "#CFC7B4"),
    },
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

.block-container { padding-top: 3.4rem; max-width: 1100px; }

.sl-header { margin-bottom: 1.4rem; }
.sl-eyebrow { font: 600 11px Inter, sans-serif; line-height: 1.6; letter-spacing:.16em; text-transform:uppercase; color: __PRIMARY__; margin-bottom:.4rem; padding-top:.15rem; }
.sl-title { font: 700 44px Fraunces, serif; letter-spacing:-.02em; color: __TEXT__; line-height:1; display:flex; align-items:baseline; gap:.5rem; }
.sl-title .dot { color: __PRIMARY__; font-size:24px; }
.sl-sprocket { height:4px; margin:.7rem 0 .6rem; background: repeating-linear-gradient(90deg, __TEXT__ 0 3px, transparent 3px 9px); opacity:.5; border-radius:2px; }
.sl-sub { font: 400 13.5px Inter, sans-serif; color: __MUTED__; }

.sl-sech { font: 600 13px Inter, sans-serif; letter-spacing:.06em; text-transform:uppercase; color: __TEXT__; margin: 1.7rem 0 .15rem; opacity:.9; }
.sl-sech-sub { font:400 12px Inter, sans-serif; color: __MUTED__; margin-bottom:.55rem; }

div[data-testid="stMetric"] { background: __SURFACE__; border:1px solid __BORDER__; border-radius:.7rem; padding:1rem 1.1rem; }
div[data-testid="stMetricValue"] { font-family:'JetBrains Mono', monospace; color: __PRIMARY__; font-weight:600; }
div[data-testid="stMetricLabel"] p { text-transform:uppercase; letter-spacing:.08em; font-size:11px; opacity:.7; }

div[data-testid="stDataFrame"] { border:1px solid __BORDER__; border-radius:.6rem; }

.sl-mark { font:700 22px Fraunces, serif; color: __TEXT__; letter-spacing:-.01em; }
.sl-mark .dot { color: __PRIMARY__; }
.sl-tag { font:600 10px Inter, sans-serif; letter-spacing:.14em; text-transform:uppercase; color: __MUTED__; margin-top:.1rem; }
</style>
"""


@st.cache_resource
def build_catalogo() -> Catalogo:
    filmes = [FilmeFactory.criar(d) for d in CSVDataSource(AGGREGATED).carregar()]
    return Catalogo(filmes)


@st.cache_data
def load_vizinhos() -> dict[str, list[str]]:
    return carregar_vizinhos(NEIGHBORS)


def _inject_css(pal: dict) -> None:
    css = (
        _CSS.replace("__PRIMARY__", pal["primary"])
        .replace("__TEXT__", pal["text"])
        .replace("__MUTED__", pal["muted"])
        .replace("__SURFACE__", pal["surface"])
        .replace("__BORDER__", pal["border"])
    )
    st.markdown(css, unsafe_allow_html=True)


def _br(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _header(catalogo: Catalogo) -> None:
    st.markdown(
        f"""
        <div class="sl-header">
          <div class="sl-eyebrow">acervo curado</div>
          <div class="sl-title">shortlist <span class="dot">●</span></div>
          <div class="sl-sprocket"></div>
          <div class="sl-sub">{_br(len(catalogo))} filmes · destilados de 25M ratings</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(titulo: str, sub: str | None = None) -> None:
    html = f'<div class="sl-sech">{titulo}</div>'
    if sub:
        html += f'<div class="sl-sech-sub">{sub}</div>'
    st.markdown(html, unsafe_allow_html=True)


def _style_fig(fig, pal: dict):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=pal["text"], size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor=pal["grid"], zerolinecolor=pal["grid"], linecolor=pal["border"]),
        yaxis=dict(gridcolor=pal["grid"], zerolinecolor=pal["grid"], linecolor=pal["border"]),
    )
    return fig


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


def _tabela(filmes, pal: dict) -> None:
    if not filmes:
        st.info("Nada bate esse recorte — afrouxe um filtro.")
        return
    df = pd.DataFrame(_linhas(filmes))
    cat = pal["cat"]

    def _badge(v):
        bg, fg = cat.get(v, (pal["surface"], pal["text"]))
        return f"background-color:{bg}; color:{fg}; font-weight:600;"

    sty = df.style.map(_badge, subset=["Categoria"])
    st.dataframe(sty, width="stretch", hide_index=True)


def tela_acervo(catalogo: Catalogo, pal: dict):
    _section("Explorar o acervo", "Filtre por gênero, categoria ou título.")
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

    st.caption(f"{_br(len(filmes))} filme(s) no recorte · mostrando até 500")
    _tabela(filmes[:500], pal)


def tela_estatisticas(catalogo: Catalogo, pal: dict):
    _section("Panorama do acervo")
    a = Analisador(catalogo)
    notas = a.distribuicao_notas()
    corr = a.correlacao_ano_nota()

    c1, c2, c3 = st.columns(3)
    c1.metric("No acervo", _br(len(catalogo)))
    c2.metric("Nota média", f"{notas.mean():.1f}")
    c3.metric("Corr ano·nota", f"{corr:+.2f}" if corr == corr else "—")

    _section("Distribuição de notas", "Onde o acervo se concentra.")
    fig = px.histogram(notas, nbins=30, color_discrete_sequence=[pal["primary"]])
    fig.update_layout(showlegend=False, xaxis_title="Nota", yaxis_title="Filmes")
    st.plotly_chart(_style_fig(fig, pal), width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        _section("Nota média por categoria")
        media = a.media_por_categoria()
        cats = list(media.keys())
        fig = px.bar(
            x=cats,
            y=[media[c] for c in cats],
            color=cats,
            color_discrete_map={c: pal["cat"].get(c, (pal["primary"], ""))[0] for c in cats},
        )
        fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Nota média")
        st.plotly_chart(_style_fig(fig, pal), width="stretch")
    with col2:
        _section("Filmes por categoria", "O dispatch de threshold, visto de cima.")
        contagem = a.contagem_por_categoria()
        cats = list(contagem.keys())
        fig = px.bar(
            x=cats,
            y=[contagem[c] for c in cats],
            color=cats,
            color_discrete_map={c: pal["cat"].get(c, (pal["primary"], ""))[0] for c in cats},
        )
        fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Qtd")
        st.plotly_chart(_style_fig(fig, pal), width="stretch")

    _section("Ano × nota", "Filme mais novo não é filme melhor — veja a nuvem.")
    pontos = [(f.year, f.avg_rating) for f in catalogo.todos() if f.year is not None]
    fig = px.scatter(
        x=[p[0] for p in pontos],
        y=[p[1] for p in pontos],
        color_discrete_sequence=[pal["primary"]],
        opacity=0.35,
    )
    fig.update_layout(xaxis_title="Ano", yaxis_title="Nota")
    st.plotly_chart(_style_fig(fig, pal), width="stretch")


def tela_recomendacoes(catalogo: Catalogo, pal: dict):
    _section("Como você quer descobrir?", "Quatro estratégias intercambiáveis (Strategy).")
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
        alvo = st.selectbox("Filme base", titulos, index=None, placeholder="Escolha um filme…")
        if alvo is None:
            st.info("Escolha um filme base pra ver os similares.")
            return
        rec = RecomendaSimilar(alvo, load_vizinhos())

    _tabela(rec.recomendar(catalogo, n=n), pal)


def main():
    st.set_page_config(page_title="shortlist", page_icon="🎬", layout="wide")
    pal = PAL
    _inject_css(pal)
    catalogo = build_catalogo()
    _header(catalogo)

    st.sidebar.markdown(
        '<div class="sl-mark">shortlist <span class="dot">●</span></div>'
        '<div class="sl-tag">caderno de cinema</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"{_br(len(catalogo))} filmes no acervo")
    tela = st.sidebar.radio("Tela", ["Acervo", "Estatísticas", "Recomendações"])

    if tela == "Acervo":
        tela_acervo(catalogo, pal)
    elif tela == "Estatísticas":
        tela_estatisticas(catalogo, pal)
    else:
        tela_recomendacoes(catalogo, pal)


main()
