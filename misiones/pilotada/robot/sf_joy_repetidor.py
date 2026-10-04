#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SafeVision - repetidor del mando.

Problema que resuelve (medido en el robot el 2026-10-03): joy_node solo publica
cuando el mando CAMBIA. Si se mantiene la palanca quieta, aunque sea a fondo,
no llega ningun mensaje; a los 0,5 s el watchdog del selector de cmd_vel
interpreta que se solto el mando y para el robot. El resultado es un avance a
tirones. Se midio un hueco de 3,8 s con la palanca sostenida.

Que hace:
  /joy  (joy_node)  ->  este nodo  ->  /joy_mando  (yahboom_joy)
  - Cada mensaje real se reenvia tal cual (botones incluidos).
  - Mientras no llegan mensajes nuevos, repite el ultimo estado de los ejes a
    20 Hz con TODOS LOS BOTONES A CERO, para que una pulsacion (marchas, luces)
    cuente una sola vez.
  - Deja de repetir si pasan SOSTENER_MAX segundos sin ningun cambio real: si
    el mando se quedara congelado, el watchdog vuelve a parar el robot.

El watchdog del selector no cambia: soltar la palanca sigue parando en 0,5 s
(soltar es un cambio real, y se repite el estado "centrado").
"""

PERIODO = 0.05        # 20 Hz
SOSTENER_MAX = 8.0    # s sin cambios reales antes de dejar de repetir


def debe_repetir(ahora, ultimo_real, ultimo_envio):
    """Logica pura (probada en tests/robot/test_joy_repetidor.py)."""
    if ultimo_real is None:
        return False
    if ahora - ultimo_real > SOSTENER_MAX:
        return False
    return ahora - ultimo_envio >= PERIODO


def botones_a_cero(botones):
    return [0] * len(botones)


def main():
    import time

    import rospy
    from sensor_msgs.msg import Joy

    rospy.init_node("sf_joy_repetidor")
    pub = rospy.Publisher("/joy_mando", Joy, queue_size=1)
    estado = {"msg": None, "real": None, "envio": 0.0}

    def recibir(msg):
        ahora = time.monotonic()
        estado["msg"] = msg
        estado["real"] = ahora
        estado["envio"] = ahora
        pub.publish(msg)

    def repetir(_evento):
        ahora = time.monotonic()
        ultimo = estado["msg"]
        if ultimo is None or not debe_repetir(ahora, estado["real"], estado["envio"]):
            return
        copia = Joy()
        copia.header.stamp = rospy.Time.now()
        copia.header.frame_id = ultimo.header.frame_id
        copia.axes = list(ultimo.axes)
        copia.buttons = botones_a_cero(ultimo.buttons)
        estado["envio"] = ahora
        pub.publish(copia)

    rospy.Subscriber("/joy", Joy, recibir, queue_size=10)
    rospy.Timer(rospy.Duration(PERIODO), repetir)
    rospy.loginfo("SafeVision: repetidor del mando activo (20 Hz, maximo %.0f s)", SOSTENER_MAX)
    rospy.spin()


if __name__ == "__main__":
    main()
