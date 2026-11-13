"""
problema.py
Formulación del problema bien definido (estados, operadores, prueba de meta y
función de costo). Es la unica interfaz que usan los algoritmos de búsqueda:

    p.estado_inicial()                      -> Estado raíz
    p.es_meta(estado)                       -> bool
    p.sucesores(estado, indice_clase=None)  -> lista de Sucesor (solo legales)
    p.valores_legales(estado, indice_clase) -> dominio restante de una variable (útil para MRV)
    p.costo_total(estado)                   -> g de un estado completo
    p.horario(estado)                       -> [(Clase, Asignacion)] para la GUI

Función de costo g
Cada asignación cuesta `costo_base` (1) + la penalización de restricciones
blandas que genera. Así g(solución) = n_clases*costo_base + penalización total:
con costo uniforme se obtiene el horario con MENOS violaciones blandas, y con
BFS (que ignora el costo) simplemente el primero que encuentra.

Orden de las variables
Por defecto se asigna siempre la primera clase libre (orden fijo). Así cada
estado se alcanza por un único camino (no hay estados repetidos ni permutaciones
equivalentes). Si B quiere MRV, pasa `indice_clase` a sucesores().
"""
from __future__ import annotations

from typing import List, NamedTuple, Optional, Tuple

from modelo import Asignacion, Clase, Estado, Franja, Operador, Salon
from restricciones import Restricciones


class Sucesor(NamedTuple):
    operador: Operador
    estado: Estado
    costo: float # costo de ESTE paso (no acumulado)


class Problema:
    def __init__(self, clases: List[Clase], dias: List[str], franjas: List[Franja],
                 salones: List[Salon],
                 max_consecutivas: Optional[int] = None,
                 peso_no_disponible: float = 5.0, peso_consecutivas: float = 3.0,
                 usar_blandas: bool = True, costo_base: float = 1.0):
        if not clases:
            raise ValueError("No hay clases por programar")
        if not dias or not franjas or not salones:
            raise ValueError("Se necesita al menos un día, una franja y un salón")
        self.clases = clases
        self.dias = dias
        self.franjas = franjas
        self.salones = salones
        self.costo_base = costo_base
        self.restricciones = Restricciones(clases, max_consecutivas, peso_no_disponible, peso_consecutivas, usar_blandas)
        # Dominio de cada variable: todas las tripletas (día, franja, salón).
        # Tamaño = len(dias) * len(franjas) * len(salones) = factor de ramificación b.
        # Todas las clases tienen el mismo dominio; se guarda una lista por clase para que cada variable tenga su propio dominio.
        self.dominios: List[List[Asignacion]] = [
            [Asignacion(d, f, s) for d in dias for f in franjas for s in salones]
            for _ in clases
        ]

    # Elementos del problema bien definido
    def estado_inicial(self) -> Estado:
        return Estado.inicial(len(self.clases))

    def es_meta(self, estado: Estado) -> bool:
        """Meta: todas las clases asignadas. Las duras ya se garantizaron al generar cada sucesor (solo se crean asignaciones legales)."""
        return estado.es_completo()

    def sucesores(self, estado: Estado, indice_clase: Optional[int] = None) -> List[Sucesor]:
        """Aplica todos los operadores legales sobre `indice_clase` (por defecto, la primera clase sin asignar)."""
        if indice_clase is None:
            indice_clase = estado.primera_libre()
            if indice_clase is None:
                return []                      # estado completo: nada que expandir
        elif estado.asignaciones[indice_clase] is not None:
            raise ValueError(f"La clase {indice_clase} ya está asignada")
        r = self.restricciones
        oc = r.construir_ocupacion(estado)     # se calcula una vez por expansión
        resultado: List[Sucesor] = []
        for a in self.dominios[indice_clase]:
            if r.viola_duras(oc, indice_clase, a):
                continue
            costo = self.costo_base + r.penalizacion_paso(oc, indice_clase, a)
            resultado.append(Sucesor(Operador(indice_clase, a), estado.asignar(indice_clase, a), costo))
        return resultado

    def valores_legales(self, estado: Estado, indice_clase: int) -> List[Asignacion]:
        """Valores del dominio que aún no violan restricciones duras (para MRV)."""
        r = self.restricciones
        oc = r.construir_ocupacion(estado)
        return [a for a in self.dominios[indice_clase]
                if not r.viola_duras(oc, indice_clase, a)]

    # Costos y presentación
    def costo_total(self, estado: Estado) -> float:
        """g de un estado: costo_base por cada clase asignada + penalizaciones."""
        return (self.costo_base * estado.num_asignadas
                + self.restricciones.penalizacion_total(estado))

    def horario(self, estado: Estado) -> List[Tuple[Clase, Asignacion]]:
        """Pares (clase, asignación) de las clases ya asignadas, para la GUI."""
        return [(self.clases[i], a) for i, a in enumerate(estado.asignaciones)
                if a is not None]