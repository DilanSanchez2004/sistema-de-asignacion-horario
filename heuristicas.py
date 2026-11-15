"""Heurísticas admisibles para la búsqueda A*."""
from math import inf

from modelo import Estado
from problema import Problema


def h1(problema: Problema, estado: Estado) -> float:
    """Costo base mínimo para asignar las clases que aún están libres."""
    return len(estado.indices_libres()) * problema.costo_base


def h2(problema: Problema, estado: Estado) -> float:
    """h1, o infinito si alguna clase pendiente no tiene valores legales.

    Usa solo la interfaz pública de Problema. valores_legales reconstruye la
    ocupación por llamada, por lo que su costo crece con las clases pendientes.
    """
    libres = estado.indices_libres()
    for indice in libres:
        if not problema.valores_legales(estado, indice):
            return inf
    return len(libres) * problema.costo_base
