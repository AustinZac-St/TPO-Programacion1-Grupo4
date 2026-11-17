"""
partida.py - Integrador (Entrega 1).

Responsabilidad en esta entrega: menú principal, submenú de ubicación
de la flota y dibujo del estado del cubo.

Es el único módulo que usa print e input: los módulos de dominio
(tablero, flota, radar, armamento, registro) reciben datos y devuelven
datos, y acá se resuelve toda la entrada y salida.

El estado de una partida es un diccionario:
    {
        "n": 8,
        "jugadores": [
            {"nombre": "Jugador 1", "cubo": [...], "flota": [...], "municion": {...}},
            {"nombre": "Jugador 2", "cubo": [...], "flota": [...], "municion": {...}},
        ],
        "turno": 0,                # índice del jugador al que le toca
        "historial": {...},        # creado con registro.crear_historial
    }

Las opciones de los menús se despachan con diccionarios que asocian
la opción tipeada con una función, sin cadenas de if / elif.
"""

import random
import re

import armamento
import flota
import radar
import registro
import tablero


class ErrorPartida(Exception):
    """
    Excepcion que se lanza cuando hay un error en la partida
    """


class ArmaNoDisponible(ErrorPartida):
    """
    Excepcion que se lanza cuando se intenta usar un arma que no está disponible.
    """

class ObjetivoInvalido(ErrorPartida):
    """
    Excepcion que se lanza cuando se intenta disparar a un objetivo
    que no es válido (fuera del cubo o ya disparado)
    """

# Expresiones regulares para validar todo lo que se tipea
PATRON_OPCION_PRINCIPAL = r"^\s*([1-5])\s*$"
PATRON_OPCION_UBICACION = r"^\s*([1-4])\s*$"
PATRON_NAVE = r"^\s*([A-Za-z0])\s*$"
PATRON_NUMERO = r"^\s*(\d+)\s*$"
PATRON_TRAMO = (r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*-"
                r"\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")

PATRON_ARMA = r"^\s*([TRCSLOGtrcslog])\s*$"
PATRON_OBJETIVO = r"^\s*(\d+\s*,\s*\d+\s*,\s*\d+)\s*$"
PATRON_EJE = r"^\s*([xyXY])\s*$"
PATRON_EJE_SONAR = r"^\s*([zxyZXY])\s*$"
PATRON_OPCION_TURNO = r"^\s*([1-3])\s*$"

NOMBRES_POR_DEFECTO = ("Jugador 1", "Jugador 2")
EJES = ("z", "x", "y")

REFERENCIAS = ("Referencias:  ~ sin explorar   N nave   o agua   X impacto"
               "   # hundido   ? detectado")


# --------------------------------------------------------------------------
# Funciones sin entrada ni salida (se pueden probar con pytest)
# --------------------------------------------------------------------------

def nueva_partida_1v1(configuracion=None):
    """
    Crea el estado inicial de una partida de dos jugadores: un cubo vacío
    y una flota vacía para cada uno (FUNCION PUBLICA).
    Recibe: configuracion (dict o None) con las claves opcionales
    "n" (tamaño del cubo) y "nombres" (tupla con los dos nombres).
    Devuelve: el estado inicial de la partida (dict).
    Lanza: ValueError si los nombres no son válidos o son iguales.
    """
    if configuracion is None:
        configuracion = {}
    n = configuracion.get("n", tablero.N_POR_DEFECTO)
    nombres = configuracion.get("nombres", NOMBRES_POR_DEFECTO)

    historial = registro.crear_historial(nombres[0], nombres[1])
    if historial is None:
        raise ValueError("Los nombres de los jugadores no son validos.")

    jugadores = []
    for nombre in nombres:
        jugadores.append({
            "nombre": nombre,
            "cubo": tablero.crear_cubo(n),
            "flota": [],
            "municion":armamento.crear_municion(),
        })
    return {
        "n": n,
        "jugadores": jugadores,
        "turno": 0,
        "historial": historial,
    }


def texto_a_tramo(texto):
    """
    Convierte un tramo tipeado como "z,x,y-z,x,y" en sus dos puntos.
    Recibe: texto (str), por ejemplo "3,4,2-3,4,7".
    Devuelve: una tupla (desde, hasta) con dos puntos (z, x, y), o None
    si el texto no tiene el formato de un tramo.
    """
    coincidencia = re.match(PATRON_TRAMO, texto)
    if coincidencia is None:
        return None
    valores = []
    for grupo in coincidencia.groups():
        valores.append(int(grupo))
    return tuple(valores[:3]), tuple(valores[3:])


def texto_de_pendientes(flota_jugador):
    """
    Arma el renglón con las naves que todavía falta ubicar.
    Recibe: la flota del jugador (lista de naves).
    Devuelve: un texto como "F x3   D x2   S x2   C x1   P x1   E x1".
    """
    partes = []
    for letra, cantidad in flota.pendientes(flota_jugador).items():
        partes.append(letra + " x" + str(cantidad))
    return "   ".join(partes)


