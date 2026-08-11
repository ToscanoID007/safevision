#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import ipaddress
import tempfile
import threading
import webbrowser

from pathlib import Path

import requests

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request
)

from werkzeug.utils import (
    secure_filename
)

from sf_motor_inferencia import (
    MotorInferencia
)


# =========================================================
# APP
# =========================================================

app = Flask(
    __name__
)

app.config[
    "MAX_CONTENT_LENGTH"
] = 2 * 1024 * 1024 * 1024


motor_ia = MotorInferencia()


# =========================================================
# ESTADO DE SESIÓN
# =========================================================

robot_ip = None
robot_estado = {}


TEMP_DIR = Path(
    tempfile.mkdtemp(
        prefix="safevision_"
    )
)



# =========================================================
# BIBLIOTECA LOCAL DE MISIONES
# =========================================================

MISSION_SUFFIX = ".sfmision"

MISSION_CONFIG_FILE = (
    Path.home()
    /
    ".config"
    /
    "safevision"
    /
    "missions.json"
)

DEFAULT_MISSION_DIR = (
    Path.home()
    /
    "SafeVision_Misiones"
)


# =========================================================
# UTILIDADES
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
        return False, "Archivo de misión inválido."

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

    if not isinstance(
        data.get(
            "points"
        ),
        list
    ):
        return False, "La misión no contiene una lista de puntos válida."

    if not isinstance(
        data.get(
            "code",
            ""
        ),
        str
    ):
        return False, "El código de misión no es válido."

    ids = set()

    for point in data["points"]:
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

        key = point_id.lower()

        if key in ids:
            return False, "Hay IDs duplicados."

        ids.add(
            key
        )

    initial_id = data.get(
        "initial_point_id"
    )

    if (
        initial_id is not None
        and
        (
            not isinstance(
                initial_id,
                str
            )
            or
            initial_id.lower()
            not in ids
        )
    ):
        return False, "Punto inicial inválido."

    return True, ""


def mission_library_dir():
    path = DEFAULT_MISSION_DIR

    if MISSION_CONFIG_FILE.exists():
        try:
            config = json.loads(
                MISSION_CONFIG_FILE.read_text(
                    encoding="utf-8"
                )
            )

            configured = config.get(
                "missions_dir"
            )

            if configured:
                path = Path(
                    configured
                ).expanduser()

        except Exception:
            pass

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return path


def save_mission_library_dir(
    path
):
    MISSION_CONFIG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MISSION_CONFIG_FILE.write_text(
        json.dumps(
            {
                "missions_dir": str(path)
            },
            ensure_ascii=False,
            indent=2
        )
        +
        "\n",
        encoding="utf-8"
    )


def find_local_mission(
    name
):
    folder = mission_library_dir()

    target = name.strip().casefold()

    for path in folder.glob(
        "*" + MISSION_SUFFIX
    ):
        if path.stem.casefold() == target:
            return path

    return None


def save_local_mission(
    mission,
    overwrite=True
):
    name = mission["name"].strip()

    folder = mission_library_dir()

    existing = find_local_mission(
        name
    )

    if (
        existing is not None
        and
        not overwrite
    ):
        raise FileExistsError(
            "Ya existe una misión llamada '{}'.".format(
                name
            )
        )

    target = (
        folder
        /
        (
            name
            +
            MISSION_SUFFIX
        )
    )

    temp = Path(
        str(target)
        +
        ".tmp"
    )

    temp.write_text(
        json.dumps(
            mission,
            ensure_ascii=False,
            indent=2
        )
        +
        "\n",
        encoding="utf-8"
    )

    temp.replace(
        target
    )

    if (
        existing is not None
        and
        existing != target
        and
        existing.exists()
    ):
        existing.unlink()

    return target


def sync_mission_to_robot(
    mission
):
    if not robot_ip:
        return {
            "ok": False,
            "state": "disconnected",
            "message": "Robot desconectado."
        }

    try:
        response = requests.post(
            "http://{}:8091/missions/save".format(
                robot_ip
            ),
            json=mission,
            timeout=4
        )

        try:
            data = response.json()

        except Exception:
            data = {}

        if response.ok:
            return {
                "ok": True,
                "state": "saved",
                "message": "Guardada en Pi."
            }

        return {
            "ok": False,
            "state": "error",
            "message": (
                data.get("error")
                or
                "La Pi rechazó la misión."
            )
        }

    except Exception as exc:
        return {
            "ok": False,
            "state": "error",
            "message": (
                "Pi no disponible: {}"
                .format(exc)
            )
        }


