import pytest

import flota
import partida
import tablero
import armamento


def responder(monkeypatch, respuestas):
    """Reemplaza input por una lista de respuestas ya tipeadas."""
    pendientes = iter(respuestas)
    monkeypatch.setattr("builtins.input", lambda mensaje="": next(pendientes))


def test_nueva_partida_1v1_por_defecto():
    estado = partida.nueva_partida_1v1()
    assert estado["n"] == 8
    assert estado["turno"] == 0
    assert [j["nombre"] for j in estado["jugadores"]] == ["Jugador 1", "Jugador 2"]
    assert estado["jugadores"][0]["cubo"] is not estado["jugadores"][1]["cubo"]
    assert estado["jugadores"][0]["flota"] == []
    assert estado["historial"]["jugadores"] == ("Jugador 1", "Jugador 2")


def test_nueva_partida_1v1_con_configuracion():
    estado = partida.nueva_partida_1v1({"n": 6, "nombres": ("Ana", "Beto")})
    assert len(estado["jugadores"][1]["cubo"]) == 6
    with pytest.raises(ValueError):
        partida.nueva_partida_1v1({"nombres": ("Ana", "Ana")})


def test_nueva_partida_1v1_municion_a_cada_jugador():
    estado = partida.nueva_partida_1v1()
    municion_1 = estado["jugadores"][0]["municion"]
    municion_2 = estado["jugadores"][1]["municion"]
    assert municion_1 is not municion_2
    assert municion_1["T"] is None
    assert municion_1["R"] == 3


def test_ejecutar_turno_dispara_registra_y_pasa_turno():
    estado = partida.nueva_partida_1v1()
    for jugador in estado["jugadores"]:
        partida.ubicacion_automatica(jugador)
    estado = partida.ejecutar_turno(estado, {"arma": "T", "objetivo": (1, 1, 1)})
    assert estado["turno"] == 1
    assert len(estado["historial"]["jugadas"]) == 1
    resumen = estado["ultimo_resumen"]
    assert resumen["impactos"] + resumen["aguas"] == 1

def test_ejecutar_turno_con_error_no_gasta_municion_ni_cambia_el_turno():
    estado = partida.nueva_partida_1v1()
    for jugador in estado["jugadores"]:
        partida.ubicacion_automatica(jugador)
    with pytest.raises(partida.ObjetivoInvalido):
        partida.ejecutar_turno(estado, {"arma": "R", "objetivo": (99, 1, 1)})
    with pytest.raises(partida.ArmaNoDisponible):
        partida.ejecutar_turno(estado, {"arma": "Z", "objetivo": (1, 1, 1)})
    with pytest.raises(partida.ArmaNoDisponible):
        partida.ejecutar_turno(estado, {"arma": "S", "objetivo": (1, 1, 1)})
    assert estado["jugadores"][0]["municion"]["R"] == 3
    assert estado["turno"] == 0
    assert len(estado["historial"]["jugadas"]) == 0


def test_ejecutar_turno_sin_municion():
    estado = partida.nueva_partida_1v1()
    for jugador in estado["jugadores"]:
        partida.ubicacion_automatica(jugador)
    estado["jugadores"][0]["municion"]["R"] = 0
    with pytest.raises(armamento.SinMunicion):
        partida.ejecutar_turno(estado, {"arma": "R", "objetivo": (1, 1, 1)})
    assert estado["turno"] == 0


def test_hay_ganador_sin_ganador_y_con_ganador():
    estado = partida.nueva_partida_1v1()
    for jugador in estado["jugadores"]:
        partida.ubicacion_automatica(jugador)
    assert partida.hay_ganador(estado) is None
    for nave in estado["jugadores"][1]["flota"]:
        nave["impactos"] = set(nave["celdas"])
    assert partida.hay_ganador(estado) == "Jugador 1"


def test_hay_ganador_sin_flotas_ubicadas():
    estado = partida.nueva_partida_1v1()
    assert partida.hay_ganador(estado) is None


def test_pedir_jugada_con_torpedo(monkeypatch):
    responder(monkeypatch, ["t", "4,2,7"])
    jugada = partida.pedir_jugada()
    assert jugada["arma"] == "T"
    assert jugada["objetivo"] == (4, 2, 7)
    assert jugada["eje"] is None


def test_pedir_jugada_vuelve_a_preguntar_si_el_dato_es_invalido(monkeypatch, capsys):
    responder(monkeypatch, ["h", "t", "4,2", "4,2,7"])
    jugada = partida.pedir_jugada()
    assert jugada["arma"] == "T"
    assert "Dato invalido" in capsys.readouterr().out


