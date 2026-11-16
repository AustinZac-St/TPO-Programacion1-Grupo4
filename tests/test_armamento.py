import armamento
import tablero


def test_catalogo_tiene_las_siete_armas_con_sus_datos():
    assert sorted(armamento.CATALOGO_ARMAS) == ["C", "G", "L", "O", "R", "S", "T"]
    for arma in armamento.CATALOGO_ARMAS.values():
        assert "nombre" in arma
        assert "municion_inicial" in arma
        assert "funcion" in arma


def test_torpedo_tiene_municion_ilimitada():
    assert armamento.CATALOGO_ARMAS["T"]["municion_inicial"] is None


def test_torpedo_afecta_solo_la_celda_apuntada():
    cubo = tablero.crear_cubo(8)
    funcion = armamento.CATALOGO_ARMAS["T"]["funcion"]
    assert funcion(cubo, (4, 2, 7)) == [(4, 2, 7)]
    assert tablero.contar_celdas_en_estado(cubo, tablero.SIN_EXPLORAR) == 512

def test_onda_expansiva_en_el_centro_afecta_27_celdas():
    cubo = tablero.crear_cubo(8)
    celdas = armamento.arma_onda_expansiva(cubo, (4, 4, 4))
    assert len(celdas) == 27
    assert celdas[0] == (4, 4, 4)
    assert (5, 5, 5) in celdas          # diagonal
    assert len(set(celdas)) == 27       # sin repetidas


def test_onda_expansiva_en_una_esquina_afecta_8_celdas():
    cubo = tablero.crear_cubo(8)
    celdas = armamento.arma_onda_expansiva(cubo, (1, 1, 1))
    assert len(celdas) == 8
    assert all(tablero.punto_dentro_del_cubo(cubo, *c) for c in celdas)


def test_torpedo_guiado_sin_naves_cae_en_el_punto():
    cubo = tablero.crear_cubo(8)
    assert armamento.arma_torpedo_guiado(cubo, (4, 4, 4)) == [(4, 4, 4)]


def test_torpedo_guiado_con_nave_en_el_punto_va_ahi():
    cubo = tablero.crear_cubo(8)
    tablero.escribir_celda(cubo, 4, 4, 4, tablero.NAVE_OCULTA)
    tablero.escribir_celda(cubo, 4, 4, 5, tablero.NAVE_OCULTA)
    assert armamento.arma_torpedo_guiado(cubo, (4, 4, 4)) == [(4, 4, 4)]


def test_torpedo_guiado_va_a_la_nave_vecina_mas_cercana():
    cubo = tablero.crear_cubo(8)
    tablero.escribir_celda(cubo, 5, 5, 5, tablero.NAVE_OCULTA)   # diagonal
    tablero.escribir_celda(cubo, 4, 4, 5, tablero.NAVE_OCULTA)   # comparte cara
    assert armamento.arma_torpedo_guiado(cubo, (4, 4, 4)) == [(4, 4, 5)]


def test_torpedo_guiado_ignora_naves_lejanas_y_celdas_ya_impactadas():
    cubo = tablero.crear_cubo(8)
    tablero.escribir_celda(cubo, 4, 4, 6, tablero.NAVE_OCULTA)   # a 2 de distancia
    tablero.escribir_celda(cubo, 4, 4, 5, tablero.IMPACTO)
    assert armamento.arma_torpedo_guiado(cubo, (4, 4, 4)) == [(4, 4, 4)]


def test_torpedo_guiado_sigue_a_una_nave_detectada_por_sonar():
    cubo = tablero.crear_cubo(8)
    tablero.escribir_celda(cubo, 3, 4, 4, tablero.DETECTADO_SONAR)
    assert armamento.arma_torpedo_guiado(cubo, (4, 4, 4)) == [(3, 4, 4)]


def test_armas_nuevas_no_modifican_el_cubo():
    cubo = tablero.crear_cubo(8)
    tablero.escribir_celda(cubo, 4, 4, 5, tablero.NAVE_OCULTA)
    copia = [[fila[:] for fila in capa] for capa in cubo]
    armamento.arma_onda_expansiva(cubo, (4, 4, 4))
    armamento.arma_torpedo_guiado(cubo, (4, 4, 4))
    assert cubo == copia


def test_todas_las_armas_de_disparo_tienen_funcion():
    for letra, datos in armamento.CATALOGO_ARMAS.items():
        if letra != "S":
            assert callable(datos["funcion"])
