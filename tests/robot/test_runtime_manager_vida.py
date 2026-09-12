# -*- coding: utf-8 -*-
"""
T3 — ¿distingue el gestor de runtime un proceso zombi de uno vivo?

Contexto: sf_runtime_manager.py lanza cada nodo con Popen y descarta el objeto
sin llamar a wait(). Si el nodo muere (por ejemplo porque otro proceso registro
un nodo ROS con el mismo nombre), queda como zombi hasta que el padre lo recoja.
_pid_alive() decide con os.kill(pid, 0), que acepta zombis, y _spawn() se niega a
relanzar mientras crea "vivo" al zombi. Reproducido en el robot el 2026-09-13
(prueba T1: PID 17478 en estado Z, perfil rechazado con "No se pudo iniciar
driver").

Este test se escribe ANTES de la correccion y debe fallar (rojo). No requiere
ROS: sf_runtime_manager es Python puro y aqui solo se ejercita _pid_alive.

Ejecucion:  python3 -m unittest tests/robot/test_runtime_manager_vida.py -v
"""
import os
import signal
import subprocess
import sys
import time
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "misiones", "pilotada", "robot"))

import sf_runtime_manager as rm  # noqa: E402


def _estado_proc(pid):
    try:
        with open("/proc/%d/status" % pid) as f:
            for linea in f:
                if linea.startswith("State:"):
                    return linea.split(":", 1)[1].strip()[0]
    except OSError:
        return None


class PidAliveTest(unittest.TestCase):

    def test_proceso_vivo_se_reporta_vivo(self):
        p = subprocess.Popen(["sleep", "30"])
        try:
            self.assertTrue(rm._pid_alive(p.pid))
        finally:
            p.kill()
            p.wait()

    def test_proceso_muerto_y_recogido_se_reporta_muerto(self):
        p = subprocess.Popen(["sleep", "30"])
        p.kill()
        p.wait()
        self.assertFalse(rm._pid_alive(p.pid))

    def test_zombi_se_reporta_muerto(self):
        """El caso del robot: hijo muerto que nadie ha recogido (estado Z)."""
        p = subprocess.Popen(["sleep", "30"])
        os.kill(p.pid, signal.SIGKILL)
        for _ in range(50):
            if _estado_proc(p.pid) == "Z":
                break
            time.sleep(0.02)
        self.assertEqual(_estado_proc(p.pid), "Z", "el fixture no produjo un zombi")
        try:
            self.assertFalse(
                rm._pid_alive(p.pid),
                "un zombi se considera vivo: el gestor no relanzara el nodo",
            )
        finally:
            p.wait()


if __name__ == "__main__":
    unittest.main()
