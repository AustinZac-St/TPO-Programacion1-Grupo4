

import json
import os

import pytest

import flota
import partida
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


# Entrega 3: guardado y carga en JSON

def estado_de_prueba():
    """Arma una partida a medio jugar: flotas ubicadas, algunos disparos
    y municion gastada."""
    estado = partida.nueva_partida_1v1({"nombres": ("Ana", "Beto")})
    for semilla, jugador in enumerate(estado["jugadores"]):
        jugador["flota"] = flota.ubicacion_automatica(jugador["cubo"], flota.CATALOGO, semilla)
    rival = estado["jugadores"][1]
    objetivo = min(rival["flota"][0]["celdas"])
    flota.recibir_impacto(rival["cubo"], rival["flota"], objetivo)
    registro.registrar_jugada(estado["historial"], "Ana", "T", objetivo, impactos=1)
    registro.registrar_jugada(estado["historial"], "Beto", "R", (1, 1, 1), aguas=7)
    estado["jugadores"][1]["municion"]["R"] -= 1
    estado["turno"] = 0
    return estado


def test_guardar_y_cargar_devuelve_el_mismo_estado(tmp_path):
    estado = estado_de_prueba()
    registro.guardar_partida(estado, "mi_partida", tmp_path)
    assert registro.cargar_partida("mi_partida", tmp_path) == estado


def test_guardar_escribe_un_json_en_la_carpeta(tmp_path):
    ruta = registro.guardar_partida(estado_de_prueba(), "p1", tmp_path)
    assert ruta == os.path.join(tmp_path, "p1.json")
    with open(ruta, encoding="utf-8") as archivo:
        assert json.load(archivo)["n"] == 8
    assert os.listdir(tmp_path) == ["p1.json"]


def test_guardar_no_modifica_el_estado(tmp_path):
    estado = estado_de_prueba()
    flota_antes = [dict(nave) for nave in estado["jugadores"][0]["flota"]]
    registro.guardar_partida(estado, "p1", tmp_path)
    assert estado["jugadores"][0]["flota"] == flota_antes
    assert type(estado["historial"]["jugadores"]) == tuple


def test_guardar_crea_la_carpeta(tmp_path):
    carpeta = os.path.join(tmp_path, "datos", "partidas")
    registro.guardar_partida(estado_de_prueba(), "p1", carpeta)
    assert registro.listar_partidas(carpeta) == ["p1"]


def test_guardar_dos_veces_reemplaza(tmp_path):
    estado = estado_de_prueba()
    registro.guardar_partida(estado, "p1", tmp_path)
    estado["turno"] = 1
    registro.guardar_partida(estado, "p1", tmp_path)
    assert registro.cargar_partida("p1", tmp_path)["turno"] == 1


def test_partida_cargada_sigue_funcionando(tmp_path):
    registro.guardar_partida(estado_de_prueba(), "p1", tmp_path)
    estado = registro.cargar_partida("p1", tmp_path)
    datos = registro.calcular_estadisticas(estado["historial"], "Ana")
    assert datos["impactos"] == 1
    rival = estado["jugadores"][1]
    resultado = flota.recibir_impacto(rival["cubo"], rival["flota"],
                                      min(rival["flota"][0]["celdas"]))
    assert resultado["resultado"] == "repetido"


@pytest.mark.parametrize("nombre", ["", "../afuera", "con espacio", "a" * 31, "año", None])
def test_nombre_de_partida_invalido(tmp_path, nombre):
    with pytest.raises(registro.NombrePartidaInvalido):
        registro.guardar_partida(estado_de_prueba(), nombre, tmp_path)
    with pytest.raises(registro.NombrePartidaInvalido):
        registro.cargar_partida(nombre, tmp_path)


def test_las_excepciones_heredan_de_la_base():
    for clase in (registro.NombrePartidaInvalido, registro.PartidaNoEncontrada,
                  registro.PartidaCorrupta, registro.ErrorArchivo):
        assert issubclass(clase, registro.ErrorRegistro)


def test_cargar_partida_inexistente(tmp_path):
    with pytest.raises(registro.PartidaNoEncontrada):
        registro.cargar_partida("no_existe", tmp_path)


