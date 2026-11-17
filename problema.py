from __future__ import annotations

from typing import List, NamedTuple, Optional, Tuple

from modelo import Asignacion, Clase, Estado, Franja, Operador, Salon
from restricciones import Restricciones


class Sucesor(NamedTuple):
    operador: Operador
    estado: Estado
    costo: float 


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
        self.dominios: List[List[Asignacion]] = [
            [Asignacion(d, f, s) for d in dias for f in franjas for s in salones]
            for _ in clases
        ]

    def estado_inicial(self) -> Estado:
        return Estado.inicial(len(self.clases))

    def es_meta(self, estado: Estado) -> bool:
        return estado.es_completo()

    def sucesores(self, estado: Estado, indice_clase: Optional[int] = None) -> List[Sucesor]:
        if indice_clase is None:
            indice_clase = estado.primera_libre()
            if indice_clase is None:
                return []                      
        elif estado.asignaciones[indice_clase] is not None:
            raise ValueError(f"La clase {indice_clase} ya está asignada")
        r = self.restricciones
        oc = r.construir_ocupacion(estado)     
        resultado: List[Sucesor] = []
        for a in self.dominios[indice_clase]:
            if r.viola_duras(oc, indice_clase, a):
                continue
            costo = self.costo_base + r.penalizacion_paso(oc, indice_clase, a)
            resultado.append(Sucesor(Operador(indice_clase, a), estado.asignar(indice_clase, a), costo))
        return resultado

    def valores_legales(self, estado: Estado, indice_clase: int) -> List[Asignacion]:
        r = self.restricciones
        oc = r.construir_ocupacion(estado)
        return [a for a in self.dominios[indice_clase]
                if not r.viola_duras(oc, indice_clase, a)]

    def costo_total(self, estado: Estado) -> float:
        return (self.costo_base * estado.num_asignadas
                + self.restricciones.penalizacion_total(estado))

    def horario(self, estado: Estado) -> List[Tuple[Clase, Asignacion]]:
        
        return [(self.clases[i], a) for i, a in enumerate(estado.asignaciones)
                if a is not None]