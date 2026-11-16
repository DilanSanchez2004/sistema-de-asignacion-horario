from __future__ import annotations

from typing import Dict, List, Tuple

from modelo import Clase, Franja, Profesor, Salon


def _filas(ruta: str) -> List[List[str]]:
   
    with open(ruta, encoding="utf-8") as f:
        lineas = [l.strip() for l in f]
    return [[c.strip() for c in l.split(",")] for l in lineas if l and not l.startswith("#")]


def leer_profesores(ruta: str) -> Dict[str, Profesor]:
    
    profesores: Dict[str, Profesor] = {}
  
    for n, fila in enumerate(_filas(ruta), 1):
        if len(fila) < 2:
            raise ValueError(f"profesores.txt, registro {n}: se esperaba id,nombre[,no_disponibles]")
        no_disp = set()
        if len(fila) > 2 and fila[2]:
            for par in fila[2].split(";"):
                dia, franja = par.split(":")        
                no_disp.add((dia.strip(), franja.strip()))
       
        profesores[fila[0]] = Profesor(fila[0], fila[1], frozenset(no_disp))
    return profesores


def leer_cursos(ruta: str) -> List[Tuple[str, str, str, str]]:
   
    cursos = []
    for n, fila in enumerate(_filas(ruta), 1):
        if len(fila) != 4:
            raise ValueError(f"cursos.txt, registro {n}: se esperaba id,nombre,id_profesor,grupo")
        cursos.append((fila[0], fila[1], fila[2], fila[3]))
    return cursos


def leer_salones(ruta: str) -> List[Salon]:
    
    return [Salon(fila[0]) for fila in _filas(ruta)]


def leer_franjas(ruta: str) -> List[Franja]:
    
    franjas = []
    for orden, fila in enumerate(_filas(ruta)):
        if len(fila) != 3:
            raise ValueError(f"franjas.txt, registro {orden + 1}: se esperaba id,inicio,fin")
        franjas.append(Franja(fila[0], fila[1], fila[2], orden))
    return franjas


def construir_clases(cursos, profesores: Dict[str, Profesor]) -> List[Clase]:
   
    clases = []
    for id_, nombre, id_prof, grupo in cursos:
        if id_prof not in profesores:
            raise ValueError(f"El curso {id_} usa el profesor '{id_prof}', que no está en profesores.txt")
        clases.append(Clase(id_, nombre, profesores[id_prof], grupo))
    return clases


LECTORES = {
    "profesores": leer_profesores,
    "cursos": leer_cursos,
    "salones": leer_salones,
    "franjas": leer_franjas,
}
