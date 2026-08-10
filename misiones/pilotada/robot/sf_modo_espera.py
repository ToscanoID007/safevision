#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import select
import socket
import sys
import time
import urllib.request


PORT = 8080

MAP_NAME = os.environ.get(
    "SAFEVISION_MAP_NAME",
    "HAB2"
)


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


def obtener_health(ip):
    try:
        with urllib.request.urlopen(
            "http://{}:{}/health".format(
                ip,
                PORT
            ),
            timeout=2
        ) as respuesta:

            return json.loads(
                respuesta.read().decode(
                    "utf-8"
                )
            )

    except Exception:
        return None


def marca(valor):
    if valor:
        return "[ OK ]"

    return "[FAIL]"


def obtener_estado(control):
    ip = obtener_ip()

    health = obtener_health(
        ip
    )

    if health is None:
        return {
            "ip": ip,
            "ros": False,
            "driver": False,
            "lidar": False,
            "map": False,
            "camera": False,
            "server": False,
            "joystick": None,
            "control": False,
            "ready": False
        }

    mapa = health.get(
        "map",
        {}
    )

    ros = bool(
        health.get(
            "ros_master",
            False
        )
    )

    driver = bool(
        health.get(
            "driver",
            False
        )
    )

    lidar = bool(
        health.get(
            "lidar",
            False
        )
    )

    map_ok = bool(
        mapa.get(
            "enabled",
            False
        )
    )

    camera = bool(
        health.get(
            "camera",
            False
        )
    )

    control_ok = bool(
        health.get(
            "control",
            False
        )
    )

    joystick = health.get(
        "joystick"
    )

    server = True

    infraestructura = bool(
        ros
        and driver
        and lidar
        and map_ok
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
        # En teclado, sf_modo_espera corre ANTES
        # de lanzar yahboom_keyboard.
        #
        listo = infraestructura

    return {
        "ip": ip,
        "ros": ros,
        "driver": driver,
        "lidar": lidar,
        "map": map_ok,
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
        "       SAFEVISION - MISIÓN PILOTADA / NIVEL 2"
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
        "{} LiDAR".format(
            marca(
                estado["lidar"]
            )
        )
    )

    print(
        ("{} Mapa " + MAP_NAME + " / AMCL").format(
            marca(
                estado["map"]
            )
        )
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
        " Mapa: {} - Localización AMCL activa".format(MAP_NAME)
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
        raise SystemExit(130)