def lineas_del_cubo(cubo, capas, mostrar_naves):
    """
    Arma el dibujo de varias capas de z, con las referencias al final.
    Recibe: el cubo, capas (lista de valores de z) y mostrar_naves (bool).
    Devuelve: lista de líneas (str) listas para imprimir.
    """
    lineas = []
    for z in capas:
        lineas.extend(tablero.dibujar_capa_z(cubo, z, mostrar_naves))
        lineas.append("")
    lineas.append(REFERENCIAS)
    return lineas


def ejecutar_turno(estado, jugada):
   """
    Ejecuta un turno de la partida: aplica el disparo del jugador al rival,
    Recibe: el estado de la partida y la jugada (dict con "arma", "objetivo" y "eje")
    Devueleve: el estado modificado de la partida.
    Lanza: ArmaNoDisponible si el arma no existe o todavía no tiene
    función, ObjetivoInvalido si el punto está fuera del cubo 
   """
   jugador = estado["jugadores"][estado["turno"]]
   rival = estado["jugadores"][1-estado["turno"]]
   letra = jugada["arma"]
   objetivo = jugada["objetivo"]
   eje = jugada.get("eje")
   if letra == "S":
        return ejecutar_sonar(estado, jugada)
   if letra not in armamento.CATALOGO_ARMAS:
        raise ArmaNoDisponible("El arma " + str(letra) + " no existe.")
   funcion = armamento.CATALOGO_ARMAS[letra]["funcion"]
   if funcion is None:
        raise ArmaNoDisponible("Esa arma todavia no esta disponible.")

   if not tablero.punto_dentro_del_cubo(rival["cubo"], *objetivo):
        raise ObjetivoInvalido("El objetivo esta fuera del cubo.")
   
   try:
        celdas = funcion(rival["cubo"], objetivo, eje)
   except ValueError:
        raise ObjetivoInvalido("El eje elegido no es valido para esa arma.")
   
   armamento.consumir_municion(jugador["municion"], letra)
   resultados = flota.disparar_celdas(rival["cubo"], rival["flota"], celdas, letra)
   resumen = flota.resumen_disparo(resultados)
   estado["ultimo_resumen"] = resumen
   registro.registrar_jugada(estado["historial"], jugador["nombre"], letra, objetivo, resumen["impactos"], resumen["aguas"], 0, resumen["hundidas"])
   estado["turno"] = 1 - estado["turno"]
   return estado

def ejecutar_sonar(estado, jugada):
    """
    Ejecuta un turno de sonar: revela un plano del cubo del rival sin
    producir daño. El plano se elige con el eje y con la coordenada del
    objetivo sobre ese eje: objetivo (7, 1, 1) y eje "z" es el plano z = 7.
    Recibe: el estado de la partida y la jugada (dict con "objetivo" y "eje").
    Devuelve: el estado modificado de la partida.
    Lanza: ObjetivoInvalido si el punto está fuera del cubo o el eje no es
    z, x ni y; armamento.SinMunicion si no queda sonar.
    """
    jugador = estado["jugadores"][estado["turno"]]
    rival = estado["jugadores"][1 - estado["turno"]]
    objetivo = jugada["objetivo"]
    eje = str(jugada.get("eje")).lower()

    if not tablero.punto_dentro_del_cubo(rival["cubo"], *objetivo):
        raise ObjetivoInvalido("El objetivo esta fuera del cubo.")
    if eje not in EJES:
        raise ObjetivoInvalido("El sonar necesita un eje: z, x o y.")
    valor = objetivo[EJES.index(eje)]

    armamento.consumir_municion(jugador["municion"], "S")
    contactos, metricas = radar.sonar(rival["cubo"], eje, valor)

    mensaje = ("Sonar en el plano " + eje + " = " + str(valor) + ": "
               + str(len(contactos)) + " contacto(s) en "
               + str(metricas["comparaciones"]) + " celdas revisadas.")
    estado["ultimo_resumen"] = {
        "impactos": 0,
        "aguas": 0,
        "hundidas": [],
        "efectos": [],
        "mensajes": [mensaje],
        "detectados": len(contactos),
    }
    registro.registrar_jugada(estado["historial"], jugador["nombre"], "S",
                              objetivo, 0, 0, len(contactos), [])
    estado["turno"] = 1 - estado["turno"]
    return estado

def hay_ganador(estado):
    """
    Indica si algún jugador ya hundió toda la flota del rival.
    Recibe: el estado de la partida (dict).
    Devuelve: el  jugador que gano, o None si no hay ganador.
    """
    for indice in range(2):
        rival = estado["jugadores"][1-indice]
        if flota.flota_hundida(rival["flota"]):
            return estado["jugadores"][indice]["nombre"]
    return None


def nueva_partida_vs_maquina(configuracion=None, dificultad=1):
    """
    Crea el estado inicial de una partida contra la máquina (FUNCION PUBLICA).
    El jugador 2 es la máquina y se marca con "es_maquina".
    Recibe: configuracion (dict o None, igual que en nueva_partida_1v1) y
    dificultad (int, por ahora hay un solo nivel: la máquina juega al azar).
    Devuelve: el estado inicial de la partida (dict).
    Lanza: ValueError si los nombres no son válidos o son iguales.
    """
    if configuracion is None:
        configuracion = {}
    nombres = configuracion.get("nombres", ("Jugador 1", "Maquina"))
    estado = nueva_partida_1v1({"n": configuracion.get("n", tablero.N_POR_DEFECTO),
                                "nombres": nombres})
    estado["jugadores"][1]["es_maquina"] = True
    estado["dificultad"] = dificultad
    return estado


