from __future__ import annotations

from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple

@dataclass(frozen=True)
class Franja:
    id: str          
    inicio: str      
    fin: str         
    orden: int 
    def __str__(self) -> str:
        return f"{self.inicio}-{self.fin}"

@dataclass(frozen=True)
class Salon:
    id: str

@dataclass(frozen=True)
class Profesor:
    id: str
    nombre: str
    no_disponibles: frozenset = frozenset()


@dataclass(frozen=True)
class Clase:
    id: str
    nombre: str                       
    profesor: Profesor
    grupo: str                       


class Asignacion(NamedTuple):
    dia: str
    franja: Franja
    salon: Salon

    def __str__(self) -> str:
        return f"{self.dia} {self.franja} en {self.salon.id}"


class Operador(NamedTuple):
    indice_clase: int
    asignacion: Asignacion

@dataclass(frozen=True, slots=True)
class Estado:
    asignaciones: Tuple[Optional[Asignacion], ...]

    @staticmethod
    def inicial(n_clases: int) -> "Estado":
        return Estado((None,) * n_clases)

    def asignar(self, indice: int, asignacion: Asignacion) -> "Estado":
        lista = list(self.asignaciones)
        lista[indice] = asignacion
        return Estado(tuple(lista))

    def primera_libre(self) -> Optional[int]:
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
    __slots__ = ("estado", "padre", "operador", "profundidad", "costo")

    def __init__(self, estado: Estado, padre: Optional["Nodo"] = None,
                 operador: Optional[Operador] = None, costo: float = 0.0):
        self.estado = estado
        self.padre = padre
        self.operador = operador
        self.costo = costo
        self.profundidad = 0 if padre is None else padre.profundidad + 1

    def camino(self) -> List[Operador]:
        ops: List[Operador] = []
        n = self
        while n.padre is not None:
            ops.append(n.operador)
            n = n.padre
        ops.reverse()
        return ops
    
@dataclass(frozen=True, slots=True)
class Resultado:
    algoritmo: str
    estado: Optional[Estado]      
    costo: float                  
    nodos_expandidos: int
    nodos_creados: int
    tiempo: float                 
    encontrado: bool
    motivo: str = ""              