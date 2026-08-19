#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import ast
import json
import math
import io
import os
import shutil
import zipfile
import socket
import subprocess
import sys
import threading
import time
import uuid
import xmlrpc.client
from pathlib import Path

import cv2
import numpy as np
import rospy
from std_msgs.msg import String
from nav_msgs.msg import OccupancyGrid
from flask import (
    Flask,
    Response,
    after_this_request,
    jsonify,
    request,
    send_file
)

import sf_mapping_manager
import sf_model_manager
import sf_runtime_manager


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

MODEL_MANAGER = sf_model_manager.ModelManager()

CONTROL_MODE = "desconocido"

NAV_COMMAND_PUB = None
NAV_STATUS_RECEIVED = False
NAV_STATUS_VERSION = 0

NAV_STATUS = {
    "state": "unavailable",
    "running": False,
    "operation": None,
    "operation_map": None,
    "request_id": None,
    "orientation_target": None,
    "remaining": [],
    "remaining_count": 0,
    "completed": [],
    "completed_count": 0,
    "current": None,
    "map": None,
    "active_map": None,
    "message": "Cola de navegación no disponible"
}


# =========================================================
# MAPA ROS EN VIVO
# Fuente: /map (nav_msgs/OccupancyGrid)
# =========================================================

LIVE_MAP_LOCK = threading.Lock()

LIVE_MAP_PNG = None
LIVE_MAP_META = None
LIVE_MAP_VERSION = 0


CAMERA_DEVICE = "/dev/video0"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
CAMERA_FOURCC = "MJPG"
JPEG_QUALITY = 70


# =========================================================
# CAMARA COMPARTIDA
# Una sola captura fisica para todos los clientes MJPEG.
# =========================================================

CAMERA_SHARED_CONDITION = threading.Condition()

CAMERA_SHARED_FRAME = None
CAMERA_SHARED_VERSION = 0
CAMERA_SHARED_THREAD = None


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


def camera_capture_loop():
    global CAMERA_SHARED_FRAME
    global CAMERA_SHARED_VERSION

    cap = None

    while True:

        if (
            cap is None
            or
            not cap.isOpened()
        ):

            if cap is not None:
                cap.release()

            cap = cv2.VideoCapture(
                CAMERA_DEVICE,
                cv2.CAP_V4L2
            )

            cap.set(
                cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter_fourcc(
                    *CAMERA_FOURCC
                )
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

            fourcc_value = int(
                cap.get(
                    cv2.CAP_PROP_FOURCC
                )
            )

            fourcc_actual = "".join(
                chr(
                    (
                        fourcc_value
                        >>
                        (8 * index)
                    )
                    &
                    0xFF
                )
                for index in range(4)
            )

            print(
                "[CAMARA] dispositivo={} "
                "formato={} "
                "resolucion={}x{} "
                "fps={}".format(
                    CAMERA_DEVICE,
                    fourcc_actual,
                    int(
                        cap.get(
                            cv2.CAP_PROP_FRAME_WIDTH
                        )
                    ),
                    int(
                        cap.get(
                            cv2.CAP_PROP_FRAME_HEIGHT
                        )
                    ),
                    cap.get(
                        cv2.CAP_PROP_FPS
                    )
                )
            )

            if not cap.isOpened():

                cap.release()
                cap = None

                time.sleep(1.0)
                continue


        success, frame = cap.read()

        if not success:

            cap.release()
            cap = None

            time.sleep(0.20)
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


        jpeg = buffer.tobytes()


        with CAMERA_SHARED_CONDITION:

            CAMERA_SHARED_FRAME = jpeg

            CAMERA_SHARED_VERSION += 1

            CAMERA_SHARED_CONDITION.notify_all()


def iniciar_camara_compartida():
    global CAMERA_SHARED_THREAD

    with CAMERA_SHARED_CONDITION:

        if (
            CAMERA_SHARED_THREAD is not None
            and
            CAMERA_SHARED_THREAD.is_alive()
        ):
            return


        CAMERA_SHARED_THREAD = threading.Thread(
            target=camera_capture_loop,
            name="safevision-camera",
            daemon=True
        )


        CAMERA_SHARED_THREAD.start()


def generar_frames():

    iniciar_camara_compartida()

    last_version = -1


    while True:

        with CAMERA_SHARED_CONDITION:

            CAMERA_SHARED_CONDITION.wait_for(
                lambda: (
                    CAMERA_SHARED_FRAME is not None
                    and
                    CAMERA_SHARED_VERSION
                    !=
                    last_version
                ),
                timeout=2.0
            )


            if (
                CAMERA_SHARED_FRAME is None
                or
                CAMERA_SHARED_VERSION
                ==
                last_version
            ):
                continue


            jpeg = CAMERA_SHARED_FRAME

            last_version = CAMERA_SHARED_VERSION


        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            +
            jpeg
            +
            b"\r\n"
        )



