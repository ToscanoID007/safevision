#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import time
import socket
import os
import threading
import nodo_yolo_pi
import servidor_web_pi

def obtener_ip():
    """Descubre la IP local de la Raspberry Pi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def iniciar_servidor_flask(puerto):
    """Arranca la aplicación Flask en un hilo secundario."""
    servidor_web_pi.app.run(host='0.0.0.0', port=puerto, debug=False, use_reloader=False)

def ejecutar_cnn_pi():
    # Mensaje temporal de carga
    os.system('clear' if os.name == 'posix' else 'cls')
    print("\n[INFO] Despertando IA e iniciando cámara... (Esto tomará unos segundos)")
    
    # 1. Inicialización
    modelo = nodo_yolo_pi.inicializar_modelo('yolov8n.pt')
    cap = nodo_yolo_pi.inicializar_camara(0)
    
    if not cap.isOpened():
        print("\n[ERROR] No se pudo abrir la cámara. Verifica la conexión física.")
        return

    # 2. Configurar el panel web (Enviamos las clases del modelo para mostrarlas en la UI)
    clases_lista = list(modelo.names.values())
    servidor_web_pi.fijar_clases(clases_lista)

    # 3. Arrancar el servidor web en un hilo paralelo
    puerto = 5000
    ip_local = obtener_ip()
    hilo_web = threading.Thread(target=iniciar_servidor_flask, args=(puerto,))
    hilo_web.daemon = True
    hilo_web.start()

    # 4. Limpiar pantalla de consola y mostrar la interfaz de texto limpia
    os.system('clear' if os.name == 'posix' else 'cls')
    print("=========================================================")
    print(" 🟢 TRANSMISIÓN DE IA EN VIVO ACTIVADA")
    print("=========================================================")
    print(f" 🌐 Abre tu navegador y pega este enlace:")
    print(f"    http://{ip_local}:{puerto}")
    print("=========================================================")
    print(" 🔴 Para cerrar la sesión y apagar la cámara, presiona:  Ctrl + C")
    print("=========================================================")

    # Variables de optimización EXTREMA (Edge Computing)
    contador_frames = 0
    intervalo_inferencia = 5  # ⚡ NUEVO: Procesar 1 de cada 5 frames (mayor fluidez)
    ultimas_detecciones = []
    
    # ⚡ NUEVO: Factor de escala ajustado para tensor ultra-pequeño (160x120)
    ESCALA_X = 640 / 160
    ESCALA_Y = 480 / 120
    
    tiempo_anterior = time.time()

    try:
        while True:
            exito, frame_original = nodo_yolo_pi.leer_camara(cap)
            if not exito:
                time.sleep(0.01)
                continue
                
            contador_frames += 1
            
            # Obtener el valor del slider desde el servidor web
            umbral_actual = servidor_web_pi.obtener_confianza()

            # Frame Skipping Extremo
            if contador_frames % intervalo_inferencia == 0:
                # ⚡ NUEVO: Inferencia a resolución mínima (160x120) para máximo rendimiento
                frame_reducido = cv2.resize(frame_original, (160, 120))
                ultimas_detecciones = nodo_yolo_pi.inferir_yolo_optimizado(
                    modelo, frame_reducido, umbral_confianza=umbral_actual
                )
            
            # Dibujar y escalar
            frame_final = nodo_yolo_pi.dibujar_cajas_escaladas(
                frame_original, ultimas_detecciones, ESCALA_X, ESCALA_Y
            )
            
            # Enviar la imagen final al servidor web
            servidor_web_pi.actualizar_frame(frame_final)

            # Calcular y enviar FPS al servidor web (se actualiza cada 10 frames para estabilidad)
            if contador_frames % 10 == 0:
                tiempo_actual = time.time()
                fps = 10 / (tiempo_actual - tiempo_anterior)
                servidor_web_pi.actualizar_metrics(fps)
                tiempo_anterior = tiempo_actual
                
    except KeyboardInterrupt:
        # Aquí el usuario presionó Ctrl + C
        pass
    finally:
        print("\n[INFO] Apagando el servidor y liberando la cámara...")
        cap.release()
        cv2.destroyAllWindows()
        time.sleep(1)

if __name__ == "__main__":
    ejecutar_cnn_pi()