def elegir_jugada_maquina(estado):
    """
    Elige de forma random la jugada de la máquina: un arma que tenga función y
    munición, y una celda del cubo del rival que todavía no se haya disparado.
    Recibe: estado (dict de la partida).
    Devuelve: la jugada (dict con "arma", "objetivo" y "eje").
    """
    jugador = estado["jugadores"][estado["turno"]]
    rival = estado["jugadores"][1 - estado["turno"]]

    armas = []
    for letra, datos in armamento.CATALOGO_ARMAS.items():
        if datos["funcion"] is not None and armamento.tiene_municion(jugador["municion"], letra):
            armas.append(letra)
    letra = random.choice(armas)

    celdas = []
    for z in range(1, estado["n"] + 1):
        for x in range(1, estado["n"] + 1):
            for y in range(1, estado["n"] + 1):
                contenido = tablero.leer_celda(rival["cubo"], z, x, y)
                if contenido == tablero.SIN_EXPLORAR or contenido == tablero.NAVE_OCULTA:
                    celdas.append((z, x, y))
    objetivo = random.choice(celdas)

    eje = None
    if letra == "L":
        eje = random.choice(["x", "y"])
    return {"arma": letra, "objetivo": objetivo, "eje": eje}


def turno_maquina(estado):
    """
    Juega el turno de la máquina: elige una jugada al azar y la ejecuta.
    Recibe: estado (dict de la partida).
    Devuelve: la jugada que hizo la máquina (dict).
    Lanza: ArmaNoDisponible si el arma no existe o todavía no tiene
    función, ObjetivoInvalido si el punto está fuera del cubo.
    """
    jugada = elegir_jugada_maquina(estado)
    ejecutar_turno(estado, jugada)
    return jugada


# --------------------------------------------------------------------------
# Entrada y salidaS
# --------------------------------------------------------------------------

def pedir_dato(mensaje, patron):
    """
    Pide un dato y lo vuelve a pedir hasta que cumpla la expresión regular.
    Recibe: mensaje (str) y patron (str, con un grupo de captura).
    Devuelve: el texto capturado por el primer grupo del patrón (str).
    """
    coincidencia = re.match(patron, input(mensaje))
    while coincidencia is None:
        print("Dato invalido. Intente de nuevo.")
        coincidencia = re.match(patron, input(mensaje))
    return coincidencia.group(1)


def pedir_jugada():
    """
    Pide el arma, el objetivo y, si el arma es el barrido láser, el eje.
    Devuelve: la jugada (dict con "arma", "objetivo" y "eje").
    """
    letra = pedir_dato("Arma:(T/R/C/S/L/O/G): ", PATRON_ARMA).upper()
    texto = pedir_dato("Objetivo:(z,x,y): ", PATRON_OBJETIVO)
    punto = tuple(tablero.texto_a_punto(texto))
    eje = None
    if letra == "L":
        eje = pedir_dato("Eje:(x/y): ", PATRON_EJE).lower()
    elif letra == "S":
        eje = pedir_dato("Eje del plano:(z/x/y): ", PATRON_EJE_SONAR).lower()
    return {"arma": letra, "objetivo": punto, "eje": eje}


def mostrar_municion(jugador):
    """
    Muestra la munición que le queda al jugador en cada arma.
    Recibe: jugador (dict).
    Devuelve: nada.
    """
    partes = []
    for letra, cantidad in jugador["municion"].items():
        if cantidad is None:
            texto = "ilimitada"
        else:
            texto = str(cantidad)
        partes.append(letra + ": " + texto)
    print("Municion -> " + "   ".join(partes))


def mostrar_resultado(resumen):
    """
    Muestra el resultado de un disparo con los textos que arma flota.py.
    Recibe: resumen (dict que devuelve flota.resumen_disparo).
    Devuelve: nada.
    """
    for mensaje in resumen["mensajes"]:
        print(mensaje)
    for nombre in resumen["hundidas"]:
        print("Hundiste: " + nombre)
    if len(resumen["efectos"]) > 0:
        print("Efectos para la Entrega 3: " + ", ".join(resumen["efectos"]))


def disparar(estado):
    """
    Pide una jugada y la ejecuta. Si hay un error, lo informa y no se
    juega el turno.
    Recibe: estado (dict de la partida).
    Devuelve: True si el disparo se realizó, False si hubo un error.
    """
    jugada = pedir_jugada()
    jugado = False
    try:
        ejecutar_turno(estado, jugada)
    except ErrorPartida as error:
        print("No se pudo disparar: " + str(error))
    except armamento.SinMunicion as error:
        print("No se pudo disparar: " + str(error))
    except flota.DisparoInvalido as error:
        print("No se pudo disparar: " + str(error))
    else:
        mostrar_resultado(estado["ultimo_resumen"])
        jugado = True
    finally:
        print("--------------------")
    return jugado


def ver_mi_cubo(estado):
    """
    Dibuja el cubo del jugador al que le toca, con sus naves.
    Recibe: estado (dict de la partida).
    Devuelve: False, porque ver el cubo no gasta el turno.
    """
    jugador = estado["jugadores"][estado["turno"]]
    return ver_cubo(jugador)