def local_mission_list():
    result = []

    for path in sorted(
        mission_library_dir().glob(
            "*" + MISSION_SUFFIX
        ),
        key=lambda item: item.name.casefold()
    ):
        result.append({
            "name": path.stem,
            "filename": path.name,
            "size": path.stat().st_size
        })

    return result


def validar_ip(valor):
    try:
        ip = ipaddress.ip_address(
            str(valor).strip()
        )

        if ip.version != 4:
            return None

        return str(ip)

    except Exception:
        return None


def error(
    mensaje,
    codigo=400
):
    return jsonify({
        "status": "error",
        "message": mensaje
    }), codigo


def consultar_robot(ip):
    # -----------------------------------------------------
    # Primero comprobar servidor rápido.
    # -----------------------------------------------------

    respuesta = requests.get(
        "http://{}:8091/".format(
            ip
        ),
        timeout=2
    )

    respuesta.raise_for_status()


    # -----------------------------------------------------
    # Después obtener diagnóstico completo.
    # -----------------------------------------------------

    try:
        health = requests.get(
            "http://{}:8091/health".format(
                ip
            ),
            timeout=6
        )

        health.raise_for_status()

        return health.json()

    except Exception:
        return {
            "ok": True,
            "ip": ip,
            "control_mode": "desconocido"
        }


# =========================================================
# INTERFAZ
# =========================================================

@app.route("/")
def index():
    return render_template(
        "index.html"
    )



# =========================================================
# SAFEVISION PROGRAMACION V1
# =========================================================

@app.route("/programar")
def programar_mision():
    return render_template(
        "programar.html"
    )



# =========================================================
# PERSISTENCIA DE MISIONES
# =========================================================

@app.route(
    "/missions/config"
)
def missions_config():
    try:
        folder = mission_library_dir()

    except Exception as exc:
        return error(
            "No se pudo abrir la carpeta de misiones: {}".format(
                exc
            ),
            500
        )

    return jsonify({
        "ok": True,
        "folder": str(folder)
    })


@app.route(
    "/missions/select-folder",
    methods=["POST"]
)
def missions_select_folder():
    try:
        import tkinter as tk

        from tkinter import filedialog

        root = tk.Tk()

        root.withdraw()

        try:
            root.attributes(
                "-topmost",
                True
            )

        except Exception:
            pass

        selected = filedialog.askdirectory(
            parent=root,
            title="Seleccionar carpeta de misiones SafeVision",
            initialdir=str(
                mission_library_dir()
            )
        )

        root.destroy()

    except Exception as exc:
        return error(
            "No se pudo abrir el selector de carpetas: {}".format(
                exc
            ),
            500
        )

    if not selected:
        return jsonify({
            "ok": False,
            "cancelled": True
        })

    path = Path(
        selected
    ).expanduser()

    if not path.is_dir():
        return error(
            "La carpeta seleccionada no es válida."
        )

    save_mission_library_dir(
        path
    )

    return jsonify({
        "ok": True,
        "folder": str(path)
    })


@app.route(
    "/missions"
)
def missions_list():
    try:
        missions = local_mission_list()

        return jsonify({
            "ok": True,
            "folder": str(
                mission_library_dir()
            ),
            "missions": missions
        })

    except Exception as exc:
        return error(
            "No se pudieron listar las misiones: {}".format(
                exc
            ),
            500
        )


@app.route(
    "/missions/load"
)
def mission_load():
    name = request.args.get(
        "name",
        ""
    ).strip()

    if not mission_name_valid(
        name
    ):
        return error(
            "Nombre de misión inválido."
        )

    path = find_local_mission(
        name
    )

    if path is None:
        return error(
            "Misión no encontrada.",
            404
        )

    try:
        mission = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception as exc:
        return error(
            "No se pudo leer la misión: {}".format(
                exc
            ),
            500
        )

    ok, message = validate_mission_data(
        mission
    )

    if not ok:
        return error(
            message
        )

    return jsonify({
        "ok": True,
        "mission": mission
    })


