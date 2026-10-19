from tablero import crear_cubo, SIN_EXPLORAR,punto_dentro_del_cubo,vecinos_de_celda
from tablero import escribir_celda, NAVE_OCULTA
from tablero import leer_celda, texto_a_punto, es_texto_de_punto_valido
from tablero import contar_celdas_en_estado, simbolo_de_estado, completar_ancho
from tablero import AGUA_MARCADA, IMPACTO, HUNDIDO, DETECTADO_SONAR
from tablero import obtener_capa_z,obtener_plano_x, obtener_plano_y,dibujar_capa_z, dibujar_plano_x, dibujar_plano_y


def test_crear_cubo_tiene_tamano_correcto():
    cubo = crear_cubo(3)
    assert len(cubo) == 3
    assert len(cubo[0]) == 3
    assert cubo[0][0][0] == SIN_EXPLORAR

def test_punto_dentro_del_cubo():
    cubo = crear_cubo(3)
    assert punto_dentro_del_cubo(cubo, 1, 1, 1) == True
    assert punto_dentro_del_cubo(cubo, 2, 2, 2) == True
    assert punto_dentro_del_cubo(cubo, 3, 3, 3) == True
    assert punto_dentro_del_cubo(cubo, 0, 1, 1) == False
    assert punto_dentro_del_cubo(cubo, 4, 1, 1) == False
    assert punto_dentro_del_cubo(cubo, 1, 0, 1) == False
    assert punto_dentro_del_cubo(cubo, 1, 4, 1) == False
    assert punto_dentro_del_cubo(cubo, 1, 1, 0) == False
    assert punto_dentro_del_cubo(cubo, 1, 1, 4) == False


def test_escribir_celda():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 1, 1, NAVE_OCULTA)
    assert cubo[0][0][0] == NAVE_OCULTA
    assert cubo[1][1][1] == SIN_EXPLORAR

def test_leer_celda():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 2, 3, 1, IMPACTO)
    assert leer_celda(cubo, 2, 3, 1) == IMPACTO
    assert leer_celda(cubo, 1, 1, 1) == SIN_EXPLORAR


def test_texto_a_punto():
    assert texto_a_punto("3,5,4") == [3, 5, 4]
    assert texto_a_punto("3, 5, 4") == [3, 5, 4]


def test_es_texto_de_punto_valido():
    assert es_texto_de_punto_valido("3,5,4", 8) == True
    assert es_texto_de_punto_valido("3, 5, 4", 8) == True
    assert es_texto_de_punto_valido("3,5", 8) == False
    assert es_texto_de_punto_valido("3,5,4,2", 8) == False
    assert es_texto_de_punto_valido("a,5,4", 8) == False
    assert es_texto_de_punto_valido("0,5,4", 8) == False
    assert es_texto_de_punto_valido("9,5,4", 8) == False


def test_contar_celdas_en_estado():
    cubo = crear_cubo(3)
    assert contar_celdas_en_estado(cubo, SIN_EXPLORAR) == 27
    assert contar_celdas_en_estado(cubo, NAVE_OCULTA) == 0
    escribir_celda(cubo, 1, 1, 1, NAVE_OCULTA)
    escribir_celda(cubo, 3, 3, 3, NAVE_OCULTA)
    assert contar_celdas_en_estado(cubo, NAVE_OCULTA) == 2
    assert contar_celdas_en_estado(cubo, SIN_EXPLORAR) == 25


def test_simbolo_de_estado():
    assert simbolo_de_estado(SIN_EXPLORAR, True) == "~"
    assert simbolo_de_estado(NAVE_OCULTA, True) == "N"
    assert simbolo_de_estado(NAVE_OCULTA, False) == "~"
    assert simbolo_de_estado(AGUA_MARCADA, True) == "o"
    assert simbolo_de_estado(IMPACTO, True) == "X"
    assert simbolo_de_estado(HUNDIDO, True) == "#"
    assert simbolo_de_estado(DETECTADO_SONAR, True) == "?"


def test_completar_ancho():
    assert completar_ancho("x1", 3) == "x1 "
    assert completar_ancho("x10", 3) == "x10"

    
def test_obtener_capa_z():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 2, 3, NAVE_OCULTA)
    capa = obtener_capa_z(cubo, 1)
    assert capa[0][0] == SIN_EXPLORAR
    assert capa[2][1] == NAVE_OCULTA
    assert len(capa) == 3


def test_obtener_plano_x():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 2, 3, NAVE_OCULTA)
    plano = obtener_plano_x(cubo, 2)
    assert plano[0][0] == SIN_EXPLORAR
    assert plano[0][2] == NAVE_OCULTA
    assert len(plano) == 3

def test_obtener_plano_y():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 2, 3, NAVE_OCULTA)
    plano = obtener_plano_y(cubo, 3)
    assert plano[0][0] == SIN_EXPLORAR
    assert plano[0][1] == NAVE_OCULTA
    assert len(plano) == 3


def test_dibujar_capa_z():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 2, 3, NAVE_OCULTA)
    lineas = dibujar_capa_z(cubo, 1, True)
    assert len(lineas) == 5
    assert lineas[0] == "========= CAPA z = 1 ========="
    assert "N" in lineas[4]
    lineas = dibujar_capa_z(cubo, 1, False)
    assert "N" not in lineas[4]


def test_dibujar_plano_x():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 2, 3, NAVE_OCULTA)
    lineas = dibujar_plano_x(cubo, 2, True)
    assert len(lineas) == 5
    assert lineas[0] == "========= PLANO x = 2 ========="
    assert "N" in lineas[2]
    lineas = dibujar_plano_x(cubo, 2, False)
    assert "N" not in lineas[2]


def test_dibujar_plano_y():
    cubo = crear_cubo(3)
    escribir_celda(cubo, 1, 2, 3, NAVE_OCULTA)
    lineas = dibujar_plano_y(cubo, 3, True)
    assert len(lineas) == 5
    assert lineas[0] == "========= PLANO y = 3 ========="
    assert "N" in lineas[2]
    lineas = dibujar_plano_y(cubo, 3, False)
    assert "N" not in lineas[2]


def test_vecinos_de_celda():
    cubo = crear_cubo(3)
    assert len(vecinos_de_celda (cubo, 2, 2, 2)) == 26
    assert len(vecinos_de_celda(cubo, 1, 1, 1)) == 7
    assert len(vecinos_de_celda(cubo, 1, 2, 2)) == 17
    assert(2, 2, 2) not in vecinos_de_celda(cubo, 2, 2, 2)