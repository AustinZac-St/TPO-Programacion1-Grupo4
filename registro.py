
import json
import os
import re
from functools import reduce

import flota


# Constantes
CANTIDAD_JUGADORES = 2

# Rutas relativas a la carpeta desde donde se ejecuta el juego
CARPETA_PARTIDAS = os.path.join("datos", "partidas")
CARPETA_EXPORTACIONES = os.path.join("datos", "exportaciones")
ARCHIVO_RANKING = os.path.join("datos", "ranking.json")
EXTENSION_PARTIDA = ".json"

#Expresiones regulares para validar los datos que se reciben
PATRON_NOMBRE = r"^\w[\w ]{0,19}$"          
PATRON_ARMA = r"^[A-Z]$"                    
PATRON_PUNTO = r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$"
PATRON_PARTIDA = r"^[A-Za-z0-9_-]{1,30}$"   # nombre de archivo de una partida



# Excepciones propias (clase base + subclases)

class ErrorRegistro(Exception):
    """Clase base de los errores de este modulo."""


class NombrePartidaInvalido(ErrorRegistro):
    """El nombre elegido para la partida no cumple PATRON_PARTIDA."""


class PartidaNoEncontrada(ErrorRegistro):
    """No existe una partida guardada con ese nombre."""


class PartidaCorrupta(ErrorRegistro):
    """El archivo de la partida existe pero no se puede reconstruir."""


class ErrorArchivo(ErrorRegistro):
    """No se pudo leer o escribir un archivo de datos."""



# Validaciones

def es_nombre_valido(nombre):
    """Objetivo: indica si un nombre de jugador o de nave es valido.
    Parametros:
      nombre: el dato a validar.
    Retorna:
      bool: True si tiene de 1 a 20 caracteres (letras, digitos, _ o
      espacios) y no empieza con espacio; False en caso contrario."""
    return re.match(PATRON_NOMBRE, str(nombre)) is not None


def es_arma_valida(arma):
    """Objetivo: indica si el arma esta escrita como una letra mayuscula.
    Parametros:
      arma: el dato a validar (por ejemplo "T").
    Retorna:
      bool: True si es una unica letra mayuscula; False en caso contrario.
    Nota: que letras existen lo define armamento.py."""
    return re.match(PATRON_ARMA, str(arma)) is not None


def es_contador_valido(valor):
    """Objetivo: indica si un valor es un entero mayor o igual a cero.
    Parametros:
      valor: el dato a validar.
    Retorna:
      bool: True si es un entero >= 0; False en caso contrario."""
    return type(valor) == int and valor >= 0


def es_punto_valido(punto):
    """Objetivo: indica si un punto (z, x, y) tiene el formato correcto.
    Parametros:
      punto (tuple): tupla de tres enteros mayores a 0.
    Retorna:
      bool: True si es una tupla o lista con tres coordenadas enteras
      mayores a 0; False en caso contrario.
    Nota: el rango contra N lo valida tablero.py."""
    if type(punto) != tuple and type(punto) != list:
        return False
    if len(punto) != 3:
        return False
    validas = list(filter(lambda c: type(c) == int and c > 0, punto))
    return len(validas) == 3


def texto_a_punto(texto):
    """Objetivo: convierte un punto tipeado como "z,x,y" en una tupla.
    Parametros:
      texto (str): por ejemplo "3,5,4".
    Retorna:
      tuple: (z, x, y) con enteros, o None si el texto no es valido."""
    coincidencia = re.match(PATRON_PUNTO, str(texto))
    if coincidencia is None:
        return None
    punto = tuple(map(int, coincidencia.groups()))
    if not es_punto_valido(punto):
        return None
    return punto


# Historial en memoria

def crear_historial(jugador1, jugador2):
    """Objetivo: crea un historial vacio para una partida nueva.
    Parametros:
      jugador1 (str): nombre del primer jugador.
      jugador2 (str): nombre del segundo jugador.
    Retorna:
      dict: historial con las claves "jugadores", "jugadas" y "ganador",
      o None si algun nombre es invalido o los dos son iguales."""
    if not es_nombre_valido(jugador1) or not es_nombre_valido(jugador2):
        return None
    if jugador1 == jugador2:
        return None
    return {
        "jugadores": (jugador1, jugador2),
        "jugadas": [],
        "ganador": None,
    }


