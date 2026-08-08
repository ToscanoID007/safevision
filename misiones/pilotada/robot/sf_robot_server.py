#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import io
import os
import socket
import subprocess
import time
from pathlib import Path

import cv2
from flask import Flask, Response, jsonify


app = Flask(__name__)

CONTROL_MODE = "desconocido"

CAMERA_DEVICE = 1
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
JPEG_QUALITY = 70

PORT = 8080

MAPS_DIR = Path(
    "/home/pi/robot_custom/mapping/maps"
)



def obtener_ip():
    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.connect(("8.8.8.8", 80))

        ip = sock.getsockname()[0]

        sock.close()

        return ip

    except Exception:
        return "127.0.0.1"


def ejecutar(comando, timeout=2):
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=timeout
        )

        return resultado.stdout.strip()

    except Exception:
        return ""


def ros_master_activo():
    salida = ejecutar(
        "rostopic list"
    )

    return "/rosout" in salida


def driver_activo():
    salida = ejecutar(
        "rosnode list"
    )

    return "/driver_node" in salida


def lidar_activo():
    salida = ejecutar(
        "rostopic list"
    )

    return "/scan" in salida


def control_activo():
    if CONTROL_MODE == "mando":
        salida = ejecutar(
            "pgrep -af '[y]ahboom_joy.launch'"
        )

        return bool(salida)

    if CONTROL_MODE == "teclado":
        salida = ejecutar(
            "pgrep -af '[y]ahboom_keyboard.launch'"
        )

        return bool(salida)

    return False


def mando_conectado():
    return os.path.exists(
        "/dev/input/js0"
    )


def camara_detectada():
    return (
        os.path.exists("/dev/video0")
        or
        os.path.exists("/dev/video1")
    )


def generar_frames():
    cap = cv2.VideoCapture(
        CAMERA_DEVICE
    )

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    cap.set(
        cv2.CAP_PROP_FPS,
        CAMERA_FPS
    )

    try:
        while True:
            success, frame = cap.read()

            if not success:
                time.sleep(0.05)
                continue

            ok, buffer = cv2.imencode(
                ".jpg",
                frame,
                [
                    int(
                        cv2.IMWRITE_JPEG_QUALITY
                    ),
                    JPEG_QUALITY
                ]
            )

            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

    finally:
        cap.release()


@app.route("/")
def index():
    return jsonify({
        "service": "SafeVision Robot Server",
        "level": 1,
        "ip": obtener_ip(),
        "video": "/video_feed",
        "health": "/health"
    })


@app.route("/health")
def health():
    ros = ros_master_activo()
    driver = driver_activo()
    lidar = lidar_activo()
    control = control_activo()
    camera = camara_detectada()

    joystick = None

    if CONTROL_MODE == "mando":
        joystick = mando_conectado()

    ready = bool(
        ros
        and driver
        and control
        and camera
    )

    if CONTROL_MODE == "mando":
        ready = ready and bool(
            joystick
        )

    return jsonify({
        "ok": ready,

        "level": 1,

        "ip": obtener_ip(),

        "control_mode": CONTROL_MODE,

        "ros_master": ros,

        "driver": driver,

        "lidar": lidar,

        "camera": camera,

        "control": control,

        "joystick": joystick,

        "map": {
            "enabled": False,
            "level": 2
        }
    })


@app.route("/video_feed")
def video_feed():
    return Response(
        generar_frames(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )



# =========================================================
# NIVEL 2 - MAPAS GUARDADOS
# =========================================================

@app.route("/maps")
def maps():
    mapas = []

    if not MAPS_DIR.exists():
        return jsonify({
            "maps": []
        })

    for yaml_path in sorted(
        MAPS_DIR.glob("*.yaml")
    ):
        nombre = yaml_path.stem
        pgm_path = MAPS_DIR / (
            nombre + ".pgm"
        )

        if not pgm_path.exists():
            continue

        mapas.append({
            "name": nombre,
            "image": (
                "/maps/{}/image".format(
                    nombre
                )
            )
        })

    return jsonify({
        "maps": mapas
    })


@app.route("/maps/<nombre>/image")
def map_image(nombre):
    # Solo permitir nombres simples.
    if (
        "/" in nombre
        or "\\" in nombre
        or ".." in nombre
    ):
        return jsonify({
            "error": "Mapa inválido"
        }), 400

    pgm_path = (
        MAPS_DIR
        /
        (nombre + ".pgm")
    )

    if not pgm_path.exists():
        return jsonify({
            "error": "Mapa no encontrado"
        }), 404

    imagen = cv2.imread(
        str(pgm_path),
        cv2.IMREAD_GRAYSCALE
    )

    if imagen is None:
        return jsonify({
            "error": "No se pudo leer el mapa"
        }), 500

    ok, buffer = cv2.imencode(
        ".png",
        imagen
    )

    if not ok:
        return jsonify({
            "error": "No se pudo convertir el mapa"
        }), 500

    return Response(
        buffer.tobytes(),
        mimetype="image/png"
    )


def main():
    global CONTROL_MODE

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--control",
        choices=[
            "teclado",
            "mando"
        ],
        required=True
    )

    args = parser.parse_args()

    CONTROL_MODE = args.control

    print(
        "=============================================="
    )
    print(
        " SAFEVISION ROBOT SERVER"
    )
    print(
        "=============================================="
    )
    print(
        " IP      : {}".format(
            obtener_ip()
        )
    )
    print(
        " Control : {}".format(
            CONTROL_MODE.upper()
        )
    )
    print(
        " Puerto  : {}".format(
            PORT
        )
    )
    print(
        " Video   : http://{}:{}/video_feed".format(
            obtener_ip(),
            PORT
        )
    )
    print(
        " Health  : http://{}:{}/health".format(
            obtener_ip(),
            PORT
        )
    )
    print(
        "=============================================="
    )

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        threaded=True,
        use_reloader=False
    )


if __name__ == "__main__":
    main()