@app.route(
    "/missions/save",
    methods=["POST"]
)
def mission_save():
    mission = request.get_json(
        silent=True
    )

    ok, message = validate_mission_data(
        mission
    )

    if not ok:
        return error(
            message
        )

    overwrite = (
        request.args.get(
            "overwrite",
            "1"
        )
        !=
        "0"
    )

    try:
        path = save_local_mission(
            mission,
            overwrite=overwrite
        )

    except FileExistsError as exc:
        return error(
            str(exc),
            409
        )

    except Exception as exc:
        return error(
            "No se pudo guardar en la PC: {}".format(
                exc
            ),
            500
        )

    pi = sync_mission_to_robot(
        mission
    )

    return jsonify({
        "ok": True,
        "mission": mission,
        "pc": {
            "ok": True,
            "path": str(path)
        },
        "pi": pi
    })


@app.route(
    "/missions/duplicate",
    methods=["POST"]
)
def mission_duplicate():
    mission = request.get_json(
        silent=True
    )

    ok, message = validate_mission_data(
        mission
    )

    if not ok:
        return error(
            message
        )

    base = mission["name"].strip()

    existing = {
        item["name"].casefold()
        for item in local_mission_list()
    }

    number = 1

    while True:
        candidate = "{}_copia{}".format(
            base,
            number
        )

        if candidate.casefold() not in existing:
            break

        number += 1

    duplicate = json.loads(
        json.dumps(
            mission
        )
    )

    duplicate["name"] = candidate

    path = save_local_mission(
        duplicate,
        overwrite=False
    )

    pi = sync_mission_to_robot(
        duplicate
    )

    return jsonify({
        "ok": True,
        "mission": duplicate,
        "pc": {
            "ok": True,
            "path": str(path)
        },
        "pi": pi
    })


@app.route(
    "/missions/delete",
    methods=["POST"]
)
def mission_delete():
    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()

    target = str(
        data.get(
            "target",
            ""
        )
    ).strip().lower()

    if not mission_name_valid(
        name
    ):
        return error(
            "Nombre de misión inválido."
        )

    if target not in (
        "pc",
        "pi",
        "ambos"
    ):
        return error(
            "Destino de eliminación inválido."
        )

    pc_result = None
    pi_result = None

    if target in (
        "pc",
        "ambos"
    ):
        path = find_local_mission(
            name
        )

        if path is None:
            pc_result = {
                "ok": False,
                "state": "missing",
                "message": "No existe en PC."
            }

        else:
            try:
                path.unlink()

                pc_result = {
                    "ok": True,
                    "state": "deleted",
                    "message": "Eliminada de PC."
                }

            except Exception as exc:
                pc_result = {
                    "ok": False,
                    "state": "error",
                    "message": str(exc)
                }

    if target in (
        "pi",
        "ambos"
    ):
        if not robot_ip:
            pi_result = {
                "ok": False,
                "state": "disconnected",
                "message": "Robot desconectado."
            }

        else:
            try:
                response = requests.post(
                    "http://{}:8091/missions/delete".format(
                        robot_ip
                    ),
                    json={
                        "name": name
                    },
                    timeout=4
                )

                try:
                    result = response.json()

                except Exception:
                    result = {}

                pi_result = {
                    "ok": bool(
                        response.ok
                    ),
                    "state": (
                        "deleted"
                        if response.ok
                        else "error"
                    ),
                    "message": (
                        "Eliminada de Pi."
                        if response.ok
                        else
                        result.get(
                            "error",
                            "No se pudo eliminar de Pi."
                        )
                    )
                }

            except Exception as exc:
                pi_result = {
                    "ok": False,
                    "state": "error",
                    "message": str(exc)
                }

    return jsonify({
        "ok": True,
        "pc": pc_result,
        "pi": pi_result
    })