def registrar_jugada(historial, jugador, arma, objetivo,
                     impactos=0, aguas=0, detectados=0, hundidas=None):
    """Objetivo: agrega una jugada al historial.
    Parametros:
      historial (dict): creado con crear_historial.
      jugador (str): quien disparo; debe pertenecer a la partida.
      arma (str): letra del arma usada (T, R, C, S, L, O, G).
      objetivo (tuple): punto apuntado (z, x, y).
      impactos (int): celdas con nave alcanzadas.
      aguas (int): celdas de agua alcanzadas.
      detectados (int): contactos revelados por el sonar.
      hundidas (list): nombres de las naves hundidas en esta jugada.
    Retorna:
      bool: True si la jugada se registro; False si algun dato es
      invalido (en ese caso el historial no se modifica)."""
    if hundidas is None:
        hundidas = []

    if jugador not in historial["jugadores"]:
        return False
    if not es_arma_valida(arma) or not es_punto_valido(objetivo):
        return False
    contadores = [impactos, aguas, detectados]
    if len(list(filter(es_contador_valido, contadores))) != len(contadores):
        return False
    if type(hundidas) != list and type(hundidas) != tuple:
        return False
    if len(list(filter(es_nombre_valido, hundidas))) != len(hundidas):
        return False

    jugada = {
        "numero": len(historial["jugadas"]) + 1,
        "jugador": jugador,
        "arma": arma,
        "objetivo": tuple(objetivo),
        "impactos": impactos,
        "aguas": aguas,
        "detectados": detectados,
        "hundidas": list(hundidas),
    }
    historial["jugadas"].append(jugada)
    return True


def obtener_jugadas(historial, jugador=None):
    """Objetivo: devuelve las jugadas registradas, todas o las de un jugador.
    Parametros:
      historial (dict): el historial de la partida.
      jugador (str o None): si es None devuelve todas las jugadas.
    Retorna:
      list: copia de las jugadas (modificarla no altera el historial)."""
    if jugador is None:
        return [jugada.copy() for jugada in historial["jugadas"]]
    return [jugada.copy() for jugada in historial["jugadas"]
            if jugada["jugador"] == jugador]


def ultimas_jugadas(historial, cantidad=5):
    """Objetivo: devuelve las ultimas jugadas, de la mas vieja a la mas nueva.
    Parametros:
      historial (dict): el historial de la partida.
      cantidad (int): cuantas jugadas devolver (mayor a 0).
    Retorna:
      list: como maximo 'cantidad' jugadas; lista vacia si cantidad no es
      un entero mayor a 0."""
    if type(cantidad) != int or cantidad <= 0:
        return []
    return obtener_jugadas(historial)[-cantidad:]


def finalizar_historial(historial, ganador):
    """Objetivo: registra al ganador de la partida.
    Parametros:
      historial (dict): el historial de la partida.
      ganador (str o None): nombre del ganador, o None si no hubo.
    Retorna:
      bool: True si se registro; False si el ganador no es de la partida."""
    if ganador is not None and ganador not in historial["jugadores"]:
        return False
    historial["ganador"] = ganador
    return True



# Estadisticas

def sumar_campo(jugadas, campo):
    """Objetivo: suma un campo numerico de todas las jugadas.
    Parametros:
      jugadas (list): lista de jugadas.
      campo (str): nombre del campo, por ejemplo "impactos".
    Retorna:
      int: la suma (0 si no hay jugadas)."""
    return reduce(lambda acumulado, jugada: acumulado + jugada[campo], jugadas, 0)


def calcular_racha_maxima(jugadas):
    """Objetivo: calcula la mayor cantidad de disparos certeros seguidos.
    Parametros:
      jugadas (list): jugadas de un jugador, en orden.
    Retorna:
      int: la racha mas larga de jugadas con al menos un impacto."""
    racha_actual = 0
    racha_maxima = 0
    for jugada in jugadas:
        if jugada["impactos"] > 0:
            racha_actual = racha_actual + 1
        else:
            racha_actual = 0
        if racha_actual > racha_maxima:
            racha_maxima = racha_actual
    return racha_maxima


def contar_armas(jugadas):
    """Objetivo: cuenta cuantas veces se uso cada arma.
    Parametros:
      jugadas (list): lista de jugadas.
    Retorna:
      dict: letra del arma -> cantidad de usos."""
    uso = {}
    for jugada in jugadas:
        uso[jugada["arma"]] = uso.get(jugada["arma"], 0) + 1
    return uso


