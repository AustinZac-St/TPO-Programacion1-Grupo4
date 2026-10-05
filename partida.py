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
            {"nombre": "Jugador 1", "cubo": [...], "flota": [...]},
            {"nombre": "Jugador 2", "cubo": [...], "flota": [...]},
        ],
        "turno": 0,                # índice del jugador al que le toca
        "historial": {...},        # creado con registro.crear_historial
    }

Las opciones de los menús se despachan con diccionarios que asocian
la opción tipeada con una función, sin cadenas de if / elif.
"""

import re

import flota
import registro
import tablero

# Expresiones regulares para validar todo lo que se tipea
PATRON_OPCION_PRINCIPAL = r"^\s*([1-5])\s*$"
PATRON_OPCION_UBICACION = r"^\s*([1-4])\s*$"
PATRON_NAVE = r"^\s*([A-Za-z0])\s*$"
PATRON_NUMERO = r"^\s*(\d+)\s*$"
PATRON_TRAMO = (r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*-"
                r"\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")

NOMBRES_POR_DEFECTO = ("Jugador 1", "Jugador 2")

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


# --------------------------------------------------------------------------
# Entrada y salida
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


def ver_cubo(jugador):
    """
    Dibuja el cubo del jugador, una capa de z o todas, con sus naves.
    Recibe: jugador (dict).
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
    for linea in lineas_del_cubo(jugador["cubo"], capas, True):
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
    print("Las dos flotas estan ubicadas.")
    print("Los turnos se agregan en la Entrega 2.")
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
    "2": opcion_no_disponible,
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


if __name__ == "__main__":
    main()
