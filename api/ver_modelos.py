#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

MODELOS_DIR = "/home/pi/robot_custom/modelos"

def mostrar_modelos():
    os.system('clear')
    print("=========================================================")
    print(" 📋 MODELOS IA INSTALADOS EN EL SISTEMA")
    print("=========================================================")

    if not os.path.exists(MODELOS_DIR):
        print("\n[INFO] La carpeta de modelos aun no existe o esta vacia.")
        return

    archivos = os.listdir(MODELOS_DIR)
    pesos = sorted([f for f in archivos if f.endswith(('.pt', '.weights'))])
    jsons = sorted([f for f in archivos if f.endswith('.json')])

    if not pesos and not jsons:
        print("\n[INFO] No hay modelos instalados actualmente en la carpeta.")
        return

    print("📦 ARCHIVOS DE MODELO (.pt / .weights):")
    if pesos:
        for idx, archivo in enumerate(pesos, 1):
            ruta = os.path.join(MODELOS_DIR, archivo)
            tamano_mb = os.path.getsize(ruta) / (1024 * 1024.0)
            print("  {}) {} ({:.2f} MB)".format(idx, archivo, tamano_mb))
    else:
        print("  - Ninguno detectado.")

    print("\n📄 METADATOS Y CLASES (.json):")
    if jsons:
        for idx, archivo in enumerate(jsons, 1):
            print("  {}) {}".format(idx, archivo))
    else:
        print("  - Ninguno detectado.")
    
    print("=========================================================")
