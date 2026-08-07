#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import socket
import cv2
import subprocess
from flask import Flask, Response, jsonify

app = Flask(__name__)
camera = None

# Variables globales para telemetría
telemetria = {
    "fps": 0,
    "kbps": 0.0,
    "resolucion": "640x480",
    "emisor": "Yahboom Robot (Raspberry Pi)",
    "nodos_activos": "Flask HTTP Server, OpenCV V4L2",
    "temp_cpu": "N/A"
}

def obtener_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def obtener_temperatura():
    try:
        temp = subprocess.check_output(['cat', '/sys/class/thermal/thermal_zone0/temp']).decode('utf-8')
        return f"{float(temp) / 1000:.1f} °C"
    except:
        return "Desconocida"

def generar_frames():
    global camera, telemetria
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    tiempo_inicio = time.time()
    frames_contados = 0
    bytes_enviados = 0
    
    while True:
        success, frame = camera.read()
        if not success:
            break
            
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        bytes_enviados += len(frame_bytes)
        frames_contados += 1
        
        # Calcular estadísticas cada segundo
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        if tiempo_transcurrido >= 1.0:
            telemetria["fps"] = frames_contados
            telemetria["kbps"] = round((bytes_enviados / 1024) / tiempo_transcurrido, 2)
            telemetria["temp_cpu"] = obtener_temperatura()
            
            # Reiniciar contadores
            frames_contados = 0
            bytes_enviados = 0
            tiempo_inicio = time.time()
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    return jsonify(telemetria)

@app.route('/')
def index():
    ip = obtener_ip()
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Stream IA - Yahboom -> PC</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
            .panel {{ background: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            h2, h3 {{ color: #4CAF50; margin-top: 0; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
            .stat-box {{ background: #2d2d2d; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }}
            .stat-value {{ font-size: 1.5em; font-weight: bold; color: #fff; }}
            pre {{ background: #000; color: #00ff00; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: monospace; border: 1px solid #444; }}
            img {{ border: 3px solid #4CAF50; border-radius: 8px; max-width: 100%; }}
            .instrucciones {{ color: #aaa; font-size: 0.9em; margin-bottom: 15px; }}
        </style>
        <script>
            function updateStats() {{
                fetch('/stats')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('fps').innerText = data.fps;
                        document.getElementById('kbps').innerText = data.kbps + " KB/s";
                        document.getElementById('temp').innerText = data.temp_cpu;
                        document.getElementById('res').innerText = data.resolucion;
                    }});
            }}
            setInterval(updateStats, 1000); // Actualizar cada 1 segundo
        </script>
    </head>
    <body>
        <div class="container">
            <!-- PANEL IZQUIERDO: Video y Telemetría -->
            <div class="panel" style="flex: 1; min-width: 400px;">
                <h2>📡 Transmisión en Vivo</h2>
                <img src="/video_feed" width="640" height="480" alt="Video del Robot" />
                
                <h3 style="margin-top: 20px;">📊 Telemetría del Robot</h3>
                <div class="stats-grid">
                    <div class="stat-box">Rendimiento FPS<br><span class="stat-value" id="fps">0</span></div>
                    <div class="stat-box">Ancho de Banda<br><span class="stat-value" id="kbps">0 KB/s</span></div>
                    <div class="stat-box">Resolución<br><span class="stat-value" id="res">Cargando...</span></div>
                    <div class="stat-box">Temp. Cerebro (Pi)<br><span class="stat-value" id="temp">Cargando...</span></div>
                </div>
                <div style="margin-top: 15px; font-size: 0.85em; color: #888;">
                    <strong>Emisor:</strong> {telemetria['emisor']}<br>
                    <strong>Nodos Activos:</strong> {telemetria['nodos_activos']}
                </div>
            </div>

            <!-- PANEL DERECHO: Código de Inferencia -->
            <div class="panel" style="flex: 1.5; min-width: 500px;">
                <h2>🧠 Código para la PC (PyTorch / YOLO)</h2>
                <p class="instrucciones">
                    Copia este código en tu PC. <strong>Solo necesitas modificar las rutas de tu modelo .pt y tu archivo .json</strong>. El script se conectará automáticamente al video del robot.
                </p>
                <pre>
import cv2
from ultralytics import YOLO
import json

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS (¡Modifica esto!)
# ==========================================
RUTA_MODELO_PT = "ruta/a/tu/modelo.pt"
RUTA_CONFIG_JSON = "ruta/a/tu/config.json"

# Dirección automática del robot Yahboom
URL_VIDEO_ROBOT = "http://{ip}:5000/video_feed"

def iniciar_inferencia():
    print("[INFO] Cargando modelo IA...")
    # Cargar modelo YOLO/PyTorch
    modelo = YOLO(RUTA_MODELO_PT)

    # (Opcional) Leer configuración JSON si la necesitas
    try:
        with open(RUTA_CONFIG_JSON, 'r') as f:
            config = json.load(f)
            print("[INFO] Configuración cargada:", config)
    except Exception as e:
        print("[AVISO] No se pudo cargar el JSON:", e)

    print("[INFO] Conectando a la cámara del robot...")
    cap = cv2.VideoCapture(URL_VIDEO_ROBOT)
    
    if not cap.isOpened():
        print("[ERROR] No se pudo conectar al video. Revisa la IP.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[AVISO] Pérdida de conexión con el robot.")
            break
            
        # ==========================================
        # 2. INFERENCIA EN TIEMPO REAL
        # ==========================================
        # Se ejecuta el modelo sobre el frame del robot
        resultados = modelo(frame, stream=True)
        
        for r in resultados:
            # Dibuja las cajas de detección sobre la imagen
            frame_anotado = r.plot()
            
        cv2.imshow('Inferencia Remota - PC (Presiona Q para salir)', frame_anotado)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    iniciar_inferencia()
                </pre>
            </div>
        </div>
    </body>
    </html>
    """

def main():
    ip = obtener_ip()
    os.system('clear' if os.name == 'posix' else 'cls')
    print("=========================================================")
    print(" 📡 SERVIDOR DE VIDEO DE ALTO RENDIMIENTO INICIADO")
    print("=========================================================")
    print(f" [INFO] 💻 Ve a tu computadora y abre en el navegador:")
    print(f"        👉 http://{ip}:5000")
    print(" [INFO] Allí verás la telemetría y el código de Python.")
    print("---------------------------------------------------------")
    print(" [INFO] Presiona Ctrl+C para detener y volver al menú.")
    print("=========================================================")
    
    try:
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        print("\n[INFO] Deteniendo la transmisión de video...")
    finally:
        if camera is not None:
            camera.release()
        time.sleep(1)

if __name__ == '__main__':
    main()
