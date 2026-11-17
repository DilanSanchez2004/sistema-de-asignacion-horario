from math import inf

from modelo import Estado
from problema import Problema


def h1(problema: Problema, estado: Estado) -> float:
    return len(estado.indices_libres()) * problema.costo_base


def h2(problema: Problema, estado: Estado) -> float:
    libres = estado.indices_libres()
    for indice in libres:
        if not problema.valores_legales(estado, indice):
            return inf
    return len(libres) * problema.costo_base