def efectividad_por_arma(jugadas):
    """Objetivo: calcula cuanto rindio cada arma.
    Parametros:
      jugadas (list): lista de jugadas.
    Retorna:
      dict: letra del arma -> diccionario con "usos", "impactos" y
      "promedio" (impactos por uso, con 2 decimales)."""
    efectividad = {}
    for jugada in jugadas:
        datos = efectividad.setdefault(jugada["arma"], {"usos": 0, "impactos": 0, "promedio": 0.0})
        datos["usos"] = datos["usos"] + 1
        datos["impactos"] = datos["impactos"] + jugada["impactos"]
        datos["promedio"] = round(datos["impactos"] / datos["usos"], 2)
    return efectividad


def ranking_armas(jugadas):
    """Objetivo: ordena las armas de la mas efectiva a la menos efectiva.
    Parametros:
      jugadas (list): lista de jugadas.
    Retorna:
      list: lista de tuplas (arma, promedio) ordenada por promedio de
      mayor a menor. Lista vacia si no hay jugadas."""
    efectividad = efectividad_por_arma(jugadas)
    pares = [(arma, datos["promedio"]) for arma, datos in efectividad.items()]
    return sorted(pares, key=lambda par: par[1], reverse=True)


def capa_mas_atacada(jugadas):
    """Objetivo: indica la capa z a la que mas se disparo.
    Parametros:
      jugadas (list): lista de jugadas.
    Retorna:
      int: el valor de z mas usado (si hay empate, el primero que se uso),
      o None si no hay jugadas."""
    capas = {}
    for jugada in jugadas:
        z = jugada["objetivo"][0]
        capas[z] = capas.get(z, 0) + 1
    if len(capas) == 0:
        return None
    return max(capas, key=capas.get)


def contar_disparos_repetidos(jugadas):
    """Objetivo: cuenta los disparos hechos a un punto ya apuntado antes.
    Parametros:
      jugadas (list): jugadas de un jugador, en orden.
    Retorna:
      int: cantidad de disparos repetidos (desperdiciados)."""
    vistos = set()
    repetidos = 0
    for jugada in jugadas:
        if jugada["objetivo"] in vistos:
            repetidos = repetidos + 1
        else:
            vistos.add(jugada["objetivo"])
    return repetidos


def calcular_estadisticas(historial, jugador):
    """Objetivo: calcula las estadisticas de un jugador.
    Parametros:
      historial (dict): el historial de la partida.
      jugador (str): nombre del jugador.
    Retorna:
      dict con: disparos, impactos, aguas, detectados, disparos_certeros,
      punteria (porcentaje de disparos certeros), naves_hundidas (list),
      cantidad_hundidas (int), uso_armas (dict), arma_favorita (str o None),
      racha_maxima, objetivos_distintos, disparos_repetidos,
      capa_mas_atacada (int o None), efectividad_armas (dict) y
      ranking_armas (list de tuplas). Devuelve None si el jugador no es
      de la partida."""
    if jugador not in historial["jugadores"]:
        return None

    jugadas = obtener_jugadas(historial, jugador)
    disparos = len(jugadas)
    certeros = len(list(filter(lambda jugada: jugada["impactos"] > 0, jugadas)))

    if disparos > 0:
        punteria = round(certeros * 100 / disparos, 1)
    else:
        punteria = 0.0

    uso_armas = contar_armas(jugadas)
    if len(uso_armas) > 0:
        arma_favorita = max(uso_armas, key=uso_armas.get)
    else:
        arma_favorita = None

    naves_hundidas = []
    for jugada in jugadas:
        naves_hundidas.extend(jugada["hundidas"])

    objetivos = {jugada["objetivo"] for jugada in jugadas}   

    return {
        "disparos": disparos,
        "impactos": sumar_campo(jugadas, "impactos"),
        "aguas": sumar_campo(jugadas, "aguas"),
        "detectados": sumar_campo(jugadas, "detectados"),
        "disparos_certeros": certeros,
        "punteria": punteria,
        "naves_hundidas": naves_hundidas,
        "uso_armas": uso_armas,
        "arma_favorita": arma_favorita,
        "cantidad_hundidas": len(naves_hundidas),
        "racha_maxima": calcular_racha_maxima(jugadas),
        "objetivos_distintos": len(objetivos),
        "disparos_repetidos": contar_disparos_repetidos(jugadas),
        "capa_mas_atacada": capa_mas_atacada(jugadas),
        "efectividad_armas": efectividad_por_arma(jugadas),
        "ranking_armas": ranking_armas(jugadas),
    }


def estadisticas_generales(historial):
    """Objetivo: calcula las estadisticas de los dos jugadores.
    Parametros:
      historial (dict): el historial de la partida.
    Retorna:
      dict: nombre del jugador -> sus estadisticas."""
    return {jugador: calcular_estadisticas(historial, jugador)
            for jugador in historial["jugadores"]}