@app.route(
    "/missions/import",
    methods=["POST"]
)
def mission_import():
    uploaded = request.files.get(
        "file"
    )

    if (
        uploaded is None
        or
        not uploaded.filename
    ):
        return error(
            "Selecciona un archivo .sfmision."
        )

    if not uploaded.filename.lower().endswith(
        MISSION_SUFFIX
    ):
        return error(
            "El archivo debe terminar en .sfmision."
        )

    raw = uploaded.read(
        2 * 1024 * 1024
        +
        1
    )

    if len(raw) > 2 * 1024 * 1024:
        return error(
            "El archivo de misión es demasiado grande."
        )

    try:
        mission = json.loads(
            raw.decode(
                "utf-8-sig"
            )
        )

    except Exception:
        return error(
            "El archivo no contiene JSON válido."
        )

    ok, message = validate_mission_data(
        mission
    )

    if not ok:
        return error(
            message
        )

    try:
        path = save_local_mission(
            mission,
            overwrite=False
        )

    except FileExistsError as exc:
        return error(
            str(exc),
            409
        )

    pi = sync_mission_to_robot(
        mission
    )

    return jsonify({
        "ok": True,
        "mission": mission,
        "pc": {
            "ok": True,
            "path": str(path)
        },
        "pi": pi
    })


@app.route(
    "/missions/download"
)
def download_mission():
    name = request.args.get(
        "name",
        ""
    ).strip()

    if not mission_name_valid(
        name
    ):
        return error(
            "Nombre de misión inválido."
        )

    path = find_local_mission(
        name
    )

    if path is None:
        return error(
            "Misión no encontrada.",
            404
        )

    return Response(
        path.read_bytes(),
        mimetype="application/json",
        headers={
            "Content-Disposition": (
                'attachment; filename="{}.sfmision"'
                .format(name)
            )
        }
    )


@app.route(
    "/misiones/archivos"
)
def mission_files_page():
    return render_template(
        "misiones_archivos.html",
        missions=local_mission_list(),
        folder=str(
            mission_library_dir()
        )
    )


# =========================================================
# CONEXIÓN
# =========================================================

@app.route(
    "/connect",
    methods=["POST"]
)
def connect():
    global robot_ip
    global robot_estado


    data = request.get_json(
        silent=True
    ) or {}


    ip = validar_ip(
        data.get(
            "ip",
            ""
        )
    )


    if not ip:
        return error(
            "IP inválida."
        )


    try:
        estado = consultar_robot(
            ip
        )

    except Exception as exc:
        return error(
            "No se pudo conectar al robot: {}".format(
                exc
            ),
            502
        )


    robot_ip = ip
    robot_estado = estado


    return jsonify({
        "status": "success",
        "message": "Robot conectado.",
        "robot": estado
    })


@app.route(
    "/robot_status"
)
def robot_status():
    global robot_estado


    if not robot_ip:
        return error(
            "Robot no conectado.",
            409
        )


    try:
        robot_estado = consultar_robot(
            robot_ip
        )

        return jsonify({
            "status": "success",
            "robot": robot_estado
        })


    except Exception as exc:
        return error(
            "Robot no disponible: {}".format(
                exc
            ),
            502
        )


# =========================================================
# MODELO
# =========================================================

@app.route(
    "/upload_model",
    methods=["POST"]
)
def upload_model():
    archivo_pt = request.files.get(
        "model_pt"
    )


    if (
        archivo_pt is None
        or
        not archivo_pt.filename
    ):
        return error(
            "Selecciona un archivo .pt."
        )


    nombre_pt = secure_filename(
        archivo_pt.filename
    )


    if not nombre_pt.lower().endswith(
        ".pt"
    ):
        return error(
            "El modelo debe ser .pt."
        )


    ruta_pt = (
        TEMP_DIR
        /
        nombre_pt
    )


    archivo_pt.save(
        str(
            ruta_pt
        )
    )


    # -----------------------------------------------------
    # JSON OPCIONAL
    # -----------------------------------------------------

    archivo_json = request.files.get(
        "model_json"
    )

    ruta_json = None


    if (
        archivo_json is not None
        and
        archivo_json.filename
    ):
        nombre_json = secure_filename(
            archivo_json.filename
        )


        if not nombre_json.lower().endswith(
            ".json"
        ):
            return error(
                "Los metadatos deben ser .json."
            )


        ruta_json = (
            TEMP_DIR
            /
            nombre_json
        )


        archivo_json.save(
            str(
                ruta_json
            )
        )


    correcto, detalle = motor_ia.cargar_modelo(
        str(
            ruta_pt
        ),
        (
            str(
                ruta_json
            )
            if ruta_json
            else None
        )
    )


    if not correcto:
        return error(
            "No se pudo cargar el modelo: {}".format(
                detalle
            ),
            500
        )


    return jsonify({
        "status": "success",
        "message": "Modelo cargado.",
        "model": motor_ia.get_info()
    })


