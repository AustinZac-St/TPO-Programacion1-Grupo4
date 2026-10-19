"""
flota.py

Catalogo de naves, reglas de ubicacion, ubicacion manual y automatica

Este modulo no usa print ni input

Convenciones:
- Un punto es una tupla (z, x, y) con valores de 1 a N.
- El cubo es una lista de listas de listas (cubo[z-1][x-1][y-1]); la
  conversion de indices vive en tablero.py (leer_celda / escribir_celda).
- La flota es una lista de diccionarios, uno por nave:
    {"id": "D1", "tipo": "D", "celdas": {(3, 5, 6), ...}, "impactos": set()}
 
Reglas implementadas:
- Cada nave ocupa una linea recta contigua sobre un eje. la estacion orbital
  (E) ocupa un bloque 2x2x2.
- Ninguna nave puede salir del cubo.
- Entre dos naves debe quedar al menos una celda libre en cualquier direccion
  (diagonales incluidas)
- Restricciones propias:
  - Submarino (S): solo mitad inferior de z (z <= N//2).
  - Crucero (C): no puede ocupar z = 1 ni z = N.
  - Portaaviones (P): solo mitad superior de z (z > N//2).
  - Estacion orbital (E): no puede tocar ninguna cara exterior del cubo.

Mitades de z: inferior z <= N//2, superior z > N//2. Con N impar la capa del
medio pertenece a la mitad SUPERIOR (con N=7: inferior 1..3, superior 4..7).

Entrega 2 - Impactos, naves averiadas y hundidas:
- Cada nave guarda ademas "golpes": {punto: cantidad de impactos recibidos}.
  Una celda queda destruida (entra en "impactos") cuando sus golpes llegan a
  la "resistencia" de la nave.
- Comportamientos propios (son datos del catalogo, sin if/elif):
  - Portaaviones (P): resistencia 2, cada celda necesita dos impactos.
  - Submarino (S): inmune al barrido laser (L).
  - Destructor (D): al ser impactado revela una celda ocupada del rival.
  - Estacion orbital (E): al hundirse otorga municion extra.
  Los efectos de D y E solo se informan; los aplica el integrador.
- Estados de una nave: intacta, averiada (algun impacto) o hundida (todas
  sus celdas destruidas). Al hundirse, sus celdas pasan a HUNDIDO en el cubo.
"""

import random
from itertools import product

from tablero import (SIN_EXPLORAR, NAVE_OCULTA, AGUA_MARCADA, IMPACTO, HUNDIDO,
                     escribir_celda, leer_celda)

Punto = tuple[int, int, int]  

MAX_INTENTOS_NAVE = 200  #intentos al azar por nave
MAX_REINICIOS = 50       #veces que se reinicia la flota completa si se traba



# Excepciones propias (clase base + subclases)

class ErrorFlota(Exception):
    """Clase base de los errores de este modulo."""


class NaveDesconocida(ErrorFlota):
    """La letra no corresponde a ningun tipo del catalogo."""


class NaveAgotada(ErrorFlota):
    """Ya se ubicaron todas las naves de ese tipo."""


class UbicacionInvalida(ErrorFlota):
    """La ubicacion propuesta no cumple las reglas."""


class DisparoInvalido(ErrorFlota):
    """El punto disparado no es valido (formato incorrecto o fuera del cubo)."""



# Catalogo. Las restricciones son datos (funciones z_valido), sin if/elif.

def _z_cualquiera(z: int, n: int) -> bool:
    return True


def _z_mitad_inferior(z: int, n: int) -> bool:
    return z <= n // 2


def _z_mitad_superior(z: int, n: int) -> bool:
    return z > n // 2


def _z_sin_extremos(z: int, n: int) -> bool:
    return 1 < z < n


