
import tablero

'''
Entrega 1: Presentacion de torpedo. Como base, en armamento, las armas no cambian los valores de las celdas, solo calculan las celdas que afectan.
'''
def arma_torpedo(cubo, punto):
    
    #Calcula las celdas que afecta un torpedo.
  
    return [punto]
catalogo_armas = {
    "T": {
        "nombre": "Torpedo",
        "municion_inicial": None,      # None = ilimitada
        "funcion": arma_torpedo,
    },
}