# -*- coding: utf-8 -*-
"""Pruebas de sf_velocidad_manual: acotado, escalado y persistencia."""
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "misiones", "pilotada", "robot"))

import sf_velocidad_manual as v  # noqa: E402


class Velocidad(unittest.TestCase):
    def setUp(self):
        self.ruta = os.path.join(tempfile.mkdtemp(), "velocidad.json")

    def test_normalizar_acota_y_rechaza(self):
        self.assertEqual(v.normalizar(0.5), 0.5)
        self.assertEqual(v.normalizar("0.3"), 0.3)
        self.assertEqual(v.normalizar(5), 1.0)       # nunca acelera
        self.assertEqual(v.normalizar(0), 0.1)       # nunca deja el robot sin control
        self.assertEqual(v.normalizar(-2), 0.1)
        for malo in (None, "rapido", float("nan"), float("inf"), [1]):
            self.assertIsNone(v.normalizar(malo))

    def test_escalar_reduce_todas_las_componentes(self):
        self.assertEqual(v.escalar(1.0, -0.5, 4.0, 0.5), (0.5, -0.25, 2.0))
        self.assertEqual(v.escalar(1.0, 0.0, 5.0, 1.0), (1.0, 0.0, 5.0))
        self.assertEqual(v.escalar(0.0, 0.0, 0.0, 0.3), (0.0, 0.0, 0.0))   # parar sigue siendo parar

    def test_escalar_con_factor_invalido_no_acelera(self):
        self.assertEqual(v.escalar(1.0, 0.0, 1.0, "x"), (1.0, 0.0, 1.0))
        self.assertEqual(v.escalar(1.0, 0.0, 1.0, 7), (1.0, 0.0, 1.0))

    def test_persistencia(self):
        self.assertEqual(v.leer(self.ruta), v.FACTOR_DEFECTO)     # sin archivo
        self.assertEqual(v.guardar(0.4, self.ruta), 0.4)
        self.assertEqual(v.leer(self.ruta), 0.4)
        with open(self.ruta, "w") as h:
            h.write("{roto")
        self.assertEqual(v.leer(self.ruta), v.FACTOR_DEFECTO)     # archivo dañado
        with self.assertRaises(ValueError):
            v.guardar("rapido", self.ruta)

    def test_resumen(self):
        r = v.resumen(0.4)
        self.assertEqual((r["porcentaje"], r["lineal_max"], r["angular_max"]), (40, 0.4, 2.0))


if __name__ == "__main__":
    unittest.main()
