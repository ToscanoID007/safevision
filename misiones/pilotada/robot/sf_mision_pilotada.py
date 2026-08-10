#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(
    "/home/pi/robot_custom/misiones/pilotada"
)

ROBOT_DIR = ROOT / "robot"


def limpiar():
    os.system(
        "clear"
    )


def ejecutar(comando):
    try:
        return subprocess.run(
            comando
        ).returncode

    except KeyboardInterrupt:
        return 130


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
        control
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
