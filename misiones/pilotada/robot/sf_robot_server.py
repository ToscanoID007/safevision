#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import ast
import json
import math
import io
import os
import socket
import subprocess
import sys
import time
import xmlrpc.client
from pathlib import Path

import cv2
import rospy
from std_msgs.msg import String
from flask import Flask, Response, jsonify, request


AUTOMATIC_ROBOT_DIR = (
    Path(__file__).resolve().parents[2]
    /
    "automatica"
    /
    "robot"
)

if str(AUTOMATIC_ROBOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(AUTOMATIC_ROBOT_DIR)
    )

from sf_mission_executor import (
    MissionPlanError,
    MissionRuntime
)


app = Flask(__name__)

MISSION_RUNTIME = MissionRuntime()

CONTROL_MODE = "desconocido"

NAV_COMMAND_PUB = None
NAV_STATUS_RECEIVED = False

NAV_STATUS = {
    "state": "unavailable",
    "running": False,
    "remaining": [],
    "remaining_count": 0,
    "completed": [],
    "completed_count": 0,
    "current": None,
    "map": None,
    "active_map": None,
    "message": "Cola de navegación no disponible"
}


CAMERA_DEVICE = 1
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
JPEG_QUALITY = 70

PORT = 8091

MAPS_DIR = Path(
    "/home/pi/robot_custom/mapping/maps"
)


MISSIONS_DIR = Path(
    "/home/pi/robot_custom/misiones/programadas"
)

MISSIONS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MISSION_SUFFIX = ".sfmision"




SAFEVISION_POSE_FILE = Path(
    "/tmp/safevision_map_pose.json"
)

SAFEVISION_INITIALPOSE_FILE = Path(
    "/tmp/safevision_initialpose_request.json"
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
        "level": 2,
        "ip": obtener_ip(),
        "video": "/video_feed",
        "health": "/health"
    })




class SafeVisionXmlRpcTransport(
    xmlrpc.client.Transport
):
    def __init__(
        self,
        timeout=1.5
    ):
        super().__init__()
        self.timeout = timeout

    def make_connection(
        self,
        host
    ):
        connection = super().make_connection(
            host
        )

        connection.timeout = self.timeout

        return connection


def estado_ros_runtime():
    uri = os.environ.get(
        "ROS_MASTER_URI",
        "http://127.0.0.1:11311"
    )

    try:
        master = xmlrpc.client.ServerProxy(
            uri,
            transport=SafeVisionXmlRpcTransport(
                timeout=1.5
            ),
            allow_none=True
        )

        code, message, state = (
            master.getSystemState(
                "/safevision_robot_server"
            )
        )

        if code != 1:
            return False, set(), set()

        publishers, subscribers, services = (
            state
        )

        nodes = set()
        topics = set()

        for topic, owners in (
            publishers + subscribers
        ):
            topics.add(topic)
            nodes.update(owners)

        for service, owners in services:
            nodes.update(owners)

        return True, nodes, topics

    except Exception:
        return False, set(), set()

