import registro


def test_validaciones():
    assert registro.es_nombre_valido("Jugador 1")
    assert not registro.es_nombre_valido("")
    assert not registro.es_nombre_valido(" Ana")
    assert registro.es_arma_valida("T")
    assert not registro.es_arma_valida("t")
    assert registro.es_punto_valido((3, 5, 4))
    assert not registro.es_punto_valido((0, 5, 4))
    assert registro.texto_a_punto(" 3, 5 ,4 ") == (3, 5, 4)
    assert registro.texto_a_punto("3,5") is None


def test_crear_historial():
    historial = registro.crear_historial("Ana", "Beto")
    assert historial == {"jugadores": ("Ana", "Beto"), "jugadas": [], "ganador": None}
    assert registro.crear_historial("Ana", "Ana") is None
    assert registro.crear_historial("Ana", "") is None


def test_registrar_jugada_numera_y_guarda():
    historial = registro.crear_historial("Ana", "Beto")
    assert registro.registrar_jugada(historial, "Ana", "T", (4, 2, 7), impactos=1)
    assert registro.registrar_jugada(historial, "Beto", "T", (6, 3, 1), aguas=1)
    jugadas = registro.obtener_jugadas(historial)
    assert [jugada["numero"] for jugada in jugadas] == [1, 2]
    assert registro.obtener_jugadas(historial, "Beto")[0]["objetivo"] == (6, 3, 1)


def test_registrar_jugada_invalida_no_modifica_el_historial():
    historial = registro.crear_historial("Ana", "Beto")
    assert not registro.registrar_jugada(historial, "Carla", "T", (1, 1, 1))
    assert not registro.registrar_jugada(historial, "Ana", "t", (1, 1, 1))
    assert not registro.registrar_jugada(historial, "Ana", "T", (1, 1))
    assert not registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1), impactos=-1)
    assert historial["jugadas"] == []


def test_ultimas_jugadas_y_copia():
    historial = registro.crear_historial("Ana", "Beto")
    for y in range(1, 8):
        registro.registrar_jugada(historial, "Ana", "T", (1, 1, y))
    ultimas = registro.ultimas_jugadas(historial, 3)
    assert [jugada["numero"] for jugada in ultimas] == [5, 6, 7]
    ultimas[0]["arma"] = "X"
    assert historial["jugadas"][4]["arma"] == "T"
    assert registro.ultimas_jugadas(historial, 0) == []


def test_finalizar_historial():
    historial = registro.crear_historial("Ana", "Beto")
    assert not registro.finalizar_historial(historial, "Carla")
    assert registro.finalizar_historial(historial, "Beto")
    assert historial["ganador"] == "Beto"
