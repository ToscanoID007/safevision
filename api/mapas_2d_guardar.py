#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import time

# --- CONFIGURACIÓN ---
MAPS_DIR = "/home/pi/robot_custom/mapping/maps"

def guardar_mapa_independiente():
    os.system('clear')
    print("=========================================================")
    print("       💾 GUARDAR MAPA 2D (MODO INDEPENDIENTE)           ")
    print("=========================================================")
    print(" Esta herramienta extraerá el mapa actual de la memoria.")
    print(" (Requiere que el nodo de SLAM esté corriendo activamente)")
    print("---------------------------------------------------------")
    
    # Asegurarnos de que el directorio de mapas exista
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

    map_name = input("\n📝 Ingresa el nombre para el mapa (sin extensión): ").strip()

    if not map_name:
        print("\n❌ Nombre no válido. Operación cancelada.")
        time.sleep(2)
        return

    full_path = os.path.join(MAPS_DIR, map_name)

    # Validar si el mapa ya existe
    if os.path.exists(f"{full_path}.yaml") or os.path.exists(f"{full_path}.pgm"):
        print(f"\n⚠️  CUIDADO: Ya existe un mapa llamado '{map_name}'.")
        resp = input(" ¿Deseas sobrescribirlo? (s/n): ").strip().lower()
        if resp != 's':
            print("\n🚫 Operación cancelada.")
            time.sleep(2)
            return

    print(f"\n⏳ Extrayendo mapa de ROS y guardando en la Raspberry Pi...")
    
    # Comando de ROS para guardar el mapa
    cmd_save = f"bash -c 'source /opt/ros/melodic/setup.bash && rosrun map_server map_saver -f {full_path}'"
    
    # Ejecutamos el comando y capturamos el resultado
    res = subprocess.run(cmd_save, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if res.returncode == 0:
        print(f"\n✅ ¡ÉXITO! Mapa guardado correctamente.")
        print(f"📁 Ruta: {full_path}")
    else:
        print("\n❌ ERROR AL GUARDAR EL MAPA.")
        print("⚠️  Es probable que el nodo de mapeo (Gmapping) no esté activo,")
        print("   o que no se haya generado suficiente información del mapa aún.")

    input("\n🔙 Presiona ENTER para volver al menú...")

if __name__ == "__main__":
    guardar_mapa_independiente()
