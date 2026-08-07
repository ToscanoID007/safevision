#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import cgi
import socket
import zipfile
import shutil
import threading
from datetime import datetime

# Compatibilidad Python 2 / 3
try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

MODELOS_DIR = "/home/pi/robot_custom/modelos"
TEMP_DIR = "/home/pi/robot_custom/temp_upload"

class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Subir Modelo IA</title><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 30px; background-color: #2b2b2b; color: white;">
            <h2>🤖 Robot Yahboom - Portal de Recepción de IA</h2>
            
            <div style="text-align: left; background: #333; padding: 20px; border-radius: 8px; width: 60%; margin: 0 auto; margin-bottom: 25px; border-left: 5px solid #ffaa00;">
                <h3 style="color: #ffaa00; margin-top: 0;">⚠️ INSTRUCCIONES IMPORTANTES ANTES DE SUBIR</h3>
                <p>Para que el robot instale el modelo correctamente, el archivo <b>.zip</b> debe tener una estructura plana. <b>NO comprimas la carpeta entera</b>, selecciona solo los archivos sueltos.</p>
                <p>El interior de tu .zip debe verse exactamente así (sin subcarpetas):</p>
                <pre style="background: #1e1e1e; padding: 15px; color: #00ffcc; border-radius: 5px; font-size: 16px;">
📦 tu_modelo.zip
 ├── 📄 yolov8n.pt       (El archivo del modelo de pesos)
 └── 📄 yolov8n.json     (El archivo de metadatos y clases)</pre>
                <p style="font-size: 14px; color: #ccc;"><i>Truco: Selecciona ambos archivos juntos en tu PC, haz clic derecho y elige "Comprimir en archivo ZIP".</i></p>
            </div>

            <form enctype="multipart/form-data" method="post" style="border: 2px dashed #00ffcc; padding: 30px; width: 60%; margin: 0 auto; background: #1e1e1e; border-radius: 10px;">
                <input type="file" name="file" accept=".zip" required style="margin-bottom: 20px; font-size: 16px; color: white;"><br>
                <input type="submit" value="🚀 Subir e Instalar Modelo" style="padding: 12px 25px; background-color: #00ffcc; color: black; font-weight: bold; font-size: 16px; border: none; cursor: pointer; border-radius: 5px;">
            </form>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type']}
        )
        
        if 'file' not in form:
            self.send_error(400, "Error: Falta el archivo")
            return
            
        file_item = form['file']
        if not file_item.filename.endswith('.zip'):
            self.send_error(400, "Error: Solo se permiten archivos .zip")
            return

        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)
            
        temp_filepath = os.path.join(TEMP_DIR, "modelo_subido.zip")
        with open(temp_filepath, 'wb') as f:
            f.write(file_item.file.read())
            
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        exito_html = "<body style='background-color: #2b2b2b;'><h2 style='color: #00ffcc; font-family: Arial; text-align: center; margin-top: 50px;'>✅ Archivo recibido con exito. Mira la terminal del robot.<br><br>Ya puedes cerrar esta ventana.</h2></body>"
        self.wfile.write(exito_html.encode('utf-8'))
        
        # Apagar el servidor automáticamente tras recibir el archivo
        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        pass  # Silenciar logs

def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def procesar_zip():
    print("\n[INFO] Descomprimiendo archivo...")
    zip_path = os.path.join(TEMP_DIR, "modelo_subido.zip")
    extract_dir = os.path.join(TEMP_DIR, "extraido")
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
        
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception as e:
        print("[ERROR] El archivo subido esta corrupto o no es un ZIP valido.")
        return

    if not os.path.exists(MODELOS_DIR):
        os.makedirs(MODELOS_DIR)

    archivos_encontrados = False
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(('.pt', '.weights', '.json')):
                archivos_encontrados = True
                ruta_origen = os.path.join(root, file)
                ruta_destino = os.path.join(MODELOS_DIR, file)
                
                if os.path.exists(ruta_destino):
                    nombre, ext = os.path.splitext(file)
                    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nuevo_nombre = "{}_{}{}".format(nombre, fecha, ext)
                    ruta_destino = os.path.join(MODELOS_DIR, nuevo_nombre)
                    print("\n[ALERTA] Ya existe un archivo llamado '{}'.".format(file))
                    print("[INFO] Renombrado automaticamente a '{}' para evitar perdida.".format(nuevo_nombre))
                
                shutil.move(ruta_origen, ruta_destino)
                print("[EXITO] {} instalado en {}".format(os.path.basename(ruta_destino), MODELOS_DIR))

    if not archivos_encontrados:
        print("\n[ERROR] No se encontraron modelos (.pt, .weights) ni metadatos (.json) dentro del ZIP.")

    # Limpieza
    shutil.rmtree(TEMP_DIR)
    print("\n[INFO] Limpieza temporal completada. Sistema listo.")

def iniciar_portal():
    ip = obtener_ip()
    puerto = 8000
    server = HTTPServer(('0.0.0.0', puerto), UploadHandler)
    
    os.system('clear')
    print("=========================================================")
    print(" 🌐 PORTAL DE RECEPCION DE MODELOS ACTIVADO")
    print("=========================================================")
    print(" 1. Abre el navegador en tu computadora.")
    print(" 2. Escribe esta direccion exacta en la barra:")
    print("    http://{}:{}".format(ip, puerto))
    print("=========================================================")
    print("[INFO] Esperando archivo .zip... (Presiona Ctrl+C para cancelar)")
    
    try:
        server.serve_forever()
        procesar_zip()
    except KeyboardInterrupt:
        print("\n[INFO] Operacion cancelada. Cerrando portal...")
        server.server_close()
