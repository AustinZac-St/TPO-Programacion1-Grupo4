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
