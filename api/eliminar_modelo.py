#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

MODELOS_DIR = "/home/pi/robot_custom/modelos"

def obtener_input(mensaje):
    try:
        return raw_input(mensaje).strip()
    except NameError:
        return input(mensaje).strip()

def eliminar_modelo_ia():
    os.system('clear')
    print("=========================================================")
    print(" 🗑️  ELIMINAR MODELO Y METADATOS")
    print("=========================================================")

    if not os.path.exists(MODELOS_DIR):
        print("\n[ERROR] La carpeta de modelos no existe.")
        return

    archivos = os.listdir(MODELOS_DIR)
    modelos = sorted([f for f in archivos if f.endswith(('.pt', '.weights'))])

    if not modelos:
        print("\n[INFO] No se encontraron modelos para eliminar.")
        return

    print("Modelos instalados en el sistema:")
    for idx, archivo in enumerate(modelos, 1):
        # Calcular tamaño para mostrarlo
        tamano = os.path.getsize(os.path.join(MODELOS_DIR, archivo)) / (1024 * 1024.0)
        print("  {}) {} ({:.2f} MB)".format(idx, archivo, tamano))
    print("  c) Cancelar")
    print("=========================================================")

    seleccion = obtener_input("\nSelecciona el modelo que deseas ELIMINAR: ").lower()

    if seleccion == 'c':
        return

    try:
        idx_seleccionado = int(seleccion) - 1
        if idx_seleccionado < 0 or idx_seleccionado >= len(modelos):
            print("\n[ERROR] Selección fuera de rango.")
            return
        
        archivo_eliminar = modelos[idx_seleccionado]
        nombre_base, _ = os.path.splitext(archivo_eliminar)
        json_asociado = nombre_base + ".json"
        
        ruta_modelo = os.path.join(MODELOS_DIR, archivo_eliminar)
        ruta_json = os.path.join(MODELOS_DIR, json_asociado)
        
        print("\n⚠️  ATENCIÓN: Estás a punto de eliminar permanentemente:")
        print("   - {}".format(archivo_eliminar))
        if os.path.exists(ruta_json):
            print("   - {}".format(json_asociado))
            
        confirmacion = obtener_input("\n¿Estás completamente seguro? (s/n): ").lower()
        
        if confirmacion == 's':
            os.remove(ruta_modelo)
            print("\n[ÉXITO] Modelo '{}' eliminado.".format(archivo_eliminar))
            
            if os.path.exists(ruta_json):
                os.remove(ruta_json)
                print("[ÉXITO] Metadatos '{}' eliminados.".format(json_asociado))
        else:
            print("\n[INFO] Operación cancelada. No se eliminó nada.")
            
    except ValueError:
        print("\n[ERROR] Por favor, ingresa un número válido.")
    except Exception as e:
        print("\n[ERROR] Ocurrió un problema al eliminar: {}".format(e))
