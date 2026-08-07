#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil

def empaquetar_dashboard():
    base_dir = "/home/pi/robot_custom/api"
    directorio_origen = os.path.join(base_dir, "dashboard_pc_src")
    directorio_destino = os.path.join(base_dir, "payload")
    nombre_archivo = "SafeVision_Dashboard" # shutil.make_archive añade el .zip automáticamente
    
    print("\n=========================================================")
    print("📦 EMPAQUETADOR DE SAFEVISION")
    print("=========================================================")
    
    # 1. Verificar que el código fuente de la PC exista
    if not os.path.exists(directorio_origen):
        print(f"❌ Error: No se encontró la carpeta origen: {directorio_origen}")
        return False
        
    # 2. Asegurar que la carpeta payload exista
    if not os.path.exists(directorio_destino):
        print(f"[INFO] Creando carpeta payload en: {directorio_destino}")
        os.makedirs(directorio_destino)
        
    ruta_final = os.path.join(directorio_destino, nombre_archivo)
    
    print(f"[INFO] Comprimiendo archivos desde: {directorio_origen}")
    
    try:
        # 3. Comprimir la carpeta entera
        shutil.make_archive(ruta_final, 'zip', directorio_origen)
        print(f"✅ ¡Empaquetado exitoso!")
        print(f"📁 Archivo listo en: {ruta_final}.zip")
        print("=========================================================\n")
        return True
    except Exception as e:
        print(f"❌ Error crítico al comprimir: {e}")
        return False

if __name__ == "__main__":
    empaquetar_dashboard()