def ver_cubo_rival(estado):
    """
    Dibuja el cubo del rival sin mostrar sus naves.
    Recibe: estado (dict de la partida).
    Devuelve: False, porque ver el cubo no gasta el turno.
    """
    rival = estado["jugadores"][1 - estado["turno"]]
    return ver_cubo(rival, False)


OPCIONES_TURNO = {
    "1": disparar,
    "2": ver_mi_cubo,
    "3": ver_cubo_rival,
}


def turno_de_jugador(estado):
    """
    Juega el turno del jugador al que le toca: muestra el menú del turno
    hasta que logre disparar.
    Recibe: estado (dict de la partida).
    Devuelve: nada. El estado queda con el turno cambiado.
    """
    jugador = estado["jugadores"][estado["turno"]]
    print()
    print("=== Turno de " + jugador["nombre"] + " ===")
    mostrar_municion(jugador)
    jugado = False
    while not jugado:
        print("1 - Disparar")
        print("2 - Ver mi cubo")
        print("3 - Ver el cubo del rival")
        opcion = pedir_dato("Opcion: ", PATRON_OPCION_TURNO)
        jugado = OPCIONES_TURNO[opcion](estado)


def turno_de_maquina(estado):
    """
    Juega el turno de la máquina y muestra qué hizo.
    Recibe: estado (dict de la partida).
    Devuelve: nada. El estado queda con el turno cambiado.
    """
    jugador = estado["jugadores"][estado["turno"]]
    print()
    print("=== Turno de " + jugador["nombre"] + " ===")
    jugada = turno_maquina(estado)
    nombre_arma = armamento.CATALOGO_ARMAS[jugada["arma"]]["nombre"]
    print(jugador["nombre"] + " dispara " + nombre_arma + " a " + str(jugada["objetivo"]))
    mostrar_resultado(estado["ultimo_resumen"])


def jugar_partida(estado):
    """
    Repite los turnos uno por jugador hasta que alguien hunda toda la
    flota del rival.Anota al ganador en el historial.
    Recibe: estado (dict de la partida, con las flotas ya ubicadas).
    Devuelve: el nombre del ganador (str).
    """
    ganador = hay_ganador(estado)
    while ganador is None:
        jugador = estado["jugadores"][estado["turno"]]
        if jugador.get("es_maquina", False):
            turno_de_maquina(estado)
        else:
            turno_de_jugador(estado)
        ganador = hay_ganador(estado)
    registro.finalizar_historial(estado["historial"], ganador)
    print()
    print("Gano " + ganador + ". Hundio toda la flota del rival.")
    return ganador


def ubicacion_manual(jugador):
    """
    Pide naves y tramos hasta completar la flota o hasta que se tipee 0.
    Modifica el cubo y la flota del jugador.
    Recibe: jugador (dict).
    Devuelve: False, para que el submenú de ubicación se vuelva a mostrar.
    """
    letras = "/".join(flota.CATALOGO)
    while not flota.flota_completa(jugador["flota"]):
        print()
        print("Pendientes: " + texto_de_pendientes(jugador["flota"]))
        print()
        letra = pedir_dato("Nave (" + letras + ", 0 = volver): ", PATRON_NAVE)
        if letra == "0":
            return False
        tramo = texto_a_tramo(input("Desde-hasta: "))
        if tramo is None:
            print("Tramo invalido. Se escribe asi: 3,4,2-3,4,7")
        else:
            try:
                flota.ubicar_nave(jugador["cubo"], jugador["flota"],
                                  letra, tramo[0], tramo[1])
            except flota.ErrorFlota as error:
                print("No se puede ubicar ahi. Intente de nuevo.")
                print("(" + str(error) + ")")
            else:
                print("Ubicada.")
    print()
    print("Flota completa.")
    return False


def ubicacion_automatica(jugador):
    """
    Ubica la flota completa al azar. Si ya había naves ubicadas, las
    descarta y empieza con un cubo vacío.
    Recibe: jugador (dict).
    Devuelve: False, para que el submenú de ubicación se vuelva a mostrar.
    """
    cubo = tablero.crear_cubo(len(jugador["cubo"]))
    try:
        flota_nueva = flota.ubicacion_automatica(cubo, flota.CATALOGO, None)
    except flota.ErrorFlota as error:
        print("No se pudo ubicar la flota: " + str(error))
    else:
        jugador["cubo"] = cubo
        jugador["flota"] = flota_nueva
        print("Flota ubicada de forma automatica.")
    return False


def ver_cubo(jugador, mostrar_naves=True):
    """
    Dibuja el cubo del jugador, una capa de z o todas, con sus naves.
    Recibe: jugador (dict)  y mostrar_naves (bool, True si se ven las naves).
    Devuelve: False, para que el submenú de ubicación se vuelva a mostrar.
    """
    n = len(jugador["cubo"])
    mensaje = "Capa de z (1 a " + str(n) + ", 0 = todas): "
    z = int(pedir_dato(mensaje, PATRON_NUMERO))
    while z > n:
        print("Dato invalido. Intente de nuevo.")
        z = int(pedir_dato(mensaje, PATRON_NUMERO))
    if z == 0:
        capas = list(range(1, n + 1))
    else:
        capas = [z]
    print()
    for linea in lineas_del_cubo(jugador["cubo"], capas, mostrar_naves):
        print(linea)
    return False