@app.route(
    "/model_info"
)
def model_info():
    return jsonify(
        motor_ia.get_info()
    )


# =========================================================
# CONFIANZA
# =========================================================

@app.route(
    "/confidence",
    methods=["POST"]
)
def confidence():
    data = request.get_json(
        silent=True
    ) or {}


    if not motor_ia.set_confianza(
        data.get(
            "confidence"
        )
    ):
        return error(
            "Confianza inválida."
        )


    return jsonify({
        "status": "success",
        "confidence": (
            motor_ia.get_info()[
                "confidence"
            ]
        )
    })


# =========================================================
# VIDEO
# =========================================================

@app.route(
    "/video_feed"
)
def video_feed():
    if not robot_ip:
        return Response(
            "Robot no conectado.",
            status=409,
            mimetype="text/plain"
        )


    origen = (
        "http://{}:8091/video_feed"
    ).format(
        robot_ip
    )


    return Response(
        motor_ia.generar_stream(
            origen
        ),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )



# =========================================================
# MAPAS - NIVEL 2
# =========================================================

@app.route("/maps")
def maps():
    if not robot_ip:
        return error(
            "Robot no conectado.",
            409
        )

    try:
        respuesta = requests.get(
            "http://{}:8091/maps".format(
                robot_ip
            ),
            timeout=3
        )

        respuesta.raise_for_status()

        return jsonify(
            respuesta.json()
        )

    except Exception as exc:
        return error(
            "No se pudieron obtener los mapas: {}".format(
                exc
            ),
            502
        )


@app.route("/map_image/<nombre>")
def map_image(nombre):
    if not robot_ip:
        return Response(
            "Robot no conectado.",
            status=409
        )

    try:
        respuesta = requests.get(
            "http://{}:8091/maps/{}/image".format(
                robot_ip,
                nombre
            ),
            timeout=5
        )

        respuesta.raise_for_status()

        return Response(
            respuesta.content,
            mimetype="image/png"
        )

    except Exception as exc:
        return Response(
            str(exc),
            status=502,
            mimetype="text/plain"
        )



# =========================================================
# SAFEVISION NIVEL 2B - POSE PROXY
# =========================================================

@app.route("/map_pose")
def dashboard_map_pose():
    if not robot_ip:
        return jsonify({
            "ok": False,
            "localized": False,
            "message": "Robot no conectado."
        }), 409

    try:
        respuesta = requests.get(
            "http://{}:8091/map_pose".format(
                robot_ip
            ),
            timeout=2
        )

        try:
            datos = respuesta.json()
        except Exception:
            datos = {
                "ok": False,
                "localized": False,
                "message": "Respuesta de pose invalida."
            }

        return jsonify(
            datos
        ), respuesta.status_code

    except Exception as exc:
        return jsonify({
            "ok": False,
            "localized": False,
            "message": "No se pudo obtener pose: {}".format(
                exc
            )
        }), 502


@app.route("/map_meta/<nombre>")
def dashboard_map_meta(nombre):
    if not robot_ip:
        return jsonify({
            "ok": False,
            "message": "Robot no conectado."
        }), 409

    try:
        respuesta = requests.get(
            "http://{}:8091/maps/{}/meta".format(
                robot_ip,
                nombre
            ),
            timeout=3
        )

        try:
            datos = respuesta.json()
        except Exception:
            datos = {
                "ok": False,
                "message": "Metadatos de mapa invalidos."
            }

        return jsonify(
            datos
        ), respuesta.status_code

    except Exception as exc:
        return jsonify({
            "ok": False,
            "message": "No se pudieron obtener metadatos: {}".format(
                exc
            )
        }), 502