@app.route("/health")
def health():
    ros, nodes, topics = (
        estado_ros_runtime()
    )

    driver = (
        "/driver_node" in nodes
    )

    lidar = (
        "/scan" in topics
    )

    map_active = (
        "/map" in topics
        and
        "/amcl" in nodes
    )

    if CONTROL_MODE == "mando":
        control = (
            "/yahboom_joy" in nodes
        )
    elif CONTROL_MODE == "teclado":
        control = (
            "/yahboom_keyboard" in nodes
        )
    else:
        control = False

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
        ready = (
            ready
            and bool(joystick)
        )

    return jsonify({
        "ok": ready,
        "level": 2,
        "ip": obtener_ip(),
        "control_mode": CONTROL_MODE,
        "ros_master": ros,
        "driver": driver,
        "lidar": lidar,
        "camera": camera,
        "control": control,
        "joystick": joystick,
        "map": {
            "enabled": map_active,
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
# MISIONES SAFEVISION
# =========================================================

def mission_name_valid(
    value
):
    if not isinstance(
        value,
        str
    ):
        return False

    name = value.strip()

    if (
        not name
        or
        len(name) > 64
        or
        name in (".", "..")
        or
        name.endswith(".")
        or
        name.lower().endswith(
            MISSION_SUFFIX
        )
    ):
        return False

    invalid = '<>:"/\\|?*'

    for char in name:
        if (
            char in invalid
            or
            ord(char) < 32
        ):
            return False

    return True


def mission_point_id_valid(
    value
):
    if not isinstance(
        value,
        str
    ):
        return False

    text = value.strip()

    if (
        len(text) != 5
        or
        not text.lower().startswith(
            "0x"
        )
    ):
        return False

    try:
        number = int(
            text[2:],
            16
        )

    except Exception:
        return False

    return (
        0
        <=
        number
        <=
        0xFFF
    )


def validate_mission_data(
    data
):
    if not isinstance(
        data,
        dict
    ):
        return False, "La misión debe ser un objeto JSON."

    if (
        data.get("format")
        !=
        "safevision-mission"
    ):
        return False, "Formato de misión inválido."

    if data.get("version") != 1:
        return False, "Versión de misión no compatible."

    if not mission_name_valid(
        data.get("name")
    ):
        return False, "Nombre de misión inválido."

    map_name = data.get(
        "map",
        ""
    )

    if (
        map_name is not None
        and
        not isinstance(
            map_name,
            str
        )
    ):
        return False, "Mapa inválido."

    code = data.get(
        "code",
        ""
    )

    if not isinstance(
        code,
        str
    ):
        return False, "El código debe ser texto."

    points = data.get(
        "points"
    )

    if not isinstance(
        points,
        list
    ):
        return False, "points debe ser una lista."

    if len(points) > 4096:
        return False, "La misión tiene demasiados puntos."

    ids = set()

    for point in points:
        if not isinstance(
            point,
            dict
        ):
            return False, "Punto inválido."

        point_id = point.get(
            "id"
        )

        if not mission_point_id_valid(
            point_id
        ):
            return False, "ID de punto inválido."

        canonical = point_id.lower()

        if canonical in ids:
            return False, "Hay IDs de punto duplicados."

        ids.add(
            canonical
        )

        alias = point.get(
            "alias",
            ""
        )

        if not isinstance(
            alias,
            str
        ):
            return False, "Alias inválido."

        try:
            float(
                point["x"]
            )

            float(
                point["y"]
            )

        except Exception:
            return False, "Coordenadas de punto inválidas."

        yaw = point.get(
            "yaw"
        )

        if yaw is not None:
            try:
                float(
                    yaw
                )

            except Exception:
                return False, "Orientación inválida."

    initial_id = data.get(
        "initial_point_id"
    )

    if (
        initial_id is not None
        and
        (
            not mission_point_id_valid(
                initial_id
            )
            or
            initial_id.lower()
            not in ids
        )
    ):
        return False, "Punto inicial inválido."

    next_id = data.get(
        "next_point_id",
        0
    )

    if (
        not isinstance(
            next_id,
            int
        )
        or
        next_id < 0
        or
        next_id > 0x1000
    ):
        return False, "Contador de IDs inválido."

    return True, ""


def mission_path(
    name
):
    return (
        MISSIONS_DIR
        /
        (
            name.strip()
            +
            MISSION_SUFFIX
        )
    )


@app.route("/missions")
def robot_missions():
    files = []

    for path in sorted(
        MISSIONS_DIR.glob(
            "*" + MISSION_SUFFIX
        ),
        key=lambda item: item.name.lower()
    ):
        files.append({
            "name": path.stem,
            "filename": path.name
        })

    return jsonify({
        "ok": True,
        "missions": files
    })


@app.route(
    "/missions/save",
    methods=["POST"]
)
def robot_mission_save():
    data = request.get_json(
        silent=True
    )

    ok, message = validate_mission_data(
        data
    )

    if not ok:
        return jsonify({
            "ok": False,
            "error": message
        }), 400

    path = mission_path(
        data["name"]
    )

    temp = Path(
        str(path)
        +
        ".tmp"
    )

    try:
        temp.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )
            +
            "\n",
            encoding="utf-8"
        )

        temp.replace(
            path
        )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": (
                "No se pudo guardar la misión: {}"
                .format(exc)
            )
        }), 500

    return jsonify({
        "ok": True,
        "name": data["name"],
        "path": str(path)
    })


@app.route(
    "/missions/delete",
    methods=["POST"]
)
def robot_mission_delete():
    data = request.get_json(
        silent=True
    ) or {}

    name = data.get(
        "name"
    )

    if not mission_name_valid(
        name
    ):
        return jsonify({
            "ok": False,
            "error": "Nombre de misión inválido."
        }), 400

    path = mission_path(
        name
    )

    if not path.exists():
        return jsonify({
            "ok": False,
            "error": "Misión no encontrada."
        }), 404

    try:
        path.unlink()

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": (
                "No se pudo eliminar: {}"
                .format(exc)
            )
        }), 500

    return jsonify({
        "ok": True,
        "name": name
    })


