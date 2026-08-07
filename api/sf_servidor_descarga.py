#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import socket
import http.server
import socketserver
import threading

def obtener_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class ServidorReutilizable(socketserver.TCPServer):
    allow_reuse_address = True

def iniciar_servidor(httpd):
    try:
        httpd.serve_forever()
    except Exception:
        pass

def main():
    puerto_inicial = 8000
    directorio_payload = os.path.join(os.path.dirname(__file__), "payload")
    
    try:
        print("\n[LOG] Preparando servidor...")
        if not os.path.exists(directorio_payload):
            print(f"[LOG] Creando directorio payload en: {directorio_payload}")
            os.makedirs(directorio_payload)
        
        os.chdir(directorio_payload)
        print(f"[LOG] Sirviendo archivos desde: {os.getcwd()}")
        
        ip_pi = obtener_ip()
        print(f"[LOG] IP detectada: {ip_pi}")

        Handler = http.server.SimpleHTTPRequestHandler
        
        # 🛠️ SOLUCIÓN: Buscar un puerto libre automáticamente
        puerto = puerto_inicial
        httpd = None
        
        while puerto < 8020: # Límite de 20 intentos
            try:
                httpd = ServidorReutilizable(("", puerto), Handler)
                break # Si tiene éxito, sale del bucle
            except OSError as e:
                if e.errno == 98: # Errno 98: Address already in use
                    print(f"[LOG] ⚠️ Puerto {puerto} ocupado. Intentando con el {puerto + 1}...")
                    puerto += 1
                else:
                    raise e
                    
        if httpd is None:
            raise Exception("No se encontraron puertos libres entre el 8000 y el 8020.")

        hilo_servidor = threading.Thread(target=iniciar_servidor, args=(httpd,))
        hilo_servidor.daemon = True
        hilo_servidor.start()

        print("\n=========================================================")
        print(f"✅ SERVIDOR DE DESCARGA ACTIVO")
        print(f"🌐 Ve a http://{ip_pi}:{puerto} en el navegador de tu PC")
        print("   para descargar el Dashboard (SafeVision_Dashboard.zip).")
        print("=========================================================")
        
        input("\n[INFO] Presiona ENTER para apagar el servidor y regresar...\n")
        
        print("[INFO] Apagando el servidor de descarga de forma segura...")
        httpd.shutdown()
        httpd.server_close()
        sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Error al levantar el servidor: {e}")
        input("\nPresiona ENTER para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()
