#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

MODELOS_DIR = "/home/pi/robot_custom/modelos"

def editar_nombre_modelo():
    os.system('clear')
    print("=========================================================")
    print(" 🏷️  EDITAR NOMBRE DE ARCHIVO DEL MODELO")
    print("=========================================================")

    if not os.path.exists(MODELOS_DIR):
        print("\n[ERROR] La carpeta de modelos no existe.")
        return

    archivos = os.listdir(MODELOS_DIR)
    modelos = sorted([f for f in archivos if f.endswith(('.pt', '.weights'))])

    if not modelos:
        print("\n[INFO] No se encontraron modelos (.pt o .weights) para renombrar.")
        return

    print("Modelos disponibles:")
    for idx, archivo in enumerate(modelos, 1):
        print("  {}) {}".format(idx, archivo))
    print("  c) Cancelar")
    print("=========================================================")

    try:
        seleccion = raw_input("\nSelecciona el modelo a renombrar: ").strip().lower()
    except NameError:
        seleccion = input("\nSelecciona el modelo a renombrar: ").strip().lower()

    if seleccion == 'c':
        return

    try:
        idx_seleccionado = int(seleccion) - 1
        if idx_seleccionado < 0 or idx_seleccionado >= len(modelos):
            print("\n[ERROR] Selección fuera de rango.")
            return
        
        archivo_viejo = modelos[idx_seleccionado]
        nombre_base, extension = os.path.splitext(archivo_viejo)
        
        try:
            nuevo_nombre_base = raw_input("\nIngresa el NUEVO nombre (sin extensión): ").strip()
        except NameError:
            nuevo_nombre_base = input("\nIngresa el NUEVO nombre (sin extensión): ").strip()
            
        if not nuevo_nombre_base:
            print("\n[ERROR] El nombre no puede estar vacío.")
            return
            
        # Reemplazar espacios por guiones bajos para evitar problemas
        nuevo_nombre_base = nuevo_nombre_base.replace(" ", "_")
        archivo_nuevo = nuevo_nombre_base + extension
        
        ruta_vieja = os.path.join(MODELOS_DIR, archivo_viejo)
        ruta_nueva = os.path.join(MODELOS_DIR, archivo_nuevo)
        
        if os.path.exists(ruta_nueva):
            print("\n[ERROR] Ya existe un archivo con el nombre '{}'.".format(archivo_nuevo))
            return
            
        os.rename(ruta_vieja, ruta_nueva)
        print("\n[ÉXITO] Modelo renombrado a: {}".format(archivo_nuevo))
        
        # Buscar si existe el .json correspondiente para renombrarlo también
        json_viejo = nombre_base + ".json"
        ruta_json_viejo = os.path.join(MODELOS_DIR, json_viejo)
        
        if os.path.exists(ruta_json_viejo):
            json_nuevo = nuevo_nombre_base + ".json"
            ruta_json_nueva = os.path.join(MODELOS_DIR, json_nuevo)
            os.rename(ruta_json_viejo, ruta_json_nueva)
            print("[ÉXITO] Metadatos actualizados a: {}".format(json_nuevo))
            
    except ValueError:
        print("\n[ERROR] Por favor, ingresa un número válido.")
    except Exception as e:
        print("\n[ERROR] Ocurrió un problema: {}".format(e))
