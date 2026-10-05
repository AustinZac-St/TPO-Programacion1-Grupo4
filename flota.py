"""
flota.py

<<<<<<< HEAD
Catálogo de naves y reglas de ubicación"""

CATALOGO_NAVES = {
    "F": {
        "nombre": "Fragata",
        "largo": 2,
        "cantidad": 3,
        "restriccion": "Sin restricción.",
        "zona": "Cualquiera",
    },
    "D": {
        "nombre": "Destructor",
        "largo": 3,
        "cantidad": 2,
        "restriccion": "Al ser impactada revela una celda ocupada del rival.",
        "zona": "Cualquiera",
    },
    "S": {
        "nombre": "Submarino",
        "largo": 3,
        "cantidad": 2,
        "restriccion": "Solo en la mitad inferior de z.",
        "zona": "Inferior",
    },
    "C": {
        "nombre": "Crucero",
        "largo": 4,
        "cantidad": 1,
        "restriccion": "No puede ocupar z = 1 ni z = N.",
        "zona": "Cualquiera, excluyendo z=1 y z=N",
    },
    "P": {
        "nombre": "Portaaviones",
        "largo": 5,
        "cantidad": 1,
        "restriccion": "Solo en la mitad superior de z.",
        "zona": "Superior",
    },
    "E": {
        "nombre": "Estación orbital",
        "largo": 8,
        "cantidad": 1,
        "restriccion": "Ocupa un bloque 2x2x2 y no puede tocar ninguna cara exterior del cubo.",
        "zona": "Interior",
    },
}

REGLAS_UBICACION = (
    "Cada nave ocupa una línea recta de celdas contiguas sobre uno de los tres ejes.",
    "La estación orbital es la excepción: ocupa un bloque de 2x2x2.",
    "Ninguna nave puede salir del cubo.",
    "Entre dos naves debe quedar al menos una celda libre en cualquier dirección, incluidas las diagonales.",
    "Submarino: solo en la mitad inferior de z.",
    "Portaaviones: solo en la mitad superior de z.",
    "Crucero: no puede ocupar z = 1 ni z = N.",
    "Estación orbital: no puede tocar ninguna cara exterior del cubo.",
)


def _punto_dentro_del_cubo(punto, n):
    z, x, y = punto
    return 1 <= z <= n and 1 <= x <= n and 1 <= y <= n


def _es_linea_contigua(puntos):
    if len(puntos) <= 1:
        return True

    zs = {p[0] for p in puntos}
    xs = {p[1] for p in puntos}
    ys = {p[2] for p in puntos}

    if len(zs) == 1 and len(xs) > 1 and len(ys) == 1:
        return max(xs) - min(xs) == len(puntos) - 1
    if len(xs) == 1 and len(ys) > 1 and len(zs) == 1:
        return max(ys) - min(ys) == len(puntos) - 1
    if len(ys) == 1 and len(zs) > 1 and len(xs) == 1:
        return max(zs) - min(zs) == len(puntos) - 1
    return False


def _es_bloque_2x2x2(puntos):
    if len(puntos) != 8:
        return False

    zs = {p[0] for p in puntos}
    xs = {p[1] for p in puntos}
    ys = {p[2] for p in puntos}

    if len(zs) != 2 or len(xs) != 2 or len(ys) != 2:
        return False

    if max(zs) - min(zs) != 1 or max(xs) - min(xs) != 1 or max(ys) - min(ys) != 1:
        return False

    bloque = set()
    for z in (min(zs), max(zs)):
        for x in (min(xs), max(xs)):
            for y in (min(ys), max(ys)):
                bloque.add((z, x, y))

    return set(puntos) == bloque


def _hay_espacio_minimo(puntos, ocupadas):
    for a in puntos:
        for b in ocupadas:
            if a == b:
                return False
            if max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2])) < 2:
                return False
    return True


