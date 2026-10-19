

import registro


def historial_de_prueba():
    """Objetivo: arma un historial con algunas jugadas cargadas.
    Retorna:
      dict: historial de Ana contra Beto con 6 jugadas."""
    historial = registro.crear_historial("Ana", "Beto")
    registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1), impactos=1)
    registro.registrar_jugada(historial, "Beto", "T", (2, 2, 2), aguas=1)
    registro.registrar_jugada(historial, "Ana", "R", (3, 3, 3), impactos=2, aguas=5)
    registro.registrar_jugada(historial, "Ana", "T", (4, 4, 4), aguas=1)
    registro.registrar_jugada(historial, "Ana", "T", (5, 5, 5), impactos=1,
                              hundidas=["Fragata"])
    registro.registrar_jugada(historial, "Beto", "S", (3, 1, 1), detectados=2)
    return historial


#validaciones

def test_nombres():
    assert registro.es_nombre_valido("Ana")
    assert registro.es_nombre_valido("Jugador 1")
    assert not registro.es_nombre_valido("")
    assert not registro.es_nombre_valido(" Ana")
    assert not registro.es_nombre_valido("Ana!")
    assert not registro.es_nombre_valido("a" * 21)


def test_armas():
    assert registro.es_arma_valida("T")
    assert not registro.es_arma_valida("t")
    assert not registro.es_arma_valida("TT")
    assert not registro.es_arma_valida("")
    assert not registro.es_arma_valida(3)


def test_puntos():
    assert registro.es_punto_valido((3, 5, 4))
    assert registro.es_punto_valido([3, 5, 4])
    assert not registro.es_punto_valido((3, 5))
    assert not registro.es_punto_valido((0, 5, 4))
    assert not registro.es_punto_valido((3, -5, 4))
    assert not registro.es_punto_valido((3, "5", 4))
    assert not registro.es_punto_valido((3, True, 4))
    assert not registro.es_punto_valido("3,5,4")
    assert not registro.es_punto_valido(354)


def test_texto_a_punto():
    assert registro.texto_a_punto("3,5,4") == (3, 5, 4)
    assert registro.texto_a_punto(" 3 , 5 , 4 ") == (3, 5, 4)
    assert registro.texto_a_punto("3,5") is None
    assert registro.texto_a_punto("3,0,4") is None
    assert registro.texto_a_punto("a,b,c") is None


# historial 

def test_crear_historial():
    historial = registro.crear_historial("Ana", "Beto")
    assert historial["jugadores"] == ("Ana", "Beto")
    assert historial["jugadas"] == []
    assert historial["ganador"] is None


def test_crear_historial_invalido():
    assert registro.crear_historial("Ana", "Ana") is None
    assert registro.crear_historial("Ana", "") is None


def test_registrar_jugada():
    historial = registro.crear_historial("Ana", "Beto")
    assert registro.registrar_jugada(historial, "Ana", "T", (4, 2, 7), impactos=1)
    assert registro.registrar_jugada(historial, "Beto", "T", (6, 3, 1), aguas=1)
    assert len(historial["jugadas"]) == 2
    assert historial["jugadas"][0]["numero"] == 1
    assert historial["jugadas"][1]["numero"] == 2
    assert historial["jugadas"][0]["objetivo"] == (4, 2, 7)


def test_registrar_jugada_invalida_no_modifica():
    historial = registro.crear_historial("Ana", "Beto")
    assert not registro.registrar_jugada(historial, "Intruso", "T", (1, 1, 1))
    assert not registro.registrar_jugada(historial, "Ana", "x", (1, 1, 1))
    assert not registro.registrar_jugada(historial, "Ana", "T", (1, 1))
    assert not registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1), impactos=-1)
    assert not registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1), hundidas="Fragata")
    assert historial["jugadas"] == []


def test_obtener_jugadas():
    historial = historial_de_prueba()
    assert len(registro.obtener_jugadas(historial)) == 6
    assert len(registro.obtener_jugadas(historial, "Ana")) == 4
    assert len(registro.obtener_jugadas(historial, "Beto")) == 2


def test_obtener_jugadas_devuelve_copia():
    historial = historial_de_prueba()
    copia = registro.obtener_jugadas(historial)
    copia[0]["arma"] = "X"
    assert historial["jugadas"][0]["arma"] == "T"


def test_ultimas_jugadas():
    historial = historial_de_prueba()
    numeros = [jugada["numero"] for jugada in registro.ultimas_jugadas(historial, 2)]
    assert numeros == [5, 6]
    assert registro.ultimas_jugadas(historial, 0) == []


def test_finalizar_historial():
    historial = registro.crear_historial("Ana", "Beto")
    assert not registro.finalizar_historial(historial, "Intruso")
    assert registro.finalizar_historial(historial, "Ana")
    assert historial["ganador"] == "Ana"


#estadisticas
def test_estadisticas_jugador():
    datos = registro.calcular_estadisticas(historial_de_prueba(), "Ana")
    assert datos["disparos"] == 4
    assert datos["impactos"] == 4
    assert datos["aguas"] == 6
    assert datos["disparos_certeros"] == 3
    assert datos["punteria"] == 75.0
    assert datos["naves_hundidas"] == ["Fragata"]
    assert datos["uso_armas"] == {"T": 3, "R": 1}
    assert datos["arma_favorita"] == "T"
    assert datos["racha_maxima"] == 2
    assert datos["objetivos_distintos"] == 4


