"""
restricciones.py  
Restricciones DURAS (no pueden violarse) y BLANDAS (se penalizan en el costo).

Restricciones duras
  1. Un salón no puede tener dos clases en la misma franja.
  2. Un profesor no puede dictar dos clases en la misma franja.
  3. Un grupo no puede tener dos clases en la misma franja.
  4. Cada clase se asigna exactamente una vez (lo garantiza la estructura del
     Estado: una posición por clase; se revisa en verificar_completo).

Restricciones blandas (suman penalización al costo del paso)
  a. Profesor en una franja que marcó como no disponible.
  b. Grupo con más de N clases consecutivas el mismo día.

"Misma franja" significa mismo día Y misma franja horaria.

Para que cada expansión sea barata, antes de generar sucesores se construye UNA
vez una `Ocupacion` (índices en conjuntos) y luego cada candidato se prueba en O(1).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from modelo import Asignacion, Clase, Estado


class Ocupacion:
    """Índices de lo que ya está ocupado en un estado parcial."""
    __slots__ = ("salones", "profesores", "grupos", "ordenes")

    def __init__(self) -> None:
        self.salones: Set[Tuple[str, str, str]] = set()     # (dia, id_franja, id_salon)
        self.profesores: Set[Tuple[str, str, str]] = set()  # (dia, id_franja, id_profesor)
        self.grupos: Set[Tuple[str, str, str]] = set()      # (dia, id_franja, grupo)
        # (grupo, dia) son las órdenes de franja ocupadas, para contar consecutivas
        self.ordenes: Dict[Tuple[str, str], Set[int]] = {}


def exceso_consecutivas(ordenes: Set[int], n: int) -> int:
    """Cuántas clases sobrepasan el límite n dentro de cada racha de franjas
    consecutivas. Ej.: órdenes {0,1,2,3}, n=2 -> racha de 4 -> exceso 2."""
    exceso = 0
    racha = 0
    previo: Optional[int] = None
    for o in sorted(ordenes):
        racha = racha + 1 if previo is not None and o == previo + 1 else 1
        if racha > n:
            exceso += 1
        previo = o
    return exceso


class Restricciones:
    def __init__(self, clases: List[Clase], max_consecutivas: Optional[int] = None,
                 peso_no_disponible: float = 5.0, peso_consecutivas: float = 3.0,
                 usar_blandas: bool = True):
        self.clases = clases
        self.max_consecutivas = max_consecutivas
        self.peso_no_disponible = peso_no_disponible
        self.peso_consecutivas = peso_consecutivas
        self.usar_blandas = usar_blandas

    # Índice de ocupación
    def construir_ocupacion(self, estado: Estado) -> Ocupacion:
        oc = Ocupacion()
        for i, a in enumerate(estado.asignaciones):
            if a is None:
                continue
            c = self.clases[i]
            oc.salones.add((a.dia, a.franja.id, a.salon.id))
            oc.profesores.add((a.dia, a.franja.id, c.profesor.id))
            oc.grupos.add((a.dia, a.franja.id, c.grupo))
            oc.ordenes.setdefault((c.grupo, a.dia), set()).add(a.franja.orden)
        return oc

    # Duras
    def viola_duras(self, oc: Ocupacion, indice: int, a: Asignacion) -> bool:
        """True si asignar clases[indice] a `a` rompe alguna restricción dura."""
        c = self.clases[indice]
        d, f = a.dia, a.franja.id
        return ((d, f, a.salon.id) in oc.salones
                or (d, f, c.profesor.id) in oc.profesores
                or (d, f, c.grupo) in oc.grupos)

    def cumple_duras(self, estado: Estado, indice: int, a: Asignacion) -> bool:
        """Versión de conveniencia (construye la ocupación en cada llamada)."""
        return not self.viola_duras(self.construir_ocupacion(estado), indice, a)

    # Blandas
    def penalizacion_paso(self, oc: Ocupacion, indice: int, a: Asignacion) -> float:
        """Penalización que AÑADE asignar clases[indice] a `a` (delta)."""
        if not self.usar_blandas:
            return 0.0
        c = self.clases[indice]
        p = 0.0
        if (a.dia, a.franja.id) in c.profesor.no_disponibles:
            p += self.peso_no_disponible
        if self.max_consecutivas is not None:
            antes = oc.ordenes.get((c.grupo, a.dia), set())
            delta = (exceso_consecutivas(antes | {a.franja.orden}, self.max_consecutivas)
                     - exceso_consecutivas(antes, self.max_consecutivas))
            p += self.peso_consecutivas * delta
        return p

    def penalizacion_total(self, estado: Estado) -> float:
        """Penalización de un estado completo, calculada desde cero.
        Coincide con la suma de las penalizaciones de paso a lo largo del camino."""
        if not self.usar_blandas:
            return 0.0
        total = 0.0
        for i, a in enumerate(estado.asignaciones):
            if a is not None and (a.dia, a.franja.id) in self.clases[i].profesor.no_disponibles:
                total += self.peso_no_disponible
        if self.max_consecutivas is not None:
            oc = self.construir_ocupacion(estado)
            for ordenes in oc.ordenes.values():
                total += self.peso_consecutivas * exceso_consecutivas(ordenes, self.max_consecutivas)
        return total

    def detalle_blandas(self, estado: Estado) -> List[str]:
        """Lista legible de violaciones blandas (para el informe/GUI)."""
        det: List[str] = []
        for i, a in enumerate(estado.asignaciones):
            if a is not None and (a.dia, a.franja.id) in self.clases[i].profesor.no_disponibles:
                det.append(f"{self.clases[i].profesor.nombre} dicta {self.clases[i].nombre} "
                           f"el {a.dia} {a.franja} (no disponible)")
        if self.max_consecutivas is not None:
            oc = self.construir_ocupacion(estado)
            for (grupo, dia), ordenes in sorted(oc.ordenes.items()):
                e = exceso_consecutivas(ordenes, self.max_consecutivas)
                if e:
                    det.append(f"Grupo {grupo}: {e} clase(s) por encima de "
                               f"{self.max_consecutivas} consecutivas el {dia}")
        return det

    # Verificación independiente ( esto nos sirve para probar los algoritmos)
    def verificar_completo(self, estado: Estado) -> List[str]:
        """Revisa TODAS las restricciones duras sobre un estado completo.
        Devuelve la lista de violaciones (vacía = horario válido).
        No depende de la generación de sucesores, por eso sirve para auditarla."""
        errores: List[str] = []
        n = len(self.clases)
        if len(estado.asignaciones) != n:
            return [f"el estado tiene {len(estado.asignaciones)} posiciones y hay {n} clases"]
        for i, a in enumerate(estado.asignaciones):
            if a is None:
                errores.append(f"la clase {self.clases[i].id} no está asignada")
        for i in range(n):
            for j in range(i + 1, n):
                a, b = estado.asignaciones[i], estado.asignaciones[j]
                if a is None or b is None or a.dia != b.dia or a.franja.id != b.franja.id:
                    continue
                ci, cj = self.clases[i], self.clases[j]
                cuando = f"{a.dia} {a.franja}"
                if a.salon.id == b.salon.id:
                    errores.append(f"salón {a.salon.id} repetido el {cuando}: {ci.id} y {cj.id}")
                if ci.profesor.id == cj.profesor.id:
                    errores.append(f"profesor {ci.profesor.nombre} repetido el {cuando}: {ci.id} y {cj.id}")
                if ci.grupo == cj.grupo:
                    errores.append(f"grupo {ci.grupo} repetido el {cuando}: {ci.id} y {cj.id}")
        return errores