# =========================================================
# MISION AUTOMATICA - RUNTIME
# =========================================================

@app.route(
    "/mission/prepare",
    methods=["POST"]
)
def mission_prepare():
    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):
        return jsonify({
            "ok": False,
            "error": "JSON inválido"
        }), 400


    mission = data.get(
        "mission"
    )

    trace = data.get(
        "trace"
    )


    ok, message = validate_mission_data(
        mission
    )

    if not ok:
        return jsonify({
            "ok": False,
            "error": message
        }), 400


    try:
        status = MISSION_RUNTIME.prepare(
            mission,
            trace
        )

    except MissionPlanError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 400


    response = dict(
        status
    )

    response["ok"] = True

    return jsonify(
        response
    )


@app.route(
    "/mission/status"
)
def mission_status():
    response = MISSION_RUNTIME.status()

    response["ok"] = True

    return jsonify(
        response
    )


@app.route(
    "/mission/start",
    methods=["POST"]
)
def mission_start():
    try:
        status = MISSION_RUNTIME.start()

    except MissionPlanError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 409


    response = dict(
        status
    )

    response["ok"] = True

    return jsonify(
        response
    )


@app.route(
    "/mission/cancel",
    methods=["POST"]
)
def mission_cancel():
    response = MISSION_RUNTIME.cancel()

    response["ok"] = True

    return jsonify(
        response
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



# =========================================================
# NIVEL 2B - LOCALIZACION
# =========================================================

def nombre_mapa_seguro(nombre):
    return not (
        "/" in nombre
        or "\\" in nombre
        or ".." in nombre
    )


@app.route("/maps/<nombre>/meta")
def map_meta(nombre):

    if not nombre_mapa_seguro(nombre):
        return jsonify({
            "ok": False,
            "error": "Mapa invalido"
        }), 400

    yaml_path = (
        MAPS_DIR
        /
        (nombre + ".yaml")
    )

    pgm_path = (
        MAPS_DIR
        /
        (nombre + ".pgm")
    )

    if (
        not yaml_path.exists()
        or not pgm_path.exists()
    ):
        return jsonify({
            "ok": False,
            "error": "Mapa no encontrado"
        }), 404

    resolution = None
    origin = [
        0.0,
        0.0,
        0.0
    ]

    try:
        for linea in yaml_path.read_text().splitlines():

            linea = linea.strip()

            if linea.startswith("resolution:"):
                resolution = float(
                    linea.split(
                        ":",
                        1
                    )[1].strip()
                )

            elif linea.startswith("origin:"):
                valor = linea.split(
                    ":",
                    1
                )[1].strip()

                origin = list(
                    ast.literal_eval(
                        valor
                    )
                )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": (
                "No se pudo leer YAML: {}"
                .format(exc)
            )
        }), 500

    if (
        resolution is None
        or resolution <= 0
    ):
        return jsonify({
            "ok": False,
            "error": "Resolucion invalida"
        }), 500

    while len(origin) < 3:
        origin.append(0.0)

    imagen = cv2.imread(
        str(pgm_path),
        cv2.IMREAD_GRAYSCALE
    )

    if imagen is None:
        return jsonify({
            "ok": False,
            "error": "No se pudo leer PGM"
        }), 500

    height, width = imagen.shape[:2]

    return jsonify({
        "ok": True,
        "name": nombre,

        "resolution": float(
            resolution
        ),

        "origin": {
            "x": float(origin[0]),
            "y": float(origin[1]),
            "yaw": float(origin[2])
        },

        "width": int(width),
        "height": int(height)
    })


@app.route("/map_pose")
def map_pose():

    if not SAFEVISION_POSE_FILE.exists():
        return jsonify({
            "ok": False,
            "localized": False,
            "error": (
                "Pose AMCL no disponible"
            )
        }), 503

    try:
        datos = json.loads(
            SAFEVISION_POSE_FILE.read_text()
        )

        datos["localized"] = bool(
            datos.get(
                "ok",
                False
            )
        )

        datos["age_seconds"] = max(
            0.0,
            time.time()
            -
            SAFEVISION_POSE_FILE.stat().st_mtime
        )

        return jsonify(
            datos
        )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "localized": False,
            "error": (
                "Pose invalida: {}"
                .format(exc)
            )
        }), 500



