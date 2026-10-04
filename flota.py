"""
flota.py

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