def validar_ubicacion_nave(tipo, puntos, n, ocupadas=None):
    """Valida que una nave pueda ubicarse en el cubo según su tipo."""
    if tipo not in CATALOGO_NAVES:
        raise ValueError(f"Tipo de nave no válido: {tipo}")

    puntos = tuple((int(z), int(x), int(y)) for z, x, y in puntos)
    if not puntos:
        return False

    if len(puntos) != CATALOGO_NAVES[tipo]["largo"]:
        return False

    if any(not _punto_dentro_del_cubo(p, n) for p in puntos):
        return False

    if tipo == "E":
        if not _es_bloque_2x2x2(puntos):
            return False
        if any(z in (1, n) or x in (1, n) or y in (1, n) for z, x, y in puntos):
            return False
    else:
        if not _es_linea_contigua(puntos):
            return False
        if tipo == "S" and any(z > n // 2 for z, _, _ in puntos):
            return False
        if tipo == "P" and any(z <= n // 2 for z, _, _ in puntos):
            return False
        if tipo == "C" and any(z in (1, n) for z, _, _ in puntos):
            return False

    if ocupadas is not None:
        for p in puntos:
            if p in ocupadas:
                return False
        if not _hay_espacio_minimo(puntos, ocupadas):
            return False

    return True


def ubicar_nave_manual(tipo, inicio, direccion, n):
    """
    Ubicación manual de una nave a partir de una celda inicial y una dirección.
    """
    if tipo not in CATALOGO_NAVES:
        raise ValueError(f"Tipo de nave no válido: {tipo}")

    largo = CATALOGO_NAVES[tipo]["largo"]
    z, x, y = inicio

    if tipo == "E":
        puntos = []
        for dz in (0, 1):
            for dx in (0, 1):
                for dy in (0, 1):
                    puntos.append((z + dz, x + dx, y + dy))
        if not validar_ubicacion_nave(tipo, puntos, n):
            raise ValueError("La estación orbital no se puede ubicar en esa posición.")
        return puntos

    if direccion not in ("x", "y", "z"):
        raise ValueError("La dirección debe ser 'x', 'y' o 'z'.")

    puntos = []
    for i in range(largo):
        if direccion == "x":
            punto = (z, x + i, y)
        elif direccion == "y":
            punto = (z, x, y + i)
        else:
            punto = (z + i, x, y)
        puntos.append(punto)

    if not validar_ubicacion_nave(tipo, puntos, n):
        raise ValueError("La nave no cumple la ubicación válida para ese tipo.")
    return puntos


def ubicar_nave_automatica(tipo, n, ocupadas=None):
    """Intenta ubicar una nave válida en cualquier posición disponible."""
    if ocupadas is None:
        ocupadas = set()

    largo = CATALOGO_NAVES[tipo]["largo"]
    direcciones = ["x", "y", "z"]

    if tipo == "E":
        for z in range(1, n - 1):
            for x in range(1, n - 1):
                for y in range(1, n - 1):
                    puntos = [
                        (z + dz, x + dx, y + dy)
                        for dz in (0, 1)
                        for dx in (0, 1)
                        for dy in (0, 1)
                    ]
                    if validar_ubicacion_nave(tipo, puntos, n, ocupadas):
                        return puntos
        raise ValueError(f"No hay ubicación automática posible para {tipo}.")

    for z in range(1, n + 1):
        for x in range(1, n + 1):
            for y in range(1, n + 1):
                for direccion in direcciones:
                    puntos = []
                    for i in range(largo):
                        if direccion == "x":
                            puntos.append((z, x + i, y))
                        elif direccion == "y":
                            puntos.append((z, x, y + i))
                        else:
                            puntos.append((z + i, x, y))
                    if all(_punto_dentro_del_cubo(p, n) for p in puntos):
                        if validar_ubicacion_nave(tipo, puntos, n, ocupadas):
                            return puntos

    raise ValueError(f"No hay ubicación automática posible para {tipo}.")


def ubicar_flota_automatica(n):
    """Genera una flota completa con ubicación automática."""
    ocupadas = set()
    flota = {}

    for tipo, datos in CATALOGO_NAVES.items():
        flota[tipo] = []
        for _ in range(datos["cantidad"]):
            puntos = ubicar_nave_automatica(tipo, n, ocupadas)
            flota[tipo].append(puntos)
            ocupadas.update(puntos)

    return flota
=======
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
"""

import random
from itertools import product

from tablero import SIN_EXPLORAR, NAVE_OCULTA, escribir_celda

Punto = tuple[int, int, int]  # (z, x, y), indices de 1 a N

MAX_INTENTOS_NAVE = 200  # intentos al azar por nave
MAX_REINICIOS = 50       # veces que se reinicia la flota completa si se traba


# --------------------------------------------------------------------------
# Excepciones propias (clase base + subclases)
# --------------------------------------------------------------------------
class ErrorFlota(Exception):
    """Clase base de los errores de este modulo."""


class NaveDesconocida(ErrorFlota):
    """La letra no corresponde a ningun tipo del catalogo."""


class NaveAgotada(ErrorFlota):
    """Ya se ubicaron todas las naves de ese tipo."""


class UbicacionInvalida(ErrorFlota):
    """La ubicacion propuesta no cumple las reglas."""


# --------------------------------------------------------------------------
# Catalogo. Las restricciones son datos (funciones z_valido), sin if/elif.
# --------------------------------------------------------------------------
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
          "z_valido": _z_cualquiera, "evita_caras": False},
    "D": {"nombre": "Destructor", "forma": "linea", "largo": 3, "cantidad": 2,
          "z_valido": _z_cualquiera, "evita_caras": False},
    "S": {"nombre": "Submarino", "forma": "linea", "largo": 3, "cantidad": 2,
          "z_valido": _z_mitad_inferior, "evita_caras": False},
    "C": {"nombre": "Crucero", "forma": "linea", "largo": 4, "cantidad": 1,
          "z_valido": _z_sin_extremos, "evita_caras": False},
    "P": {"nombre": "Portaaviones", "forma": "linea", "largo": 5, "cantidad": 1,
          "z_valido": _z_mitad_superior, "evita_caras": False},
    "E": {"nombre": "Estacion orbital", "forma": "bloque", "largo": 2, "cantidad": 1,
          "z_valido": _z_sin_extremos, "evita_caras": True},
}


def cantidad_celdas(spec: dict) -> int:
    """Recibe la definicion de una nave; devuelve cuantas celdas ocupa."""
    return spec["largo"] ** 3 if spec["forma"] == "bloque" else spec["largo"]


# --------------------------------------------------------------------------
# Geometria basica
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Validacion
# --------------------------------------------------------------------------
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

    # Solapamiento directo (se revisa primero para dar el mensaje correcto).
    choque = set(puntos) & set(puntos_existentes)
    if choque:
        raise UbicacionInvalida(f"La celda {min(choque)} ya esta ocupada.")

    # Separacion: distancia Chebyshev >= 2 con toda celda de otra nave.
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


# --------------------------------------------------------------------------
# Consultas sobre la flota
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Ubicacion manual
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Ubicacion automatica
# --------------------------------------------------------------------------
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
    # Primero las naves grandes: son las que mas cuesta acomodar.
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


if __name__ == "__main__":
    # Demo: ubicacion automatica en N=8 y validacion de la flota resultante.
    from tablero import crear_cubo
    cubo = crear_cubo(8)
    flota = ubicacion_automatica(cubo, CATALOGO, semilla=42)
    for nave in flota:
        print(nave["id"], sorted(nave["celdas"]))
    print(validar_flota([(n["tipo"], list(n["celdas"])) for n in flota], 8))
>>>>>>> 7e18e0a (Modificaciones varias a las funciones. Agregado de ubicar_nave, ubicacion_automatica. Fixes a algunas funciones)
