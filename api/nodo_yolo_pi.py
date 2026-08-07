#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] Falta la librería 'ultralytics'. Instálala con: pip install ultralytics")

def inicializar_modelo(ruta_modelo='yolov8n.pt'):
    return YOLO(ruta_modelo)

def inicializar_camara(indice_camara=0):
    cap = cv2.VideoCapture(indice_camara)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # ⚡ NUEVO: Elimina el retraso (lag) del video
    return cap

def leer_camara(cap):
    return cap.read()

def inferir_yolo_optimizado(modelo, frame_reducido, umbral_confianza=0.5):
    """Hace la inferencia tomando en cuenta el umbral seleccionado en la web."""
    resultados = modelo(frame_reducido, stream=True, verbose=False)
    detecciones = []
    
    for r in resultados:
        for caja in r.boxes:
            confianza = float(caja.conf[0])
            if confianza >= umbral_confianza:
                x1, y1, x2, y2 = map(int, caja.xyxy[0])
                clase = int(caja.cls[0])
                nombre_clase = modelo.names[clase]
                detecciones.append({
                    'coords': (x1, y1, x2, y2),
                    'conf': confianza,
                    'nombre': nombre_clase
                })
    return detecciones

def dibujar_cajas_escaladas(frame_original, detecciones, escala_x=2.0, escala_y=2.0):
    frame_dibujado = frame_original.copy()
    for det in detecciones:
        x1, y1, x2, y2 = det['coords']
        nx1, ny1 = int(x1 * escala_x), int(y1 * escala_y)
        nx2, ny2 = int(x2 * escala_x), int(y2 * escala_y)
        
        cv2.rectangle(frame_dibujado, (nx1, ny1), (nx2, ny2), (0, 255, 0), 2)
        texto = f"{det['nombre']} {det['conf']:.2f}"
        cv2.putText(frame_dibujado, texto, (nx1, ny1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
    return frame_dibujado
