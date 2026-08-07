#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import time

MAPS_DIR = "/home/pi/robot_custom/mapping/maps"
EDITOR_SCRIPT = "/home/pi/robot_custom/api/robot_map_editor.py"

# Configuraciones de tu PC
LAPTOP_USER = "toscano"
LAPTOP_IP = "192.168.1.76"

def listar_mapas():
    if not os.path.exists(MAPS_DIR):
        print(f"❌ La carpeta de mapas no existe: {MAPS_DIR}")
        return []
    archivos = [f for f in os.listdir(MAPS_DIR) if f.endswith('.pgm')]
    return sorted(archivos)

def editar_mapa_remoto(mapa_nombre):
    ruta_local_mapa = os.path.join(MAPS_DIR, mapa_nombre)
    ruta_remota_mapa = f"/home/{LAPTOP_USER}/{mapa_nombre}"

    print("\n" + "="*57)
    print(" 🚀 INICIANDO EDICIÓN REMOTA...")
    print("="*57)

    # 1. Comprobar dependencias en la PC (Laptop)
    print("🔍 1/5 Verificando librerías de Python en la PC...")
    cmd_check = f'ssh {LAPTOP_USER}@{LAPTOP_IP} "python3 -c \\"import PIL, tkinter\\""'
    res = subprocess.run(cmd_check, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if res.returncode != 0:
        print("⚡ Instalando dependencias necesarias en la PC (pedirá tu contraseña sudo)...")
        cmd_install = f'ssh -t {LAPTOP_USER}@{LAPTOP_IP} "sudo apt-get update && sudo apt-get install -y python3-pil python3-pil.imagetk python3-tk rsync"'
        subprocess.run(cmd_install, shell=True)
    else:
        print("✅ Dependencias listas.")

    # 2. Mandar el script del editor a la PC
    print("🔄 2/5 Enviando script del editor a la PC...")
    cmd_sync_script = f"rsync -az {EDITOR_SCRIPT} {LAPTOP_USER}@{LAPTOP_IP}:~/robot_map_editor.py"
    subprocess.run(cmd_sync_script, shell=True)

    # 3. Mandar el mapa a editar
    print(f"📤 3/5 Enviando el mapa '{mapa_nombre}' a la PC...")
    cmd_sync_map = f"rsync -avzP {ruta_local_mapa} {LAPTOP_USER}@{LAPTOP_IP}:{ruta_remota_mapa}"
    subprocess.run(cmd_sync_map, shell=True)

    # 4. Ejecutar el editor en la PC
    print("\n🖥️  4/5 Abriendo el editor en la pantalla de la PC...")
    print("   👉 Ve a tu laptop, edita el mapa y presiona 'Guardar y Salir'.")
    # Se exporta DISPLAY=:0 para que la interfaz gráfica se abra en la pantalla principal de la laptop
    cmd_run_editor = f'ssh -t {LAPTOP_USER}@{LAPTOP_IP} "export DISPLAY=:0; python3 ~/robot_map_editor.py {ruta_remota_mapa}"'
    subprocess.run(cmd_run_editor, shell=True)

    # 5. Traer el mapa de regreso
    print("\n📥 5/5 Recuperando el mapa editado desde la PC al robot...")
    cmd_pull_map = f"rsync -avzP {LAPTOP_USER}@{LAPTOP_IP}:{ruta_remota_mapa} {ruta_local_mapa}"
    subprocess.run(cmd_pull_map, shell=True)

    print(f"\n✅ ¡Proceso completado! Mapa '{mapa_nombre}' sobrescrito y actualizado con éxito.")

def main():
    while True:
        os.system('clear')
        print("=========================================================")
        print("          🎨 SELECCIONA UN MAPA PARA EDITAR              ")
        print("=========================================================")
        
        mapas = listar_mapas()
        if not mapas:
            print(" No hay mapas (.pgm) disponibles para editar.")
            input("\nPresiona ENTER para volver...")
            break
            
        for idx, mapa in enumerate(mapas, 1):
            peso_kb = os.path.getsize(os.path.join(MAPS_DIR, mapa)) / 1024.0
            print(f" [{idx}] 🗺️ {mapa} ({peso_kb:.1f} KB)")
            
        print("\n [0] 🔙 Cancelar / Volver")
        print("=========================================================")
        
        opcion = input(f" Selecciona el mapa (0-{len(mapas)}): ").strip()
        
        if opcion == "0":
            break
        elif opcion.isdigit() and 1 <= int(opcion) <= len(mapas):
            mapa_seleccionado = mapas[int(opcion) - 1]
            editar_mapa_remoto(mapa_seleccionado)
            input("\nPresiona ENTER para continuar...")
        else:
            print("❌ Opción inválida.")
            time.sleep(1)

if __name__ == "__main__":
    main()
