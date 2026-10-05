# Operación Cubo

Batalla naval en 3D por consola.
Trabajo Práctico Integrador de Programación 1 / Algoritmo y Estructura de Datos 1.

## Integrantes

- Austin Zacarias Stelli- 1231965
- Bisanzio Geronimo - 1244258
- Juan Ignacio Chedufau Moleon - 1242733
- Rafael Lepage - 1181469
## Requisitos

- Python 3.10 o superior
- Dependencias listadas en requirements.txt

## Instalación

```
pip install -r requirements.txt
```

La única dependencia es pytest, y solo hace falta para correr las pruebas.

## Ejecución

Desde la carpeta del proyecto:

```
python partida.py
```

Para correr las pruebas unitarias:

```
python -m pytest
```

## Menús

### Menú principal

```
===== OPERACION CUBO =====
1 - Partida uno contra uno
2 - Partida uno contra la maquina
3 - Partida maquina contra maquina
4 - Continuar una partida guardada
5 - Salir
```

En la Entrega 1 funcionan las opciones 1 y 5. La opción 1 crea la partida y
hace que cada jugador ubique su flota. Las opciones 2, 3 y 4 avisan que
todavía no están disponibles.

### Submenú de ubicación

```
--- Flota de Jugador 1 ---
1 - Ubicacion manual
2 - Ubicacion automatica
3 - Ver el cubo
4 - Continuar
```

- **Ubicación manual:** muestra las naves pendientes, pide la letra de la nave
  (F/D/S/C/P/E) y el tramo con los dos extremos unidos por un guión, por
  ejemplo `3,5,4-3,5,5`. Los puntos se escriben en el orden z, x, y. Para la
  estación orbital se indican dos esquinas opuestas del bloque. Con `0` se
  vuelve al submenú.
- **Ubicación automática:** ubica la flota completa al azar respetando las
  mismas reglas. Si ya había naves ubicadas, las reemplaza.
- **Ver el cubo:** dibuja una capa de z, o todas con `0`.
- **Continuar:** pasa al siguiente jugador. Solo se puede con la flota completa.

Un dato inválido nunca corta el programa: se avisa y se vuelve a preguntar.