# forma "linea": "largo" es el largo de la recta; forma "bloque": "largo" es el lado del cubo.
CATALOGO = {
    "F": {"nombre": "Fragata", "forma": "linea", "largo": 2, "cantidad": 3,
          "z_valido": _z_cualquiera, "evita_caras": False,
          "resistencia": 1, "inmune_a": (), "efecto": None, "femenino": True},
    "D": {"nombre": "Destructor", "forma": "linea", "largo": 3, "cantidad": 2,
          "z_valido": _z_cualquiera, "evita_caras": False,
          "resistencia": 1, "inmune_a": (), "efecto": "revela_celda"},
    "S": {"nombre": "Submarino", "forma": "linea", "largo": 3, "cantidad": 2,
          "z_valido": _z_mitad_inferior, "evita_caras": False,
          "resistencia": 1, "inmune_a": ("L",), "efecto": None},
    "C": {"nombre": "Crucero", "forma": "linea", "largo": 4, "cantidad": 1,
          "z_valido": _z_sin_extremos, "evita_caras": False,
          "resistencia": 1, "inmune_a": (), "efecto": None},
    "P": {"nombre": "Portaaviones", "forma": "linea", "largo": 5, "cantidad": 1,
          "z_valido": _z_mitad_superior, "evita_caras": False,
          "resistencia": 2, "inmune_a": (), "efecto": None},
    "E": {"nombre": "Estacion orbital", "forma": "bloque", "largo": 2, "cantidad": 1,
          "z_valido": _z_sin_extremos, "evita_caras": True,
          "resistencia": 1, "inmune_a": (), "efecto": "municion_extra", "femenino": True},
}

# Momento en que se dispara el efecto propio de cada nave.
# "revela_celda" ocurre en cada impacto; "municion_extra" solo al hundirse.
EFECTO_AL_IMPACTAR = ("revela_celda",)
EFECTO_AL_HUNDIRSE = ("municion_extra",)


def cantidad_celdas(spec: dict) -> int:
    """Recibe la definicion de una nave; devuelve cuantas celdas ocupa."""
    return spec["largo"] ** 3 if spec["forma"] == "bloque" else spec["largo"]



# Geometria basica