def lider_en(estadisticas, campo):
    """Objetivo: indica que jugador tiene el valor mas alto en un campo.
    Parametros:
      estadisticas (dict): resultado de estadisticas_generales.
      campo (str): por ejemplo "punteria" o "impactos".
    Retorna:
      str: nombre del jugador que va adelante, o None si hay empate."""
    mejor = max(estadisticas, key=lambda nombre: estadisticas[nombre][campo])
    empatados = [nombre for nombre in estadisticas
                 if estadisticas[nombre][campo] == estadisticas[mejor][campo]]
    if len(empatados) > 1:
        return None
    return mejor


def comparar_jugadores(historial):
    """Objetivo: compara a los dos jugadores de la partida.
    Parametros:
      historial (dict): el historial de la partida.
    Retorna:
      dict con:
        lider_punteria, lider_impactos, lider_hundidas (str o None si
        hay empate),
        armas_en_comun (list): armas que usaron los dos,
        armas_exclusivas (dict): jugador -> armas que solo uso el."""
    estadisticas = estadisticas_generales(historial)
    jugador1, jugador2 = historial["jugadores"]
    armas1 = set(estadisticas[jugador1]["uso_armas"].keys())
    armas2 = set(estadisticas[jugador2]["uso_armas"].keys())

    return {
        "lider_punteria": lider_en(estadisticas, "punteria"),
        "lider_impactos": lider_en(estadisticas, "impactos"),
        "lider_hundidas": lider_en(estadisticas, "cantidad_hundidas"),
        "armas_en_comun": sorted(armas1 & armas2),
        "armas_exclusivas": {
            jugador1: sorted(armas1 - armas2),
            jugador2: sorted(armas2 - armas1),
        },
    }


def jugada_destacada(historial, jugador=None):
    """Objetivo: busca la mejor jugada de la partida o de un jugador.
    La mejor es la que mas naves hundio; si empatan, la de mas impactos.
    Parametros:
      historial (dict): el historial de la partida.
      jugador (str o None): si es None busca entre todas las jugadas.
    Retorna:
      dict: la jugada destacada, o None si ninguna jugada tuvo impactos."""
    jugadas = obtener_jugadas(historial, jugador)
    con_impactos = list(filter(lambda jugada: jugada["impactos"] > 0, jugadas))
    if len(con_impactos) == 0:
        return None
    return max(con_impactos, key=lambda jugada: (len(jugada["hundidas"]), jugada["impactos"]))



# Resumen al terminar


def nombre_o_empate(nombre):
    """Objetivo: devuelve el nombre, o "empate" si no hay lider.
    Parametros:
      nombre (str o None): resultado de lider_en.
    Retorna:
      str: el nombre o la palabra "empate"."""
    if nombre is None:
        return "empate"
    return nombre


def lista_o_guion(elementos):
    """Objetivo: une una lista de textos con comas, o devuelve "-" si esta vacia.
    Parametros:
      elementos (list): lista de cadenas.
    Retorna:
      str: los elementos separados por coma, o "-"."""
    if len(elementos) == 0:
        return "-"
    return ", ".join(elementos)


def describir_jugada(jugada):
    """Objetivo: arma una frase que describe una jugada.
    Parametros:
      jugada (dict): una jugada del historial.
    Retorna:
      str: por ejemplo "#5 de Ana con T en (5, 5, 5): 1 impacto(s)"."""
    texto = (f"#{jugada['numero']} de {jugada['jugador']} con {jugada['arma']} "
             f"en {jugada['objetivo']}: {jugada['impactos']} impacto(s)")
    if len(jugada["hundidas"]) > 0:
        texto = texto + ", hundio " + ", ".join(jugada["hundidas"])
    return texto


