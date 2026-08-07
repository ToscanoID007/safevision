#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import socket
import zipfile
import shutil
import threading
import time

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

MODELOS_DIR = "/home/pi/robot_custom/modelos"
TEMP_EXPORT_DIR = "/home/pi/robot_custom/temp_export"

nombre_zip_global = "modelo.zip"

class DownloadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global nombre_zip_global
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Exportar Modelo IA</title><meta charset="utf-8"></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 30px; background-color: #2b2b2b; color: white;">
                <h2>🤖 Robot Yahboom - Portal de Exportación</h2>
                <div style="background: #333; padding: 20px; border-radius: 8px; width: 60%; margin: 0 auto; margin-bottom: 25px; border-left: 5px solid #00ffcc; text-align: left;">
                    <h3 style="color: #00ffcc; margin-top: 0;">📦 MODELO LISTO PARA DESCARGAR</h3>
                    <p>Tu archivo <b>{nombre_zip}</b> contiene el modelo de red neuronal y sus metadatos listos para usar.</p>
                </div>
                <div style="border: 2px dashed #00ffcc; padding: 30px; width: 60%; margin: 0 auto; background: #1e1e1e; border-radius: 10px;">
                    <a href="/descargar" style="display: inline-block; padding: 15px 30px; background-color: #00ffcc; color: black; font-weight: bold; font-size: 18px; border-radius: 5px; text-decoration: none;">📥 Descargar {nombre_zip}</a>
                    <p style="font-size: 13px; color: #aaa; margin-top: 20px;">El portal web se cerrará automáticamente en el robot al finalizar la descarga.</p>
                </div>
            </body>
            </html>
            """.replace("{nombre_zip}", nombre_zip_global)
            self.wfile.write(html.encode('utf-8'))

        elif self.path == '/descargar':
            ruta_zip = os.path.join(TEMP_EXPORT_DIR, nombre_zip_global)
            if os.path.exists(ruta_zip):
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                self.send_header('Content-Disposition', 'attachment; filename="{}"'.format(nombre_zip_global))
                self.send_header('Content-Length', str(os.path.getsize(ruta_zip)))
                self.end_headers()
                
                with open(ruta_zip, 'rb') as f:
                    self.wfile.write(f.read())
                
                # Apagar servidor 1 segundo después para asegurar envío
                threading.Thread(target=self.apagar_servidor).start()
            else:
                self.send_error(404, "Archivo no encontrado")

    def apagar_servidor(self):
        time.sleep(1)
        self.server.shutdown()

    def log_message(self, format, *args):
        pass

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

def obtener_input(mensaje):
    try:
        return raw_input(mensaje).strip()
    except NameError:
        return input(mensaje).strip()

def exportar_modelo_ia():
    global nombre_zip_global
    os.system('clear')
    print("=========================================================")
    print(" 📤 EXPORTAR MODELO (LINK MÁGICO)")
    print("=========================================================")

    if not os.path.exists(MODELOS_DIR):
        print("\n[ERROR] La carpeta de modelos no existe.")
        return

    archivos = os.listdir(MODELOS_DIR)
    modelos = sorted([f for f in archivos if f.endswith(('.pt', '.weights'))])

    if not modelos:
        print("\n[INFO] No hay modelos para exportar.")
        return

    print("Modelos disponibles:")
    for idx, archivo in enumerate(modelos, 1):
        print("  {}) {}".format(idx, archivo))
    print("  c) Cancelar")
    print("=========================================================")

    seleccion = obtener_input("\nSelecciona el modelo que deseas EXPORTAR: ").lower()
    if seleccion == 'c': return

    try:
        idx = int(seleccion) - 1
        if idx < 0 or idx >= len(modelos):
            print("\n[ERROR] Selección inválida.")
            return
            
        archivo_base = modelos[idx]
        nombre_sin_ext, _ = os.path.splitext(archivo_base)
        json_asociado = nombre_sin_ext + ".json"
        
        nuevo_nombre = obtener_input("\nIngresa un nombre para el .zip (Enter para usar '{}'): ".format(nombre_sin_ext))
        if not nuevo_nombre:
            nombre_zip_global = nombre_sin_ext + ".zip"
        else:
            nombre_zip_global = nuevo_nombre.replace(" ", "_").replace(".zip", "") + ".zip"
            
        if not os.path.exists(TEMP_EXPORT_DIR):
            os.makedirs(TEMP_EXPORT_DIR)
            
        ruta_zip = os.path.join(TEMP_EXPORT_DIR, nombre_zip_global)
        ruta_modelo = os.path.join(MODELOS_DIR, archivo_base)
        ruta_json = os.path.join(MODELOS_DIR, json_asociado)
        
        print("\n[INFO] Empaquetando archivo .zip...")
        with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(ruta_modelo, arcname=archivo_base)
            if os.path.exists(ruta_json):
                zipf.write(ruta_json, arcname=json_asociado)
                
        ip = obtener_ip()
        puerto = 8000
        server = HTTPServer(('0.0.0.0', puerto), DownloadHandler)
        
        os.system('clear')
        print("=========================================================")
        print(" 🌐 PORTAL DE SALIDA ACTIVADO")
        print("=========================================================")
        print(" 1. Abre tu navegador en la computadora")
        print(" 2. Ingresa a: http://{}:{}".format(ip, puerto))
        print("=========================================================")
        print("[INFO] Esperando a que descargues... (Ctrl+C para cancelar)")
        
        try:
            server.serve_forever()
            print("\n[ÉXITO] Descarga completada. Apagando portal...")
        except KeyboardInterrupt:
            print("\n[INFO] Operación cancelada por el usuario.")
            server.server_close()
            
        # Limpieza del zip temporal
        if os.path.exists(TEMP_EXPORT_DIR):
            shutil.rmtree(TEMP_EXPORT_DIR)
            print("[INFO] Sistema limpiado.")
            
    except ValueError:
        print("\n[ERROR] Ingresa un número válido.")
    except Exception as e:
        print("\n[ERROR] {}".format(e))
        if os.path.exists(TEMP_EXPORT_DIR):
            shutil.rmtree(TEMP_EXPORT_DIR)
