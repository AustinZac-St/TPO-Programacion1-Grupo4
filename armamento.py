
import tablero

'''
Entrega 1: Presentacion de torpedo. Como base, en armamento, las armas no cambian los valores de las celdas, solo calculan las celdas que afectan.
'''
def arma_torpedo(cubo, punto):

    #Calcula las celdas que afecta un torpedo.

    return [punto]
# "funcion": None = arma del catalogo que todavia no esta implementada
# (Entrega 2: R, C, S y L. Entrega 3: O y G).
catalogo_armas = {
    "T": {
        "nombre": "Torpedo",
        "municion_inicial": None,      # None = ilimitada
        "funcion": arma_torpedo,
    },
    "R": {
        "nombre": "Misil de racimo",
        "municion_inicial": 3,
        "funcion": None,
    },
    "C": {
        "nombre": "Carga de profundidad",
        "municion_inicial": 2,
        "funcion": None,
    },
    "S": {
        "nombre": "Sonar",
        "municion_inicial": 4,
        "funcion": None,
    },
    "L": {
        "nombre": "Barrido laser",
        "municion_inicial": 2,
        "funcion": None,
    },
    "O": {
        "nombre": "Onda expansiva",
        "municion_inicial": 1,
        "funcion": None,
    },
    "G": {
        "nombre": "Torpedo guiado",
        "municion_inicial": 1,
        "funcion": None,
    },
}