def test_estadisticas_sin_disparos():
    historial = registro.crear_historial("Ana", "Beto")
    datos = registro.calcular_estadisticas(historial, "Beto")
    assert datos["disparos"] == 0
    assert datos["punteria"] == 0.0
    assert datos["arma_favorita"] is None
    assert registro.calcular_estadisticas(historial, "Intruso") is None


def test_estadisticas_generales():
    datos = registro.estadisticas_generales(historial_de_prueba())
    assert set(datos.keys()) == {"Ana", "Beto"}
    assert datos["Beto"]["detectados"] == 2


#resumen 
def test_generar_resumen():
    historial = historial_de_prueba()
    registro.finalizar_historial(historial, "Ana")
    texto = "\n".join(registro.generar_resumen(historial))
    assert "Ganador: Ana" in texto
    assert "Jugadas totales: 6" in texto
    assert "Punteria: 75.0%" in texto
    assert "Fragata" in texto


def test_resumen_sin_ganador():
    historial = registro.crear_historial("Ana", "Beto")
    texto = "\n".join(registro.generar_resumen(historial))
    assert "ninguno" in texto


#Entrega 2:estadisticas nuevas 

def test_efectividad_y_ranking_de_armas():
    datos = registro.calcular_estadisticas(historial_de_prueba(), "Ana")
    assert datos["efectividad_armas"]["T"] == {"usos": 3, "impactos": 2, "promedio": 0.67}
    assert datos["efectividad_armas"]["R"] == {"usos": 1, "impactos": 2, "promedio": 2.0}
    assert datos["ranking_armas"] == [("R", 2.0), ("T", 0.67)]


def test_ranking_sin_jugadas():
    assert registro.ranking_armas([]) == []


def test_capa_mas_atacada():
    historial = registro.crear_historial("Ana", "Beto")
    registro.registrar_jugada(historial, "Ana", "T", (2, 1, 1))
    registro.registrar_jugada(historial, "Ana", "T", (4, 1, 1))
    registro.registrar_jugada(historial, "Ana", "T", (4, 2, 2))
    assert registro.calcular_estadisticas(historial, "Ana")["capa_mas_atacada"] == 4
    assert registro.calcular_estadisticas(historial, "Beto")["capa_mas_atacada"] is None


def test_disparos_repetidos():
    historial = registro.crear_historial("Ana", "Beto")
    registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1))
    registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1))
    registro.registrar_jugada(historial, "Ana", "T", (2, 2, 2))
    registro.registrar_jugada(historial, "Ana", "T", (1, 1, 1))
    datos = registro.calcular_estadisticas(historial, "Ana")
    assert datos["disparos_repetidos"] == 2
    assert datos["objetivos_distintos"] == 2


def test_cantidad_hundidas():
    datos = registro.estadisticas_generales(historial_de_prueba())
    assert datos["Ana"]["cantidad_hundidas"] == 1
    assert datos["Beto"]["cantidad_hundidas"] == 0


def test_comparar_jugadores():
    comparacion = registro.comparar_jugadores(historial_de_prueba())
    assert comparacion["lider_punteria"] == "Ana"
    assert comparacion["lider_impactos"] == "Ana"
    assert comparacion["lider_hundidas"] == "Ana"
    assert comparacion["armas_en_comun"] == ["T"]
    assert comparacion["armas_exclusivas"] == {"Ana": ["R"], "Beto": ["S"]}


def test_comparar_jugadores_empate():
    historial = registro.crear_historial("Ana", "Beto")
    comparacion = registro.comparar_jugadores(historial)
    assert comparacion["lider_punteria"] is None
    assert comparacion["lider_impactos"] is None
    assert comparacion["armas_en_comun"] == []


def test_jugada_destacada():
    historial = historial_de_prueba()
    
    assert registro.jugada_destacada(historial)["numero"] == 5
    assert registro.jugada_destacada(historial, "Beto") is None
    assert registro.jugada_destacada(registro.crear_historial("Ana", "Beto")) is None


def test_describir_jugada():
    jugada = registro.jugada_destacada(historial_de_prueba())
    texto = registro.describir_jugada(jugada)
    assert texto == "#5 de Ana con T en (5, 5, 5): 1 impacto(s), hundio Fragata"


#Entrega 2:

def test_resumen_completo():
    historial = historial_de_prueba()
    registro.finalizar_historial(historial, "Ana")
    texto = "\n".join(registro.generar_resumen(historial))
    assert "COMPARACION" in texto
    assert "Mejor punteria: Ana" in texto
    assert "Armas usadas por los dos: T" in texto
    assert "Armas que uso solo Beto: S" in texto
    assert "1. R  2.00" in texto
    assert "Jugada destacada: #5 de Ana" in texto
    assert "Naves hundidas (1): Fragata" in texto


def test_resumen_partida_vacia():
    historial = registro.crear_historial("Ana", "Beto")
    texto = "\n".join(registro.generar_resumen(historial))
    assert "Mejor punteria: empate" in texto
    assert "Jugada destacada: ninguna" in texto
    assert "Naves hundidas (0): -" in texto