def resumen_jugador(jugador, datos):
    """Objetivo: arma las lineas del resumen de un jugador.
    Parametros:
      jugador (str): nombre del jugador.
      datos (dict): sus estadisticas (ver calcular_estadisticas).
    Retorna:
      list: lista de cadenas."""
    if datos["arma_favorita"] is None:
        favorita = "-"
    else:
        favorita = datos["arma_favorita"]
    if datos["capa_mas_atacada"] is None:
        capa = "-"
    else:
        capa = f"z = {datos['capa_mas_atacada']}"

    lineas = [
        "",
        f"--- {jugador} ---",
        f"Disparos: {datos['disparos']}   Certeros: {datos['disparos_certeros']}"
        f"   Punteria: {datos['punteria']:.1f}%",
        f"Impactos: {datos['impactos']}   Agua: {datos['aguas']}"
        f"   Detectados: {datos['detectados']}",
        f"Racha maxima de aciertos: {datos['racha_maxima']}",
        f"Arma mas usada: {favorita}",
        f"Capa mas atacada: {capa}",
        f"Disparos repetidos: {datos['disparos_repetidos']}",
        f"Naves hundidas ({datos['cantidad_hundidas']}): {lista_o_guion(datos['naves_hundidas'])}",
    ]

    if len(datos["ranking_armas"]) > 0:
        lineas.append("Ranking de armas (impactos por uso):")
        for posicion, (arma, promedio) in enumerate(datos["ranking_armas"]):
            lineas.append(f"  {posicion + 1}. {arma}  {promedio:.2f}")
    return lineas


def generar_resumen(historial):
    """Objetivo: arma el resumen de la partida como lineas de texto.
    No imprime nada: el integrador decide como mostrarlo.
    Parametros:
      historial (dict): el historial de la partida.
    Retorna:
      list: lista de cadenas, una por renglon del resumen."""
    if historial["ganador"] is None:
        texto_ganador = "Ganador: ninguno (partida sin terminar)"
    else:
        texto_ganador = f"Ganador: {historial['ganador']}"

    lineas = [
        "=" * 36,
        "       RESUMEN DE LA PARTIDA",
        "=" * 36,
        texto_ganador,
        f"Jugadas totales: {len(historial['jugadas'])}",
    ]

    estadisticas = estadisticas_generales(historial)
    for jugador, datos in estadisticas.items():
        lineas.extend(resumen_jugador(jugador, datos))

    comparacion = comparar_jugadores(historial)
    jugador1, jugador2 = historial["jugadores"]
    lineas.append("")
    lineas.append("-" * 12 + " COMPARACION " + "-" * 11)
    lineas.append(f"Mejor punteria: {nombre_o_empate(comparacion['lider_punteria'])}")
    lineas.append(f"Mas impactos: {nombre_o_empate(comparacion['lider_impactos'])}")
    lineas.append(f"Mas naves hundidas: {nombre_o_empate(comparacion['lider_hundidas'])}")
    lineas.append(f"Armas usadas por los dos: {lista_o_guion(comparacion['armas_en_comun'])}")
    for jugador in (jugador1, jugador2):
        exclusivas = comparacion["armas_exclusivas"][jugador]
        lineas.append(f"Armas que uso solo {jugador}: {lista_o_guion(exclusivas)}")

    destacada = jugada_destacada(historial)
    lineas.append("")
    if destacada is None:
        lineas.append("Jugada destacada: ninguna")
    else:
        lineas.append(f"Jugada destacada: {describir_jugada(destacada)}")

    return lineas



# Entrega 3: guardado y carga en JSON

def es_nombre_partida_valido(nombre):
    """Objetivo: indica si un nombre sirve para guardar una partida.
    Parametros:
      nombre: el dato a validar.
    Retorna:
      bool: True si es un texto de 1 a 30 letras sin acento, digitos, _ o -;
      False en caso contrario (asi no puede escaparse de la carpeta)."""
    return type(nombre) == str and re.match(PATRON_PARTIDA, nombre) is not None


def ruta_partida(nombre, carpeta=CARPETA_PARTIDAS):
    """Objetivo: arma la ruta relativa del archivo de una partida.
    Parametros:
      nombre (str): nombre de la partida, sin extension.
      carpeta (str): carpeta de las partidas.
    Retorna:
      str: por ejemplo "datos/partidas/mi_partida.json".
    Lanza:
      NombrePartidaInvalido si el nombre no cumple PATRON_PARTIDA."""
    if not es_nombre_partida_valido(nombre):
        raise NombrePartidaInvalido(
            f"'{nombre}' no es un nombre valido (de 1 a 30 letras, digitos, _ o -).")
    return os.path.join(carpeta, nombre + EXTENSION_PARTIDA)


def historial_a_datos(historial):
    """Objetivo: pasa el historial a un diccionario que se puede guardar en JSON.
    Parametros:
      historial (dict): creado con crear_historial.
    Retorna:
      dict: copia del historial con las tuplas convertidas en listas."""
    jugadas = []
    for jugada in historial["jugadas"]:
        copia = jugada.copy()
        copia["objetivo"] = list(jugada["objetivo"])
        jugadas.append(copia)
    return {
        "jugadores": list(historial["jugadores"]),
        "jugadas": jugadas,
        "ganador": historial["ganador"],
    }


