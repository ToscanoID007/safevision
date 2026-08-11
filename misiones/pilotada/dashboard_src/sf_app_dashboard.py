#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
# UTILIDADES
# =========================================================

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
