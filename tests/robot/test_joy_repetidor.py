# -*- coding: utf-8 -*-
"""Pruebas de la logica del repetidor del mando (sin ROS)."""
import os
import sys
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "misiones", "pilotada", "robot"))

import sf_joy_repetidor as r  # noqa: E402


class Repetidor(unittest.TestCase):
    def test_sin_mensaje_real_no_repite(self):
        self.assertFalse(r.debe_repetir(10.0, None, 0.0))

    def test_palanca_sostenida_repite_a_20_hz(self):
        # ultimo cambio real hace 2 s, ultimo envio hace 60 ms -> toca repetir
        self.assertTrue(r.debe_repetir(12.0, 10.0, 11.94))
        # ultimo envio hace 20 ms -> todavia no
        self.assertFalse(r.debe_repetir(12.0, 10.0, 11.98))

    def test_deja_de_repetir_si_el_mando_se_congela(self):
        self.assertTrue(r.debe_repetir(10.0 + r.SOSTENER_MAX - 0.1, 10.0, 0.0))
        self.assertFalse(r.debe_repetir(10.0 + r.SOSTENER_MAX + 0.1, 10.0, 0.0))

    def test_cubre_el_hueco_medido_en_el_robot(self):
        # Se midio un hueco de 3,8 s con la palanca sostenida: debe cubrirse.
        self.assertTrue(r.debe_repetir(10.0 + 3.8, 10.0, 10.0 + 3.7))
        # y el periodo es menor que el watchdog del selector (0,5 s)
        self.assertLess(r.PERIODO, 0.5)

    def test_las_repeticiones_no_pulsan_botones(self):
        self.assertEqual(r.botones_a_cero([1, 0, 1, 1]), [0, 0, 0, 0])
        self.assertEqual(r.botones_a_cero([]), [])


if __name__ == "__main__":
    unittest.main()
