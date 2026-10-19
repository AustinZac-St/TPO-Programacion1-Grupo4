"""
radar.py - Búsquedas y sonar (Entregas 1 y 2).

Búsqueda optimizada: revisa primero las celdas con z + x + y par. Toda nave
ocupa al menos dos celdas contiguas sobre un eje, y esas celdas tienen
paridades distintas, así que toda nave intacta tiene una celda par: alcanza
con N³ / 2 comparaciones. Si no encuentra nada, revisa las impares.

Todas las búsquedas devuelven el resultado y sus métricas:
    {"comparaciones": 128, "tiempo_ms": 0.42, "profundidad_max": 4}

Este módulo NO usa print ni input.
"""

import time

from tablero import (DETECTADO_SONAR, NAVE_OCULTA, escribir_celda,
                     leer_celda)


def crear_metricas(comparaciones, inicio, profundidad_max):
    """
    Arma el diccionario de métricas de una búsqueda.
    Recibe: comparaciones, inicio (time.perf_counter()) y profundidad_max.
    Devuelve: dict con "comparaciones", "tiempo_ms" y "profundidad_max".
    """
    tiempo_ms = (time.perf_counter() - inicio) * 1000
    return {
        "comparaciones": comparaciones,
        "tiempo_ms": round(tiempo_ms, 4),
        "profundidad_max": profundidad_max,
    }


def busqueda_lineal(cubo, estado=NAVE_OCULTA):
    """
    Busca la primera celda con un estado recorriendo z, x, y con for anidados.
    Recibe: el cubo y el estado a buscar (por defecto nave oculta).
    Devuelve: (punto, metricas); punto es (z, x, y) o None.
    """
    inicio = time.perf_counter()
    comparaciones = 0
    n = len(cubo)
    for z in range(1, n + 1):
        for x in range(1, n + 1):
            for y in range(1, n + 1):
                comparaciones = comparaciones + 1
                if leer_celda(cubo, z, x, y) == estado:
                    return (z, x, y), crear_metricas(comparaciones, inicio, 0)
    return None, crear_metricas(comparaciones, inicio, 0)


def _buscar_por_paridad(cubo, estado, paridad):
    """
    Busca un estado solo en las celdas con z + x + y de una paridad.
    Recibe: el cubo, el estado y paridad (0 = pares, 1 = impares).
    Devuelve: (punto, comparaciones); punto es None si no lo encuentra.
    """
    comparaciones = 0
    n = len(cubo)
    for z in range(1, n + 1):
        for x in range(1, n + 1):
            # primer y con la paridad pedida (1 o 2), después de a dos
            primer_y = 1 + (z + x + 1 + paridad) % 2
            for y in range(primer_y, n + 1, 2):
                comparaciones = comparaciones + 1
                if leer_celda(cubo, z, x, y) == estado:
                    return (z, x, y), comparaciones
    return None, comparaciones


def busqueda_optimizada(cubo, estado=NAVE_OCULTA):
    """
    Busca una celda con un estado: primero en las pares, después en las
    impares (ver la justificación al principio del módulo).
    Recibe: el cubo y el estado a buscar (por defecto nave oculta).
    Devuelve: (punto, metricas); punto es (z, x, y) o None.
    """
    inicio = time.perf_counter()
    punto, comparaciones_pares = _buscar_por_paridad(cubo, estado, 0)
    if punto is not None:
        return punto, crear_metricas(comparaciones_pares, inicio, 0)
    punto, comparaciones_impares = _buscar_por_paridad(cubo, estado, 1)
    comparaciones = comparaciones_pares + comparaciones_impares
    return punto, crear_metricas(comparaciones, inicio, 0)


# Arma el punto (z, x, y) con el valor fijo del eje y las otras dos coordenadas
PUNTOS_DEL_PLANO = {
    "z": lambda valor, i, j: (valor, i, j),
    "x": lambda valor, i, j: (i, valor, j),
    "y": lambda valor, i, j: (i, j, valor),
}


def sonar(cubo, eje, valor):
    """
    Revela un plano del cubo y marca sus naves como detectadas por sonar.
    No produce daño.
    Recibe: el cubo, eje ("z", "x" o "y") y valor (de 1 a N).
    Devuelve: (contactos, metricas); contactos es la lista de puntos con nave.
    Lanza: ValueError si el eje o el valor no son válidos.
    """
    eje = str(eje).lower()
    n = len(cubo)
    if eje not in PUNTOS_DEL_PLANO:
        raise ValueError("El sonar va sobre el eje z, x o y.")
    if not 1 <= valor <= n:
        raise ValueError("El valor del plano va de 1 a " + str(n) + ".")

    inicio = time.perf_counter()
    armar_punto = PUNTOS_DEL_PLANO[eje]
    comparaciones = 0
    contactos = []
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            z, x, y = armar_punto(valor, i, j)
            comparaciones = comparaciones + 1
            if leer_celda(cubo, z, x, y) in (NAVE_OCULTA, DETECTADO_SONAR):
                escribir_celda(cubo, z, x, y, DETECTADO_SONAR)
                contactos.append((z, x, y))
    return contactos, crear_metricas(comparaciones, inicio, 0)
