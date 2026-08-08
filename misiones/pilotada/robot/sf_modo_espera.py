#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import select
import socket
import subprocess
import sys
import time
import urllib.request


PORT = 8080


def ejecutar(comando):
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=2
        )

        return resultado.stdout.strip()

    except Exception:
        return ""


def obtener_ip():
    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.connect(
            ("8.8.8.8", 80)
        )

        ip = sock.getsockname()[0]

        sock.close()

        return ip

    except Exception:
        return "127.0.0.1"


def servidor_activo(ip):
    try:
        with urllib.request.urlopen(
            "http://{}:{}/".format(
                ip,
                PORT
            ),
            timeout=1
        ) as respuesta:

            json.loads(
                respuesta.read().decode(
                    "utf-8"
                )
            )

            return True

    except Exception:
        return False


def marca(valor):
    if valor:
        return "[ OK ]"

    return "[FAIL]"


def obtener_estado(control):
    ip = obtener_ip()

    topics = ejecutar(
        "rostopic list"
    )

    nodes = ejecutar(
        "rosnode list"
    )

    ros = "/rosout" in topics

    driver = "/driver_node" in nodes

    camera = (
        os.path.exists("/dev/video0")
        or
        os.path.exists("/dev/video1")
    )

    server = servidor_activo(
        ip
    )

    joystick = None
    control_ok = False

    if control == "mando":

        joystick = os.path.exists(
            "/dev/input/js0"
        )

        control_ok = (
            "/joy_node" in nodes
            and
            "/yahboom_joy" in nodes
        )

    elif control == "teclado":

        control_ok = (
            "/yahboom_keyboard" in nodes
            or
            "/keyboard_ctrl" in nodes
        )

    infraestructura = bool(
        ros
        and driver
        and camera
        and server
    )

    if control == "mando":
        listo = bool(
            infraestructura
            and joystick
            and control_ok
        )
    else:
        #
        # En modo teclado el nodo todavía NO se lanza.
        # Se inicia después de ENTER.
        #
        listo = infraestructura

    return {
        "ip": ip,
        "ros": ros,
        "driver": driver,
        "camera": camera,
        "server": server,
        "joystick": joystick,
        "control": control_ok,
        "ready": listo
    }


def mostrar(control):
    estado = obtener_estado(
        control
    )

    os.system(
        "clear"
    )

    print(
        "========================================================="
    )
    print(
        "       SAFEVISION - MISIÓN PILOTADA / NIVEL 1"
    )
    print(
        "========================================================="
    )
    print("")
    print(
        " Control : {}".format(
            control.upper()
        )
    )
    print(
        " IP      : {}".format(
            estado["ip"]
        )
    )
    print("")

    print(
        "{} ROS Master".format(
            marca(
                estado["ros"]
            )
        )
    )

    print(
        "{} Driver Rosmaster".format(
            marca(
                estado["driver"]
            )
        )
    )

    print(
        "[ -- ] LiDAR / mapa (Nivel 2)"
    )

    print(
        "{} Cámara".format(
            marca(
                estado["camera"]
            )
        )
    )

    print(
        "{} Robot Server :{}".format(
            marca(
                estado["server"]
            ),
            PORT
        )
    )

    if control == "mando":

        print(
            "{} Mando /dev/input/js0".format(
                marca(
                    estado["joystick"]
                )
            )
        )

        print(
            "{} Control MANDO".format(
                marca(
                    estado["control"]
                )
            )
        )

    else:

        if estado["control"]:
            print(
                "[ OK ] Control TECLADO"
            )
        else:
            print(
                "[WAIT] Control TECLADO"
            )

    print("")
    print(
        "---------------------------------------------------------"
    )

    if estado["ready"]:
        print(
            " ESTADO: LISTO"
        )
    else:
        print(
            " ESTADO: REVISAR COMPONENTES"
        )

    print(
        "---------------------------------------------------------"
    )

    print("")
    print(
        " Dashboard"
    )

    print(
        "   IP:    {}".format(
            estado["ip"]
        )
    )

    print(
        "   Video: http://{}:{}/video_feed".format(
            estado["ip"],
            PORT
        )
    )

    print(
        "   Salud: http://{}:{}/health".format(
            estado["ip"],
            PORT
        )
    )

    print("")
    print(
        " Mapa: desactivado - Nivel 2"
    )
    print("")

    if control == "teclado":

        print(
            " ENTER = entrar al control por teclado"
        )

    else:

        print(
            " Mando activo."
        )

        print(
            " Ctrl+C = finalizar operación"
        )

    print("")
    print(
        " Diagnóstico actualizado cada 2 segundos."
    )

    print(
        "========================================================="
    )


def modo_teclado():
    while True:

        mostrar(
            "teclado"
        )

        listo, _, _ = select.select(
            [sys.stdin],
            [],
            [],
            2
        )

        if listo:

            sys.stdin.readline()

            return 0


def modo_mando():
    #
    # IMPORTANTE:
    #
    # No usamos select() sobre stdin.
    #
    # El mando funciona independientemente de esta
    # terminal y el diagnóstico debe permanecer vivo
    # hasta que el operador pulse Ctrl+C.
    #
    while True:

        mostrar(
            "mando"
        )

        time.sleep(
            2
        )


def main():
    if len(sys.argv) != 2:

        print(
            "Uso: sf_modo_espera.py teclado|mando"
        )

        return 1

    control = (
        sys.argv[1]
        .strip()
        .lower()
    )

    if control == "teclado":
        return modo_teclado()

    if control == "mando":
        return modo_mando()

    print(
        "Control inválido."
    )

    return 1


if __name__ == "__main__":

    try:
        raise SystemExit(
            main()
        )

    except KeyboardInterrupt:
        pass