def continuar(jugador):
    """
    Cierra el submenú de ubicación, solo si la flota está completa.
    Recibe: jugador (dict).
    Devuelve: True si la flota está completa, False si faltan naves.
    """
    if not flota.flota_completa(jugador["flota"]):
        print("Todavia faltan naves: " + texto_de_pendientes(jugador["flota"]))
        return False
    return True


OPCIONES_UBICACION = {
    "1": ubicacion_manual,
    "2": ubicacion_automatica,
    "3": ver_cubo,
    "4": continuar,
}


def submenu_ubicacion(jugador):
    """
    Muestra el submenú de ubicación hasta que el jugador tenga la flota
    completa y elija continuar.
    Recibe: jugador (dict).
    Devuelve: nada.
    """
    listo = False
    while not listo:
        print()
        print("--- Flota de " + jugador["nombre"] + " ---")
        print("1 - Ubicacion manual")
        print("2 - Ubicacion automatica")
        print("3 - Ver el cubo")
        print("4 - Continuar")
        opcion = pedir_dato("Opcion: ", PATRON_OPCION_UBICACION)
        listo = OPCIONES_UBICACION[opcion](jugador)


def partida_uno_contra_uno():
    """
    Crea una partida de dos jugadores y les hace ubicar las flotas.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    estado = nueva_partida_1v1()
    for jugador in estado["jugadores"]:
        submenu_ubicacion(jugador)
    print()
    print("Las dos flotas estan ubicadas.Empieza la partida.")
    jugar_partida(estado)
    return False


def partida_uno_contra_la_maquina():
    """
    Crea una partida contra la máquina: el jugador ubica su flota y la de
    la máquina se ubica sola.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    estado = nueva_partida_vs_maquina()
    submenu_ubicacion(estado["jugadores"][0])
    ubicacion_automatica(estado["jugadores"][1])
    print()
    print("Las dos flotas estan ubicadas. Empieza la partida.")
    jugar_partida(estado)
    return False