@app.route("/")
def index():
    return jsonify({
        "service": "SafeVision Robot Server",
        "level": 2,
        "ip": obtener_ip(),
        "video": "/video_feed",
        "health": "/health",
        "runtime": "/runtime/status",
        "runtime_profile": "/runtime/profile",
        "runtime_control": "/runtime/control"
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


# =========================================================
# SAFEVISION RUNTIME MANAGER · ETAPA 1
# Observabilidad solamente. No arranca ni detiene nodos.
# =========================================================

@app.route("/runtime/status")
def runtime_status():

    return jsonify(
        sf_runtime_manager.status(
            CONTROL_MODE
        )
    )


@app.route(
    "/runtime/profile",
    methods=["POST"]
)
def runtime_profile():

    global CONTROL_MODE

    data = request.get_json(
        silent=True
    ) or {}

    profile = data.get("profile")
    map_name = data.get("map")
    control = data.get("control") or CONTROL_MODE

    result = sf_runtime_manager.apply_profile(
        profile,
        map_name=map_name,
        control_mode=control
    )

    if result.get("ok") and control in ("mando", "teclado"):
        CONTROL_MODE = control

    return jsonify(result), (200 if result.get("ok") else 409)


@app.route(
    "/runtime/control",
    methods=["POST"]
)
def runtime_control():

    global CONTROL_MODE

    data = request.get_json(
        silent=True
    ) or {}

    mode = data.get(
        "mode"
    )

    result = sf_runtime_manager.set_control_mode(
        mode
    )

    if result.get(
        "ok"
    ):
        CONTROL_MODE = str(
            mode
        ).strip().lower()

    return jsonify(
        result
    ), (
        200
        if result.get("ok")
        else 409
    )


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


MISSION_NAV_LOAD_TIMEOUT = 3.0
MISSION_NAV_RESULT_TIMEOUT = 180.0
MISSION_NAV_ORIENTATION_TIMEOUT = 40.0
MISSION_NAV_POLL_INTERVAL = 0.05

MISSION_NAV_POSITION_TOLERANCE = 1e-6
MISSION_NAV_YAW_TOLERANCE = 1e-6


def mission_nav_snapshot():
    return (
        dict(NAV_STATUS),
        bool(NAV_STATUS_RECEIVED),
        int(NAV_STATUS_VERSION)
    )


def mission_nav_yaw_matches(
    expected,
    actual
):
    if (
        expected is None
        or actual is None
    ):
        return (
            expected is None
            and actual is None
        )

    try:
        expected = float(
            expected
        )

        actual = float(
            actual
        )

    except Exception:
        return False


    delta = math.atan2(
        math.sin(
            actual
            -
            expected
        ),
        math.cos(
            actual
            -
            expected
        )
    )

    return (
        abs(delta)
        <=
        MISSION_NAV_YAW_TOLERANCE
    )


def mission_nav_point_matches(
    expected,
    actual
):
    if not isinstance(
        expected,
        dict
    ):
        return False

    if not isinstance(
        actual,
        dict
    ):
        return False


    if str(
        actual.get("id")
    ) != str(
        expected.get("id")
    ):
        return False


    try:
        dx = abs(
            float(actual["x"])
            -
            float(expected["x"])
        )

        dy = abs(
            float(actual["y"])
            -
            float(expected["y"])
        )

    except Exception:
        return False


    if (
        dx
        >
        MISSION_NAV_POSITION_TOLERANCE
    ):
        return False

    if (
        dy
        >
        MISSION_NAV_POSITION_TOLERANCE
    ):
        return False


    return mission_nav_yaw_matches(
        expected.get("yaw"),
        actual.get("yaw")
    )


def mission_nav_ready_matches(
    status,
    map_name,
    point
):
    if not isinstance(
        status,
        dict
    ):
        return False


    if status.get(
        "state"
    ) != "ready":
        return False


    if bool(
        status.get(
            "running"
        )
    ):
        return False


    if status.get(
        "map"
    ) != map_name:
        return False


    if status.get(
        "active_map"
    ) != map_name:
        return False


    remaining = status.get(
        "remaining"
    )

    if not isinstance(
        remaining,
        list
    ):
        return False

    if len(
        remaining
    ) != 1:
        return False


    if not mission_nav_point_matches(
        point,
        remaining[0]
    ):
        return False


    if int(
        status.get(
            "completed_count",
            0
        )
    ) != 0:
        return False


    return True


def mission_orientation_status_matches(
    status,
    map_name,
    request_id,
    target_yaw
):
    if not isinstance(
        status,
        dict
    ):
        return False

    if status.get(
        "operation"
    ) != "orient":
        return False

    if status.get(
        "operation_map"
    ) != map_name:
        return False

    if str(
        status.get(
            "request_id",
            ""
        )
    ) != str(
        request_id
    ):
        return False

    return mission_nav_yaw_matches(
        target_yaw,
        status.get(
            "orientation_target"
        )
    )


def mission_execute_orientation_action(
    map_name,
    action,
    cancel_event,
    report
):
    if not isinstance(
        map_name,
        str
    ) or not map_name:
        raise RuntimeError(
            "La misión no tiene mapa válido"
        )

    try:
        target_yaw = float(
            action.get(
                "target_yaw"
            )
        )

    except Exception:
        raise RuntimeError(
            "orientar() no contiene target_yaw válido"
        )

    if not math.isfinite(
        target_yaw
    ):
        raise RuntimeError(
            "orientar() contiene target_yaw no finito"
        )

    target_yaw = math.atan2(
        math.sin(
            target_yaw
        ),
        math.cos(
            target_yaw
        )
    )

    if cancel_event.is_set():
        return

    status, available, command_version = (
        mission_nav_snapshot()
    )

    if not available:
        raise RuntimeError(
            "Cola de navegación no disponible"
        )

    request_id = (
        "mission-orient-{}"
        .format(
            uuid.uuid4().hex
        )
    )

    command = {
        "command": "orient",
        "map": map_name,
        "request_id": request_id,
        "target_yaw": target_yaw
    }

    if not publicar_nav_command(
        command
    ):
        raise RuntimeError(
            "No se pudo publicar orient"
        )

    report(
        "orienting",
        "Iniciando orientación"
    )

    deadline = (
        time.monotonic()
        +
        MISSION_NAV_ORIENTATION_TIMEOUT
    )

    while (
        time.monotonic()
        <
        deadline
    ):
        if cancel_event.is_set():
            publicar_nav_command({
                "command": "cancel"
            })

            return

        status, available, version = (
            mission_nav_snapshot()
        )

        if (
            not available
            or
            version <= command_version
        ):
            time.sleep(
                MISSION_NAV_POLL_INTERVAL
            )

            continue

        if not mission_orientation_status_matches(
            status,
            map_name,
            request_id,
            target_yaw
        ):
            time.sleep(
                MISSION_NAV_POLL_INTERVAL
            )

            continue

        state = status.get(
            "state"
        )

        message = status.get(
            "message",
            ""
        )

        if (
            state == "completed"
            and
            not bool(
                status.get(
                    "running"
                )
            )
        ):
            return

        if state == "error":
            raise RuntimeError(
                message
                or
                "Error durante orientación"
            )

        if state == "cancelled":
            raise RuntimeError(
                message
                or
                "Orientación cancelada"
            )

        report(
            "orienting",
            message
            or
            "Orientando"
        )

        time.sleep(
            MISSION_NAV_POLL_INTERVAL
        )

    publicar_nav_command({
        "command": "cancel"
    })

    raise RuntimeError(
        "Timeout esperando orientación"
    )


def mission_execute_nav_action(
    map_name,
    action,
    cancel_event,
    report
):
    if not isinstance(
        map_name,
        str
    ) or not map_name:
        raise RuntimeError(
            "La misión no tiene mapa válido"
        )


    point = action.get(
        "point"
    )

    if not isinstance(
        point,
        dict
    ):
        raise RuntimeError(
            "La acción ir() no contiene punto"
        )


    nav_point = {
        "id": str(
            point["id"]
        ),
        "x": float(
            point["x"]
        ),
        "y": float(
            point["y"]
        ),
        "yaw": (
            None
            if point.get("yaw") is None
            else float(
                point["yaw"]
            )
        )
    }


    status, available, load_version = (
        mission_nav_snapshot()
    )

    if not available:
        raise RuntimeError(
            "Cola de navegación no disponible"
        )


    load_command = {
        "command": "load",
        "map": map_name,
        "points": [
            nav_point
        ]
    }


    if not publicar_nav_command(
        load_command
    ):
        raise RuntimeError(
            "No se pudo publicar load"
        )


    report(
        "navigating",
        "Preparando navegación hacia {}".format(
            nav_point["id"]
        )
    )


    deadline = (
        time.monotonic()
        +
        MISSION_NAV_LOAD_TIMEOUT
    )


    while (
        time.monotonic()
        <
        deadline
    ):
        if cancel_event.is_set():
            publicar_nav_command({
                "command": "clear"
            })

            return


        status, available, version = (
            mission_nav_snapshot()
        )


        if (
            available
            and
            version > load_version
            and
            mission_nav_ready_matches(
                status,
                map_name,
                nav_point
            )
        ):
            break


        if (
            available
            and
            version > load_version
            and
            status.get("state") == "error"
            and
            status.get("map") == map_name
        ):
            raise RuntimeError(
                status.get(
                    "message",
                    "Error cargando navegación"
                )
            )


        time.sleep(
            MISSION_NAV_POLL_INTERVAL
        )

    else:
        raise RuntimeError(
            "Timeout confirmando cola de navegación"
        )


    start_version = (
        mission_nav_snapshot()[2]
    )


    if cancel_event.is_set():
        publicar_nav_command({
            "command": "clear"
        })

        return


    if not publicar_nav_command({
        "command": "start"
    }):
        raise RuntimeError(
            "No se pudo publicar start"
        )


    report(
        "navigating",
        "Navegando hacia {}".format(
            nav_point["id"]
        )
    )


    deadline = (
        time.monotonic()
        +
        MISSION_NAV_RESULT_TIMEOUT
    )


    while (
        time.monotonic()
        <
        deadline
    ):
        if cancel_event.is_set():
            publicar_nav_command({
                "command": "cancel"
            })

            return


        status, available, version = (
            mission_nav_snapshot()
        )


        if (
            not available
            or
            version <= start_version
        ):
            time.sleep(
                MISSION_NAV_POLL_INTERVAL
            )

            continue


        state = status.get(
            "state"
        )

        message = status.get(
            "message",
            ""
        )


        if state == "completed":
            completed = status.get(
                "completed"
            )

            if not isinstance(
                completed,
                list
            ) or len(
                completed
            ) != 1:
                raise RuntimeError(
                    "Estado completed sin punto confirmado"
                )


            if not mission_nav_point_matches(
                nav_point,
                completed[0]
            ):
                raise RuntimeError(
                    "El punto completado no coincide con ir()"
                )


            if int(
                status.get(
                    "remaining_count",
                    -1
                )
            ) != 0:
                raise RuntimeError(
                    "Navegación completada con puntos pendientes"
                )


            return


        if state == "error":
            raise RuntimeError(
                message
                or
                "Error de navegación"
            )


        if state == "cancelled":
            raise RuntimeError(
                message
                or
                "Navegación cancelada"
            )


        if state == "relocalizing":
            report(
                "relocalizing",
                message
                or
                "Relocalizando"
            )

        else:
            report(
                "navigating",
                message
                or
                "Navegando"
            )


        time.sleep(
            MISSION_NAV_POLL_INTERVAL
        )


    publicar_nav_command({
        "command": "cancel"
    })

    raise RuntimeError(
        "Timeout esperando navegación"
    )


@app.route(
    "/mission/start",
    methods=["POST"]
)
def mission_start():
    runtime_status = (
        MISSION_RUNTIME.status()
    )

    mission_map = runtime_status.get(
        "map"
    )


    def action_executor(
        action,
        cancel_event,
        report
    ):
        action_name = action.get(
            "name"
        )

        if action_name == "ir":
            return mission_execute_nav_action(
                mission_map,
                action,
                cancel_event,
                report
            )

        if action_name == "orientar":
            return mission_execute_orientation_action(
                mission_map,
                action,
                cancel_event,
                report
            )

        raise RuntimeError(
            "Acción sin adapter: {}".format(
                action_name
            )
        )


    try:
        status = MISSION_RUNTIME.start(
            action_executor,
            executor_actions={
                "ir",
                "orientar"
            }
        )

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


# =========================================================
# GESTION DE MAPAS
# =========================================================

def normalizar_nombre_mapa(nombre):

    if not isinstance(
        nombre,
        str
    ):
        return None


    nombre = nombre.strip()


    if (
        not nombre
        or len(nombre) > 80
        or not nombre_mapa_seguro(nombre)
    ):
        return None


    if nombre.lower().endswith(
        (
            ".yaml",
            ".pgm",
            ".zip"
        )
    ):
        return None


    if any(
        ord(char) < 32
        for char in nombre
    ):
        return None


    return nombre


def rutas_mapa(nombre):

    return (
        MAPS_DIR / (
            nombre + ".yaml"
        ),
        MAPS_DIR / (
            nombre + ".pgm"
        )
    )


def mapa_completo(nombre):

    yaml_path, pgm_path = (
        rutas_mapa(nombre)
    )

    return (
        yaml_path.is_file()
        and
        pgm_path.is_file()
    )


def nombre_mapa_ocupado(
    nombre,
    excluir=None
):

    objetivo = nombre.casefold()

    excluir_cf = (
        excluir.casefold()
        if isinstance(
            excluir,
            str
        )
        else None
    )


    if not MAPS_DIR.exists():
        return None


    vistos = set()


    for pattern in (
        "*.yaml",
        "*.pgm"
    ):

        for path in MAPS_DIR.glob(
            pattern
        ):

            stem = path.stem

            key = stem.casefold()


            if key in vistos:
                continue


            vistos.add(
                key
            )


            if (
                excluir_cf is not None
                and key == excluir_cf
            ):
                continue


            if key == objetivo:
                return stem


    return None


def yaml_con_imagen(
    contenido,
    nuevo_nombre
):

    lineas = contenido.splitlines(
        keepends=True
    )


    for index, linea in enumerate(
        lineas
    ):

        stripped = linea.lstrip()


        if not stripped.startswith(
            "image:"
        ):
            continue


        prefijo = linea[
            :len(linea) - len(stripped)
        ]


        if linea.endswith(
            "\r\n"
        ):
            final = "\r\n"

        elif linea.endswith(
            "\n"
        ):
            final = "\n"

        else:
            final = ""


        lineas[index] = (
            prefijo
            +
            "image: "
            +
            nuevo_nombre
            +
            ".pgm"
            +
            final
        )


        return "".join(
            lineas
        )


    return None


def error_mapa(
    mensaje,
    codigo
):

    return jsonify({
        "ok": False,
        "error": mensaje
    }), codigo


@app.route(
    "/maps/rename",
    methods=["POST"]
)
def map_rename():

    data = request.get_json(
        silent=True
    ) or {}


    nombre = normalizar_nombre_mapa(
        data.get("name")
    )

    nuevo = normalizar_nombre_mapa(
        data.get("new_name")
    )


    if not nombre or not nuevo:

        return error_mapa(
            "Nombre de mapa invalido",
            400
        )


    if not mapa_completo(
        nombre
    ):

        return error_mapa(
            "Mapa no encontrado",
            404
        )


    if nombre == nuevo:

        return error_mapa(
            "El nuevo nombre es igual al actual",
            409
        )


    ocupado = nombre_mapa_ocupado(
        nuevo,
        excluir=nombre
    )


    if ocupado is not None:

        return error_mapa(
            (
                "Ya existe un mapa llamado "
                "'{}'".format(
                    ocupado
                )
            ),
            409
        )


    old_yaml, old_pgm = (
        rutas_mapa(nombre)
    )

    new_yaml, new_pgm = (
        rutas_mapa(nuevo)
    )


    try:

        contenido = (
            old_yaml.read_text()
        )


        contenido_nuevo = (
            yaml_con_imagen(
                contenido,
                nuevo
            )
        )


        if contenido_nuevo is None:

            return error_mapa(
                "El YAML no contiene image:",
                409
            )


        tmp_yaml = MAPS_DIR / (
            ".maprename-{}-{}.yaml".format(
                os.getpid(),
                int(
                    time.time()
                    *
                    1000
                )
            )
        )

        tmp_pgm = MAPS_DIR / (
            ".maprename-{}-{}.pgm".format(
                os.getpid(),
                int(
                    time.time()
                    *
                    1000
                )
            )
        )


        tmp_yaml.write_text(
            contenido_nuevo
        )

        shutil.copy2(
            str(old_pgm),
            str(tmp_pgm)
        )


        tmp_yaml.replace(
            new_yaml
        )

        tmp_pgm.replace(
            new_pgm
        )


        old_yaml.unlink()
        old_pgm.unlink()


        return jsonify({
            "ok": True,
            "name": nuevo,
            "message": (
                "Mapa renombrado correctamente."
            )
        })


    except Exception as exc:

        return error_mapa(
            "No se pudo renombrar: {}".format(
                exc
            ),
            500
        )


@app.route(
    "/maps/duplicate",
    methods=["POST"]
)
def map_duplicate():

    data = request.get_json(
        silent=True
    ) or {}


    nombre = normalizar_nombre_mapa(
        data.get("name")
    )

    nuevo = normalizar_nombre_mapa(
        data.get("new_name")
    )


    if not nombre or not nuevo:

        return error_mapa(
            "Nombre de mapa invalido",
            400
        )


    if not mapa_completo(
        nombre
    ):

        return error_mapa(
            "Mapa no encontrado",
            404
        )


    ocupado = nombre_mapa_ocupado(
        nuevo
    )


    if ocupado is not None:

        return error_mapa(
            (
                "Ya existe un mapa llamado "
                "'{}'".format(
                    ocupado
                )
            ),
            409
        )


    old_yaml, old_pgm = (
        rutas_mapa(nombre)
    )

    new_yaml, new_pgm = (
        rutas_mapa(nuevo)
    )


    try:

        contenido_nuevo = (
            yaml_con_imagen(
                old_yaml.read_text(),
                nuevo
            )
        )


        if contenido_nuevo is None:

            return error_mapa(
                "El YAML no contiene image:",
                409
            )


        shutil.copy2(
            str(old_pgm),
            str(new_pgm)
        )


        try:

            new_yaml.write_text(
                contenido_nuevo
            )

        except Exception:

            if new_pgm.exists():
                new_pgm.unlink()

            raise


        return jsonify({
            "ok": True,
            "name": nuevo,
            "source": nombre,
            "message": (
                "Mapa duplicado correctamente."
            )
        })


    except Exception as exc:

        return error_mapa(
            "No se pudo duplicar: {}".format(
                exc
            ),
            500
        )


@app.route(
    "/maps/delete",
    methods=["POST"]
)
def map_delete():

    data = request.get_json(
        silent=True
    ) or {}


    nombre = normalizar_nombre_mapa(
        data.get("name")
    )


    if not nombre:

        return error_mapa(
            "Nombre de mapa invalido",
            400
        )


    if not mapa_completo(
        nombre
    ):

        return error_mapa(
            "Mapa no encontrado",
            404
        )


    yaml_path, pgm_path = (
        rutas_mapa(nombre)
    )


    trash_dir = (
        MAPS_DIR
        /
        ".safevision_delete"
    )


    trash_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    token = "{}-{}".format(
        os.getpid(),
        int(
            time.time()
            *
            1000
        )
    )


    trash_yaml = (
        trash_dir
        /
        (
            token
            +
            "-"
            +
            nombre
            +
            ".yaml"
        )
    )

    trash_pgm = (
        trash_dir
        /
        (
            token
            +
            "-"
            +
            nombre
            +
            ".pgm"
        )
    )


    try:

        yaml_path.replace(
            trash_yaml
        )


        try:

            pgm_path.replace(
                trash_pgm
            )

        except Exception:

            trash_yaml.replace(
                yaml_path
            )

            raise


        try:
            trash_yaml.unlink()
        except Exception:
            pass


        try:
            trash_pgm.unlink()
        except Exception:
            pass


        return jsonify({
            "ok": True,
            "name": nombre,
            "message": (
                "Mapa eliminado correctamente."
            )
        })


    except Exception as exc:

        return error_mapa(
            "No se pudo eliminar: {}".format(
                exc
            ),
            500
        )



# =========================================================
# TRANSFERENCIA DE MAPAS
# =========================================================

def nombre_descarga_mapa(
    nombre
):

    limpio = "".join(
        char
        if (
            char.isalnum()
            or char in "._-"
        )
        else "_"
        for char in nombre
    )

    return limpio or "mapa"


@app.route(
    "/maps/<nombre>/export",
    methods=["GET"]
)
def map_export(
    nombre
):

    nombre = normalizar_nombre_mapa(
        nombre
    )


    if not nombre:

        return error_mapa(
            "Nombre de mapa invalido",
            400
        )


    if not mapa_completo(
        nombre
    ):

        return error_mapa(
            "Mapa no encontrado",
            404
        )


    yaml_path, pgm_path = (
        rutas_mapa(nombre)
    )


    output = io.BytesIO()


    try:

        with zipfile.ZipFile(
            output,
            "w",
            compression=zipfile.ZIP_DEFLATED
        ) as archive:

            archive.write(
                str(yaml_path),
                arcname=(
                    nombre
                    +
                    ".yaml"
                )
            )

            archive.write(
                str(pgm_path),
                arcname=(
                    nombre
                    +
                    ".pgm"
                )
            )


        payload = output.getvalue()

        safe_name = nombre_descarga_mapa(
            nombre
        )


        return Response(
            payload,
            mimetype="application/zip",
            headers={
                "Content-Disposition":
                    (
                        'attachment; filename="'
                        +
                        safe_name
                        +
                        '.zip"'
                    )
            }
        )


    except Exception as exc:

        return error_mapa(
            "No se pudo exportar: {}".format(
                exc
            ),
            500
        )


@app.route(
    "/maps/import",
    methods=["POST"]
)
def map_import():

    uploaded = request.files.get(
        "file"
    )


    if uploaded is None:

        return error_mapa(
            "Falta el archivo ZIP",
            400
        )


    filename = (
        uploaded.filename
        or ""
    )


    if not filename.lower().endswith(
        ".zip"
    ):

        return error_mapa(
            "Solo se permiten archivos ZIP",
            400
        )


    try:

        payload = uploaded.read()

    except Exception as exc:

        return error_mapa(
            "No se pudo leer el archivo: {}".format(
                exc
            ),
            400
        )


    if not payload:

        return error_mapa(
            "El archivo ZIP esta vacio",
            400
        )


    if len(payload) > 20 * 1024 * 1024:

        return error_mapa(
            "El archivo ZIP supera 20 MB",
            413
        )


    try:

        archive = zipfile.ZipFile(
            io.BytesIO(
                payload
            ),
            "r"
        )

    except Exception:

        return error_mapa(
            "El archivo no es un ZIP valido",
            400
        )


    try:

        infos = [
            item
            for item in archive.infolist()
            if not item.is_dir()
        ]


        if len(infos) != 2:

            return error_mapa(
                (
                    "El ZIP debe contener exactamente "
                    "un YAML y un PGM"
                ),
                400
            )


        for item in infos:

            raw_name = item.filename


            if (
                "/"
                in raw_name
                or "\\"
                in raw_name
                or raw_name
                in (
                    ".",
                    ".."
                )
            ):

                return error_mapa(
                    "El ZIP no debe contener carpetas",
                    400
                )


            if item.file_size > 30 * 1024 * 1024:

                return error_mapa(
                    "Archivo interno demasiado grande",
                    413
                )


        yaml_infos = [
            item
            for item in infos
            if item.filename.lower().endswith(
                ".yaml"
            )
        ]

        pgm_infos = [
            item
            for item in infos
            if item.filename.lower().endswith(
                ".pgm"
            )
        ]


        if (
            len(yaml_infos) != 1
            or len(pgm_infos) != 1
        ):

            return error_mapa(
                (
                    "El ZIP debe contener "
                    "un .yaml y un .pgm"
                ),
                400
            )


        yaml_info = yaml_infos[0]
        pgm_info = pgm_infos[0]


        yaml_base = Path(
            yaml_info.filename
        ).stem

        pgm_base = Path(
            pgm_info.filename
        ).stem


        if (
            yaml_base.casefold()
            !=
            pgm_base.casefold()
        ):

            return error_mapa(
                (
                    "El YAML y PGM deben tener "
                    "el mismo nombre base"
                ),
                400
            )


        requested_name = (
            request.form.get(
                "name"
            )
            or yaml_base
        )


        nombre = normalizar_nombre_mapa(
            requested_name
        )


        if not nombre:

            return error_mapa(
                "Nombre de mapa invalido",
                400
            )


        ocupado = nombre_mapa_ocupado(
            nombre
        )


        if ocupado is not None:

            return error_mapa(
                (
                    "Ya existe un mapa llamado "
                    "'{}'".format(
                        ocupado
                    )
                ),
                409
            )


        try:

            yaml_original = (
                archive.read(
                    yaml_info
                )
                .decode(
                    "utf-8"
                )
            )

        except Exception:

            return error_mapa(
                "No se pudo leer el YAML",
                400
            )


        pgm_data = archive.read(
            pgm_info
        )


        if not (
            pgm_data.startswith(
                b"P5"
            )
            or pgm_data.startswith(
                b"P2"
            )
        ):

            return error_mapa(
                "El archivo PGM no es valido",
                400
            )


        yaml_final = yaml_con_imagen(
            yaml_original,
            nombre
        )


        if yaml_final is None:

            return error_mapa(
                "El YAML no contiene image:",
                400
            )


        MAPS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )


        yaml_path, pgm_path = (
            rutas_mapa(
                nombre
            )
        )


        token = "{}-{}".format(
            os.getpid(),
            int(
                time.time()
                *
                1000
            )
        )


        tmp_yaml = (
            MAPS_DIR
            /
            (
                ".import-"
                +
                token
                +
                ".yaml"
            )
        )

        tmp_pgm = (
            MAPS_DIR
            /
            (
                ".import-"
                +
                token
                +
                ".pgm"
            )
        )


        try:

            tmp_yaml.write_text(
                yaml_final
            )

            tmp_pgm.write_bytes(
                pgm_data
            )


            tmp_yaml.replace(
                yaml_path
            )

            tmp_pgm.replace(
                pgm_path
            )


        except Exception:

            for path in (
                tmp_yaml,
                tmp_pgm
            ):

                try:

                    if path.exists():
                        path.unlink()

                except Exception:
                    pass


            for path in (
                yaml_path,
                pgm_path
            ):

                try:

                    if path.exists():
                        path.unlink()

                except Exception:
                    pass


            raise


        return jsonify({
            "ok": True,
            "name": nombre,
            "message": (
                "Mapa importado correctamente."
            )
        })


    except Exception as exc:

        return error_mapa(
            "No se pudo importar: {}".format(
                exc
            ),
            500
        )


    finally:

        try:
            archive.close()
        except Exception:
            pass



# =========================================================
# EDITOR WEB DE MAPAS
# =========================================================

def validar_pgm_editor(
    payload
):

    if not isinstance(
        payload,
        bytes
    ):
        return None, "Contenido invalido"


    if len(payload) > 40 * 1024 * 1024:
        return None, "PGM demasiado grande"


    try:

        partes = payload.split(
            b"\n",
            3
        )


        if len(partes) != 4:

            return None, "Cabecera PGM invalida"


        magic = partes[0].strip()

        if magic != b"P5":

            return None, (
                "Solo se acepta PGM binario P5"
            )


        dimensiones = (
            partes[1]
            .strip()
            .split()
        )


        if len(dimensiones) != 2:

            return None, "Dimensiones PGM invalidas"


        width = int(
            dimensiones[0]
        )

        height = int(
            dimensiones[1]
        )


        max_value = int(
            partes[2].strip()
        )


        if (
            width <= 0
            or height <= 0
            or width > 10000
            or height > 10000
        ):

            return None, "Dimensiones fuera de rango"


        if max_value != 255:

            return None, "PGM debe utilizar maximo 255"


        pixels = partes[3]


        if len(pixels) != width * height:

            return None, (
                "Cantidad de pixeles invalida"
            )


        return (
            {
                "width": width,
                "height": height,
                "pixels": pixels
            },
            None
        )


    except Exception as exc:

        return None, (
            "PGM invalido: {}"
            .format(
                exc
            )
        )


@app.route(
    "/maps/<nombre>/edit",
    methods=["POST"]
)
def map_edit(
    nombre
):

    nombre = normalizar_nombre_mapa(
        nombre
    )


    if not nombre:

        return error_mapa(
            "Nombre de mapa invalido",
            400
        )


    if not mapa_completo(
        nombre
    ):

        return error_mapa(
            "Mapa no encontrado",
            404
        )


    payload = request.get_data(
        cache=False
    )


    parsed, error_text = (
        validar_pgm_editor(
            payload
        )
    )


    if parsed is None:

        return error_mapa(
            error_text,
            400
        )


    yaml_path, pgm_path = (
        rutas_mapa(
            nombre
        )
    )


    original = cv2.imread(
        str(pgm_path),
        cv2.IMREAD_GRAYSCALE
    )


    if original is None:

        return error_mapa(
            "No se pudo leer el PGM original",
            500
        )


    original_height, original_width = (
        original.shape[:2]
    )


    if (
        parsed["width"]
        != original_width
        or parsed["height"]
        != original_height
    ):

        return error_mapa(
            (
                "El editor no puede cambiar "
                "las dimensiones del mapa"
            ),
            409
        )


    backup_dir = (
        MAPS_DIR
        /
        ".safevision_edit_backup"
    )


    backup_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    backup_path = (
        backup_dir
        /
        (
            nombre
            +
            ".pgm"
        )
    )


    token = "{}-{}".format(
        os.getpid(),
        int(
            time.time()
            *
            1000
        )
    )


    tmp_path = (
        MAPS_DIR
        /
        (
            ".edit-"
            +
            token
            +
            ".pgm"
        )
    )


    try:

        shutil.copy2(
            str(pgm_path),
            str(backup_path)
        )


        tmp_path.write_bytes(
            payload
        )


        prueba = cv2.imread(
            str(tmp_path),
            cv2.IMREAD_GRAYSCALE
        )


        if prueba is None:

            raise RuntimeError(
                "OpenCV no pudo validar el PGM editado"
            )


        ph, pw = prueba.shape[:2]


        if (
            pw != original_width
            or ph != original_height
        ):

            raise RuntimeError(
                "Dimensiones alteradas al validar"
            )


        tmp_path.replace(
            pgm_path
        )


        return jsonify({
            "ok": True,
            "name": nombre,
            "width": original_width,
            "height": original_height,
            "message": (
                "Mapa guardado correctamente."
            )
        })


    except Exception as exc:

        try:

            if tmp_path.exists():
                tmp_path.unlink()

        except Exception:
            pass


        return error_mapa(
            "No se pudo guardar: {}".format(
                exc
            ),
            500
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
    global NAV_STATUS_VERSION

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
            NAV_STATUS_VERSION += 1

    except Exception:
        pass


def live_map_callback(msg):
    global LIVE_MAP_PNG
    global LIVE_MAP_META
    global LIVE_MAP_VERSION

    width = int(msg.info.width)
    height = int(msg.info.height)

    if (
        width <= 0
        or
        height <= 0
        or
        len(msg.data) != width * height
    ):
        return

    grid = np.asarray(
        msg.data,
        dtype=np.int16
    ).reshape(
        (height, width)
    )

    # Convencion SafeVision/map_saver:
    # libre=254, ocupado=0, desconocido=205.
    image = np.full(
        (height, width),
        205,
        dtype=np.uint8
    )

    image[grid == 0] = 254
    image[grid >= 65] = 0

    # OccupancyGrid: origen inferior izquierdo.
    # PNG: origen superior izquierdo.
    image = np.flipud(image)

    ok, encoded = cv2.imencode(
        ".png",
        image
    )

    if not ok:
        return

    q = msg.info.origin.orientation

    siny_cosp = 2.0 * (
        q.w * q.z
        +
        q.x * q.y
    )

    cosy_cosp = 1.0 - 2.0 * (
        q.y * q.y
        +
        q.z * q.z
    )

    origin_yaw = math.atan2(
        siny_cosp,
        cosy_cosp
    )

    meta = {
        "ok": True,
        "frame_id": (
            msg.header.frame_id
            or
            "map"
        ),
        "resolution": float(
            msg.info.resolution
        ),
        "width": width,
        "height": height,
        "origin": {
            "x": float(
                msg.info.origin.position.x
            ),
            "y": float(
                msg.info.origin.position.y
            ),
            "yaw": float(
                origin_yaw
            )
        },
        "map_load_time": float(
            msg.info.map_load_time.to_sec()
        ),
        "ros_stamp": float(
            msg.header.stamp.to_sec()
        ),
        "updated_at": float(
            time.time()
        )
    }

    png = encoded.tobytes()

    with LIVE_MAP_LOCK:

        LIVE_MAP_VERSION += 1

        meta["version"] = (
            LIVE_MAP_VERSION
        )

        LIVE_MAP_PNG = png
        LIVE_MAP_META = meta


@app.route("/mapping/map")
def mapping_live_map():

    with LIVE_MAP_LOCK:

        png = LIVE_MAP_PNG
        version = LIVE_MAP_VERSION

    if png is None:

        return Response(
            "Mapa ROS no disponible.",
            status=503,
            mimetype="text/plain"
        )

    response = Response(
        png,
        mimetype="image/png"
    )

    response.headers[
        "Cache-Control"
    ] = "no-store, no-cache, must-revalidate"

    response.headers[
        "X-SafeVision-Map-Version"
    ] = str(
        version
    )

    return response


@app.route("/mapping/meta")
def mapping_live_meta():

    with LIVE_MAP_LOCK:

        if LIVE_MAP_META is None:

            return jsonify({
                "ok": False,
                "available": False,
                "error": (
                    "Mapa ROS no disponible"
                )
            }), 503

        meta = dict(
            LIVE_MAP_META
        )

    meta["available"] = True

    return jsonify(
        meta
    )


# =========================================================
# SESION DE MAPEO
# =========================================================

@app.route(
    "/mapping/session/status"
)
def mapping_session_status():
    return jsonify(
        sf_mapping_manager.status()
    )


@app.route(
    "/mapping/session/start",
    methods=["POST"]
)
def mapping_session_start():

    data = request.get_json(
        silent=True
    ) or {}

    name = normalizar_nombre_mapa(
        data.get("name")
    )

    if name is None:
        return jsonify({
            "ok": False,
            "error": "Nombre de mapa invalido"
        }), 400

    result = sf_mapping_manager.start(
        name
    )

    return jsonify(
        result
    ), (
        200
        if result.get("ok")
        else 409
    )


@app.route(
    "/mapping/session/save",
    methods=["POST"]
)
def mapping_session_save():

    result = sf_mapping_manager.save()

    return jsonify(
        result
    ), (
        200
        if result.get("ok")
        else 409
    )


@app.route(
    "/mapping/session/discard",
    methods=["POST"]
)
def mapping_session_discard():

    result = sf_mapping_manager.discard()

    return jsonify(
        result
    ), (
        200
        if result.get("ok")
        else 409
    )


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

    rospy.Subscriber(
        "/map",
        OccupancyGrid,
        live_map_callback,
        queue_size=1
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


def cancelar_navegacion_para_mapeo():
    return publicar_nav_command(
        {
            "command": "cancel"
        }
    )


def configurar_mapping_manager():
    sf_mapping_manager.configure(
        MAPS_DIR,
        cancelar_navegacion_para_mapeo,
        normalizar_nombre_mapa,
        nombre_mapa_ocupado,
        mapa_completo,
        rutas_mapa,
    )


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


# =========================================================
# REDES V2 - MODELOS IA
# =========================================================

def _model_api_error(exc):
    if isinstance(
        exc,
        sf_model_manager.ModelNotFound
    ):
        status = 404

    elif isinstance(
        exc,
        sf_model_manager.ModelConflict
    ):
        status = 409

    elif isinstance(
        exc,
        sf_model_manager.InvalidModel
    ):
        status = 400

    else:
        status = 500

    return jsonify({
        "ok": False,
        "error": str(exc)
    }), status


@app.route("/models")
def models_list():
    try:
        return jsonify({
            "ok": True,
            "models": (
                MODEL_MANAGER.list_models()
            )
        })

    except Exception as exc:
        return _model_api_error(
            exc
        )


@app.route("/models/<nombre>")
def models_get(nombre):
    try:
        return jsonify({
            "ok": True,
            "model": (
                MODEL_MANAGER.get(
                    nombre
                )
            )
        })

    except Exception as exc:
        return _model_api_error(
            exc
        )


@app.route(
    "/models/import",
    methods=["POST"]
)
def models_import():
    upload = request.files.get(
        "file"
    )

    if (
        upload is None
        or
        not upload.filename
    ):
        return jsonify({
            "ok": False,
            "error": "Falta ZIP."
        }), 400

    if not upload.filename.lower().endswith(
        ".zip"
    ):
        return jsonify({
            "ok": False,
            "error": "Solo se acepta .zip."
        }), 400

    temp_upload = (
        Path("/tmp")
        /
        (
            "safevision_model_upload_{}.zip".format(
                uuid.uuid4().hex
            )
        )
    )

    try:
        upload.save(
            str(
                temp_upload
            )
        )

        with temp_upload.open(
            "rb"
        ) as file_handle:
            imported = (
                MODEL_MANAGER.import_zip(
                    file_handle
                )
            )

        return jsonify({
            "ok": True,
            "models": imported
        })

    except Exception as exc:
        return _model_api_error(
            exc
        )

    finally:
        try:
            if temp_upload.exists():
                temp_upload.unlink()
        except Exception:
            pass


@app.route(
    "/models/<nombre>/rename",
    methods=["POST"]
)
def models_rename(nombre):
    data = request.get_json(
        silent=True
    ) or {}

    try:
        return jsonify({
            "ok": True,
            "model": (
                MODEL_MANAGER.rename(
                    nombre,
                    data.get(
                        "name",
                        ""
                    )
                )
            )
        })

    except Exception as exc:
        return _model_api_error(
            exc
        )


@app.route(
    "/models/<nombre>/metadata",
    methods=["PUT"]
)
def models_metadata(nombre):
    data = request.get_json(
        silent=True
    )

    try:
        return jsonify({
            "ok": True,
            "model": (
                MODEL_MANAGER.update_metadata(
                    nombre,
                    data
                )
            )
        })

    except Exception as exc:
        return _model_api_error(
            exc
        )


@app.route(
    "/models/<nombre>",
    methods=["DELETE"]
)
def models_delete(nombre):
    try:
        return jsonify({
            "ok": True,
            "deleted": (
                MODEL_MANAGER.delete(
                    nombre
                )
            )
        })

    except Exception as exc:
        return _model_api_error(
            exc
        )


@app.route(
    "/models/<nombre>/artifact/<extension>"
)
def models_artifact(
    nombre,
    extension
):
    try:
        path = (
            MODEL_MANAGER.artifact_path(
                nombre,
                extension
            )
        )

        return send_file(
            str(path),
            as_attachment=True,
            download_name=path.name,
            max_age=0
        )

    except Exception as exc:
        return _model_api_error(
            exc
        )


@app.route(
    "/models/<nombre>/export"
)
def models_export(nombre):
    try:
        path = (
            MODEL_MANAGER.export_to_temp(
                nombre
            )
        )

        @after_this_request
        def cleanup(response):
            try:
                path.unlink()
            except Exception:
                pass

            return response

        stem = MODEL_MANAGER.get(
            nombre
        )["name"]

        return send_file(
            str(path),
            as_attachment=True,
            download_name=(
                "{}.zip".format(
                    stem
                )
            ),
            mimetype="application/zip",
            max_age=0
        )

    except Exception as exc:
        return _model_api_error(
            exc
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

    configurar_mapping_manager()

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

    try:
        app.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            threaded=True,
            use_reloader=False
        )

    finally:
        sf_mapping_manager.shutdown()


if __name__ == "__main__":
    main()
