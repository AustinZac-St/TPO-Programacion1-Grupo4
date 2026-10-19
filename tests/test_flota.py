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



# Entrega 2: impactos, naves averiadas y hundidas

def cubo_con_naves():
    """Arma un cubo de 8 con una fragata, un destructor, un submarino,
    un portaaviones y la estacion orbital ubicados a mano."""
    cubo = tablero.crear_cubo(8)
    naves = []
    flota.ubicar_nave(cubo, naves, "F", (3, 1, 1), (3, 1, 2))
    flota.ubicar_nave(cubo, naves, "D", (3, 5, 1), (3, 5, 3))
    flota.ubicar_nave(cubo, naves, "S", (1, 1, 6), (1, 3, 6))
    flota.ubicar_nave(cubo, naves, "P", (6, 1, 1), (6, 5, 1))
    flota.ubicar_nave(cubo, naves, "E", (4, 5, 5), (5, 6, 6))
    return cubo, naves


def test_disparo_al_agua_marca_la_celda():
    cubo, naves = cubo_con_naves()
    resultado = flota.recibir_impacto(cubo, naves, (8, 8, 8))
    assert resultado["resultado"] == "agua"
    assert resultado["nave"] is None
    assert resultado["mensaje"] == "Agua."
    assert tablero.leer_celda(cubo, 8, 8, 8) == tablero.AGUA_MARCADA


def test_impacto_deja_la_nave_averiada():
    cubo, naves = cubo_con_naves()
    resultado = flota.recibir_impacto(cubo, naves, (3, 5, 2), "T")
    destructor = flota.buscar_nave(naves, (3, 5, 2))
    assert resultado["resultado"] == "impacto"
    assert resultado["nave"] == "D1"
    assert resultado["mensaje"] == "Impacto. Destructor averiado (1 de 3)."
    assert flota.estado_nave(destructor) == "averiada"
    assert tablero.leer_celda(cubo, 3, 5, 2) == tablero.IMPACTO


def test_hundir_una_nave_marca_todas_sus_celdas():
    cubo, naves = cubo_con_naves()
    flota.recibir_impacto(cubo, naves, (3, 1, 1))
    resultado = flota.recibir_impacto(cubo, naves, (3, 1, 2))
    assert resultado["hundida"]
    assert resultado["mensaje"] == "Impacto. Fragata hundida."
    assert tablero.leer_celda(cubo, 3, 1, 1) == tablero.HUNDIDO
    assert tablero.leer_celda(cubo, 3, 1, 2) == tablero.HUNDIDO
    assert [nave["id"] for nave in flota.naves_hundidas(naves)] == ["F1"]


def test_disparo_repetido_no_cambia_nada():
    cubo, naves = cubo_con_naves()
    flota.recibir_impacto(cubo, naves, (3, 5, 2))
    assert flota.recibir_impacto(cubo, naves, (3, 5, 2))["resultado"] == "repetido"
    flota.recibir_impacto(cubo, naves, (8, 8, 8))
    assert flota.recibir_impacto(cubo, naves, (8, 8, 8))["resultado"] == "repetido"
    assert len(flota.buscar_nave(naves, (3, 5, 2))["impactos"]) == 1


def test_portaaviones_necesita_dos_impactos_por_celda():
    cubo, naves = cubo_con_naves()
    primero = flota.recibir_impacto(cubo, naves, (6, 3, 1))
    assert primero["resultado"] == "resiste"
    assert tablero.leer_celda(cubo, 6, 3, 1) == tablero.NAVE_OCULTA
    segundo = flota.recibir_impacto(cubo, naves, (6, 3, 1))
    assert segundo["resultado"] == "impacto"
    assert segundo["mensaje"] == "Impacto. Portaaviones averiado (1 de 5)."
    assert tablero.leer_celda(cubo, 6, 3, 1) == tablero.IMPACTO


def test_submarino_es_inmune_al_laser():
    cubo, naves = cubo_con_naves()
    resultado = flota.recibir_impacto(cubo, naves, (1, 2, 6), "L")
    assert resultado["resultado"] == "inmune"
    assert resultado["mensaje"] == "Agua."
    assert tablero.leer_celda(cubo, 1, 2, 6) == tablero.NAVE_OCULTA
    assert flota.recibir_impacto(cubo, naves, (1, 2, 6), "T")["resultado"] == "impacto"


def test_destructor_avisa_que_revela_una_celda():
    cubo, naves = cubo_con_naves()
    assert flota.recibir_impacto(cubo, naves, (3, 5, 1))["efecto"] == "revela_celda"
    assert flota.recibir_impacto(cubo, naves, (3, 1, 1))["efecto"] is None


def test_estacion_da_municion_extra_solo_al_hundirse():
    cubo, naves = cubo_con_naves()
    estacion = flota.buscar_nave(naves, (4, 5, 5))
    puntos = sorted(estacion["celdas"])
    resultados = flota.disparar_celdas(cubo, naves, puntos)
    efectos = [r["efecto"] for r in resultados]
    assert efectos == [None] * 7 + ["municion_extra"]
    assert flota.describir_nave(estacion) == "Estacion orbital hundida"


def test_resumen_de_un_disparo_con_varias_celdas():
    cubo, naves = cubo_con_naves()
    celdas = [(3, 1, 1), (3, 1, 2), (3, 2, 1), (8, 8, 8)]
    resumen = flota.resumen_disparo(flota.disparar_celdas(cubo, naves, celdas, "R"))
    assert resumen["impactos"] == 2
    assert resumen["aguas"] == 2
    assert resumen["hundidas"] == ["Fragata"]
    assert resumen["efectos"] == []
    assert resumen["mensajes"] == ["Impacto. Fragata averiada (1 de 2).",
                                   "Impacto. Fragata hundida.", "Agua."]


def test_estado_de_flota_y_flota_hundida():
    cubo = tablero.crear_cubo(8)
    naves = []
    assert not flota.flota_hundida(naves)
    flota.ubicar_nave(cubo, naves, "F", (3, 1, 1), (3, 1, 2))
    assert flota.estado_de_flota(naves) == [
        {"id": "F1", "nombre": "Fragata", "estado": "intacta", "destruidas": 0, "total": 2}]
    flota.disparar_celdas(cubo, naves, [(3, 1, 1), (3, 1, 2)])
    assert flota.flota_hundida(naves)
    assert flota.naves_a_flote(naves) == []


def test_celda_para_revelar():
    cubo, naves = cubo_con_naves()
    celda = flota.celda_para_revelar(naves, semilla=3)
    nave = flota.buscar_nave(naves, celda)
    assert nave is not None and celda not in nave["impactos"]
    assert flota.celda_para_revelar(naves, 3) == celda
    assert flota.celda_para_revelar([], 3) is None


def test_disparo_invalido_lanza_excepcion():
    cubo, naves = cubo_con_naves()
    for punto in [(0, 1, 1), (9, 1, 1), (1, 1), "1,1,1", (1, "2", 3)]:
        with pytest.raises(flota.DisparoInvalido):
            flota.recibir_impacto(cubo, naves, punto)
    assert issubclass(flota.DisparoInvalido, flota.ErrorFlota)
