"""
busquedas.py
Algoritmos de búsqueda sobre un `Problema`. Todos devuelven un `Resultado`.

En este archivo implementamos: busqueda_amplitud (BFS) y busqueda_costo_uniforme (UCS) 
Quedaria faltand profundidad, profundización iterativa y A*  (agregar abajo y registrarlos en ALGORITMOS)

Cosas de la clase que se respetan:
  - La prueba de meta se hace al EXPANDIR (sacar) un nodo, no al generarlo.
  - Nodos expandidos = nodos sacados de la frontera (incluido el nodo meta).
  - Nodos creados    = nodos metidos en el árbol (incluida la raíz).
  - Al expandir un nodo meta no se crean sus hijos.

Límites: el espacio crece como b^d (b = franjas*salones), así que BFS y UCS
solo terminan en instancias pequeñas. `limite_nodos` y `limite_segundos`
evitan que la interfaz se congele; si se alcanzan, encontrado=False y el
"motivo" lo indica ("limite_nodos" / "limite_tiempo").
"""
from __future__ import annotations

import heapq
import time
from collections import deque
from typing import Callable, Dict, Optional

from modelo import Nodo, Resultado
from problema import Problema

LIMITE_NODOS_DEFECTO = 200_000
LIMITE_SEGUNDOS_DEFECTO = 30.0


def _resultado(nombre: str, nodo: Optional[Nodo], expandidos: int, creados: int,
               t0: float, motivo: str) -> Resultado:
    """Empaqueta el resultado (nodo meta -> solución)."""
    return Resultado(
        algoritmo=nombre,
        estado=nodo.estado if nodo else None,
        costo=nodo.costo if nodo else 0.0,
        nodos_expandidos=expandidos,
        nodos_creados=creados,
        tiempo=time.perf_counter() - t0,
        encontrado=nodo is not None,
        motivo="" if nodo else motivo,
    )


def busqueda_amplitud(problema: Problema,
                      limite_nodos: Optional[int] = LIMITE_NODOS_DEFECTO,
                      limite_segundos: Optional[float] = LIMITE_SEGUNDOS_DEFECTO) -> Resultado:
    """Búsqueda preferente por amplitud (BFS). Frontera: cola FIFO.

    Completa; óptima solo si todos los pasos cuestan lo mismo (aquí las
    penalizaciones blandas rompen eso, así que NO garantiza el mínimo g).
    Complejidad temporal y espacial O(b^d)."""
    nombre = "Amplitud (BFS)"
    t0 = time.perf_counter()
    raiz = Nodo(problema.estado_inicial())
    cola = deque([raiz])
    creados, expandidos = 1, 0

    while cola:
        nodo = cola.popleft()
        expandidos += 1
        if problema.es_meta(nodo.estado):
            return _resultado(nombre, nodo, expandidos, creados, t0, "")
        if limite_nodos is not None and expandidos >= limite_nodos:
            return _resultado(nombre, None, expandidos, creados, t0, "limite_nodos")
        if limite_segundos is not None and time.perf_counter() - t0 > limite_segundos:
            return _resultado(nombre, None, expandidos, creados, t0, "limite_tiempo")
        for s in problema.sucesores(nodo.estado):
            cola.append(Nodo(s.estado, nodo, s.operador, nodo.costo + s.costo))
            creados += 1

    return _resultado(nombre, None, expandidos, creados, t0, "sin_solucion")


def busqueda_costo_uniforme(problema: Problema,
                            limite_nodos: Optional[int] = LIMITE_NODOS_DEFECTO,
                            limite_segundos: Optional[float] = LIMITE_SEGUNDOS_DEFECTO) -> Resultado:
    """Búsqueda de costo uniforme (UCS). Frontera: cola de prioridad por g.

    Siempre expande el nodo de menor g, así que el primer nodo meta que sale
    es el de MENOR costo (menos violaciones blandas). Requiere costos de paso
    > 0 (aquí siempre >= costo_base). Desempates por orden de creación (FIFO)
    para que el resultado sea determinista. Con costos de paso iguales se
    comporta como BFS."""
    nombre = "Costo uniforme"
    t0 = time.perf_counter()
    raiz = Nodo(problema.estado_inicial())
    contador = 0                                   # desempate estable en el heap
    frontera = [(0.0, contador, raiz)]
    creados, expandidos = 1, 0

    while frontera:
        _, _, nodo = heapq.heappop(frontera)
        expandidos += 1
        if problema.es_meta(nodo.estado):
            return _resultado(nombre, nodo, expandidos, creados, t0, "")
        if limite_nodos is not None and expandidos >= limite_nodos:
            return _resultado(nombre, None, expandidos, creados, t0, "limite_nodos")
        if limite_segundos is not None and time.perf_counter() - t0 > limite_segundos:
            return _resultado(nombre, None, expandidos, creados, t0, "limite_tiempo")
        for s in problema.sucesores(nodo.estado):
            hijo = Nodo(s.estado, nodo, s.operador, nodo.costo + s.costo)
            contador += 1
            heapq.heappush(frontera, (hijo.costo, contador, hijo))
            creados += 1

    return _resultado(nombre, None, expandidos, creados, t0, "sin_solucion")


# Registro para la GUI (esto lo hace la persona C): nombre mostrado en el combobox -> función.
# Para la persona B: agregue aquí DFS, profundización iterativa y A*.
ALGORITMOS: Dict[str, Callable[..., Resultado]] = {
    "Amplitud (BFS)": busqueda_amplitud,
    "Costo uniforme": busqueda_costo_uniforme,
}