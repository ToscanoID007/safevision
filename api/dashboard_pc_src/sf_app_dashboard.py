#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from flask import Flask, render_template, request, jsonify, Response
from sf_conexion_ssh import conexion_robot
from sf_motor_inferencia import MotorInferencia

app = Flask(__name__)

# Instancia global del motor de inferencia YOLO
motor_ia = MotorInferencia(model_path="yolov8n.pt", conf_threshold=0.5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/conectar_robot', methods=['POST'])
def conectar_robot():
    data = request.get_json() or {}
    ip = data.get('ip')
    if conexion_robot.conectar(ip):
        return jsonify({"status": "success", "message": "Conectado al robot."})
    return jsonify({"status": "error", "message": "Fallo la conexión SSH."}), 400

@app.route('/upload_models', methods=['POST'])
def upload_models():
    if 'model_pt' not in request.files:
        return jsonify({"status": "error", "message": "Falta el archivo .pt"}), 400
    
    file_pt = request.files['model_pt']
    temp_path = os.path.join("/tmp", file_pt.filename)
    file_pt.save(temp_path)
    
    if motor_ia.cargar_modelo(temp_path):
        return jsonify({"status": "success", "message": f"Modelo {file_pt.filename} cargado exitosamente."})
    return jsonify({"status": "error", "message": "Error al procesar el archivo del modelo."}), 500

@app.route('/set_control', methods=['POST'])
def set_control():
    data = request.get_json() or {}
    modo = data.get('mode', '')
    
    if modo == 'teclado':
        conexion_robot.iniciar_teleop_teclado()
    elif modo == 'mando':
        conexion_robot.iniciar_teleop_mando()
    elif modo == 'camara':
        conexion_robot.encender_camara()
    elif modo == 'apagar':
        conexion_robot.apagar_todo()
    else:
        return jsonify({"status": "error", "message": "Modo no reconocido."}), 400
        
    return jsonify({"status": "success", "message": f"Comando '{modo}' ejecutado."})

@app.route('/update_confidence', methods=['POST'])
def update_confidence():
    data = request.get_json() or {}
    nueva_confianza = data.get('confidence', 0.5)
    motor_ia.set_confianza(nueva_confianza)
    return jsonify({"status": "success", "value": nueva_confianza})

@app.route('/mover_robot', methods=['POST'])
def mover_robot():
    """Proxy unificado para reenviar teclas o direcciones del frontend al API del robot."""
    if not conexion_robot.ip:
        return jsonify({"status": "error", "message": "Sin conexión IP con el robot"}), 400
    
    data = request.get_json() or {}
    try:
        url_pi = f"http://{conexion_robot.ip}:5002/mover"
        res = requests.post(url_pi, json=data, timeout=1)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fallo al comunicar con la Pi: {str(e)}"}), 500

@app.route('/video_feed')
def video_feed():
    ip_target = conexion_robot.ip if conexion_robot.ip else "127.0.0.1"
    return Response(motor_ia.generar_frames(ip_robot=ip_target, puerto=8080),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/map_feed')
def map_feed():
    return "Stream del Mapa"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
