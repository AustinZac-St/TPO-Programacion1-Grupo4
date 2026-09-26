"""
tablero.py - Módulo del cubo (Entrega 1).

Responsabilidad: crear el cubo, validar puntos, leer y escribir celdas,
operaciones de matrices y dibujo de una capa de z.

El cubo es una lista de listas de listas: cubo[z][x][y].
Los ejes que ve el usuario van de 1 a N, pero las listas de Python
van de 0 a N-1. Por eso todas las funciones que reciben un punto
le restan 1 a cada valor antes de usarlo como índice.

Este módulo NO usa print ni input: recibe datos y devuelve datos.
Toda la entrada y salida vive en el integrador
"""

N_POR_DEFECTO = 8

# Estados de las celdas (cada estados con un nombre propio)
SIN_EXPLORAR = 0
NAVE_OCULTA = 1
AGUA_MARCADA= 2
IMPACTO = 3
HUNDIDO = 4
DETECTADO_SONAR = 5


def crear_cubo(n):
    """
    Crea un cubo de n x n x n con todas las celdas sin explorar.
    Recibe: n (int), el tamaño del cubo.
    Devuelve: el cubo (lista de listas de listas).
    """
    cubo = []
    for z in range(n):
        capa = []
        for x in range(n):
            celdas_de_x = []
            for y in range(n):
                celdas_de_x.append(SIN_EXPLORAR)
            capa.append(celdas_de_x)
        cubo.append(capa)
    return cubo


def punto_dentro_del_cubo(cubo, z, x, y):
    """
    Verifica que un punto (con ejes de 1 a N) esté dentro del cubo.
    Recibe: el cubo y los valores z, x, y (int).
    Devuelve: True si el punto está dentro, False si no.
    """
    n = len(cubo)
    if z < 1 or z > n:
        return False
    if x < 1 or x > n:
        return False
    if y < 1 or y > n:
        return False
    return True


def es_texto_de_punto_valido(texto, n):
    """
    Verifica que un texto tipeado tenga el formato de un punto: "z,x,y".
    Acepta espacios alrededor de los números (por ejemplo "3, 5, 4").
    Recibe: texto (str) y n (int), el tamaño del cubo.
    Devuelve: True si es un punto válido dentro del cubo, False si no.
    """
    partes = texto.split(",")
    if len(partes) != 3:
        return False
    for parte in partes:
        parte = parte.strip()
        if not parte.isdigit():
            return False
        valor = int(parte)
        if valor < 1 or valor > n:
            return False
    return True


def texto_a_punto(texto):
    """
    Convierte un texto "z,x,y" en una lista de tres enteros [z, x, y].
    Antes de llamarla hay que validar el texto con es_texto_de_punto_valido.
    Recibe: texto (str).
    Devuelve: lista [z, x, y] de enteros.
    """
    partes = texto.split(",")
    punto = []
    for parte in partes:
        punto.append(int(parte.strip()))
    return punto


def leer_celda(cubo, z, x, y):
    """
    Devuelve el estado de una celda.
    Recibe: el cubo y el punto z, x, y (ejes de 1 a N).
    Devuelve: el estado de la celda (int).
    """
    return cubo[z - 1][x - 1][y - 1]


def escribir_celda(cubo, z, x, y, estado):
    """
    Cambia el estado de una celda. Modifica el cubo recibido
    (las listas se pasan por referencia).
    Recibe: el cubo, el punto z, x, y (ejes de 1 a N) y el nuevo estado.
    Devuelve: nada.
    """
    cubo[z - 1][x - 1][y - 1] = estado


def obtener_capa_z(cubo, z):
    """
    Operación de matrices: arma la matriz de la capa z ordenada para
    dibujarla, donde cada fila es un valor de y y cada columna un valor de x.
    Ojo: en el cubo el orden es [z][x][y], por eso hay que trasponer.
    Recibe: el cubo y z (de 1 a N).
    Devuelve: matriz de n x n con capa[y][x].
    """
    n = len(cubo)
    capa = []
    for y in range(n):
        fila = []
        for x in range(n):
            fila.append(cubo[z - 1][x][y])
        capa.append(fila)
    return capa


def contar_celdas_en_estado(cubo, estado):
    """
    Operación de matrices: cuenta cuántas celdas del cubo tienen un estado.
    Recibe: el cubo y el estado a contar.
    Devuelve: la cantidad de celdas (int).
    """
    cantidad = 0
    for capa in cubo:
        for celdas_de_x in capa:
            for celda in celdas_de_x:
                if celda == estado:
                    cantidad = cantidad + 1
    return cantidad


def simbolo_de_estado(estado, mostrar_naves):
    """
    Devuelve el símbolo con el que se dibuja un estado.
    Si mostrar_naves es False (tablero del rival), la nave oculta
    se dibuja como agua sin explorar.
    Recibe: estado (int) y mostrar_naves (bool).
    Devuelve: el símbolo (str).
    Referencias: 
      ~ sin explorar
      o agua 
      X impacto
      # hundido 
      ? detectado
    """
    if estado == NAVE_OCULTA:
        if mostrar_naves:
            return "N"
        return "~"
    if estado == AGUA_MARCADA:
        return "o"
    if estado == IMPACTO:
        return "X"
    if estado == HUNDIDO:
        return "#"
    if estado == DETECTADO_SONAR:
        return "?"
    return "~"


def completar_ancho(texto, ancho):
    """
    Agrega espacios a la derecha de un texto hasta llegar al ancho pedido.
    Sirve para que las columnas queden alineadas aunque N sea 10 o más.
    Recibe: texto (str) y ancho (int).
    Devuelve: el texto completado (str).
    """
    return texto + " " * (ancho - len(texto))


def dibujar_capa_z(cubo, z, mostrar_naves):
    """
    Arma el dibujo de una capa de z con encabezados de x y de y.
    No imprime nada: devuelve las líneas para que las imprima partida.py.
    Recibe: el cubo, z (de 1 a N) y mostrar_naves (bool).
    Devuelve: lista de líneas (str).
    """
    n = len(cubo)
    ancho = len("x" + str(n))
    lineas = []

    lineas.append("========= CAPA z = " + str(z) + " =========")

    encabezado = []
    for x in range(1, n + 1):
        encabezado.append(completar_ancho("x" + str(x), ancho))
    lineas.append(completar_ancho("", ancho) + " " + " ".join(encabezado))

    capa = obtener_capa_z(cubo, z)
    for y in range(n):
        simbolos = []
        for x in range(n):
            simbolo = simbolo_de_estado(capa[y][x], mostrar_naves)
            simbolos.append(completar_ancho(simbolo, ancho))
        etiqueta = completar_ancho("y" + str(y + 1), ancho)
        lineas.append(etiqueta + " " + " ".join(simbolos))

    return lineas