def opcion_no_disponible():
    """
    Avisa que la opción elegida corresponde a una entrega posterior.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    print("Esa opcion todavia no esta disponible.")
    return False


def salir():
    """
    Devuelve: True, para que el menú principal se cierre.
    """
    print("Hasta la proxima.")
    return True


OPCIONES_PRINCIPAL = {
    "1": partida_uno_contra_uno,
    "2": partida_uno_contra_la_maquina,
    "3": opcion_no_disponible,
    "4": opcion_no_disponible,
    "5": salir,
}


def menu_principal():
    """
    Muestra el menú principal después de cada acción, hasta elegir salir.
    Devuelve: nada.
    """
    terminar = False
    while not terminar:
        print()
        print("===== OPERACION CUBO =====")
        print("1 - Partida uno contra uno")
        print("2 - Partida uno contra la maquina")
        print("3 - Partida maquina contra maquina")
        print("4 - Continuar una partida guardada")
        print("5 - Salir")
        opcion = pedir_dato("Opcion: ", PATRON_OPCION_PRINCIPAL)
        terminar = OPCIONES_PRINCIPAL[opcion]()


def main():
    """
    Punto de entrada del programa. Captura el cierre de la entrada
    (Ctrl+C o Ctrl+D) para que el programa nunca termine con un error.
    """
    try:
        menu_principal()
    except (EOFError, KeyboardInterrupt):
        print()
        print("Programa interrumpido.")
    finally:
        print("Fin de Operacion Cubo.")




# ENTREGA 3


class NombreDePartidaInvalido(ErrorPartida):
    """
    Excepcion que se lanza cuando el nombre elegido para guardar una
    partida no cumple la expresión regular PATRON_NOMBRE_PARTIDA.
    """


PATRON_OPCION_TURNO_CON_GUARDADO = r"^\s*([1-4])\s*$"
PATRON_NIVEL = r"^\s*([12])\s*$"
PATRON_NOMBRE_PARTIDA = r"^\s*([A-Za-z0-9_-]{1,30})\s*$"

NOMBRES_MAQUINAS = ("Maquina 1", "Maquina 2")


VECINOS_ORTOGONALES = ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                       (0, -1, 0), (0, 0, 1), (0, 0, -1))


ESTADOS_SIN_DISPARAR = (tablero.SIN_EXPLORAR, tablero.NAVE_OCULTA,
                        tablero.DETECTADO_SONAR)


ERRORES_DE_ARCHIVO = (ErrorPartida, registro.ErrorRegistro, OSError, ValueError)



# Entrega 3: máquina contra máquina

def validar_dificultad(dificultad):
    """
    Verifica que la dificultad de una máquina exista.
    Recibe: dificultad (int).
    Devuelve: nada.
    Lanza: ValueError si no es 1 ni 2.
    """
    if dificultad not in (1, 2):
        raise ValueError("La dificultad debe ser 1 (azar) o 2 (cazadora).")


def nueva_partida_maquina_vs_maquina(configuracion=None, dificultades=(1, 2)):
    """
    Crea el estado inicial de una partida entre dos máquinas (FUNCION
    PUBLICA). Como nadie ubica a mano, las dos flotas se ubican solas.
    Recibe: configuracion (dict o None) con las claves opcionales "n",
    "nombres" y "semillas" (tupla de dos semillas para la ubicación
    automática; misma semilla, misma flota) y dificultades (tupla con el
    nivel de cada máquina, 1 o 2).
    Devuelve: el estado inicial de la partida, con las flotas ubicadas (dict).
    Lanza: ValueError si los nombres o las dificultades no son válidos;
    flota.ErrorFlota si no se pudo ubicar alguna flota.
    """
    for dificultad in dificultades:
        validar_dificultad(dificultad)
    if configuracion is None:
        configuracion = {}
    nombres = configuracion.get("nombres", NOMBRES_MAQUINAS)
    semillas = configuracion.get("semillas", (None, None))
    estado = nueva_partida_1v1({"n": configuracion.get("n", tablero.N_POR_DEFECTO),
                                "nombres": nombres})
    for jugador, dificultad, semilla in zip(estado["jugadores"], dificultades, semillas):
        jugador["es_maquina"] = True
        jugador["dificultad"] = dificultad
        jugador["flota"] = flota.ubicacion_automatica(jugador["cubo"], flota.CATALOGO, semilla)
    return estado




def celdas_sin_disparar(cubo):
    """
    Lista las celdas del cubo en las que todavía no se disparó.
    Recibe: el cubo del rival.
    Devuelve: lista de puntos (z, x, y).
    """
    n = len(cubo)
    celdas = []
    for z in range(1, n + 1):
        for x in range(1, n + 1):
            for y in range(1, n + 1):
                if tablero.leer_celda(cubo, z, x, y) in ESTADOS_SIN_DISPARAR:
                    celdas.append((z, x, y))
    return celdas


def armas_con_municion(jugador):
    """
    Lista las armas que la máquina puede usar: con función y con munición.
    Recibe: jugador (dict).
    Devuelve: lista de letras.
    """
    armas = []
    for letra, datos in armamento.CATALOGO_ARMAS.items():
        if datos["funcion"] is not None and armamento.tiene_municion(jugador["municion"], letra):
            armas.append(letra)
    return armas


def armar_jugada(letra, objetivo):
    """
    Arma el diccionario de una jugada. Si el arma es el barrido láser,
    elige el eje al azar.
    Recibe: letra del arma y objetivo (z, x, y).
    Devuelve: la jugada (dict con "arma", "objetivo" y "eje").
    """
    eje = None
    if letra == "L":
        eje = random.choice(["x", "y"])
    return {"arma": letra, "objetivo": objetivo, "eje": eje}


def objetivos_de_caza(cubo):
    """
    Busca las celdas donde seguramente hay una nave del rival: las
    vecinas de un impacto de una nave que todavía no se hundió y las
    celdas detectadas por el sonar. Solo usa lo que ve el que dispara:
    nunca lee NAVE_OCULTA.
    Recibe: el cubo del rival.
    Devuelve: lista de puntos sin repetidos, de mayor a menor prioridad.
    """
    sin_disparar = set(celdas_sin_disparar(cubo))
    objetivos = []
    n = len(cubo)
    for z in range(1, n + 1):
        for x in range(1, n + 1):
            for y in range(1, n + 1):
                if tablero.leer_celda(cubo, z, x, y) == tablero.IMPACTO:
                    for dz, dx, dy in VECINOS_ORTOGONALES:
                        vecino = (z + dz, x + dx, y + dy)
                        if vecino in sin_disparar and vecino not in objetivos:
                            objetivos.append(vecino)
    for celda in sorted(sin_disparar):
        if tablero.leer_celda(cubo, *celda) == tablero.DETECTADO_SONAR and celda not in objetivos:
            objetivos.append(celda)
    return objetivos


def celdas_para_explorar(cubo):
    """
    Elige las celdas que conviene explorar cuando no hay nada para cazar:
    descarta las vecinas de una nave hundida (ahí no puede haber otra
    nave, porque entre naves queda una celda libre) y se queda con las de
    suma z + x + y par, como un tablero de ajedrez: como la nave más chica
    ocupa 2 celdas seguidas, siempre toca alguna de esas.
    Recibe: el cubo del rival.
    Devuelve: lista de puntos; si el filtro la deja vacía, se relaja.
    """
    sin_disparar = celdas_sin_disparar(cubo)
    descartadas = set()
    for celda in sin_disparar:
        for vecino in tablero.vecinos_de_celda(cubo, *celda):
            if tablero.leer_celda(cubo, *vecino) == tablero.HUNDIDO:
                descartadas.add(celda)
    candidatas = [c for c in sin_disparar
                  if c not in descartadas and (c[0] + c[1] + c[2]) % 2 == 0]
    if len(candidatas) == 0:
        candidatas = [c for c in sin_disparar if c not in descartadas]
    if len(candidatas) == 0:
        candidatas = sin_disparar
    return candidatas


def jugada_cazadora(estado):
    """
    Nivel 2 de la máquina. Si tiene dónde cazar (impactos de una nave a
    flote o detecciones del sonar), dispara un torpedo ahí para no gastar
    munición. Si no, explora con cualquier arma disponible en una celda
    elegida por celdas_para_explorar.
    Recibe: estado (dict de la partida).
    Devuelve: la jugada (dict con "arma", "objetivo" y "eje").
    """
    jugador = estado["jugadores"][estado["turno"]]
    rival = estado["jugadores"][1 - estado["turno"]]
    objetivos = objetivos_de_caza(rival["cubo"])
    if len(objetivos) > 0:
        return armar_jugada("T", objetivos[0])
    letra = random.choice(armas_con_municion(jugador))
    objetivo = random.choice(celdas_para_explorar(rival["cubo"]))
    return armar_jugada(letra, objetivo)


ESTRATEGIAS_MAQUINA = {
    1: elegir_jugada_maquina,
    2: jugada_cazadora,
}


def nivel_de_la_maquina(estado):
    """
    Indica el nivel de la máquina a la que le toca: el de ese jugador o,
    si no tiene, el de la partida (nueva_partida_vs_maquina lo guarda en
    estado["dificultad"]).
    Recibe: estado (dict de la partida).
    Devuelve: 1 o 2 (int).
    """
    jugador = estado["jugadores"][estado["turno"]]
    return jugador.get("dificultad", estado.get("dificultad", 1))


def turno_maquina_con_nivel(estado):
    """
    Juega el turno de la máquina según su nivel, con el diccionario
    ESTRATEGIAS_MAQUINA (sin cadenas de if / elif).
    Recibe: estado (dict de la partida).
    Devuelve: la jugada que hizo la máquina (dict).
    Lanza: ArmaNoDisponible u ObjetivoInvalido (ver ejecutar_turno).
    """
    jugada = ESTRATEGIAS_MAQUINA[nivel_de_la_maquina(estado)](estado)
    ejecutar_turno(estado, jugada)
    return jugada



def guardar_estado(estado, nombre):
    """
    Guarda la partida en un archivo con registro.guardar_partida.
    Recibe: estado (dict de la partida) y nombre de la partida (str).
    Devuelve: nada.
    Lanza: NombreDePartidaInvalido si el nombre no es válido, y los
    errores de registro.py (registro.ErrorRegistro) si no se pudo guardar.
    """
    if re.match(PATRON_NOMBRE_PARTIDA, nombre) is None:
        raise NombreDePartidaInvalido("El nombre solo admite letras, numeros, - y _ (hasta 30).")
    registro.guardar_partida(estado, nombre.strip())


def cargar_estado(nombre):
    """
    Carga una partida guardada con registro.cargar_partida.
    Recibe: nombre de la partida (str).
    Devuelve: el estado de la partida (dict), listo para seguir jugando.
    Lanza: los errores de registro.py (registro.ErrorRegistro): partida no
    encontrada, archivo corrupto o que no se pudo leer.
    """
    return registro.cargar_partida(nombre)




def guardar_y_salir(estado):
    """
    Pide un nombre, guarda la partida y marca el estado para volver al
    menú principal. Si no se pudo guardar, avisa y se sigue jugando.
    Recibe: estado (dict de la partida).
    Devuelve: True si se guardó (termina el menú del turno), False si no.
    """
    nombre = pedir_dato("Nombre de la partida (letras, numeros, - y _): ",
                        PATRON_NOMBRE_PARTIDA)
    guardada = False
    try:
        guardar_estado(estado, nombre)
    except ERRORES_DE_ARCHIVO as error:
        print("No se pudo guardar la partida: " + str(error))
    else:
        estado["salir"] = True
        guardada = True
        print("Partida guardada como '" + nombre + "'.")
    finally:
        print("--------------------")
    return guardada


OPCIONES_TURNO_CON_GUARDADO = {
    "1": disparar,
    "2": ver_mi_cubo,
    "3": ver_cubo_rival,
    "4": guardar_y_salir,
}


def turno_de_jugador_con_guardado(estado):
    """
    Igual que turno_de_jugador (Entrega 2), con la opción de guardar la
    partida y salir.
    Recibe: estado (dict de la partida).
    Devuelve: nada. El estado queda con el turno cambiado, o marcado con
    "salir" si se guardó.
    """
    jugador = estado["jugadores"][estado["turno"]]
    print()
    print("=== Turno de " + jugador["nombre"] + " ===")
    mostrar_municion(jugador)
    jugado = False
    while not jugado:
        print("1 - Disparar")
        print("2 - Ver mi cubo")
        print("3 - Ver el cubo del rival")
        print("4 - Guardar y salir")
        opcion = pedir_dato("Opcion: ", PATRON_OPCION_TURNO_CON_GUARDADO)
        jugado = OPCIONES_TURNO_CON_GUARDADO[opcion](estado)


def turno_de_maquina_con_nivel(estado):
    """
    Igual que turno_de_maquina (Entrega 2), pero la máquina juega según
    su nivel.
    Recibe: estado (dict de la partida).
    Devuelve: nada. El estado queda con el turno cambiado.
    """
    jugador = estado["jugadores"][estado["turno"]]
    print()
    print("=== Turno de " + jugador["nombre"] + " ===")
    jugada = turno_maquina_con_nivel(estado)
    nombre_arma = armamento.CATALOGO_ARMAS[jugada["arma"]]["nombre"]
    print(jugador["nombre"] + " dispara " + nombre_arma + " a " + str(jugada["objetivo"]))
    mostrar_resultado(estado["ultimo_resumen"])


# Qué función juega el turno según si el jugador es una máquina o no.
TURNOS = {
    True: turno_de_maquina_con_nivel,
    False: turno_de_jugador_con_guardado,
}


def jugar_partida_con_guardado(estado):
    """
    Igual que jugar_partida (Entrega 2), pero se puede guardar y salir,
    cada máquina juega según su nivel y al terminar se muestra el
    resumen de registro.py.
    Recibe: estado (dict de la partida, con las flotas ya ubicadas).
    Devuelve: el nombre del ganador (str), o None si se guardó para
    seguir después.
    """
    ganador = hay_ganador(estado)
    while ganador is None and not estado.get("salir", False):
        jugador = estado["jugadores"][estado["turno"]]
        TURNOS[jugador.get("es_maquina", False)](estado)
        ganador = hay_ganador(estado)
    if estado.pop("salir", False):
        print("Volviendo al menu principal.")
        return None
    registro.finalizar_historial(estado["historial"], ganador)
    print()
    print("Gano " + ganador + ". Hundio toda la flota del rival.")
    print()
    for linea in registro.generar_resumen(estado["historial"]):
        print(linea)
    return ganador


def pedir_nivel(mensaje):
    """
    Pide el nivel de una máquina.
    Recibe: mensaje (str).
    Devuelve: 1 (azar) o 2 (cazadora), como int.
    """
    print("Niveles: 1 = juega al azar   2 = caza las naves que impacta")
    return int(pedir_dato(mensaje, PATRON_NIVEL))


def partida_uno_contra_uno_con_guardado():
    """
    Igual que partida_uno_contra_uno (Entrega 1), pero la partida se
    puede guardar.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    estado = nueva_partida_1v1()
    for jugador in estado["jugadores"]:
        submenu_ubicacion(jugador)
    print()
    print("Las dos flotas estan ubicadas. Empieza la partida.")
    jugar_partida_con_guardado(estado)
    return False


