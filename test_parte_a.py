"""Pruebas del núcleo y de BFS/UCS. 
Ejecutar: python3 test_parte_a.py
"""
import itertools
import unittest
from unittest import mock

from modelo import Clase, Estado, Franja, Profesor, Salon
from problema import Problema
from busquedas import (
    ALGORITMOS,
    busqueda_amplitud,
    busqueda_a_estrella_h1,
    busqueda_a_estrella_h2,
    busqueda_costo_uniforme,
    busqueda_profundidad_interativa,
)
from heuristicas import h1, h2


def franjas(n=3):
    return [Franja(f"F{k}", f"{7+2*k:02d}:00", f"{9+2*k:02d}:00", k) for k in range(n)]


def instancia(no_disp=frozenset(), max_consec=None, nfr=3, ndias=2):
    pA = Profesor("PA", "Prof_A", frozenset(no_disp))
    pB = Profesor("PB", "Prof_B")
    clases = [Clase("c1", "Calculo", pA, "G1"), Clase("c2", "Algebra", pA, "G2"),
              Clase("c3", "Fisica", pB, "G1"), Clase("c4", "Quimica", pB, "G2")]
    dias = ["Lunes", "Martes", "Miercoles"][:ndias]
    return Problema(clases, dias, franjas(nfr), [Salon("S1"), Salon("S2")],
                    max_consecutivas=max_consec)


class TestNucleo(unittest.TestCase):
    def test_estado_inicial_y_sucesores_legales(self):
        p = instancia()
        s0 = p.estado_inicial()
        self.assertFalse(p.es_meta(s0))
        suc = p.sucesores(s0)
        self.assertEqual(len(suc), 2 * 3 * 2)      # 2 días x 3 franjas x 2 salones
        for s in suc:
            self.assertEqual(s.estado.num_asignadas, 1)
            self.assertEqual(s.costo, 1.0)

    def test_no_se_generan_conflictos(self):
        p = instancia()
        e = p.estado_inicial()
        primero = p.sucesores(e)[0]                
        e1 = primero.estado
        a1 = primero.operador.asignacion
        for s in p.sucesores(e1):
            a = s.operador.asignacion
            self.assertFalse(a.dia == a1.dia and a.franja == a1.franja)
        self.assertTrue(any(s.operador.asignacion.franja == a1.franja
                            and s.operador.asignacion.dia != a1.dia
                            for s in p.sucesores(e1)))

    def test_valores_legales_y_variable_dinamica(self):
        p = instancia()
        e = p.sucesores(p.estado_inicial())[0].estado
        self.assertLess(len(p.valores_legales(e, 1)), len(p.dominios[1]))
        suc = p.sucesores(e, indice_clase=3)       
        self.assertTrue(all(s.operador.indice_clase == 3 for s in suc))


