"""
radar.py - Módulo de búsquedas (Entrega 1).

Responsabilidad en esta entrega: búsqueda lineal con métricas.

La búsqueda lineal recorre el cubo con tres ciclos for anidados, en el
orden z, x, y, sin ninguna estructura auxiliar, y se detiene en la
primera celda que tiene el estado buscado.

Todas las búsquedas devuelven el resultado más un diccionario con las
métricas de la corrida:
    {"comparaciones": 128, "tiempo_ms": 0.42, "profundidad_max": 4}

Este módulo NO usa print ni input: recibe datos y devuelve datos.
"""

import time

from tablero import NAVE_OCULTA, leer_celda


def crear_metricas(comparaciones, inicio, profundidad_max):
    """
    Arma el diccionario de métricas de una búsqueda.
    Recibe: comparaciones (int), inicio (float, el valor de
    time.perf_counter() al empezar) y profundidad_max (int).
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
    Busca la primera celda del cubo que tiene un estado, recorriendo
    con ciclos for anidados (z, después x, después y).
    Por defecto busca una nave oculta, es decir, localiza una nave.
    Recibe: el cubo y el estado a buscar (int).
    Devuelve: una tupla (punto, metricas). El punto es (z, x, y) con
    ejes de 1 a N, o None si ninguna celda tiene ese estado.
    Como no es recursiva, "profundidad_max" siempre vale 0.
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
