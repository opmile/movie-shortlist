"""Catalogo — coleção encapsulada de Filme, read-only pós-build.

Filtros devolvem list[Filme] NOVA; nunca mutam a coleção interna (a instância é
compartilhada entre reruns do Streamlit via @st.cache_resource — mutação vazaria).
"""

from shortlist.domain import Filme


class Catalogo:
    def __init__(self, filmes: list[Filme]):
        self._filmes = list(filmes)

    def __len__(self) -> int:
        return len(self._filmes)

    def todos(self) -> list[Filme]:
        return list(self._filmes)

    def filtrar_por_genero(self, genero: str) -> list[Filme]:
        return [f for f in self._filmes if genero in f.genres]

    def buscar_por_titulo(self, termo: str) -> list[Filme]:
        t = termo.lower()
        return [f for f in self._filmes if t in f.title.lower()]

    def por_categoria(self, categoria: str) -> list[Filme]:
        return [f for f in self._filmes if f.categoria() == categoria]