def datos_a_historial(datos):
    """Objetivo: reconstruye el historial a partir de lo que devuelve
    historial_a_datos.
    Parametros:
      datos (dict): el historial leido del archivo.
    Retorna:
      dict: el historial con jugadores y objetivos como tuplas.
    Lanza:
      PartidaCorrupta si falta algun dato."""
    try:
        jugadas = []
        for jugada in datos["jugadas"]:
            copia = dict(jugada)
            copia["objetivo"] = tuple(jugada["objetivo"])
            jugadas.append(copia)
        historial = {
            "jugadores": tuple(datos["jugadores"]),
            "jugadas": jugadas,
            "ganador": datos["ganador"],
        }
    except (KeyError, TypeError) as error:
        raise PartidaCorrupta(f"El historial guardado esta incompleto: {error}") from error
    if len(historial["jugadores"]) != CANTIDAD_JUGADORES:
        raise PartidaCorrupta("El historial guardado no tiene dos jugadores.")
    return historial


def estado_a_datos(estado):
    """Objetivo: pasa el estado de una partida a datos que se pueden guardar en JSON.
    El estado original no se modifica.
    Parametros:
      estado (dict): el estado de la partida (ver partida.py).
    Retorna:
      dict: copia del estado con flotas e historial convertidos."""
    datos = dict(estado)
    jugadores = []
    for jugador in estado["jugadores"]:
        copia = dict(jugador)
        copia["flota"] = flota.flota_a_datos(jugador["flota"])
        jugadores.append(copia)
    datos["jugadores"] = jugadores
    datos["historial"] = historial_a_datos(estado["historial"])
    return datos


def datos_a_estado(datos):
    """Objetivo: reconstruye el estado de una partida a partir de lo que
    devuelve estado_a_datos.
    Parametros:
      datos (dict): el estado leido del archivo.
    Retorna:
      dict: el estado listo para seguir jugando.
    Lanza:
      PartidaCorrupta si falta algun dato o alguna flota no es valida."""
    try:
        estado = dict(datos)
        jugadores = []
        for jugador in datos["jugadores"]:
            copia = dict(jugador)
            copia["flota"] = flota.datos_a_flota(jugador["flota"])
            jugadores.append(copia)
        estado["jugadores"] = jugadores
        estado["historial"] = datos_a_historial(datos["historial"])
        if type(datos["n"]) != int or datos["turno"] not in range(CANTIDAD_JUGADORES):
            raise ValueError("'n' o 'turno' no son validos")
    except (KeyError, TypeError, ValueError) as error:
        raise PartidaCorrupta(f"La partida guardada esta incompleta: {error}") from error
    except flota.ErrorFlota as error:
        raise PartidaCorrupta(f"La flota guardada no es valida: {error}") from error
    if len(jugadores) != CANTIDAD_JUGADORES:
        raise PartidaCorrupta("La partida guardada no tiene dos jugadores.")
    return estado


