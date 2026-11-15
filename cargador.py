from __future__ import annotations

from typing import Dict, List, Tuple

from modelo import Clase, Franja, Profesor, Salon


def _filas(ruta: str) -> List[List[str]]:
    """[CLAVE 1] Lector genérico: lo usan las cuatro funciones de abajo.
    - Abre el archivo en UTF-8 (para tildes y ñ).
    - Quita espacios de cada línea con strip().
    - Descarta líneas vacías y comentarios (las que empiezan con '#').
    - Parte cada línea por comas y limpia cada pedazo.
    Resultado: una lista de listas, p. ej. [["P1", "Prof_A", "Lunes:F1"], ...]"""
    with open(ruta, encoding="utf-8") as f:
        lineas = [l.strip() for l in f]
    return [[c.strip() for c in l.split(",")] for l in lineas if l and not l.startswith("#")]


def leer_profesores(ruta: str) -> Dict[str, Profesor]:
    """[CLAVE 2] Devuelve un DICCIONARIO {id_profesor: Profesor}.
    Es diccionario (no lista) porque cursos.txt referencia al profesor por id y
    así se busca en O(1) en construir_clases."""
    profesores: Dict[str, Profesor] = {}
    # enumerate(..., 1) numera desde 1 para poder decir "registro n" si hay error
    for n, fila in enumerate(_filas(ruta), 1):
        if len(fila) < 2:
            # [CLAVE 3] Validación: lanzar ValueError con un mensaje claro. La
            # interfaz lo atrapa y lo muestra junto al botón como "✖ error: ..."
            raise ValueError(f"profesores.txt, registro {n}: se esperaba id,nombre[,no_disponibles]")
        no_disp = set()
        if len(fila) > 2 and fila[2]:
            # [CLAVE 4] Restricción: "Lunes:F1;Martes:F2" se parte primero
            # por ';' (cada franja) y luego por ':' (día y id de franja).
            # Se guarda como pares (dia, id_franja), que es lo que espera
            # restricciones.py en Profesor.no_disponibles.
            for par in fila[2].split(";"):
                dia, franja = par.split(":")        # "Lunes:F1" -> ("Lunes", "F1")
                no_disp.add((dia.strip(), franja.strip()))
        # frozenset porque Profesor es un dataclass inmutable (frozen=True)
        profesores[fila[0]] = Profesor(fila[0], fila[1], frozenset(no_disp))
    return profesores


def leer_cursos(ruta: str) -> List[Tuple[str, str, str, str]]:
    """[CLAVE 5] Devuelve tuplas (id, nombre, id_profesor, grupo), NO objetos Clase.
    Razón: para crear una Clase hace falta el objeto Profesor, que viene de otro
    archivo. Así el usuario puede cargar cursos.txt antes que profesores.txt;
    la unión se hace después en construir_clases."""
    cursos = []
    for n, fila in enumerate(_filas(ruta), 1):
        if len(fila) != 4:
            raise ValueError(f"cursos.txt, registro {n}: se esperaba id,nombre,id_profesor,grupo")
        cursos.append((fila[0], fila[1], fila[2], fila[3]))
    return cursos


def leer_salones(ruta: str) -> List[Salon]:
    """Un Salon por línea; solo importa el id (primera columna)."""
    return [Salon(fila[0]) for fila in _filas(ruta)]


def leer_franjas(ruta: str) -> List[Franja]:
    """[CLAVE 6] El campo `orden` de cada Franja es la posición de la línea en el
    archivo (0, 1, 2...). Por eso franjas.txt debe estar ordenado de la más
    temprana a la más tarde: restricciones.py usa `orden` para detectar clases
    consecutivas (dos franjas son consecutivas si sus órdenes difieren en 1)."""
    franjas = []
    for orden, fila in enumerate(_filas(ruta)):
        if len(fila) != 3:
            raise ValueError(f"franjas.txt, registro {orden + 1}: se esperaba id,inicio,fin")
        franjas.append(Franja(fila[0], fila[1], fila[2], orden))
    return franjas


def construir_clases(cursos, profesores: Dict[str, Profesor]) -> List[Clase]:
    """[CLAVE 7] Une cursos + profesores y crea las Clase (las VARIABLES del CSP).
    Se llama justo antes de crear el Problema, cuando ya están los dos archivos.
    Si un curso nombra un profesor que no existe, se avisa con un error claro."""
    clases = []
    for id_, nombre, id_prof, grupo in cursos:
        if id_prof not in profesores:
            raise ValueError(f"El curso {id_} usa el profesor '{id_prof}', que no está en profesores.txt")
        clases.append(Clase(id_, nombre, profesores[id_prof], grupo))
    return clases


# [CLAVE 8] Tabla "clave del archivo -> función lectora". La interfaz la usa para
# no repetir código: un solo método _examinar sirve para los cuatro botones.
LECTORES = {
    "profesores": leer_profesores,
    "cursos": leer_cursos,
    "salones": leer_salones,
    "franjas": leer_franjas,
}