def test_pedir_jugada_con_laser_pide_el_eje(monkeypatch):
    responder(monkeypatch, ["L", "1,1,1", "x"])
    jugada = partida.pedir_jugada()
    assert jugada["arma"] == "L"
    assert jugada["eje"] == "x"


def test_texto_a_tramo():
    assert partida.texto_a_tramo("3,4,2-3,4,7") == ((3, 4, 2), (3, 4, 7))
    assert partida.texto_a_tramo(" 3, 4 ,2 - 3,4,7 ") == ((3, 4, 2), (3, 4, 7))
    assert partida.texto_a_tramo("3,4,2") is None
    assert partida.texto_a_tramo("3,4,2-3,4") is None
    assert partida.texto_a_tramo("a,4,2-3,4,7") is None
    assert partida.texto_a_tramo("") is None


def test_texto_de_pendientes():
    jugador = partida.nueva_partida_1v1()["jugadores"][0]
    assert partida.texto_de_pendientes(jugador["flota"]) == \
        "F x3   D x2   S x2   C x1   P x1   E x1"
    flota.ubicar_nave(jugador["cubo"], jugador["flota"], "C", (2, 1, 1), (2, 1, 4))
    assert partida.texto_de_pendientes(jugador["flota"]) == \
        "F x3   D x2   S x2   P x1   E x1"


def test_lineas_del_cubo():
    cubo = tablero.crear_cubo(3)
    lineas = partida.lineas_del_cubo(cubo, [1, 3], True)
    assert lineas[0] == "========= CAPA z = 1 ========="
    assert "========= CAPA z = 3 =========" in lineas
    assert lineas[-1] == partida.REFERENCIAS


def test_pedir_dato_insiste_hasta_que_el_dato_es_valido(monkeypatch, capsys):
    responder(monkeypatch, ["", "9", "hola", " 3 "])
    assert partida.pedir_dato("Opcion: ", partida.PATRON_OPCION_PRINCIPAL) == "3"
    assert capsys.readouterr().out.count("Dato invalido") == 3


def test_ubicacion_manual_como_en_la_consigna(monkeypatch, capsys):
    jugador = partida.nueva_partida_1v1()["jugadores"][0]
    responder(monkeypatch, [
        "F", "3,5,4-3,5,5",     # se ubica
        "d", "3,5,6-3,5,8",     # pegada a la fragata: no se puede
        "Q", "1,1,1-1,1,2",     # nave que no existe
        "F", "cualquier cosa",  # tramo mal escrito
        "0",
    ])
    assert partida.ubicacion_manual(jugador) is False
    salida = capsys.readouterr().out
    assert salida.count("Ubicada.") == 1
    assert salida.count("No se puede ubicar ahi. Intente de nuevo.") == 2
    assert "Tramo invalido" in salida
    assert len(jugador["flota"]) == 1


def test_ubicacion_automatica_reemplaza_lo_ubicado_a_mano():
    jugador = partida.nueva_partida_1v1()["jugadores"][0]
    flota.ubicar_nave(jugador["cubo"], jugador["flota"], "F", (1, 1, 1), (1, 1, 2))
    partida.ubicacion_automatica(jugador)
    assert flota.flota_completa(jugador["flota"])
    assert tablero.contar_celdas_en_estado(jugador["cubo"], tablero.NAVE_OCULTA) == 35


def test_continuar_exige_la_flota_completa(capsys):
    jugador = partida.nueva_partida_1v1()["jugadores"][0]
    assert partida.continuar(jugador) is False
    assert "Todavia faltan naves" in capsys.readouterr().out
    partida.ubicacion_automatica(jugador)
    assert partida.continuar(jugador) is True


def test_programa_completo_de_punta_a_punta(monkeypatch, capsys):
    responder(monkeypatch, [
        "7", "2",               # opcion invalida y opcion aun no disponible
        "1",                    # partida uno contra uno
        "4",                    # Jugador 1 quiere continuar sin flota
        "2", "3", "99", "4",    # automatica, ver capa 99 (invalida) y capa 4
        "3", "0", "4",          # ver todas las capas y continuar
        "2", "4",               # Jugador 2: automatica y continuar
        "5",                    # salir
    ])
    partida.main()
    salida = capsys.readouterr().out
    assert salida.count("===== OPERACION CUBO =====") == 3
    assert "Esa opcion todavia no esta disponible." in salida
    assert "--- Flota de Jugador 2 ---" in salida
    assert "========= CAPA z = 8 =========" in salida
    assert "Las dos flotas estan ubicadas." in salida
    assert "Hasta la proxima." in salida


def test_main_no_se_corta_si_se_cierra_la_entrada(monkeypatch, capsys):
    def sin_entrada(mensaje=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", sin_entrada)
    partida.main()
    assert "Programa interrumpido." in capsys.readouterr().out
