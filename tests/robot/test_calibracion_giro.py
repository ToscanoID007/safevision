# -*- coding: utf-8 -*-
"""Pruebas de la comprobacion del giroscopo al arrancar el core."""
import os
import sys
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "misiones", "pilotada", "robot"))

import sf_runtime_manager as rm  # noqa: E402


class CalibracionGiro(unittest.TestCase):
    def test_caso_real_detectado(self):
        # Medido el 2026-10-03: crudo ~0, calibrado 4,54 rad/s con el robot quieto
        self.assertIs(rm.calibracion_giroscopo_ok(0.0001, 4.5434), False)

    def test_sesgo_sano_aceptado(self):
        self.assertIs(rm.calibracion_giroscopo_ok(0.003, -0.01), True)
        # robot girando durante la comprobacion, pero bien calibrado: la diferencia es pequena
        self.assertIs(rm.calibracion_giroscopo_ok(1.20, 1.22), True)

    def test_sin_datos_no_bloquea(self):
        self.assertIsNone(rm.calibracion_giroscopo_ok(None, 0.5))
        self.assertIsNone(rm.calibracion_giroscopo_ok(0.0, None))

    def test_motivo_se_consume_una_vez(self):
        rm.MOTIVOS["core"] = "el robot se movió"
        self.assertEqual(rm._motivo("core"), ": el robot se movió")
        self.assertEqual(rm._motivo("core"), "")


if __name__ == "__main__":
    unittest.main()
