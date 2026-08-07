#!/usr/bin/env python3
import os
import socket
import http.server
import socketserver
import threading
import time

RUTA_BASE = os.path.expanduser("~/robot_custom")
ARCHIVO_TXT = os.path.join(RUTA_BASE, "arbol_direcciones.txt")

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generar_arbol(ruta, prefijo=""):
    lineas = []
    try:
        elementos = sorted(os.listdir(ruta))
    except PermissionError:
        return lineas

    elementos = [e for e in elementos if not e.startswith('.') and e != '__pycache__']

    for i, elemento in enumerate(elementos):
        es_ultimo = (i == len(elementos) - 1)
        conector = "└── " if es_ultimo else "├── "
        ruta_completa = os.path.join(ruta, elemento)
        
        lineas.append(f"{prefijo}{conector}{elemento}")
        
        if os.path.isdir(ruta_completa):
            extension_prefijo = "    " if es_ultimo else "│   "
            lineas.extend(generar_arbol(ruta_completa, prefijo + extension_prefijo))
                
    return lineas

def main():
    if not os.path.exists(RUTA_BASE):
        print(f"❌ Error: No existe la carpeta {RUTA_BASE}")
        return

    lineas_arbol = generar_arbol(RUTA_BASE)
    encabezado = f"ESTRUCTURA DE DIRECCIONES: {RUTA_BASE}\n" + "="*50
    texto_completo = encabezado + "\n" + "\n".join(lineas_arbol)

    with open(ARCHIVO_TXT, "w", encoding="utf-8") as f:
        f.write(texto_completo)

    print("\n" + "="*50)
    print(texto_completo)
    print("="*50 + "\n")

    ip_pi = obtener_ip_local()
    print(f"✅ Generado localmente en: {ARCHIVO_TXT}")
    print(f"🌐 Para verlo o descargarlo en tu PC, entra a este enlace en tu navegador:")
    print(f"👉 http://{ip_pi}:8888\n")

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(texto_completo.encode('utf-8'))
        def log_message(self, format, *args):
            pass

    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", 8888), CustomHandler) as httpd:
            timer = threading.Thread(target=httpd.serve_forever)
            timer.daemon = True
            timer.start()
            time.sleep(20)
            httpd.shutdown()
    except Exception:
        pass

if __name__ == "__main__":
    main()