def partida_contra_la_maquina_con_nivel():
    """
    Igual que partida_uno_contra_la_maquina (Entrega 2), pero se elige el
    nivel de la máquina y la partida se puede guardar.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    estado = nueva_partida_vs_maquina(None, pedir_nivel("Nivel de la maquina: "))
    submenu_ubicacion(estado["jugadores"][0])
    ubicacion_automatica(estado["jugadores"][1])
    print()
    print("Las dos flotas estan ubicadas. Empieza la partida.")
    jugar_partida_con_guardado(estado)
    return False


def partida_maquina_contra_maquina():
    """
    Crea una partida entre dos máquinas, con el nivel que se elija para
    cada una, y la juega mostrando cada turno.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    niveles = (pedir_nivel("Nivel de la Maquina 1: "),
               pedir_nivel("Nivel de la Maquina 2: "))
    try:
        estado = nueva_partida_maquina_vs_maquina(None, niveles)
    except flota.ErrorFlota as error:
        print("No se pudo ubicar alguna flota: " + str(error))
    else:
        print()
        print("Las dos flotas se ubicaron solas. Empieza la partida.")
        jugar_partida_con_guardado(estado)
    return False


def elegir_partida_guardada(nombres):
    """
    Muestra las partidas guardadas numeradas y pide una.
    Recibe: nombres (lista de str, no vacía).
    Devuelve: el nombre elegido (str), o None si se tipea 0 para volver.
    """
    print()
    print("--- Partidas guardadas ---")
    for posicion, nombre in enumerate(nombres):
        print(str(posicion + 1) + " - " + nombre)
    print("0 - Volver")
    opcion = int(pedir_dato("Opcion: ", PATRON_NUMERO))
    while opcion > len(nombres):
        print("Dato invalido. Intente de nuevo.")
        opcion = int(pedir_dato("Opcion: ", PATRON_NUMERO))
    if opcion == 0:
        return None
    return nombres[opcion - 1]