@pytest.mark.parametrize("contenido", [
    "esto no es json",
    "[1, 2, 3]",
    '{"n": 8}',
    '{"n": 8, "turno": 0, "jugadores": [], "historial": '
    '{"jugadores": ["A", "B"], "jugadas": [], "ganador": null}}',
])
def test_cargar_partida_corrupta(tmp_path, contenido):
    with open(os.path.join(tmp_path, "rota.json"), "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    with pytest.raises(registro.PartidaCorrupta):
        registro.cargar_partida("rota", tmp_path)


def test_cargar_partida_con_flota_rota(tmp_path):
    registro.guardar_partida(estado_de_prueba(), "p1", tmp_path)
    ruta = os.path.join(tmp_path, "p1.json")
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)
    datos["jugadores"][0]["flota"][0]["tipo"] = "Z"
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo)
    with pytest.raises(registro.PartidaCorrupta):
        registro.cargar_partida("p1", tmp_path)


def test_guardar_algo_que_no_es_json_no_deja_archivos(tmp_path):
    estado = estado_de_prueba()
    estado["extra"] = {1, 2}
    with pytest.raises(registro.ErrorArchivo):
        registro.guardar_partida(estado, "p1", tmp_path)
    assert os.listdir(tmp_path) == []


def test_listar_partidas(tmp_path):
    assert registro.listar_partidas(os.path.join(tmp_path, "no_existe")) == []
    for nombre in ("beto", "ana"):
        registro.guardar_partida(estado_de_prueba(), nombre, tmp_path)
    open(os.path.join(tmp_path, "notas.txt"), "w").close()
    assert registro.listar_partidas(tmp_path) == ["ana", "beto"]


def test_borrar_partida(tmp_path):
    registro.guardar_partida(estado_de_prueba(), "p1", tmp_path)
    assert registro.borrar_partida("p1", tmp_path)
    assert not registro.borrar_partida("p1", tmp_path)
    assert registro.listar_partidas(tmp_path) == []


# Entrega 3: exportacion y ranking

def test_exportar_resumen(tmp_path):
    historial = historial_de_prueba()
    ruta = registro.exportar_resumen(historial, "resumen", tmp_path)
    with open(ruta, encoding="utf-8") as archivo:
        assert archivo.read().splitlines() == registro.generar_resumen(historial)


def test_exportar_historial(tmp_path):
    historial = historial_de_prueba()
    ruta = registro.exportar_historial(historial, "historial", tmp_path)
    with open(ruta, encoding="utf-8") as archivo:
        assert registro.datos_a_historial(json.load(archivo)) == historial


def test_exportar_con_nombre_invalido(tmp_path):
    with pytest.raises(registro.NombrePartidaInvalido):
        registro.exportar_resumen(historial_de_prueba(), "../x", tmp_path)


def partida_terminada(jugador1, jugador2, ganador):
    """Arma un historial terminado con una jugada de cada uno."""
    historial = registro.crear_historial(jugador1, jugador2)
    registro.registrar_jugada(historial, jugador1, "T", (1, 1, 1), impactos=1)
    registro.registrar_jugada(historial, jugador2, "T", (2, 2, 2), aguas=1)
    registro.finalizar_historial(historial, ganador)
    return historial


def test_ranking_vacio(tmp_path):
    archivo = os.path.join(tmp_path, "ranking.json")
    assert registro.ranking(archivo) == []
    assert "Todavia no hay" in registro.texto_ranking([])[-1]


def test_registrar_resultado_y_ranking(tmp_path):
    archivo = os.path.join(tmp_path, "ranking.json")
    registro.registrar_resultado(partida_terminada("Ana", "Beto", "Ana"), archivo)
    registro.registrar_resultado(partida_terminada("Ana", "Ciro", "Ciro"), archivo)
    resultado = registro.registrar_resultado(partida_terminada("Beto", "Ana", "Ana"), archivo)
    assert resultado["punteria"] == {"Beto": 100.0, "Ana": 0.0}

    filas = registro.ranking(archivo)
    assert [fila["jugador"] for fila in filas] == ["Ana", "Ciro", "Beto"]
    assert filas[0] == {"jugador": "Ana", "partidas": 3, "victorias": 2,
                        "derrotas": 1, "porcentaje": 66.7}
    lineas = registro.texto_ranking(filas, cantidad=2)
    assert len(lineas) == 4
    assert lineas[2].startswith(" 1. Ana")


def test_registrar_resultado_sin_ganador(tmp_path):
    with pytest.raises(registro.ErrorRegistro):
        registro.registrar_resultado(historial_de_prueba(), os.path.join(tmp_path, "r.json"))


def test_ranking_corrupto(tmp_path):
    archivo = os.path.join(tmp_path, "ranking.json")
    with open(archivo, "w", encoding="utf-8") as f:
        f.write('{"no": "es una lista"}')
    with pytest.raises(registro.PartidaCorrupta):
        registro.ranking(archivo)