def distancia_chebyshev(a: Punto, b: Punto) -> int:
    """Devuelve la distancia Chebyshev: el mayor salto en valor absoluto."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def puntos_de_linea(inicio: Punto, eje: str, largo: int) -> list[Punto]:
    """Recibe punto inicial, eje ('z', 'x' o 'y') y largo.

    Devuelve: la lista de puntos de la recta.
    Lanza: ValueError si el eje no es valido.
    """
    z, x, y = inicio
    pasos = {
        "z": lambda i: (z + i, x, y),
        "x": lambda i: (z, x + i, y),
        "y": lambda i: (z, x, y + i),
    }
    if eje not in pasos:
        raise ValueError("El eje debe ser 'x', 'y' o 'z'")
    return [pasos[eje](i) for i in range(largo)]


def puntos_de_bloque(esquina: Punto, tamano: tuple[int, int, int]) -> list[Punto]:
    """Recibe esquina minima y tamano (dz, dx, dy); devuelve los puntos del bloque."""
    z0, x0, y0 = esquina
    dz, dx, dy = tamano
    return [(z0 + iz, x0 + ix, y0 + iy)
            for iz in range(dz) for ix in range(dx) for iy in range(dy)]


def dentro_del_cubo(punto: Punto, n: int) -> bool:
    """Devuelve True si el punto esta dentro del cubo de lado n."""
    return all(1 <= c <= n for c in punto)


def puntos_de_tramo(tipo: str, desde: Punto, hasta: Punto,
                       catalogo: dict = CATALOGO) -> list[Punto]:
    """Convierte un tramo 'desde-hasta' en la lista de puntos que ocupa.

    Para la estacion orbital, desde y hasta son esquinas opuestas del bloque.
    Recibe: letra de la nave, punto desde, punto hasta, catalogo.
    Devuelve: lista de puntos.
    Lanza: NaveDesconocida, UbicacionInvalida (el tramo no tiene la forma o el largo de la nave).
    """
    if tipo not in catalogo:
        raise NaveDesconocida(f"No existe la nave '{tipo}'.")
    spec = catalogo[tipo]
    saltos = spec["largo"] - 1
    difs = [abs(h - d) for d, h in zip(desde, hasta)]
    if spec["forma"] == "bloque":
        forma_ok = all(d == saltos for d in difs)
    else:
        forma_ok = sorted(difs) == [0, 0, saltos]
    if not forma_ok:
        raise UbicacionInvalida("El tramo no tiene la forma o el largo de la nave.")
    rangos = [range(min(d, h), max(d, h) + 1) for d, h in zip(desde, hasta)]
    return list(product(*rangos))



# Validacion

def _forma_linea(spec: dict, puntos: list[Punto]) -> bool:
    largo = spec["largo"]
    spans = [max(p[i] for p in puntos) - min(p[i] for p in puntos) for i in range(3)]
    return len(puntos) == largo and sorted(spans) == [0, 0, largo - 1]


def _forma_bloque(spec: dict, puntos: list[Punto]) -> bool:
    lado = spec["largo"]
    spans = [max(p[i] for p in puntos) - min(p[i] for p in puntos) for i in range(3)]
    return len(puntos) == lado ** 3 and all(s == lado - 1 for s in spans)


FORMAS = {"linea": _forma_linea, "bloque": _forma_bloque}


def validar_ubicacion_nave(tipo: str, puntos: list[Punto], n: int,
                            puntos_existentes: set[Punto],
                            catalogo: dict = CATALOGO) -> None:
    """Valida la ubicacion de UNA nave segun su tipo y las reglas generales.

    Recibe: letra de la nave, puntos propuestos, tamano del cubo, puntos ya ocupados por otras naves y catalogo.
    Devuelve: None si es valida.
    Lanza: NaveDesconocida si el tipo no existe; UbicacionInvalida si no cumple alguna regla .
    """
    if tipo not in catalogo:
        raise NaveDesconocida(f"Tipo de nave desconocido: {tipo}")
    spec = catalogo[tipo]

    if len(set(puntos)) != len(puntos):
        raise UbicacionInvalida("La nave tiene celdas repetidas.")

    for p in puntos:
        if not dentro_del_cubo(p, n):
            raise UbicacionInvalida(f"Punto fuera del cubo: {p}")

    if not FORMAS[spec["forma"]](spec, puntos):
        raise UbicacionInvalida(
            f"{spec['nombre']}: forma o cantidad de celdas incorrecta.")

    if not all(spec["z_valido"](p[0], n) for p in puntos):
        raise UbicacionInvalida(f"{spec['nombre']}: altura (z) no permitida.")

    if spec["evita_caras"] and any(not (1 < c < n) for p in puntos for c in p):
        raise UbicacionInvalida(f"{spec['nombre']}: no puede tocar una cara exterior.")

    # Solapamiento directo
    choque = set(puntos) & set(puntos_existentes)
    if choque:
        raise UbicacionInvalida(f"La celda {min(choque)} ya esta ocupada.")

    # Separacion:
    for p in puntos:
        for q in puntos_existentes:
            if distancia_chebyshev(p, q) < 2:
                raise UbicacionInvalida(f"Nave demasiado cerca entre {p} y {q}.")


def validar_flota(ubicaciones: list[tuple[str, list[Punto]]], n: int,
                   catalogo: dict = CATALOGO) -> tuple[bool, str]:
    """Valida una flota completa.

    Recibe: lista de (tipo, puntos), tamano del cubo y catalogo.
    Devuelve: (True, "") si cumple, o (False, motivo).
    No lanza excepciones del modulo: las convierte en el motivo.
    """
    existentes: set[Punto] = set()
    conteo = {k: 0 for k in catalogo}
    for tipo, puntos_nave in ubicaciones:
        try:
            validar_ubicacion_nave(tipo, puntos_nave, n, existentes, catalogo)
        except ErrorFlota as e:
            return False, f"Error en nave {tipo}: {e}"
        conteo[tipo] += 1
        existentes.update(puntos_nave)
    for tipo, spec in catalogo.items():
        if conteo[tipo] != spec["cantidad"]:
            return False, (f"Cantidad incorrecta de naves {tipo}: se requiere "
                           f"{spec['cantidad']}, hay {conteo[tipo]}")
    return True, ""


# Consultas sobre la flota

def contar_colocadas(flota: list[dict], letra: str) -> int:
    """Recibe la flota y una letra; devuelve cuantas naves de ese tipo hay."""
    return sum(1 for nave in flota if nave["tipo"] == letra)


def pendientes(flota: list[dict], catalogo: dict = CATALOGO) -> dict[str, int]:
    """Devuelve {letra: cantidad_restante} solo para los tipos que aun faltan."""
    faltan = {l: s["cantidad"] - contar_colocadas(flota, l) for l, s in catalogo.items()}
    return {l: c for l, c in faltan.items() if c > 0}


def flota_completa(flota: list[dict], catalogo: dict = CATALOGO) -> bool:
    """Devuelve True si no queda ninguna nave pendiente."""
    return not pendientes(flota, catalogo)


def puntos_ocupados(flota: list[dict]) -> set[Punto]:
    """Devuelve el conjunto de todos los puntos ocupados por la flota."""
    return {p for nave in flota for p in nave["celdas"]}



# Ubicacion manual

def _ubicar(cubo: list, flota: list[dict], catalogo: dict, letra: str,
            desde: Punto, hasta: Punto) -> tuple[list, list[dict]]:
    """Nucleo de la ubicacion: valida, escribe en el cubo y registra la nave."""
    puntos = puntos_de_tramo(letra, desde, hasta, catalogo)
    if contar_colocadas(flota, letra) >= catalogo[letra]["cantidad"]:
        raise NaveAgotada(f"Ya se ubicaron todas las {catalogo[letra]['nombre']}.")
    validar_ubicacion_nave(letra, puntos, len(cubo), puntos_ocupados(flota), catalogo)
    for punto in puntos:
        escribir_celda(cubo, *punto, NAVE_OCULTA)
    flota.append({
        "id": f"{letra}{contar_colocadas(flota, letra) + 1}",
        "tipo": letra,
        "celdas": set(puntos),
        "impactos": set(),
        "golpes": {},
    })
    return cubo, flota


def ubicar_nave(cubo: list, flota: list[dict], nave: str,
                desde: Punto, hasta: Punto) -> tuple[list, list[dict]]:
    """Ubica una nave en el cubo (FUNCION PUBLICA).

    Recibe: cubo, flota (lista), letra de la nave y puntos (z, x, y) desde/hasta.
    Devuelve: (cubo, flota) actualizados (se modifican en el lugar).
    Lanza: NaveDesconocida, NaveAgotada o UbicacionInvalida. Ante cualquier
           error el cubo y la flota quedan intactos.
    """
    return _ubicar(cubo, flota, CATALOGO, str(nave).upper(), desde, hasta)



# Ubicacion automatica
def _tramo_al_azar(rng: random.Random, spec: dict, n: int) -> tuple[Punto, Punto]:
    saltos = spec["largo"] - 1
    if spec["forma"] == "bloque":
        desde = tuple(rng.randint(1, n - saltos) for _ in range(3))
        return desde, tuple(c + saltos for c in desde)
    eje = rng.randrange(3)
    desde = tuple(rng.randint(1, n - saltos if i == eje else n) for i in range(3))
    hasta = tuple(c + saltos if i == eje else c for i, c in enumerate(desde))
    return desde, hasta


def _ubicar_al_azar(cubo: list, flota: list[dict], catalogo: dict,
                    letra: str, rng: random.Random) -> None:
    for _ in range(MAX_INTENTOS_NAVE):
        desde, hasta = _tramo_al_azar(rng, catalogo[letra], len(cubo))
        try:
            _ubicar(cubo, flota, catalogo, letra, desde, hasta)
        except UbicacionInvalida:
            continue
        return
    raise UbicacionInvalida(f"No hubo lugar para {catalogo[letra]['nombre']}.")


def _limpiar(cubo: list, flota: list[dict]) -> None:
    for nave in flota:
        for punto in nave["celdas"]:
            escribir_celda(cubo, *punto, SIN_EXPLORAR)


def ubicacion_automatica(cubo: list, catalogo: dict = CATALOGO,
                         semilla: int | None = None) -> list[dict]:
    """Ubica la flota completa al azar (FUNCION PUBLICA).

    Recibe: cubo VACIO, catalogo y semilla (misma semilla -> misma flota).
    Devuelve: la flota ubicada; el cubo se modifica en el lugar.
    Lanza: ErrorFlota si tras MAX_REINICIOS intentos no logra ubicarla.
    """
    rng = random.Random(semilla)
   
    orden = sorted(catalogo, key=lambda l: -cantidad_celdas(catalogo[l]))
    for _ in range(MAX_REINICIOS):
        flota: list[dict] = []
        try:
            for letra in orden:
                for _ in range(catalogo[letra]["cantidad"]):
                    _ubicar_al_azar(cubo, flota, catalogo, letra, rng)
        except UbicacionInvalida:
            _limpiar(cubo, flota)
            continue
        return flota
    raise ErrorFlota("No se pudo ubicar la flota automaticamente.")



# Entrega 2: estado de las naves

def buscar_nave(flota, punto):
    """Busca la nave que ocupa un punto.

    Recibe: la flota (lista de naves) y un punto (z, x, y).
    Devuelve: el diccionario de la nave, o None si el punto es agua.
    """
    for nave in flota:
        if punto in nave["celdas"]:
            return nave
    return None


def esta_hundida(nave):
    """Recibe una nave; devuelve True si todas sus celdas estan destruidas."""
    return len(nave["impactos"]) == len(nave["celdas"])


def esta_averiada(nave):
    """Recibe una nave; devuelve True si tiene impactos pero sigue a flote."""
    return len(nave["impactos"]) > 0 and not esta_hundida(nave)


def estado_nave(nave):
    """Indica el estado de una nave.

    Recibe: una nave.
    Devuelve: "hundida", "averiada" o "intacta" (str).
    """
    if esta_hundida(nave):
        return "hundida"
    if esta_averiada(nave):
        return "averiada"
    return "intacta"


def naves_averiadas(flota):
    """Recibe la flota; devuelve la lista de naves averiadas."""
    return list(filter(esta_averiada, flota))


def naves_hundidas(flota):
    """Recibe la flota; devuelve la lista de naves hundidas."""
    return list(filter(esta_hundida, flota))


def naves_a_flote(flota):
    """Recibe la flota; devuelve la lista de naves que no estan hundidas."""
    return [nave for nave in flota if not esta_hundida(nave)]


def flota_hundida(flota):
    """Indica si toda la flota fue hundida (sirve para saber si hay ganador).

    Recibe: la flota.
    Devuelve: True si hay naves y todas estan hundidas; False en otro caso.
    """
    return len(flota) > 0 and len(naves_a_flote(flota)) == 0


def describir_nave(nave, catalogo=CATALOGO):
    """Arma el texto del estado de una nave, como lo pide la consigna.

    Recibe: una nave y el catalogo.
    Devuelve: por ejemplo "Destructor averiado (1 de 3)" o "Fragata hundida".
    """
    spec = catalogo[nave["tipo"]]
    terminacion = "a" if spec.get("femenino", False) else "o"
    if esta_hundida(nave):
        return f"{spec['nombre']} hundid{terminacion}"
    if esta_averiada(nave):
        return (f"{spec['nombre']} averiad{terminacion} "
                f"({len(nave['impactos'])} de {len(nave['celdas'])})")
    return f"{spec['nombre']} intact{terminacion}"


def estado_de_flota(flota, catalogo=CATALOGO):
    """Resume el estado de cada nave de la flota.

    Recibe: la flota y el catalogo.
    Devuelve: lista de diccionarios, uno por nave, con "id", "nombre",
              "estado", "destruidas" y "total".
    """
    return [{"id": nave["id"],
             "nombre": catalogo[nave["tipo"]]["nombre"],
             "estado": estado_nave(nave),
             "destruidas": len(nave["impactos"]),
             "total": len(nave["celdas"])}
            for nave in flota]



# Entrega 2: impactos
def _validar_punto_disparo(cubo, punto):
    """Lanza DisparoInvalido si el punto no es (z, x, y) dentro del cubo."""
    if type(punto) not in (tuple, list) or len(punto) != 3:
        raise DisparoInvalido(f"El punto {punto} no tiene la forma (z, x, y).")
    if not all(type(c) == int for c in punto) or not dentro_del_cubo(punto, len(cubo)):
        raise DisparoInvalido(f"El punto {punto} esta fuera del cubo.")


def _resultado(resultado, nave=None, efecto=None, mensaje="Agua."):
    """Arma el diccionario que devuelve recibir_impacto."""
    return {
        "resultado": resultado,
        "nave": None if nave is None else nave["id"],
        "tipo": None if nave is None else nave["tipo"],
        "hundida": nave is not None and esta_hundida(nave),
        "efecto": efecto,
        "mensaje": mensaje,
    }


def _hundir(cubo, nave):
    """Marca como HUNDIDO todas las celdas de una nave en el cubo."""
    for punto in nave["celdas"]:
        escribir_celda(cubo, *punto, HUNDIDO)


def recibir_impacto(cubo, flota, punto, arma=None, catalogo=CATALOGO):
    """Aplica un impacto sobre una celda de la flota (y del cubo) del rival.

    Reglas:
    - Agua: la celda pasa a AGUA_MARCADA.
    - Nave: suma un golpe a la celda. Cuando llega a la resistencia de la
      nave (2 para el portaaviones), la celda queda destruida y pasa a
      IMPACTO. Si se destruyen todas, la nave se hunde y sus celdas pasan a
      HUNDIDO.
    - Si la nave es inmune al arma (submarino contra laser) no pasa nada.
    - Una celda ya destruida o ya marcada como agua no cambia.

    Recibe: cubo y flota del rival, punto (z, x, y), letra del arma (o None)
            y catalogo.
    Devuelve: diccionario con
        "resultado": "agua", "impacto", "resiste", "inmune" o "repetido",
        "nave": id de la nave o None,  "tipo": letra o None,
        "hundida": bool,
        "efecto": "revela_celda", "municion_extra" o None,
        "mensaje": texto para mostrar, por ejemplo
                   "Impacto. Destructor averiado (1 de 3)."
    Lanza: DisparoInvalido si el punto no es valido.
    """
    _validar_punto_disparo(cubo, punto)
    punto = tuple(punto)
    nave = buscar_nave(flota, punto)

    if nave is None:
        if leer_celda(cubo, *punto) == AGUA_MARCADA:
            return _resultado("repetido", mensaje="Ya se habia disparado ahi.")
        escribir_celda(cubo, *punto, AGUA_MARCADA)
        return _resultado("agua")

    spec = catalogo[nave["tipo"]]
    if punto in nave["impactos"]:
        return _resultado("repetido", nave, mensaje="Ya se habia disparado ahi.")
    if arma is not None and str(arma).upper() in spec.get("inmune_a", ()):
        
        return _resultado("inmune", nave)

    golpes = nave.setdefault("golpes", {})
    golpes[punto] = golpes.get(punto, 0) + 1
    resistencia = spec.get("resistencia", 1)
    if golpes[punto] < resistencia:
        return _resultado("resiste", nave, mensaje=(
            f"Impacto. {spec['nombre']} resiste "
            f"(celda danada {golpes[punto]} de {resistencia})."))

    nave["impactos"].add(punto)
    escribir_celda(cubo, *punto, IMPACTO)
    if esta_hundida(nave):
        _hundir(cubo, nave)
    efecto = spec.get("efecto")
    corresponde = (efecto in EFECTO_AL_IMPACTAR
                   or (efecto in EFECTO_AL_HUNDIRSE and esta_hundida(nave)))
    if not corresponde:
        efecto = None
    return _resultado("impacto", nave, efecto,
                      f"Impacto. {describir_nave(nave, catalogo)}.")


def disparar_celdas(cubo, flota, celdas, arma=None, catalogo=CATALOGO):
    """Aplica un impacto en cada una de las celdas que afecta un arma.

    Recibe: cubo y flota del rival, lista de puntos (la que devuelve la
            funcion del arma en armamento.py), letra del arma y catalogo.
    Devuelve: lista con el resultado de cada celda (ver recibir_impacto).
    Lanza: DisparoInvalido si alguna celda no es valida; las celdas
           anteriores ya quedan aplicadas.
    """
    return [recibir_impacto(cubo, flota, punto, arma, catalogo) for punto in celdas]


def resumen_disparo(resultados, catalogo=CATALOGO):
    """Junta los resultados de un disparo en un solo resumen.

    Los datos coinciden con lo que pide registro.registrar_jugada.
    Recibe: la lista que devuelve disparar_celdas y el catalogo.
    Devuelve: diccionario con "impactos" (int), "aguas" (int),
              "hundidas" (lista de nombres de naves hundidas en este disparo),
              "efectos" (lista de efectos a aplicar) y
              "mensajes" (lista de textos sin repetir, en orden).
    """
    impactos = len([r for r in resultados if r["resultado"] in ("impacto", "resiste")])
    aguas = len([r for r in resultados if r["resultado"] in ("agua", "inmune")])
    hundidas = []
    for r in resultados:
        nombre = None if r["tipo"] is None else catalogo[r["tipo"]]["nombre"]
        if r["resultado"] == "impacto" and r["hundida"] and nombre not in hundidas:
            hundidas.append(nombre)
    efectos = [r["efecto"] for r in resultados if r["efecto"] is not None]
    mensajes = []
    for r in resultados:
        if r["mensaje"] not in mensajes:
            mensajes.append(r["mensaje"])
    return {"impactos": impactos, "aguas": aguas, "hundidas": hundidas,
            "efectos": efectos, "mensajes": mensajes}


def celda_para_revelar(flota, semilla=None):
    """Elige una celda ocupada y todavia no destruida de una flota.

    Sirve para el efecto del destructor: cuando lo impactan, se revela una
    celda ocupada del RIVAL (se le pasa la flota del rival).
    Recibe: la flota y una semilla (misma semilla -> misma celda).
    Devuelve: un punto (z, x, y), o None si no quedan celdas sin destruir.
    """
    candidatas = sorted(p for nave in flota for p in nave["celdas"]
                        if p not in nave["impactos"])
    if len(candidatas) == 0:
        return None
    return random.Random(semilla).choice(candidatas)


if __name__ == "__main__":
    #Demo:
    from tablero import crear_cubo
    cubo = crear_cubo(8)
    flota = ubicacion_automatica(cubo, CATALOGO, semilla=42)
    for nave in flota:
        print(nave["id"], sorted(nave["celdas"]))
    print(validar_flota([(n["tipo"], list(n["celdas"])) for n in flota], 8))
