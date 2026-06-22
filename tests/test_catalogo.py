def test_len_reflete_filmes(catalogo):
    assert len(catalogo) == 8


def test_todos_devolve_copia(catalogo):
    a = catalogo.todos()
    a.clear()
    assert len(catalogo) == 8


def test_filtrar_por_genero(catalogo):
    dramas = catalogo.filtrar_por_genero("Drama")
    titulos = {f.title for f in dramas}
    assert titulos == {"Old Classic", "Quiet Gem", "Obscure", "Drama Three"}


def test_buscar_por_titulo_case_insensitive(catalogo):
    assert {f.title for f in catalogo.buscar_por_titulo("big")} == {"Big Hit"}


def test_por_categoria(catalogo):
    assert {f.title for f in catalogo.por_categoria("Blockbuster")} == {"Big Hit", "Action Two"}


def test_filtros_nao_mutam(catalogo):
    catalogo.filtrar_por_genero("Drama")
    assert len(catalogo) == 8
