"""
modelo.py
Clases de datos del problema de asignación de horarios y del árbol de búsqueda.

Todo es INMUTABLE y hashable (dataclass frozen / NamedTuple) para que los
estados puedan compararse, guardarse en conjuntos y no se modifiquen por error
al compartirse entre nodos del árbol

Representación del estado 
Variables : una por cada clase (Clase)
Dominio   : conjunto de tripletas (día, franja_horaria, salón) Ej.: ("Lunes", 07:00-09:00, Salon_101)
Estado    : tupla de longitud n (n = número de clases). La posición i guarda la
            Asignacion (día, franja, salón) de la clase i, o None si aún no se
            ha asignado.
Estado inicial : todo None.   
Meta : ninguna posición es None (y, como solo se generan sucesores legales, además se cumplen las restricciones duras).
Operador  : asignar una clase aún sin asignar a una tripleta (día, franja, salón).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple

# Datos de entrada (Esto lo llena el cargador de la Persona C)
@dataclass(frozen=True)
class Franja:
    """Una franja horaria (solo la hora, sin día), p. ej. 07:00-09:00.
    La misma franja existe en todos los días; el día va aparte en la Asignacion."""
    id: str          # identificador único, p. ej. "F1"
    inicio: str      # "07:00"
    fin: str         # "09:00"
    orden: int       # posición en el día (0, 1, 2, ...). Dos franjas son consecutivas si sus órdenes difieren en 1.

    def __str__(self) -> str:
        return f"{self.inicio}-{self.fin}"

@dataclass(frozen=True)
class Salon:
    id: str

@dataclass(frozen=True)
class Profesor:
    id: str
    nombre: str
    # pares (dia, id_franja) que marcó como NO disponibles (restricción blanda),
    # p. ej. frozenset({("Lunes", "F1"), ("Martes", "F1")})
    no_disponibles: frozenset = frozenset()


@dataclass(frozen=True)
class Clase:
    """Una sesión que debe programarse exactamente una vez.

    Si un curso tiene varias sesiones semanales, el cargador debe crear varias
    Clase (p. ej. "Calculo-1", "Calculo-2"); el núcleo las trata como
    variables independientes.
    """
    id: str
    nombre: str                       # nombre de la materia
    profesor: Profesor
    grupo: str                        # grupo de estudiantes

# Estado y operadores
class Asignacion(NamedTuple):
    """Valor del dominio: la tripleta (día, franja_horaria, salón)."""
    dia: str
    franja: Franja
    salon: Salon

    def __str__(self) -> str:
        return f"{self.dia} {self.franja} en {self.salon.id}"


class Operador(NamedTuple):
    """Acción: asignar la clase `indice_clase` a la tripleta `asignacion`."""
    indice_clase: int
    asignacion: Asignacion

@dataclass(frozen=True)
class Estado:
    """Asignación parcial o completa. asignaciones[i] corresponde a clases[i]."""
    asignaciones: Tuple[Optional[Asignacion], ...]

    @staticmethod
    def inicial(n_clases: int) -> "Estado":
        return Estado((None,) * n_clases)

    def asignar(self, indice: int, asignacion: Asignacion) -> "Estado":
        """Devuelve un NUEVO estado con la clase `indice` asignada."""
        lista = list(self.asignaciones)
        lista[indice] = asignacion
        return Estado(tuple(lista))

    def primera_libre(self) -> Optional[int]:
        """Índice de la primera clase sin asignar (None si ya están todas)."""
        for i, a in enumerate(self.asignaciones):
            if a is None:
                return i
        return None

    def indices_libres(self) -> List[int]:
        return [i for i, a in enumerate(self.asignaciones) if a is None]

    @property
    def num_asignadas(self) -> int:
        return sum(1 for a in self.asignaciones if a is not None)

    def es_completo(self) -> bool:
        return all(a is not None for a in self.asignaciones)

# Árbol de búsqueda
class Nodo:
    """Nodo del árbol de búsqueda: estado, padre, operador aplicado, profundidad y costo g desde la raíz."""
    __slots__ = ("estado", "padre", "operador", "profundidad", "costo")

    def __init__(self, estado: Estado, padre: Optional["Nodo"] = None,
                 operador: Optional[Operador] = None, costo: float = 0.0):
        self.estado = estado
        self.padre = padre
        self.operador = operador
        self.costo = costo
        self.profundidad = 0 if padre is None else padre.profundidad + 1

    def camino(self) -> List[Operador]:
        """Secuencia de operadores desde la raíz hasta este nodo."""
        ops: List[Operador] = []
        n = self
        while n.padre is not None:
            ops.append(n.operador)
            n = n.padre
        ops.reverse()
        return ops
    
@dataclass
class Resultado:
    """Lo que devuelve cualquier algoritmo de búsqueda (lo usa la GUI/estadísticas)."""
    algoritmo: str
    estado: Optional[Estado]      # solución encontrada o None
    costo: float                  # g de la solución (0 si no hay)
    nodos_expandidos: int
    nodos_creados: int
    tiempo: float                 # segundos
    encontrado: bool
    motivo: str = ""              # "", "sin_solucion", "limite_nodos", "limite_tiempo"