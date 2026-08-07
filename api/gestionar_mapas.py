#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from utils import ejecutar, pausar

MAPS_DIR = "/home/pi/robot_custom/mapping/maps"

def leer_entrada(mensaje):
    try:
        return input(mensaje)
    except NameError:
        return raw_input(mensaje)

def obtener_ip_laptop():
    ssh_client = os.environ.get('SSH_CLIENT', '')
    if ssh_client:
        return ssh_client.split()[0]
    return "192.168.1.76"

def abrir_visor_gui_remoto(ruta_yaml):
    laptop_ip = obtener_ip_laptop()
    print("\n🖥️ Desplegando mapa interactivo en la Laptop (" + laptop_ip + ")...")
    
    # Lanza el visor en la Pi redireccionando el entorno gráfico a la pantalla de la Laptop
    cmd_visor = "DISPLAY=" + laptop_ip + ":0.0 python3 /home/pi/robot_custom/api/visor_mapa.py '" + ruta_yaml + "' >/dev/null 2>&1 &"
    subprocess.Popen(cmd_visor, shell=True)

def gestionar_mapa_individual(nombre_mapa_sin_ext):
    ruta_yaml = os.path.join(MAPS_DIR, nombre_mapa_sin_ext + ".yaml")
    ruta_pgm = os.path.join(MAPS_DIR, nombre_mapa_sin_ext + ".pgm")

    while True:
        os.system('clear')
        print("=========================================================")
        print("       ⚙️  GESTIONANDO MAPA: " + nombre_mapa_sin_ext)
        print("=========================================================")
        print(" [1] 👁️  Visualizar mapa (GUI / Zoom)")
        print(" [2] 📄 Ver detalles del mapa (Info YAML)")
        print(" [3] ✏️  Renombrar mapa")
        print(" [4] 🗑️  Eliminar mapa")
        print(" [0] 🔙 Volver a la lista de mapas")
        print("=========================================================")
        
        opc = leer_entrada(" Selecciona una opción: ").strip()

        if opc == "1":
            abrir_visor_gui_remoto(ruta_yaml)
            pausar()
        elif opc == "2":
            print("\n📄 Contenido del archivo YAML:\n")
            if os.path.exists(ruta_yaml):
                with open(ruta_yaml, 'r') as f:
                    print(f.read())
            else:
                print("❌ Archivo YAML no encontrado.")
            pausar()
        elif opc == "3":
            nuevo_nombre = leer_entrada("\n✏️  Nuevo nombre para el mapa (sin extensión): ").strip()
            if nuevo_nombre:
                nueva_ruta_yaml = os.path.join(MAPS_DIR, nuevo_nombre + ".yaml")
                nueva_ruta_pgm = os.path.join(MAPS_DIR, nuevo_nombre + ".pgm")
                
                if os.path.exists(ruta_yaml): os.rename(ruta_yaml, nueva_ruta_yaml)
                if os.path.exists(ruta_pgm): os.rename(ruta_pgm, nueva_ruta_pgm)
                
                print("✅ Mapa renombrado con éxito a: " + nuevo_nombre)
                pausar()
                break
        elif opc == "4":
            conf = leer_entrada("\n⚠️  ¿Seguro que deseas eliminar '" + nombre_mapa_sin_ext + "'? (s/n): ").strip().lower()
            if conf == 's':
                if os.path.exists(ruta_yaml): os.remove(ruta_yaml)
                if os.path.exists(ruta_pgm): os.remove(ruta_pgm)
                print("🗑️ Mapa eliminado correctamente.")
                pausar()
                break
        elif opc == "0":
            break

def menu_gestionar_mapas():
    while True:
        os.system('clear')
        print("=========================================================")
        print("       👁️  VER Y GESTIONAR MAPAS 2D                     ")
        print("=========================================================")
        print(" 📂 Mapas encontrados en: " + MAPS_DIR + "\n")

        mapas_yaml = sorted([f[:-5] for f in os.listdir(MAPS_DIR) if f.endswith('.yaml')]) if os.path.exists(MAPS_DIR) else []

        if not mapas_yaml:
            print("❌ No se encontraron mapas.")
            pausar()
            return

        for idx, m in enumerate(mapas_yaml, 1):
            print(" [{}] 🗺️  {}".format(idx, m))

        print("\n [0] 🔙 Volver al Menú Principal")
        print("=========================================================")
        
        choice = leer_entrada(" Selecciona el mapa que deseas gestionar (número): ").strip()
        
        if choice == "0":
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(mapas_yaml):
            gestionar_mapa_individual(mapas_yaml[int(choice) - 1])

if __name__ == "__main__":
    menu_gestionar_mapas()