class TestBusquedas(unittest.TestCase):
    def test_bfs_y_ucs_encuentran_horario_valido(self):
        p = instancia()
        for alg in (busqueda_amplitud, busqueda_costo_uniforme, busqueda_profundidad_interativa):
            r = alg(p)
            self.assertTrue(r.encontrado, r.algoritmo)
            self.assertEqual(p.restricciones.verificar_completo(r.estado), [])
            self.assertGreater(r.nodos_expandidos, 0)
            self.assertGreaterEqual(r.nodos_creados, r.nodos_expandidos)

    def test_bfs_expande_por_niveles(self):
        pA = Profesor("PA", "A")
        p = Problema([Clase("c", "X", pA, "G")], ["Lunes", "Martes"], franjas(), [Salon("S1")])
        r = busqueda_amplitud(p)
        self.assertEqual(r.nodos_expandidos, 2)    
        self.assertEqual(r.nodos_creados, 7)       
        
    def test_sin_solucion(self):
        pA = Profesor("PA", "A")
        p = Problema([Clase("a", "X", pA, "G1"), Clase("b", "Y", pA, "G2")],
                     ["Lunes"], [Franja("F0", "07:00", "09:00", 0)], [Salon("S1"), Salon("S2")])
        for alg in (busqueda_amplitud, busqueda_costo_uniforme, busqueda_profundidad_interativa):
            r = alg(p)
            self.assertFalse(r.encontrado)
            self.assertEqual(r.motivo, "sin_solucion")

    def test_iddfs_respeta_limite_nodos_dentro_de_una_iteracion(self):
        pA = Profesor("PA", "A")
        p = Problema([Clase("a", "X", pA, "G1"), Clase("b", "Y", pA, "G2")],
                     ["Lunes"], [Franja("F0", "07:00", "09:00", 0)], [Salon("S1"), Salon("S2")])
        r = busqueda_profundidad_interativa(p, limite_nodos=3)
        self.assertFalse(r.encontrado)
        self.assertEqual(r.motivo, "limite_nodos")
        self.assertEqual(r.nodos_expandidos, 3)

    def test_iddfs_detecta_agotamiento_al_llegar_al_limite_de_nodos(self):
        pA = Profesor("PA", "A")
        p = Problema([Clase("a", "X", pA, "G1"), Clase("b", "Y", pA, "G2")],
                     ["Lunes"], [Franja("F0", "07:00", "09:00", 0)], [Salon("S1"), Salon("S2")])
        sin_limite = busqueda_profundidad_interativa(p, limite_nodos=None, limite_segundos=None)
        r = busqueda_profundidad_interativa(
            p, limite_nodos=sin_limite.nodos_expandidos, limite_segundos=None
        )
        self.assertFalse(r.encontrado)
        self.assertEqual(r.motivo, "sin_solucion")
        self.assertEqual(r.nodos_expandidos, sin_limite.nodos_expandidos)

    def test_iddfs_respeta_limite_tiempo_durante_una_iteracion(self):
        p = instancia()
        with mock.patch("busquedas.time.perf_counter", side_effect=[0, 0, 0, 1, 1]):
            r = busqueda_profundidad_interativa(p, limite_nodos=None, limite_segundos=0.5)
        self.assertFalse(r.encontrado)
        self.assertEqual(r.motivo, "limite_tiempo")
        self.assertEqual(r.nodos_expandidos, 1)

    def test_limite_de_nodos(self):
        r = busqueda_amplitud(instancia(), limite_nodos=3)
        self.assertFalse(r.encontrado)
        self.assertEqual(r.motivo, "limite_nodos")

    def test_ucs_optimo_blandas_no_disponible(self):
        # Prof_A no puede en las dos primeras franjas de cada día: UCS debe evitarlas
        nd = {("Lunes", "F0"), ("Lunes", "F1"), ("Martes", "F0"), ("Martes", "F1")}
        p = instancia(no_disp=nd)
        r = busqueda_costo_uniforme(p)
        self.assertEqual(p.restricciones.penalizacion_total(r.estado), 0.0)
        self.assertEqual(r.costo, p.costo_total(r.estado))
        self.assertEqual(r.costo, 4.0)

    def test_ucs_menor_o_igual_que_bfs(self):
        p = instancia(no_disp={("Lunes", "F0"), ("Lunes", "F1"), ("Martes", "F0")}, max_consec=1)
        rb, ru = busqueda_amplitud(p), busqueda_costo_uniforme(p)
        self.assertLessEqual(ru.costo, rb.costo)

    def test_ucs_es_el_minimo_global_por_fuerza_bruta(self):
        p = instancia(no_disp={("Lunes", "F0"), ("Lunes", "F2")}, max_consec=2, nfr=3, ndias=1)
        dominios = p.dominios
        mejor = None
        for combo in itertools.product(*dominios):
            e = Estado(tuple(combo))
            if p.restricciones.verificar_completo(e):
                continue
            c = p.costo_total(e)
            mejor = c if mejor is None or c < mejor else mejor
        self.assertEqual(busqueda_costo_uniforme(p).costo, mejor)

    def test_costo_acumulado_igual_a_costo_total(self):
        p = instancia(no_disp={("Lunes", "F0"), ("Lunes", "F1")}, max_consec=1)
        for alg in (busqueda_amplitud, busqueda_costo_uniforme):
            r = alg(p)
            self.assertAlmostEqual(r.costo, p.costo_total(r.estado))

    def test_heuristicas_cuentan_clases_pendientes(self):
        p = instancia()
        raiz = p.estado_inicial()
        parcial = p.sucesores(raiz)[0].estado
        self.assertEqual(h1(p, raiz), 4.0)
        self.assertEqual(h1(p, parcial), 3.0)
        self.assertEqual(h2(p, raiz), 4.0)

    def test_a_estrella_h1_y_h2_encuentran_solucion_optima(self):
        p = instancia(no_disp={("Lunes", "F0"), ("Lunes", "F1")}, max_consec=1)
        costo_optimo = busqueda_costo_uniforme(p).costo
        for algoritmo in (busqueda_a_estrella_h1, busqueda_a_estrella_h2):
            r = algoritmo(p)
            self.assertTrue(r.encontrado, r.algoritmo)
            self.assertEqual(r.costo, costo_optimo)
            self.assertEqual(p.restricciones.verificar_completo(r.estado), [])

    def test_a_estrella_h2_poda_y_cuenta_hijos_sin_valores_legales(self):
        pA = Profesor("PA", "A")
        p = Problema([Clase("a", "X", pA, "G1"), Clase("b", "Y", pA, "G2")],
                     ["Lunes"], [Franja("F0", "07:00", "09:00", 0)], [Salon("S1"), Salon("S2")])
        primer_hijo = p.sucesores(p.estado_inicial())[0].estado
        self.assertEqual(h2(p, p.estado_inicial()), 2.0)
        self.assertEqual(h2(p, primer_hijo), float("inf"))
        r = busqueda_a_estrella_h2(p)
        self.assertFalse(r.encontrado)
        self.assertEqual(r.motivo, "sin_solucion")
        self.assertEqual(r.nodos_creados, 3)
        self.assertEqual(r.nodos_expandidos, 1)

    def test_a_estrella_esta_registrada_con_firma_de_la_interfaz(self):
        self.assertIn("A* (h1)", ALGORITMOS)
        self.assertIn("A* (h2)", ALGORITMOS)
        r = ALGORITMOS["A* (h1)"](instancia(), 1, None)
        self.assertEqual(r.motivo, "limite_nodos")
        self.assertEqual(r.nodos_expandidos, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)