def continuar_partida_guardada():
    """
    Lista las partidas guardadas, carga la elegida y la retoma en el punto
    exacto en que se dejó.
    Devuelve: False, para que el menú principal se vuelva a mostrar.
    """
    try:
        nombres = registro.listar_partidas()
    except ERRORES_DE_ARCHIVO as error:
        print("No se pudieron leer las partidas guardadas: " + str(error))
        return False
    if len(nombres) == 0:
        print("No hay partidas guardadas.")
        return False

    nombre = elegir_partida_guardada(nombres)
    if nombre is None:
        return False
    try:
        estado = cargar_estado(nombre)
    except ERRORES_DE_ARCHIVO as error:
        print("No se pudo cargar la partida '" + nombre + "': " + str(error))
    else:
        print("Partida '" + nombre + "' cargada. Le toca a "
              + estado["jugadores"][estado["turno"]]["nombre"] + ".")
        jugar_partida_con_guardado(estado)
    return False



OPCIONES_PRINCIPAL["1"] = partida_uno_contra_uno_con_guardado
OPCIONES_PRINCIPAL["2"] = partida_contra_la_maquina_con_nivel
OPCIONES_PRINCIPAL["3"] = partida_maquina_contra_maquina
OPCIONES_PRINCIPAL["4"] = continuar_partida_guardada


if __name__ == "__main__":
    main()