def escribir_json(ruta, datos):
    """Objetivo: escribe datos en un archivo JSON, creando la carpeta si hace falta.
    Primero escribe un archivo temporal y despues lo renombra, asi un error
    a mitad de camino no deja el archivo anterior roto.
    Parametros:
      ruta (str): ruta relativa del archivo.
      datos: lo que se va a guardar (debe poder pasarse a JSON).
    Retorna:
      str: la ruta escrita.
    Lanza:
      ErrorArchivo si no se pudo escribir."""
    temporal = ruta + ".tmp"
    try:
        carpeta = os.path.dirname(ruta)
        if carpeta != "":
            os.makedirs(carpeta, exist_ok=True)
        with open(temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
    except (OSError, TypeError, ValueError) as error:
        raise ErrorArchivo(f"No se pudo escribir {ruta}: {error}") from error
    else:
        return ruta
    finally:
        if os.path.exists(temporal):
            os.remove(temporal)


def leer_json(ruta):
    """Objetivo: lee un archivo JSON.
    Parametros:
      ruta (str): ruta relativa del archivo.
    Retorna:
      los datos leidos.
    Lanza:
      FileNotFoundError si el archivo no existe,
      PartidaCorrupta si el contenido no es JSON valido,
      ErrorArchivo si no se pudo leer por otro motivo."""
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PartidaCorrupta(f"{ruta} no tiene un JSON valido.") from error
    except OSError as error:
        raise ErrorArchivo(f"No se pudo leer {ruta}: {error}") from error


def guardar_partida(estado, nombre, carpeta=CARPETA_PARTIDAS):
    """Objetivo: guarda una partida a medio jugar en un archivo JSON
    (FUNCION PUBLICA). Si ya existe una partida con ese nombre, la reemplaza.
    Parametros:
      estado (dict): el estado de la partida.
      nombre (str): nombre de la partida (ver PATRON_PARTIDA).
      carpeta (str): carpeta de las partidas.
    Retorna:
      str: la ruta del archivo escrito.
    Lanza:
      NombrePartidaInvalido si el nombre no es valido,
      ErrorArchivo si no se pudo escribir."""
    ruta = ruta_partida(nombre, carpeta)
    return escribir_json(ruta, estado_a_datos(estado))


def cargar_partida(nombre, carpeta=CARPETA_PARTIDAS):
    """Objetivo: carga una partida guardada para seguir jugandola
    (FUNCION PUBLICA).
    Parametros:
      nombre (str): nombre de la partida (como lo devuelve listar_partidas).
      carpeta (str): carpeta de las partidas.
    Retorna:
      dict: el estado de la partida en el punto en que se guardo.
    Lanza:
      NombrePartidaInvalido si el nombre no es valido,
      PartidaNoEncontrada si no existe,
      PartidaCorrupta si el archivo no se puede reconstruir,
      ErrorArchivo si no se pudo leer."""
    ruta = ruta_partida(nombre, carpeta)
    try:
        datos = leer_json(ruta)
    except FileNotFoundError as error:
        raise PartidaNoEncontrada(f"No hay ninguna partida llamada '{nombre}'.") from error
    if type(datos) != dict:
        raise PartidaCorrupta(f"{ruta} no contiene una partida.")
    return datos_a_estado(datos)


def listar_partidas(carpeta=CARPETA_PARTIDAS):
    """Objetivo: lista las partidas guardadas (FUNCION PUBLICA).
    Parametros:
      carpeta (str): carpeta de las partidas.
    Retorna:
      list: nombres de las partidas (sin extension), en orden alfabetico.
      Lista vacia si todavia no se guardo ninguna."""
    if not os.path.isdir(carpeta):
        return []
    nombres = []
    for archivo in os.listdir(carpeta):
        nombre, extension = os.path.splitext(archivo)
        if extension == EXTENSION_PARTIDA and es_nombre_partida_valido(nombre):
            nombres.append(nombre)
    return sorted(nombres)


def borrar_partida(nombre, carpeta=CARPETA_PARTIDAS):
    """Objetivo: borra una partida guardada (por ejemplo, cuando termina).
    Parametros:
      nombre (str): nombre de la partida.
      carpeta (str): carpeta de las partidas.
    Retorna:
      bool: True si se borro; False si no existia.
    Lanza:
      NombrePartidaInvalido si el nombre no es valido,
      ErrorArchivo si no se pudo borrar."""
    ruta = ruta_partida(nombre, carpeta)
    try:
        os.remove(ruta)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise ErrorArchivo(f"No se pudo borrar {ruta}: {error}") from error
    return True



# Entrega 3: exportacion y ranking

def exportar_resumen(historial, nombre, carpeta=CARPETA_EXPORTACIONES):
    """Objetivo: exporta el resumen de una partida a un archivo de texto.
    Parametros:
      historial (dict): el historial de la partida.
      nombre (str): nombre del archivo, sin extension (ver PATRON_PARTIDA).
      carpeta (str): carpeta de las exportaciones.
    Retorna:
      str: la ruta del archivo escrito.
    Lanza:
      NombrePartidaInvalido si el nombre no es valido,
      ErrorArchivo si no se pudo escribir."""
    if not es_nombre_partida_valido(nombre):
        raise NombrePartidaInvalido(f"'{nombre}' no es un nombre valido.")
    ruta = os.path.join(carpeta, nombre + ".txt")
    try:
        os.makedirs(carpeta, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("\n".join(generar_resumen(historial)) + "\n")
    except OSError as error:
        raise ErrorArchivo(f"No se pudo escribir {ruta}: {error}") from error
    return ruta


def exportar_historial(historial, nombre, carpeta=CARPETA_EXPORTACIONES):
    """Objetivo: exporta el historial completo (todas las jugadas) a JSON.
    Parametros:
      historial (dict): el historial de la partida.
      nombre (str): nombre del archivo, sin extension (ver PATRON_PARTIDA).
      carpeta (str): carpeta de las exportaciones.
    Retorna:
      str: la ruta del archivo escrito.
    Lanza:
      NombrePartidaInvalido si el nombre no es valido,
      ErrorArchivo si no se pudo escribir."""
    if not es_nombre_partida_valido(nombre):
        raise NombrePartidaInvalido(f"'{nombre}' no es un nombre valido.")
    ruta = os.path.join(carpeta, nombre + ".json")
    return escribir_json(ruta, historial_a_datos(historial))


def cargar_resultados(archivo=ARCHIVO_RANKING):
    """Objetivo: lee los resultados de las partidas terminadas.
    Parametros:
      archivo (str): ruta del archivo del ranking.
    Retorna:
      list: lista de resultados {"jugadores": [...], "ganador": ...};
      lista vacia si el archivo todavia no existe.
    Lanza:
      PartidaCorrupta si el archivo no tiene el formato esperado,
      ErrorArchivo si no se pudo leer."""
    try:
        resultados = leer_json(archivo)
    except FileNotFoundError:
        return []
    if type(resultados) != list:
        raise PartidaCorrupta(f"{archivo} no tiene una lista de resultados.")
    return resultados


def registrar_resultado(historial, archivo=ARCHIVO_RANKING):
    """Objetivo: agrega el resultado de una partida terminada al archivo
    del ranking.
    Parametros:
      historial (dict): historial con el ganador ya registrado
      (ver finalizar_historial).
      archivo (str): ruta del archivo del ranking.
    Retorna:
      dict: el resultado agregado.
    Lanza:
      ErrorRegistro si la partida no tiene ganador,
      PartidaCorrupta o ErrorArchivo si falla el archivo."""
    if historial["ganador"] is None:
        raise ErrorRegistro("La partida todavia no tiene ganador.")
    jugador1, jugador2 = historial["jugadores"]
    resultado = {
        "jugadores": [jugador1, jugador2],
        "ganador": historial["ganador"],
        "jugadas": len(historial["jugadas"]),
        "punteria": {
            jugador1: calcular_estadisticas(historial, jugador1)["punteria"],
            jugador2: calcular_estadisticas(historial, jugador2)["punteria"],
        },
    }
    resultados = cargar_resultados(archivo)
    resultados.append(resultado)
    escribir_json(archivo, resultados)
    return resultado


def calcular_ranking(resultados):
    """Objetivo: arma el ranking de jugadores a partir de los resultados.
    Parametros:
      resultados (list): lo que devuelve cargar_resultados.
    Retorna:
      list: un diccionario por jugador con "jugador", "partidas",
      "victorias", "derrotas" y "porcentaje" (de victorias), ordenado por
      victorias, despues por porcentaje y despues por nombre."""
    tabla = {}
    for resultado in resultados:
        for jugador in resultado["jugadores"]:
            fila = tabla.setdefault(jugador, {"jugador": jugador, "partidas": 0,
                                              "victorias": 0, "derrotas": 0})
            fila["partidas"] += 1
            if resultado["ganador"] == jugador:
                fila["victorias"] += 1
            else:
                fila["derrotas"] += 1
    for fila in tabla.values():
        fila["porcentaje"] = round(fila["victorias"] * 100 / fila["partidas"], 1)
    return sorted(tabla.values(),
                  key=lambda fila: (-fila["victorias"], -fila["porcentaje"], fila["jugador"]))


def ranking(archivo=ARCHIVO_RANKING):
    """Objetivo: devuelve el ranking guardado.
    Parametros:
      archivo (str): ruta del archivo del ranking.
    Retorna:
      list: ver calcular_ranking.
    Lanza:
      PartidaCorrupta o ErrorArchivo si falla el archivo."""
    return calcular_ranking(cargar_resultados(archivo))


def texto_ranking(filas, cantidad=10):
    """Objetivo: arma las lineas de texto del ranking para mostrar.
    No imprime nada: el integrador decide como mostrarlo.
    Parametros:
      filas (list): lo que devuelve ranking o calcular_ranking.
      cantidad (int): cuantos puestos mostrar.
    Retorna:
      list: lista de cadenas, una por renglon."""
    lineas = ["===== RANKING =====",
              f"{'#':>2}  {'Jugador':<20} {'PJ':>3} {'PG':>3} {'PP':>3} {'%':>6}"]
    if len(filas) == 0:
        lineas.append("Todavia no hay partidas terminadas.")
        return lineas
    for posicion, fila in enumerate(filas[:cantidad]):
        lineas.append(f"{posicion + 1:>2}. {fila['jugador']:<20} {fila['partidas']:>3} "
                      f"{fila['victorias']:>3} {fila['derrotas']:>3} {fila['porcentaje']:>5.1f}%")
    return lineas