# =========================================================
# ESTADO LOCAL
# =========================================================

@app.route(
    "/health"
)
def health():
    return jsonify({
        "status": "ok",
        "robot_ip": robot_ip,
        "model": motor_ia.get_info()
    })


# =========================================================
# MAIN
# =========================================================

def abrir_navegador():
    try:
        webbrowser.open(
            "http://127.0.0.1:5000"
        )

    except Exception:
        pass



# =========================================================
# SAFEVISION NIVEL 2B - INITIALPOSE PROXY
# =========================================================

@app.route("/initialpose", methods=["POST"])
def dashboard_initialpose():

    if not robot_ip:
        return jsonify({
            "ok": False,
            "message": "Robot no conectado."
        }), 409

    datos = request.get_json(
        silent=True
    ) or {}

    try:
        respuesta = requests.post(
            "http://{}:8091/initialpose".format(
                robot_ip
            ),
            json=datos,
            timeout=3
        )

        try:
            contenido = respuesta.json()

        except Exception:
            contenido = {
                "ok": False,
                "message": (
                    "Respuesta initialpose invalida."
                )
            }

        return jsonify(
            contenido
        ), respuesta.status_code

    except Exception as exc:

        return jsonify({
            "ok": False,
            "message": (
                "No se pudo enviar initialpose: {}"
                .format(exc)
            )
        }), 502



# =========================================================
# SAFEVISION NIVEL 3C - NAV PROXY
# =========================================================

def nav_proxy_response(respuesta):

    try:
        contenido = respuesta.json()

    except Exception:
        contenido = {
            "ok": False,
            "error": "Respuesta de navegación inválida."
        }

    return jsonify(
        contenido
    ), respuesta.status_code


@app.route("/nav/status")
def dashboard_nav_status():

    if not robot_ip:
        return jsonify({
            "ok": False,
            "available": False,
            "error": "Robot no conectado."
        }), 409

    try:
        respuesta = requests.get(
            "http://{}:8091/nav/status".format(
                robot_ip
            ),
            timeout=2
        )

        return nav_proxy_response(
            respuesta
        )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "available": False,
            "error": (
                "No se pudo consultar navegación: {}"
                .format(exc)
            )
        }), 502


@app.route(
    "/nav/queue",
    methods=["POST"]
)
def dashboard_nav_queue():

    if not robot_ip:
        return jsonify({
            "ok": False,
            "error": "Robot no conectado."
        }), 409

    datos = request.get_json(
        silent=True
    ) or {}

    try:
        respuesta = requests.post(
            "http://{}:8091/nav/queue".format(
                robot_ip
            ),
            json=datos,
            timeout=3
        )

        return nav_proxy_response(
            respuesta
        )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": (
                "No se pudo cargar la cola: {}"
                .format(exc)
            )
        }), 502


def dashboard_nav_simple(
    comando
):

    if not robot_ip:
        return jsonify({
            "ok": False,
            "error": "Robot no conectado."
        }), 409

    try:
        respuesta = requests.post(
            "http://{}:8091/nav/{}".format(
                robot_ip,
                comando
            ),
            timeout=3
        )

        return nav_proxy_response(
            respuesta
        )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": (
                "No se pudo ejecutar {}: {}"
                .format(
                    comando,
                    exc
                )
            )
        }), 502


@app.route(
    "/nav/start",
    methods=["POST"]
)
def dashboard_nav_start():
    return dashboard_nav_simple(
        "start"
    )


@app.route(
    "/nav/cancel",
    methods=["POST"]
)
def dashboard_nav_cancel():
    return dashboard_nav_simple(
        "cancel"
    )


@app.route(
    "/nav/clear",
    methods=["POST"]
)
def dashboard_nav_clear():
    return dashboard_nav_simple(
        "clear"
    )


if __name__ == "__main__":

    threading.Timer(
        1.0,
        abrir_navegador
    ).start()


    print(
        "=============================================="
    )

    print(
        " SafeVision Dashboard"
    )

    print(
        " http://127.0.0.1:5000"
    )

    print(
        "=============================================="
    )


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )
