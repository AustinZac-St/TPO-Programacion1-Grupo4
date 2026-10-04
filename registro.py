import re
from functools import reduce

# Constantes

CANTIDAD_JUGADORES = 2

# Expresiones regulares para validar los datos que se reciben
PATRON_NOMBRE = r"^\w[\w ]{0,19}$"          
PATRON_ARMA = r"^[A-Z]$"                    
PATRON_PUNTO = r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$"   


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


def calcular_estadisticas(historial, jugador):
    """Objetivo: calcula las estadisticas de un jugador.
    Parametros:
      historial (dict): el historial de la partida.
      jugador (str): nombre del jugador.
    Retorna:
      dict con: disparos, impactos, aguas, detectados, disparos_certeros,
      punteria (porcentaje de disparos certeros), naves_hundidas (list),
      uso_armas (dict), arma_favorita (str o None), racha_maxima y
      objetivos_distintos. Devuelve None si el jugador no es de la partida."""
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
        "racha_maxima": calcular_racha_maxima(jugadas),
        "objetivos_distintos": len(objetivos),
    }


def estadisticas_generales(historial):
    """Objetivo: calcula las estadisticas de los dos jugadores.
    Parametros:
      historial (dict): el historial de la partida.
    Retorna:
      dict: nombre del jugador -> sus estadisticas."""
    return {jugador: calcular_estadisticas(historial, jugador)
            for jugador in historial["jugadores"]}


# ---------------------------------------------------------------------------
# Resumen al terminar
# ---------------------------------------------------------------------------

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
        "===== RESUMEN DE LA PARTIDA =====",
        texto_ganador,
        f"Jugadas totales: {len(historial['jugadas'])}",
    ]

    estadisticas = estadisticas_generales(historial)
    for jugador, datos in estadisticas.items():
        if len(datos["naves_hundidas"]) > 0:
            hundidas = ", ".join(datos["naves_hundidas"])
        else:
            hundidas = "ninguna"
        if datos["arma_favorita"] is None:
            favorita = "-"
        else:
            favorita = datos["arma_favorita"]

        lineas.append("")
        lineas.append(f"--- {jugador} ---")
        lineas.append(f"Disparos: {datos['disparos']}")
        lineas.append(f"Impactos: {datos['impactos']}   Agua: {datos['aguas']}"
                      f"   Detectados: {datos['detectados']}")
        lineas.append(f"Punteria: {datos['punteria']}%")
        lineas.append(f"Racha maxima de aciertos: {datos['racha_maxima']}")
        lineas.append(f"Arma mas usada: {favorita}")
        lineas.append(f"Naves hundidas: {hundidas}")

    return lineas
