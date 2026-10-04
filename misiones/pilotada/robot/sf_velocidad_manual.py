# -*- coding: utf-8 -*-
"""
SafeVision - velocidad del control manual (mando y teclado web).

Un factor entre 0.1 y 1.0 que el selector de cmd_vel aplica a las ordenes
manuales antes de mandarlas a los motores. Solo reduce: nunca supera los
limites del mando. La navegacion autonoma no se ve afectada.

Lo usan:
  - sf_cmd_vel_selector.py: aplica el factor (el lazo critico sigue en el robot);
  - sf_robot_server.py: GET/POST /runtime/speed, guarda el valor y lo publica.

Sin dependencias de ROS: se prueba con unittest en cualquier maquina.
"""

import json
import math
import os

FACTOR_MIN = 0.1
FACTOR_MAX = 1.0
FACTOR_DEFECTO = 1.0

TOPICO = "/safevision/manual_speed_scale"
ARCHIVO = os.environ.get(
    "SAFEVISION_VELOCIDAD_FILE",
    os.path.join(os.path.expanduser("~"), ".safevision_velocidad.json"),
)

# Limites de fabrica del nodo yahboom_joy (sus valores por defecto), para
# mostrar la velocidad maxima resultante.
LINEAL_MAX = 1.0    # m/s
ANGULAR_MAX = 5.0   # rad/s


def normalizar(valor):
    """Devuelve el factor acotado a [0.1, 1.0], o None si no es un numero."""
    try:
        factor = float(valor)
    except (TypeError, ValueError):
        return None
    if math.isnan(factor) or math.isinf(factor):
        return None
    return round(min(FACTOR_MAX, max(FACTOR_MIN, factor)), 2)


def escalar(vx, vy, wz, factor):
    """Aplica el factor a las tres componentes que mueve el mando."""
    f = normalizar(factor)
    if f is None:
        f = FACTOR_DEFECTO
    return vx * f, vy * f, wz * f


def leer(ruta=None):
    ruta = ruta or ARCHIVO
    try:
        with open(ruta) as handle:
            factor = normalizar(json.load(handle).get("factor"))
    except Exception:
        factor = None
    return FACTOR_DEFECTO if factor is None else factor


def guardar(factor, ruta=None):
    ruta = ruta or ARCHIVO
    f = normalizar(factor)
    if f is None:
        raise ValueError("Velocidad inválida: usa un número entre 0.1 y 1.0.")
    temporal = ruta + ".tmp"
    with open(temporal, "w") as handle:
        json.dump({"factor": f}, handle)
    os.replace(temporal, ruta)
    return f


def resumen(factor):
    f = normalizar(factor)
    if f is None:
        f = FACTOR_DEFECTO
    return {
        "factor": f,
        "porcentaje": int(round(f * 100)),
        "lineal_max": round(LINEAL_MAX * f, 2),
        "angular_max": round(ANGULAR_MAX * f, 2),
        "minimo": FACTOR_MIN,
        "maximo": FACTOR_MAX,
    }
