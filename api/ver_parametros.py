#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json

MODELOS_DIR = "/home/pi/robot_custom/modelos"

def ver_parametros_modelo():
    os.system('clear')
    print("=========================================================")
    print(" 📊 VISUALIZADOR DE PARÁMETROS Y CLASES IA")
    print("=========================================================")

    if not os.path.exists(MODELOS_DIR):
        print("\n[ERROR] La carpeta de modelos no existe.")
        return

    archivos = os.listdir(MODELOS_DIR)
    jsons = sorted([f for f in archivos if f.endswith('.json')])

    if not jsons:
        print("\n[INFO] No se encontraron archivos de configuración (.json).")
        print("Asegúrate de haber importado un modelo con sus metadatos.")
        return

    print("Archivos de configuración disponibles:")
    for idx, archivo in enumerate(jsons, 1):
        print("  {}) {}".format(idx, archivo))
    print("  c) Cancelar")
    print("=========================================================")

    try:
        seleccion = raw_input("\nSelecciona el número del archivo a leer: ").strip().lower()
    except NameError:
        seleccion = input("\nSelecciona el número del archivo a leer: ").strip().lower()

    if seleccion == 'c':
        return

    try:
        idx_seleccionado = int(seleccion) - 1
        if idx_seleccionado < 0 or idx_seleccionado >= len(jsons):
            print("\n[ERROR] Selección fuera de rango.")
            return
        
        archivo_seleccionado = jsons[idx_seleccionado]
        ruta_completa = os.path.join(MODELOS_DIR, archivo_seleccionado)
        
        with open(ruta_completa, 'r') as f:
            datos = json.load(f)
            
        os.system('clear')
        print("=========================================================")
        print(" 📄 METADATOS DEL MODELO: {}".format(archivo_seleccionado))
        print("=========================================================")
        
        for clave, valor in datos.items():
            clave_formateada = clave.replace('_', ' ').capitalize()
            if isinstance(valor, list):
                print(" 🔹 {}:".format(clave_formateada))
                for item in valor:
                    print("    - {}".format(item))
            else:
                print(" 🔹 {}: {}".format(clave_formateada, valor))
                
        print("=========================================================")
        
    except ValueError:
        print("\n[ERROR] Por favor, ingresa un número válido.")
    except Exception as e:
        print("\n[ERROR] No se pudo leer el archivo JSON: {}".format(e))

