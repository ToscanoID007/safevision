#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import sys
from pathlib import Path


ROOT = Path(
    "/home/pi/robot_custom/misiones/pilotada"
)

ROBOT_DIR = ROOT / "robot"

MAPS_DIR = Path(
    "/home/pi/robot_custom/mapping/maps"
)


def limpiar():
    os.system(
        "clear"
    )


def ejecutar(comando):
    handler_original = signal.getsignal(
        signal.SIGINT
    )

    def mantener_padre(_signum, _frame):
        return None

    signal.signal(
        signal.SIGINT,
        mantener_padre
    )

    try:
        return subprocess.run(
            comando
        ).returncode

    finally:
        signal.signal(
            signal.SIGINT,
            handler_original
        )


def descargar_dashboard():
    servidor = (
        ROBOT_DIR
        / "sf_servidor_descarga.py"
    )

    if not servidor.exists():
        print("")
        print(
            "Dashboard aún no empaquetado."
        )
        print(
            "La infraestructura de descarga "
            "se configurará en la siguiente fase."
        )

        input(
            "\nENTER para regresar..."
        )

        return

    ejecutar([
        sys.executable,
        str(servidor)
    ])


def mapas_disponibles():
    mapas = []

    if not MAPS_DIR.exists():
        return mapas

    yaml_paths = sorted(
        MAPS_DIR.glob("*.yaml"),
        key=lambda path: path.stem.casefold()
    )

    for yaml_path in yaml_paths:
        nombre = yaml_path.stem

        pgm_path = (
            MAPS_DIR
            / (nombre + ".pgm")
        )

        if pgm_path.is_file():
            mapas.append(
                nombre
            )

    return mapas


def seleccionar_mapa():
    while True:
        limpiar()

        mapas = mapas_disponibles()

        print(
            "========================================================="
        )
        print(
            "          SAFEVISION - SELECCIÓN DE MAPA"
        )
        print(
            "========================================================="
        )
        print("")

        if not mapas:
            print(
                " No hay mapas 2D completos disponibles."
            )
            print(
                " Se requiere un archivo .yaml y su .pgm."
            )

            input(
                "\nENTER para regresar..."
            )

            return None

        for indice, mapa in enumerate(
            mapas,
            1
        ):
            etiqueta = ""

            if mapa == "HAB2":
                etiqueta = " [MAPA DE PRUEBAS]"

            print(
                " {}. {}{}".format(
                    indice,
                    mapa,
                    etiqueta
                )
            )

        cancelar = len(mapas) + 1

        print("")
        print(
            " {}. Cancelar".format(
                cancelar
            )
        )
        print("")
        print(
            "========================================================="
        )

        opcion = input(
            "\nSelecciona mapa: "
        ).strip()

        try:
            indice = int(
                opcion
            )
        except ValueError:
            continue

        if indice == cancelar:
            return None

        if 1 <= indice <= len(mapas):
            return mapas[
                indice - 1
            ]


def seleccionar_control():
    while True:
        limpiar()

        print(
            "========================================================="
        )
        print(
            "       SAFEVISION - SELECCIÓN DE CONTROL"
        )
        print(
            "========================================================="
        )
        print("")
        print(
            " 1. Teclado"
        )
        print(
            "    yahboom_keyboard.launch"
        )
        print("")
        print(
            " 2. Mando / Joystick"
        )
        print(
            "    yahboom_joy.launch"
        )
        print("")
        print(
            " 3. Cancelar"
        )
        print("")
        print(
            "========================================================="
        )

        opcion = input(
            "\nSelecciona [1-3]: "
        ).strip()

        if opcion == "1":
            return "teclado"

        if opcion == "2":
            return "mando"

        if opcion == "3":
            return None


def iniciar_operacion():
    mapa = seleccionar_mapa()

    if not mapa:
        return

    control = seleccionar_control()

    if not control:
        return

    launcher = (
        ROBOT_DIR
        / "sf_operacion_pilotada.sh"
    )

    ejecutar([
        "bash",
        str(launcher),
        control,
        mapa
    ])


def menu():
    while True:
        limpiar()

        print(
            "========================================================="
        )
        print(
            "           SAFEVISION - MISIÓN PILOTADA"
        )
        print(
            "========================================================="
        )
        print("")
        print(
            " Nivel 1: Pilotaje + Red Neuronal"
        )
        print(
            " Nivel 2: Pilotaje + Mapa       [ACTIVO]"
        )
        print(
            " Nivel 3: Navegación asistida   [FUTURO]"
        )
        print("")
        print(
            "---------------------------------------------------------"
        )
        print("")
        print(
            " 1. Iniciar operación pilotada"
        )
        print(
            " 2. Descargar Dashboard Ubuntu"
        )
        print(
            " 3. Regresar"
        )
        print("")
        print(
            "========================================================="
        )

        opcion = input(
            "\nSelecciona [1-3]: "
        ).strip()

        if opcion == "1":
            iniciar_operacion()

        elif opcion == "2":
            descargar_dashboard()

        elif opcion == "3":
            return

        else:
            input(
                "\nOpción inválida. ENTER..."
            )


if __name__ == "__main__":
    try:
        menu()

    except KeyboardInterrupt:
        pass
