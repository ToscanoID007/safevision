# -*- coding: utf-8 -*-
"""
T5 — gestor de nodos: arranque y parada de recursos individuales con dependencias.

Se escribe ANTES de la implementacion y debe fallar (rojo). Ejercita solo la
logica de dependencias: los arrancadores y paradores reales se sustituyen por
registradores de llamadas, y el estado del robot por un conjunto controlado.

Reglas que se exigen (derivadas de la auditoria de apply_profile y del ciclo de
mapeo en sf_runtime_manager.py):
  - arrancar X arranca antes sus requisitos que falten, en el orden del gestor;
  - parar X para antes todo lo que dependa de X, en orden inverso;
  - con una sesion de mapeo activa no se permite ninguna accion;
  - los recursos de solo lectura (ros_master, robot_server, camera, teclado,
    mapping) no aceptan acciones;
  - un fallo a mitad de la cadena detiene la cadena y lo reporta.

Ejecucion:  python3 -m unittest tests/robot/test_runtime_manager_recursos.py -v
"""
import os
import sys
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "misiones", "pilotada", "robot"))

import sf_runtime_manager as rm  # noqa: E402


class _Escenario:
    """Sustituye el mundo real: activos, mapeo, arrancadores y paradores."""

    def __init__(self, activos, mapeando=False, fallan=()):
        self.activos = set(activos)
        self.mapeando = mapeando
        self.fallan = set(fallan)
        self.llamadas = []

    def arrancar(self, nombre):
        def _f():
            self.llamadas.append("+" + nombre)
            if nombre in self.fallan:
                return False
            self.activos.add(nombre)
            return True
        return _f

    def parar(self, nombre):
        def _f():
            self.llamadas.append("-" + nombre)
            self.activos.discard(nombre)
            return True
        return _f

    def instalar(self):
        self._orig = (dict(rm._STARTERS), dict(rm._STOPPERS), rm._active_set, rm._mapping_active)
        for n in rm.START_ORDER:
            rm._STARTERS[n] = self.arrancar(n)
            rm._STOPPERS[n] = self.parar(n)
        rm._active_set = lambda: set(self.activos)
        rm._mapping_active = lambda: self.mapeando

    def restaurar(self):
        rm._STARTERS.clear(); rm._STARTERS.update(self._orig[0])
        rm._STOPPERS.clear(); rm._STOPPERS.update(self._orig[1])
        rm._active_set, rm._mapping_active = self._orig[2], self._orig[3]


class RecursosTest(unittest.TestCase):

    def _con(self, *a, **k):
        e = _Escenario(*a, **k); e.instalar(); self.addCleanup(e.restaurar); return e

    def test_orden_de_arranque_conocido(self):
        self.assertEqual(rm.START_ORDER[:3], ["driver", "core", "selector"])
        self.assertEqual(rm.START_ORDER[-2:], ["navigation", "nav_queue"])

    def test_arrancar_resuelve_requisitos_en_orden(self):
        e = self._con(activos={"driver"})
        r = rm.start_resource("navigation")
        self.assertTrue(r["ok"], r)
        self.assertEqual(e.llamadas, ["+core", "+selector", "+lidar", "+localization", "+navigation"])

    def test_arrancar_lo_ya_activo_no_hace_nada(self):
        e = self._con(activos={"driver", "core", "selector", "lidar"})
        r = rm.start_resource("lidar")
        self.assertTrue(r["ok"])
        self.assertEqual(e.llamadas, [])

    def test_parar_apaga_dependientes_en_orden_inverso(self):
        e = self._con(activos=set(rm.START_ORDER))
        r = rm.stop_resource("lidar")
        self.assertTrue(r["ok"], r)
        self.assertEqual(e.llamadas, ["-nav_queue", "-navigation", "-pose_exporter", "-localization", "-lidar"])

    def test_parar_driver_apaga_todo(self):
        e = self._con(activos=set(rm.START_ORDER))
        rm.stop_resource("driver")
        self.assertEqual(e.llamadas[-1], "-driver")
        self.assertEqual(set(e.llamadas), {"-" + n for n in rm.START_ORDER})

    def test_fallo_a_mitad_detiene_la_cadena(self):
        e = self._con(activos=set(), fallan={"core"})
        r = rm.start_resource("lidar" if "core" not in rm.transitive_deps("lidar") else "localization")
        self.assertFalse(r["ok"])
        self.assertIn("core", r["message"])
        self.assertNotIn("+localization", e.llamadas)

    def test_mapeo_activo_bloquea_todo(self):
        e = self._con(activos={"driver", "core", "lidar", "selector", "mapping"}, mapeando=True)
        for accion in (rm.start_resource, rm.stop_resource):
            r = accion("lidar")
            self.assertFalse(r["ok"]); self.assertIn("mapeo", r["message"].lower())
        self.assertEqual(e.llamadas, [])

    def test_solo_lectura_rechaza_acciones(self):
        self._con(activos=set())
        for n in ("ros_master", "robot_server", "camera", "teclado", "mapping"):
            self.assertFalse(rm.start_resource(n)["ok"])
            self.assertFalse(rm.stop_resource(n)["ok"])

    def test_desconocido_rechazado(self):
        self._con(activos=set())
        self.assertFalse(rm.start_resource("bailar")["ok"])


if __name__ == "__main__":
    unittest.main()
