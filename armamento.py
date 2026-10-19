
import tablero

'''
Entrega 1: Presentacion de torpedo. Como base, en armamento, las armas no cambian los valores de las celdas, solo calculan las celdas que afectan.
'''
def arma_torpedo(cubo, punto, eje=None):
    """
    Calcula las celdas que afecta un torpedo.
    El torpedo afecta únicamente la celda apuntada.
    Recibe: el cubo (no lo usa, está por uniformidad de firma),
            punto (tupla (z, x, y) con ejes de 1 a N) y
            eje (no lo usa).
    Devuelve: lista con la única celda afectada [(z, x, y)].
    """
    return [punto]


class SinMunicion(Exception):
    """Se intentó usar un arma que ya no tiene munición."""


def _vecinos_ortogonales(cubo, punto):
    """
    Devuelve las celdas que comparten una cara con el punto (arriba, abajo
    y los cuatro costados), descartando las que quedan fuera del cubo.
    """
    z, x, y = punto
    desplazamientos = ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                       (0, -1, 0), (0, 0, 1), (0, 0, -1))
    vecinos = []
    for dz, dx, dy in desplazamientos:
        vecino = (z + dz, x + dx, y + dy)
        if tablero.punto_dentro_del_cubo(cubo, *vecino):
            vecinos.append(vecino)
    return vecinos


def _recta(cubo, punto, eje):
    """
    Devuelve todos los puntos de la recta que pasa por 'punto' siguiendo un
    eje: recorre ese eje de 1 a N y deja fijos los otros dos.
    El eje se resuelve con un diccionario de funciones, no con if/elif.
    """
    z, x, y = punto
    armar = {
        "z": lambda i: (i, x, y),
        "x": lambda i: (z, i, y),
        "y": lambda i: (z, x, i),
    }
    return [armar[eje](i) for i in range(1, len(cubo) + 1)]


def arma_racimo(cubo, punto, eje=None):
    """
    Calcula las celdas que afecta un misil de racimo: la celda apuntada y
    sus seis vecinas ortogonales. En un borde o una esquina son menos,
    porque las vecinas que caerían fuera del cubo no se cuentan.
    Recibe: el cubo, punto (z, x, y) y eje (no lo usa).
    Devuelve: lista de hasta siete celdas, la apuntada primero.
    """
    return [punto] + _vecinos_ortogonales(cubo, punto)


def arma_carga_profundidad(cubo, punto, eje=None):
    """
    Calcula las celdas que afecta una carga de profundidad: toda la recta
    sobre el eje z que pasa por el punto apuntado (z de 1 a N, con x e y fijos).
    Recibe: el cubo, punto (z, x, y) y eje (no lo usa).
    Devuelve: lista de N celdas.
    """
    return _recta(cubo, punto, "z")

def arma_barrido_laser(cubo, punto, eje=None):
    """
    Calcula las celdas que afecta un barrido láser: una recta completa
    sobre el eje x o sobre el eje y, a elección, que pasa por el punto.
    Recibe: el cubo, punto (z, x, y) y eje ("x" o "y").
    Devuelve: lista de N celdas.
    Lanza: ValueError si el eje no es "x" ni "y".
    """
    eje = str(eje).lower()
    if eje not in ("x", "y"):
        raise ValueError("El barrido laser va sobre el eje x o el eje y.")
    return _recta(cubo, punto, eje)

CATALOGO_ARMAS = {
    "T": {
        "nombre": "Torpedo",
        "municion_inicial": None,      # None = munición ilimitada
        "funcion": arma_torpedo,
    },
    "R": {
        "nombre": "Misil de racimo",
        "municion_inicial": 3,
        "funcion": arma_racimo,
    },
    "C": {
        "nombre": "Carga de profundidad",
        "municion_inicial": 2,
        "funcion": arma_carga_profundidad,
    },
    "S": {
        "nombre": "Sonar",
        "municion_inicial": 4,
        "funcion": None,               # el sonar por planos va en radar.py
    },
    "L": {
        "nombre": "Barrido laser",
        "municion_inicial": 2,
        "funcion": arma_barrido_laser,
    },
    "O": {
        "nombre": "Onda expansiva",
        "municion_inicial": 1,
        "funcion": None,               # Entrega 3
    },
    "G": {
        "nombre": "Torpedo guiado",
        "municion_inicial": 1,
        "funcion": None,               # Entrega 3
    },
}


def crear_municion():
    """
    Arma la munición inicial de un jugador a partir del catálogo.
    Recibe: nada.
    Devuelve: diccionario {letra: cantidad}; None significa ilimitada.
    """
    municion = {}
    for letra, datos in CATALOGO_ARMAS.items():
        municion[letra] = datos["municion_inicial"]
    return municion


def tiene_municion(municion, letra):
    """
    Indica si a un arma le queda munición.
    Recibe: el diccionario de munición y la letra del arma.
    Devuelve: True si es ilimitada o le queda al menos una; False si no.
    """
    cantidad = municion.get(letra, 0)
    return cantidad is None or cantidad > 0


def consumir_municion(municion, letra):
    """
    Descuenta una unidad de munición. Las armas ilimitadas no se descuentan.
    Recibe: el diccionario de munición y la letra del arma.
    Devuelve: el diccionario actualizado (se modifica en el lugar).
    Lanza: SinMunicion si al arma no le queda munición.
    """
    if not tiene_municion(municion, letra):
        raise SinMunicion(f"No queda municion de {CATALOGO_ARMAS[letra]['nombre']}.")
    if municion[letra] is not None:
        municion[letra] = municion[letra] - 1
    return municion
