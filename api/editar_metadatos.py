#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json

MODELOS_DIR = "/home/pi/robot_custom/modelos"

# Función auxiliar para compatibilidad de inputs
def obtener_input(mensaje):
    try:
        return raw_input(mensaje).strip()
    except NameError:
        return input(mensaje).strip()

def editar_metadatos_modelo():
    os.system('clear')
    print("=========================================================")
    print(" 📝 EDITAR METADATOS Y CLASES (.json)")
    print("=========================================================")

    if not os.path.exists(MODELOS_DIR):
        print("\n[ERROR] La carpeta de modelos no existe.")
        return

    archivos = os.listdir(MODELOS_DIR)
    jsons = sorted([f for f in archivos if f.endswith('.json')])

    if not jsons:
        print("\n[INFO] No se encontraron archivos de configuración (.json).")
        return

    print("Archivos de configuración disponibles:")
    for idx, archivo in enumerate(jsons, 1):
        print("  {}) {}".format(idx, archivo))
    print("  c) Cancelar")
    print("=========================================================")

    seleccion = obtener_input("\nSelecciona el archivo a editar: ").lower()

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
            
        # Asegurar que exista la clave clases
        if "clases" not in datos:
            datos["clases"] = []
            
        while True:
            os.system('clear')
            print("=========================================================")
            print(" Editando: {}".format(archivo_seleccionado))
            print("=========================================================")
            print(" 1) Nombre interno: {}".format(datos.get("nombre_modelo", "N/A")))
            print(" 2) Versión: {}".format(datos.get("version", "N/A")))
            print(" 3) 🏷️  Gestionar Clases ({} actuales)".format(len(datos.get("clases", []))))
            print(" 4) 💾 Guardar y Salir")
            print(" 5) ❌ Descartar y Salir")
            print("=========================================================")
            
            opc = obtener_input("¿Qué deseas editar? (1-5): ")
                
            if opc == '1':
                nuevo_nombre = obtener_input("Nuevo nombre interno: ")
                if nuevo_nombre: datos["nombre_modelo"] = nuevo_nombre
                
            elif opc == '2':
                nueva_version = obtener_input("Nueva versión: ")
                if nueva_version: datos["version"] = nueva_version
                
            elif opc == '3':
                # --- SUBMENÚ DE GESTIÓN DE CLASES ---
                while True:
                    os.system('clear')
                    print("=========================================================")
                    print(" 🏷️  GESTIÓN DE CLASES")
                    print("=========================================================")
                    clases_actuales = datos.get("clases", [])
                    if not clases_actuales:
                        print("  [No hay clases registradas]")
                    else:
                        for i, c in enumerate(clases_actuales, 1):
                            print("  {}) {}".format(i, c))
                    print("=========================================================")
                    print(" a) ➕ Agregar nueva clase")
                    print(" e) ✏️  Editar una clase existente")
                    print(" d) 🗑️  Eliminar una clase")
                    print(" r) 🔙 Regresar al menú anterior")
                    print("=========================================================")
                    
                    opc_clase = obtener_input("Selecciona una opción (a/e/d/r): ").lower()
                    
                    if opc_clase == 'r':
                        break
                        
                    elif opc_clase == 'a':
                        nueva_c = obtener_input("Nombre de la nueva clase: ")
                        if nueva_c:
                            datos["clases"].append(nueva_c)
                            
                    elif opc_clase == 'e':
                        if not clases_actuales:
                            obtener_input("\nNo hay clases para editar. Presiona Enter...")
                            continue
                        try:
                            idx_c = int(obtener_input("\nNúmero de la clase a editar: ")) - 1
                            if 0 <= idx_c < len(clases_actuales):
                                edit_c = obtener_input("Nuevo nombre para '{}': ".format(clases_actuales[idx_c]))
                                if edit_c:
                                    datos["clases"][idx_c] = edit_c
                            else:
                                obtener_input("\n[ERROR] Número inválido. Presiona Enter...")
                        except ValueError:
                            obtener_input("\n[ERROR] Ingresa un número. Presiona Enter...")
                            
                    elif opc_clase == 'd':
                        if not clases_actuales:
                            obtener_input("\nNo hay clases para eliminar. Presiona Enter...")
                            continue
                        try:
                            idx_c = int(obtener_input("\nNúmero de la clase a eliminar: ")) - 1
                            if 0 <= idx_c < len(clases_actuales):
                                eliminada = datos["clases"].pop(idx_c)
                                obtener_input("\n[ÉXITO] Clase '{}' eliminada. Presiona Enter...".format(eliminada))
                            else:
                                obtener_input("\n[ERROR] Número inválido. Presiona Enter...")
                        except ValueError:
                            obtener_input("\n[ERROR] Ingresa un número. Presiona Enter...")
                            
            elif opc == '4':
                with open(ruta_completa, 'w') as f:
                    json.dump(datos, f, indent=4)
                print("\n[ÉXITO] Metadatos guardados correctamente.")
                break
                
            elif opc == '5':
                print("\n[INFO] Cambios descartados.")
                break
                
    except ValueError:
        print("\n[ERROR] Por favor, ingresa un número válido.")
    except Exception as e:
        print("\n[ERROR] Ocurrió un problema: {}".format(e))
