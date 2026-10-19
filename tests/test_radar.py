import pytest

import flota
import radar
import tablero


def test_busqueda_lineal_en_cubo_vacio_no_encuentra_nada():
    cubo = tablero.crear_cubo(4)
    punto, metricas = radar.busqueda_lineal(cubo)
    assert punto is None
    assert metricas["comparaciones"] == 64
    assert metricas["profundidad_max"] == 0
    assert metricas["tiempo_ms"] >= 0


def test_busqueda_lineal_encuentra_la_primera_celda_con_nave():
    cubo = tablero.crear_cubo(4)
    tablero.escribir_celda(cubo, 2, 1, 3, tablero.NAVE_OCULTA)
    tablero.escribir_celda(cubo, 2, 1, 4, tablero.NAVE_OCULTA)
    punto, metricas = radar.busqueda_lineal(cubo)
    assert punto == (2, 1, 3)
    assert metricas["comparaciones"] == 16 + 3


def test_busqueda_lineal_de_otro_estado():
    cubo = tablero.crear_cubo(3)
    tablero.escribir_celda(cubo, 1, 1, 1, tablero.NAVE_OCULTA)
    tablero.escribir_celda(cubo, 3, 3, 3, tablero.IMPACTO)
    punto, metricas = radar.busqueda_lineal(cubo, tablero.IMPACTO)
    assert punto == (3, 3, 3)
    assert metricas["comparaciones"] == 27


def cubo_con_una_nave(n, celdas):
    cubo = tablero.crear_cubo(n)
    for (z, x, y) in celdas:
        tablero.escribir_celda(cubo, z, x, y, tablero.NAVE_OCULTA)
    return cubo


def test_busqueda_optimizada_en_cubo_vacio_revisa_todo():
    cubo = tablero.crear_cubo(4)
    punto, metricas = radar.busqueda_optimizada(cubo)
    assert punto is None
    assert metricas["comparaciones"] == 64
    assert metricas["profundidad_max"] == 0


def test_busqueda_optimizada_encuentra_cada_nave_con_la_mitad_de_comparaciones():
    n = 8
    for semilla in range(5):
        naves = flota.ubicacion_automatica(tablero.crear_cubo(n), flota.CATALOGO, semilla)
        for nave in naves:
            cubo = cubo_con_una_nave(n, nave["celdas"])
            punto, metricas = radar.busqueda_optimizada(cubo)
            assert punto in nave["celdas"]
            assert metricas["comparaciones"] <= n ** 3 // 2


def test_busqueda_optimizada_solo_mira_celdas_pares_primero():
    # (1,1,3) tiene suma impar y se saltea; (1,1,4) es la segunda celda par.
    cubo = cubo_con_una_nave(4, [(1, 1, 3), (1, 1, 4)])
    punto, metricas = radar.busqueda_optimizada(cubo)
    assert punto == (1, 1, 4)
    assert metricas["comparaciones"] == 2


def test_busqueda_optimizada_encuentra_restos_en_celdas_impares():
    # Fragata con su celda par ya impactada: solo queda la impar.
    cubo = cubo_con_una_nave(4, [(1, 1, 3)])
    tablero.escribir_celda(cubo, 1, 1, 2, tablero.IMPACTO)
    punto, metricas = radar.busqueda_optimizada(cubo)
    assert punto == (1, 1, 3)
    assert metricas["comparaciones"] == 32 + 2


def test_busqueda_optimizada_hace_menos_comparaciones_que_la_lineal():
    cubo = cubo_con_una_nave(8, [(8, 8, 7), (8, 8, 8)])
    _, lineal = radar.busqueda_lineal(cubo)
    _, optimizada = radar.busqueda_optimizada(cubo)
    assert optimizada["comparaciones"] < lineal["comparaciones"]


def test_sonar_sobre_z_detecta_las_naves_del_plano():
    cubo = cubo_con_una_nave(4, [(3, 1, 1), (3, 1, 2), (2, 1, 1)])
    contactos, metricas = radar.sonar(cubo, "z", 3)
    assert sorted(contactos) == [(3, 1, 1), (3, 1, 2)]
    assert metricas["comparaciones"] == 16
    assert tablero.leer_celda(cubo, 3, 1, 1) == tablero.DETECTADO_SONAR
    assert tablero.leer_celda(cubo, 2, 1, 1) == tablero.NAVE_OCULTA


def test_sonar_sobre_x_y_sobre_y():
    cubo = cubo_con_una_nave(4, [(1, 2, 4), (2, 2, 4)])
    contactos, _ = radar.sonar(cubo, "X", 2)
    assert sorted(contactos) == [(1, 2, 4), (2, 2, 4)]

    cubo = cubo_con_una_nave(4, [(1, 2, 4), (2, 2, 4)])
    contactos, _ = radar.sonar(cubo, "y", 3)
    assert contactos == []


def test_sonar_no_cambia_agua_ni_impactos_y_repite_contactos():
    cubo = cubo_con_una_nave(4, [(1, 1, 1)])
    tablero.escribir_celda(cubo, 1, 2, 2, tablero.IMPACTO)
    tablero.escribir_celda(cubo, 1, 3, 3, tablero.AGUA_MARCADA)
    radar.sonar(cubo, "z", 1)
    contactos, _ = radar.sonar(cubo, "z", 1)
    assert contactos == [(1, 1, 1)]
    assert tablero.leer_celda(cubo, 1, 2, 2) == tablero.IMPACTO
    assert tablero.leer_celda(cubo, 1, 3, 3) == tablero.AGUA_MARCADA
    assert tablero.contar_celdas_en_estado(cubo, tablero.SIN_EXPLORAR) == 61


def test_sonar_con_eje_o_valor_invalido():
    cubo = tablero.crear_cubo(4)
    with pytest.raises(ValueError):
        radar.sonar(cubo, "w", 1)
    with pytest.raises(ValueError):
        radar.sonar(cubo, "z", 5)
    with pytest.raises(ValueError):
        radar.sonar(cubo, "z", 0)
