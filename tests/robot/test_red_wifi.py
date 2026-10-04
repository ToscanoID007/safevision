# -*- coding: utf-8 -*-
"""Pruebas del gestor de Wi-Fi (sf_red_wifi): funciones puras y reglas, sin nmcli real."""
import os
import sys
import tempfile
import time
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "misiones", "pilotada", "robot"))

import sf_red_wifi as w  # noqa: E402

ESCANEO = "\n".join([
    "Mega_2.4G_38FE:80:WPA2:2437 MHz",
    "Mega_5G_38FE:90:WPA2:5180 MHz",
    "DualBand:70:WPA2:2412 MHz",
    "DualBand:95:WPA2:5745 MHz",
    "Red\\:con\\:dos:40:WPA1 WPA2:2462 MHz",
    "Cafe:55::2412 MHz",
    "Uni:60:WPA2 802.1X:2437 MHz",
    "SafeVision-Robot:99:WPA2:2437 MHz",
    ":30:WPA2:2412 MHz",
    "Mega_2.4G_38FE:50:WPA2:2437 MHz",
])


class Parseo(unittest.TestCase):
    def setUp(self):
        self.redes = {r["ssid"]: r for r in w.parsear_escaneo(ESCANEO)}

    def test_dividir_con_escapes(self):
        self.assertEqual(w.dividir_terse("a\\:b:c\\\\d:e"), ["a:b", "c\\d", "e"])

    def test_banda(self):
        self.assertEqual(w.banda_de("2437 MHz"), "2.4")
        self.assertEqual(w.banda_de("5180 MHz"), "5")
        self.assertIsNone(w.banda_de("raro"))

    def test_unica_por_ssid_con_mejor_senal(self):
        self.assertEqual(self.redes["Mega_2.4G_38FE"]["senal"], 80)
        self.assertEqual(list(self.redes).count("Mega_2.4G_38FE"), 1)

    def test_compatibilidad_por_banda(self):
        self.assertTrue(self.redes["Mega_2.4G_38FE"]["compatible"])
        self.assertFalse(self.redes["Mega_5G_38FE"]["compatible"])
        self.assertTrue(self.redes["DualBand"]["compatible"])
        self.assertEqual(self.redes["DualBand"]["bandas"], ["2.4", "5"])
        self.assertEqual(self.redes["DualBand"]["senal_24"], 70)

    def test_excluye_red_propia_y_ocultas(self):
        self.assertNotIn("SafeVision-Robot", self.redes)
        self.assertNotIn("", self.redes)

    def test_tipos_de_seguridad(self):
        self.assertTrue(self.redes["Cafe"]["abierta"])
        self.assertTrue(self.redes["Uni"]["empresarial"])
        self.assertIn("Red:con:dos", self.redes)

    def test_orden_elegibles_primero(self):
        lista = w.parsear_escaneo(ESCANEO)
        elegible = [r["compatible"] and not r["empresarial"] for r in lista]
        primera_no = elegible.index(False)
        self.assertTrue(all(elegible[:primera_no]))
        self.assertFalse(any(elegible[primera_no:]))


class Validacion(unittest.TestCase):
    def test_ssid(self):
        self.assertIsNone(w.validar_ssid("Mega_2.4G_38FE"))
        self.assertIsNotNone(w.validar_ssid(""))
        self.assertIsNotNone(w.validar_ssid("x" * 33))
        self.assertIsNotNone(w.validar_ssid("SafeVision-Robot"))
        self.assertIsNotNone(w.validar_ssid("a\nb"))

    def test_clave(self):
        self.assertIsNone(w.validar_clave(""))
        self.assertIsNone(w.validar_clave("12345678"))
        self.assertIsNone(w.validar_clave("0123456789abcdef" * 4))
        self.assertIsNotNone(w.validar_clave("corta"))
        self.assertIsNotNone(w.validar_clave("x" * 64))
        self.assertIsNotNone(w.validar_clave("clave\tmala"))

    def test_orden_fija_24_ghz_y_no_mete_clave_si_es_abierta(self):
        args = w.orden_agregar("Casa", "secreta123")
        self.assertIn("bg", args[args.index("802-11-wireless.band") + 1])
        self.assertEqual(args[args.index("wifi-sec.psk") + 1], "secreta123")
        self.assertNotIn("wifi-sec.psk", w.orden_agregar("Cafe", ""))
        self.assertNotIn("802-11-wireless.hidden", w.orden_agregar("Casa", "secreta123"))
        oculta = w.orden_agregar("Oculta", "secreta123", oculta=True)
        self.assertEqual(oculta[oculta.index("802-11-wireless.hidden") + 1], "yes")


