import pytest

import flota
import tablero


def test_ubicar_nave_escribe_el_cubo_y_registra_la_nave():
    cubo = tablero.crear_cubo(8)
    naves = []
    flota.ubicar_nave(cubo, naves, "f", (3, 5, 4), (3, 5, 5))
    assert naves[0]["id"] == "F1"
    assert naves[0]["celdas"] == {(3, 5, 4), (3, 5, 5)}
    assert tablero.leer_celda(cubo, 3, 5, 4) == tablero.NAVE_OCULTA


def test_ubicar_nave_pegada_a_otra_falla_y_no_modifica_nada():
    cubo = tablero.crear_cubo(8)
    naves = []
    flota.ubicar_nave(cubo, naves, "F", (3, 5, 4), (3, 5, 5))
    with pytest.raises(flota.UbicacionInvalida):
        flota.ubicar_nave(cubo, naves, "D", (3, 5, 6), (3, 5, 8))
    assert len(naves) == 1
    assert tablero.contar_celdas_en_estado(cubo, tablero.NAVE_OCULTA) == 2


def test_restricciones_de_cada_tipo():
    casos = [
        ("S", (5, 1, 1), (5, 1, 3)),   # submarino en la mitad superior
        ("P", (4, 1, 1), (4, 1, 5)),   # portaaviones en la mitad inferior
        ("C", (1, 1, 1), (1, 1, 4)),   # crucero en z = 1
        ("E", (1, 2, 2), (2, 3, 3)),   # estacion tocando una cara
        ("F", (1, 1, 1), (1, 1, 3)),   # largo incorrecto
        ("F", (1, 8, 8), (1, 8, 9)),   # fuera del cubo
    ]
    for tipo, desde, hasta in casos:
        with pytest.raises(flota.UbicacionInvalida):
            flota.ubicar_nave(tablero.crear_cubo(8), [], tipo, desde, hasta)


def test_nave_desconocida_y_nave_agotada():
    cubo = tablero.crear_cubo(8)
    naves = []
    with pytest.raises(flota.NaveDesconocida):
        flota.ubicar_nave(cubo, naves, "Q", (1, 1, 1), (1, 1, 2))
    flota.ubicar_nave(cubo, naves, "C", (2, 1, 1), (2, 1, 4))
    with pytest.raises(flota.NaveAgotada):
        flota.ubicar_nave(cubo, naves, "C", (5, 1, 1), (5, 1, 4))


def test_ubicacion_automatica_arma_una_flota_valida():
    for semilla in range(20):
        cubo = tablero.crear_cubo(8)
        naves = flota.ubicacion_automatica(cubo, flota.CATALOGO, semilla)
        ubicaciones = [(nave["tipo"], list(nave["celdas"])) for nave in naves]
        assert flota.validar_flota(ubicaciones, 8) == (True, "")
        assert flota.flota_completa(naves)
        assert tablero.contar_celdas_en_estado(cubo, tablero.NAVE_OCULTA) == 35


def test_misma_semilla_da_la_misma_flota():
    primera = flota.ubicacion_automatica(tablero.crear_cubo(8), flota.CATALOGO, 7)
    segunda = flota.ubicacion_automatica(tablero.crear_cubo(8), flota.CATALOGO, 7)
    assert primera == segunda


def test_pendientes_descuenta_las_naves_ubicadas():
    naves = []
    flota.ubicar_nave(tablero.crear_cubo(8), naves, "F", (1, 1, 1), (1, 1, 2))
    assert flota.pendientes(naves)["F"] == 2
    assert not flota.flota_completa(naves)
