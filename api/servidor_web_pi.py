import cv2
import time
import logging
from flask import Flask, render_template_string, Response, request, jsonify

# Silenciar logs innecesarios de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

ultimo_frame = None
confianza_actual = 0.5
fps_actual = 0.0
clases_modelo = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoreo Robot - Raspberry Pi</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #11111b; color: #cdd6f4; text-align: center; margin: 0; padding: 15px; }
        h1 { color: #89b4fa; font-size: 1.8em; margin-bottom: 5px; }
        p { color: #a6adc8; margin-top: 0; font-size: 0.9em; }
        .container { max-width: 800px; margin: 10px auto; background: #1e1e2e; padding: 15px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); border: 1px solid #313244; }
        .dashboard { display: flex; justify-content: space-around; margin-bottom: 12px; background: #181825; padding: 10px; border-radius: 10px; border: 1px solid #45475a; }
        .stat-box { font-size: 1em; }
        .stat-label { color: #a6adc8; display: block; font-size: 0.8em; text-transform: uppercase; }
        .val-fps { color: #f9e2af; font-weight: bold; font-size: 1.3em; }
        .val-conf { color: #a6e3a1; font-weight: bold; font-size: 1.3em; }
        img { width: 100%; max-width: 640px; border-radius: 12px; border: 2px solid #89b4fa; background-color: #000; }
        .controls { margin-top: 12px; background: #181825; padding: 12px; border-radius: 10px; border: 1px solid #45475a; }
        input[type=range] { width: 65%; cursor: pointer; accent-color: #89b4fa; }
        .classes-box { margin-top: 12px; background: #181825; padding: 12px; border-radius: 10px; text-align: left; border: 1px solid #45475a; }
        .classes-title { color: #89b4fa; font-size: 0.9em; margin-top: 0; margin-bottom: 8px; }
        .tags-container { display: flex; flex-wrap: wrap; gap: 6px; max-height: 100px; overflow-y: auto; }
        .tag { background: #313244; color: #89b4fa; padding: 3px 8px; border-radius: 6px; font-size: 0.8em; border: 1px solid #45475a; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Panel de Visión Artificial</h1>
        <p>Transmisión Optimizada con Frame Skipping</p>

        <div class="dashboard">
            <div class="stat-box">
                <span class="stat-label">Rendimiento Inferencia</span>
                <span id="fps-val" class="val-fps">0.0 FPS</span>
            </div>
            <div class="stat-box">
                <span class="stat-label">Umbral Confianza</span>
                <span id="conf-val" class="val-conf">50%</span>
            </div>
        </div>

        <img src="/video_feed" alt="Transmisión en vivo">

        <div class="controls">
            <label for="slider-conf" style="font-weight: bold; font-size:0.9em;">Sensibilidad del Modelo:</label><br><br>
            <input type="range" min="0.05" max="0.95" step="0.05" value="0.5" id="slider-conf" oninput="actualizarConfianza(this.value)">
        </div>

        <div class="classes-box">
            <h3 class="classes-title">🏷️ Clases Detectables (<span id="num-classes">0</span>):</h3>
            <div id="classes-list" class="tags-container">Cargando clases...</div>
        </div>
    </div>

    <script>
        function actualizarConfianza(val) {
            document.getElementById('conf-val').innerText = Math.round(val * 100) + '%';
            fetch('/set_confianza', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({confianza: parseFloat(val)})
            });
        }

        function solicitarEstado() {
            fetch('/get_info')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('fps-val').innerText = data.fps.toFixed(1) + ' FPS';
                    const listContainer = document.getElementById('classes-list');
                    document.getElementById('num-classes').innerText = data.clases.length;
                    if (data.clases.length > 0) {
                        listContainer.innerHTML = data.clases.map(c => `<span class="tag">${c}</span>`).join('');
                    } else {
                        listContainer.innerHTML = '<span style="color:#a6adc8;">Sin información</span>';
                    }
                })
                .catch(err => console.error(err));
        }

        setInterval(solicitarEstado, 1000);
        solicitarEstado();
    </script>
</body>
</html>
"""

def actualizar_frame(frame):
    global ultimo_frame
    ultimo_frame = frame

def actualizar_metrics(fps):
    global fps_actual
    fps_actual = fps

def fijar_clases(clases):
    global clases_modelo
    clases_modelo = clases

def obtener_confianza():
    global confianza_actual
    return confianza_actual

def generar_frames():
    global ultimo_frame
    while True:
        if ultimo_frame is not None:
            # Compresión JPEG reducida a 60% para liberar CPU
            ret, buffer = cv2.imencode('.jpg', ultimo_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_info')
def get_info():
    global fps_actual, clases_modelo
    return jsonify({'fps': fps_actual, 'clases': clases_modelo})

@app.route('/set_confianza', methods=['POST'])
def set_confianza():
    global confianza_actual
    data = request.get_json()
    if data and 'confianza' in data:
        confianza_actual = float(data['confianza'])
        return jsonify({'status': 'ok', 'confianza': confianza_actual})
    return jsonify({'status': 'error'}), 400