class Reglas(unittest.TestCase):
    """Reglas de agregar/olvidar/conectar con nmcli simulado."""

    def setUp(self):
        self.ordenes = []
        self.activa = "Mega_2.4G_38FE"
        self.perfiles = [
            {"nombre": "Mega_2.4G_38FE", "ssid": "Mega_2.4G_38FE", "banda": "auto", "prioridad": "10", "activa": True},
            {"nombre": "Lab", "ssid": "Lab", "banda": "bg", "prioridad": "10", "activa": False},
        ]
        self._orig = (w._nmcli, w.conexion_activa, w.perfiles_guardados, w.CERROJO)
        w._nmcli = lambda args, timeout=20: (self.ordenes.append(list(args)) or (0, "", ""))
        w.conexion_activa = lambda: self.activa
        w.perfiles_guardados = lambda: self.perfiles
        self.tmp = tempfile.mkdtemp()
        w.CERROJO = os.path.join(self.tmp, "cerrojo")

    def tearDown(self):
        w._nmcli, w.conexion_activa, w.perfiles_guardados, w.CERROJO = self._orig

    def test_agregar_reemplaza_la_existente(self):
        r = w.agregar("Lab", "nuevaclave1")
        self.assertTrue(r["ok"])
        self.assertEqual(self.ordenes[0], ["connection", "delete", "Lab"])
        self.assertEqual(self.ordenes[1][:3], ["connection", "add", "type"])

    def test_no_cambia_la_clave_de_la_red_en_uso(self):
        r = w.agregar("Mega_2.4G_38FE", "otraclave1")
        self.assertFalse(r["ok"])
        self.assertEqual(self.ordenes, [])

    def test_validacion_antes_de_tocar_nada(self):
        self.assertFalse(w.agregar("Nueva", "corta")["ok"])
        self.assertEqual(self.ordenes, [])

    def test_mensajes_nunca_incluyen_la_clave(self):
        w._nmcli = lambda args, timeout=20: (1, "", "Error: fallo con secreta123")
        r = w.agregar("Nueva", "secreta123")
        self.assertFalse(r["ok"])
        self.assertNotIn("secreta123", r["message"])
        self.assertIn("***", r["message"])

    def test_olvidar(self):
        self.assertFalse(w.olvidar("Mega_2.4G_38FE")["ok"])   # en uso
        self.assertFalse(w.olvidar("SafeVision-AP")["ok"])    # red propia
        self.assertFalse(w.olvidar("NoExiste")["ok"])
        self.assertTrue(w.olvidar("Lab")["ok"])

    def test_conectar_rechaza_desconocida_y_la_activa_no_cambia(self):
        self.assertFalse(w.conectar("NoExiste")["ok"])
        r = w.conectar("Mega_2.4G_38FE")
        self.assertTrue(r["ok"])
        self.assertFalse(r["cambio"])

    def test_conectar_con_cerrojo_vigente(self):
        with open(w.CERROJO, "w") as h:
            h.write(str(int(time.time())))
        self.assertFalse(w.conectar("Lab")["ok"])


if __name__ == "__main__":
    unittest.main()