@app.route("/initialpose", methods=["POST"])
def safevision_initialpose():

    datos = request.get_json(
        silent=True
    ) or {}

    try:
        x = float(
            datos["x"]
        )

        y = float(
            datos["y"]
        )

        yaw = float(
            datos["yaw"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):
        return jsonify({
            "ok": False,
            "error": (
                "Se requieren x, y y yaw numericos"
            )
        }), 400


    if not (
        math.isfinite(x)
        and math.isfinite(y)
        and math.isfinite(yaw)
    ):
        return jsonify({
            "ok": False,
            "error": "Pose invalida"
        }), 400


    request_id = "{:.6f}".format(
        time.time()
    )


    solicitud = {
        "request_id": request_id,
        "x": x,
        "y": y,
        "yaw": yaw,
        "created_at": time.time()
    }


    temporal = Path(
        str(
            SAFEVISION_INITIALPOSE_FILE
        )
        +
        ".tmp"
    )


    temporal.write_text(
        json.dumps(
            solicitud,
            sort_keys=True
        )
    )


    os.replace(
        str(temporal),
        str(
            SAFEVISION_INITIALPOSE_FILE
        )
    )


    return jsonify({
        "ok": True,
        "accepted": True,
        "request_id": request_id,
        "x": x,
        "y": y,
        "yaw": yaw
    }), 202



# =========================================================
# NIVEL 3C - PUENTE HTTP <-> COLA DE NAVEGACION
# =========================================================

def nav_status_callback(msg):
    global NAV_STATUS
    global NAV_STATUS_RECEIVED

    try:
        data = json.loads(
            msg.data
        )

        if isinstance(
            data,
            dict
        ):
            NAV_STATUS = data
            NAV_STATUS_RECEIVED = True

    except Exception:
        pass


def iniciar_nav_bridge():
    global NAV_COMMAND_PUB

    if not rospy.core.is_initialized():
        rospy.init_node(
            "safevision_robot_server",
            anonymous=False,
            disable_signals=True
        )

    NAV_COMMAND_PUB = rospy.Publisher(
        "/safevision/nav/command",
        String,
        queue_size=10
    )

    rospy.Subscriber(
        "/safevision/nav/status",
        String,
        nav_status_callback,
        queue_size=20
    )


def publicar_nav_command(data):
    if NAV_COMMAND_PUB is None:
        return False

    if (
        NAV_COMMAND_PUB.get_num_connections()
        < 1
    ):
        return False

    NAV_COMMAND_PUB.publish(
        String(
            data=json.dumps(
                data,
                separators=(",", ":")
            )
        )
    )

    return True


@app.route("/nav/status")
def nav_status():
    response = dict(
        NAV_STATUS
    )

    response["available"] = bool(
        NAV_STATUS_RECEIVED
    )

    return jsonify(
        response
    )


@app.route(
    "/nav/queue",
    methods=["POST"]
)
def nav_queue_load():
    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):
        return jsonify({
            "ok": False,
            "error": "JSON inválido"
        }), 400

    map_name = data.get(
        "map"
    )

    points = data.get(
        "points"
    )

    if (
        not isinstance(map_name, str)
        or not map_name.strip()
    ):
        return jsonify({
            "ok": False,
            "error": "Falta mapa"
        }), 400

    if not isinstance(
        points,
        list
    ):
        return jsonify({
            "ok": False,
            "error": "points debe ser una lista"
        }), 400

    if len(points) > 50:
        return jsonify({
            "ok": False,
            "error": "Máximo 50 puntos"
        }), 400

    command = {
        "command": "load",
        "map": map_name.strip(),
        "points": points
    }

    if not publicar_nav_command(
        command
    ):
        return jsonify({
            "ok": False,
            "error": "Cola de navegación no disponible"
        }), 503

    return jsonify({
        "ok": True,
        "accepted": True,
        "command": "load",
        "count": len(points)
    }), 202


def nav_simple_command(
    command
):
    if not publicar_nav_command({
        "command": command
    }):
        return jsonify({
            "ok": False,
            "error": "Cola de navegación no disponible"
        }), 503

    return jsonify({
        "ok": True,
        "accepted": True,
        "command": command
    }), 202


@app.route(
    "/nav/start",
    methods=["POST"]
)
def nav_start():
    return nav_simple_command(
        "start"
    )


@app.route(
    "/nav/cancel",
    methods=["POST"]
)
def nav_cancel():
    return nav_simple_command(
        "cancel"
    )


@app.route(
    "/nav/clear",
    methods=["POST"]
)
def nav_clear():
    return nav_simple_command(
        "clear"
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

    iniciar_nav_bridge()

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
