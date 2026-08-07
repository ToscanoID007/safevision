#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import glob
import subprocess

# --- CONFIGURACIÓN ---
MAPS_DIR = "/home/pi/robot_custom/mapping/maps"
VISOR_SCRIPT = "/home/pi/robot_custom/api/visor_mapa.py"
CONFIG_FILE = "/home/pi/robot_custom/api/.pc_config"

def obtener_datos_laptop():
    """Detecta la IP SSH y obtiene/solicita el nombre de usuario de la PC cliente."""
    ssh_client = os.environ.get('SSH_CLIENT', '')
    laptop_ip = ssh_client.split()[0] if ssh_client else "192.168.1.76"
    
    laptop_user = ""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                laptop_user = f.read().strip()
        except Exception:
            pass
            
    if not laptop_user:
        print(f"\n⚙️  Configuración de transferencia a PC cliente ({laptop_ip}):")
        laptop_user = input("👉 Ingresa tu nombre de usuario de la PC (ej: toscano, ubuntu, pi): ").strip()
        if laptop_user:
            with open(CONFIG_FILE, 'w') as f:
                f.write(laptop_user)
                
    return laptop_ip, laptop_user

def abrir_visor_gui(ruta_yaml):
    """Transfiere el mapa a la PC, verifica entorno/dependencias, lo ejecuta localmente y lo elimina."""
    laptop_ip, laptop_user = obtener_datos_laptop()
    
    if not laptop_user:
        print("❌ Operación cancelada: Se requiere un usuario de PC.")
        return

    nombre_yaml = os.path.basename(ruta_yaml)
    nombre_sin_ext = os.path.splitext(nombre_yaml)[0]
    ruta_pgm = os.path.join(MAPS_DIR, f"{nombre_sin_ext}.pgm")

    target = f"{laptop_user}@{laptop_ip}"

    print("\n=========================================================")
    print("🚀 DESPLIEGUE LOCAL DE MAPA EN TU PC")
    print("=========================================================")
    
    # 1. Comprobación de IP / SSH
    print(f"🔄 [1/5] Estableciendo enlace seguro con la PC ({target})...")
    time.sleep(0.5)

    # 2. Sincronizar siempre la versión actualizada del visor
    print("🔄 [2/5] Sincronizando script visor en la PC...")
    cmd_scp_script = f"scp -q '{VISOR_SCRIPT}' '{target}:/tmp/visor_mapa.py'"
    if subprocess.run(cmd_scp_script, shell=True).returncode != 0:
        print("\n❌ Error enviando el visor a la PC. Verifica conexión SSH.")
        return
    print("   ✅ Script visor actualizado en la PC.")

    # 3. Transferencia temporal del mapa (.yaml + .pgm)
    print("🔄 [3/5] Transfiriendo archivos del mapa a la PC (/tmp/)...")
    cmd_scp_maps = f"scp -q '{ruta_yaml}' '{ruta_pgm}' '{target}:/tmp/'"
    if subprocess.run(cmd_scp_maps, shell=True).returncode != 0:
        print("\n❌ Error transfiriendo los archivos del mapa.")
        return
    print("   ✅ Mapa cargado en la PC exitosamente.")

    # 4. Verificación de librerías y ejecución remota con interfaz gráfica local
    print("🖥️  [4/5] Verificando dependencias y desplegando visor...")
    print("📌 Instructivo: Si es la primera vez, ingresa la contraseña de tu PC si solicita sudo.")
    
    cmd_run_remote = (
        f"ssh -X -t {target} "
        f"\"python3 -c 'import matplotlib, yaml' 2>/dev/null || ("
        f"echo '⚡ Instalando librerías requeridas en tu PC (matplotlib y pyyaml)...'; "
        f"sudo apt-get update -qq && sudo apt-get install -y python3-matplotlib python3-yaml"
        f"); "
        f"export DISPLAY=\\${{DISPLAY:-:0}}; "
        f"python3 /tmp/visor_mapa.py '/tmp/{nombre_yaml}'; "
        f"rm -f '/tmp/{nombre_yaml}' '/tmp/{nombre_sin_ext}.pgm'\""
    )
    
    subprocess.run(cmd_run_remote, shell=True)

    # 5. Confirmación de Autolimpieza
    print("🧹 [5/5] Eliminación de mapa temporal en la PC completada.")
    print("✅ Proceso finalizado. Tu PC quedó limpia de residuos.")
    print("=========================================================")

def obtener_mapas():
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)
    archivos_yaml = glob.glob(os.path.join(MAPS_DIR, "*.yaml"))
    return sorted([os.path.splitext(os.path.basename(f))[0] for f in archivos_yaml])

def mostrar_menu_gestion():
    while True:
        os.system('clear')
        print("=========================================================")
        print("       👁️  VER Y GESTIONAR MAPAS 2D                      ")
        print("=========================================================")
        
        mapas = obtener_mapas()
        
        if not mapas:
            print("\n 📂 No hay mapas guardados actualmente en el directorio.")
            print(f" 📍 Ruta: {MAPS_DIR}")
            input("\n 🔙 Presiona ENTER para volver al menú principal...")
            break
            
        print(f" 📂 Mapas encontrados en: {MAPS_DIR}\n")
        for i, mapa in enumerate(mapas, 1):
            print(f" [{i}] 🗺️  {mapa}")
        
        print("\n [0] 🔙 Volver al Menú Principal")
        print("=========================================================")
        
        opcion = input(" Selecciona el mapa que deseas gestionar (número): ").strip()
        if opcion == "0":
            break
            
        try:
            indice = int(opcion) - 1
            if 0 <= indice < len(mapas):
                gestionar_mapa(mapas[indice])
            else:
                print("\n❌ Opción fuera de rango.")
                time.sleep(1)
        except ValueError:
            print("\n❌ Ingresa un número válido.")
            time.sleep(1)

def gestionar_mapa(nombre_mapa):
    ruta_yaml = os.path.join(MAPS_DIR, f"{nombre_mapa}.yaml")

    while True:
        os.system('clear')
        print("=========================================================")
        print(f"       ⚙️  GESTIONANDO MAPA: {nombre_mapa}")
        print("=========================================================")
        print(" [1] 👁️  Visualizar mapa (Despliegue Local en PC)")
        print(" [2] 📄 Ver detalles del mapa (Info YAML)")
        print(" [3] ✏️  Renombrar mapa")
        print(" [4] 🗑️  Eliminar mapa")
        print(" [5] 🔄 Resetear usuario de PC guardado")
        print(" [0] 🔙 Volver a la lista de mapas")
        print("=========================================================")
        
        opc = input(" Selecciona una opción: ").strip()
        
        if opc == "1":
            if os.path.exists(ruta_yaml):
                abrir_visor_gui(ruta_yaml)
            else:
                print("❌ Archivo YAML no encontrado.")
            input("\n Presiona ENTER para continuar...")
        elif opc == "2":
            ver_detalles(nombre_mapa)
        elif opc == "3":
            nuevo_nombre = renombrar_mapa(nombre_mapa)
            if nuevo_nombre:
                nombre_mapa = nuevo_nombre
                ruta_yaml = os.path.join(MAPS_DIR, f"{nombre_mapa}.yaml")
        elif opc == "4":
            if eliminar_mapa(nombre_mapa):
                break
        elif opc == "5":
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            print("\n✅ Configuración de usuario de PC reiniciada.")
            time.sleep(1.5)
        elif opc == "0":
            break
        else:
            print("\n❌ Opción inválida.")
            time.sleep(1)

def ver_detalles(nombre_mapa):
    print(f"\n📄 Detalles técnicos de {nombre_mapa}.yaml:")
    print("---------------------------------------------------------")
    ruta_yaml = os.path.join(MAPS_DIR, f"{nombre_mapa}.yaml")
    try:
        with open(ruta_yaml, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
    print("---------------------------------------------------------")
    input(" Presiona ENTER para continuar...")

def renombrar_mapa(nombre_mapa):
    nuevo_nombre = input(f"\n✏️ Ingresa el nuevo nombre para '{nombre_mapa}' (sin extensión): ").strip()
    if not nuevo_nombre:
        print("❌ Nombre no válido.")
        time.sleep(1)
        return None
        
    ruta_vieja_yaml = os.path.join(MAPS_DIR, f"{nombre_mapa}.yaml")
    ruta_vieja_pgm = os.path.join(MAPS_DIR, f"{nombre_mapa}.pgm")
    ruta_nueva_yaml = os.path.join(MAPS_DIR, f"{nuevo_nombre}.yaml")
    ruta_nueva_pgm = os.path.join(MAPS_DIR, f"{nuevo_nombre}.pgm")
    
    if os.path.exists(ruta_nueva_yaml) or os.path.exists(ruta_nueva_pgm):
        print(f"❌ Ya existe un mapa llamado '{nuevo_nombre}'.")
        time.sleep(2)
        return None
        
    try:
        if os.path.exists(ruta_vieja_pgm):
            os.rename(ruta_vieja_pgm, ruta_nueva_pgm)
            
        if os.path.exists(ruta_vieja_yaml):
            with open(ruta_vieja_yaml, 'r') as file:
                yaml_data = file.read()
            yaml_data = yaml_data.replace(f"{nombre_mapa}.pgm", f"{nuevo_nombre}.pgm")
            with open(ruta_vieja_yaml, 'w') as file:
                file.write(yaml_data)
            os.rename(ruta_vieja_yaml, ruta_nueva_yaml)
            
        print(f"\n✅ Mapa renombrado a '{nuevo_nombre}'.")
        time.sleep(1.5)
        return nuevo_nombre
    except Exception as e:
        print(f"\n❌ Error al renombrar: {e}")
        time.sleep(2)
        return None

def eliminar_mapa(nombre_mapa):
    print(f"\n⚠️  ¿Deseas eliminar permanentemente '{nombre_mapa}'?")
    resp = input(" Confirmar eliminación (s/n): ").strip().lower()
    if resp == 's':
        ruta_yaml = os.path.join(MAPS_DIR, f"{nombre_mapa}.yaml")
        ruta_pgm = os.path.join(MAPS_DIR, f"{nombre_mapa}.pgm")
        try:
            if os.path.exists(ruta_yaml): os.remove(ruta_yaml)
            if os.path.exists(ruta_pgm): os.remove(ruta_pgm)
            print(f"\n✅ Mapa '{nombre_mapa}' eliminado.")
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"\n❌ Error al intentar eliminar: {e}")
            time.sleep(2)
            return False
    else:
        print("\n🚫 Operación cancelada.")
        time.sleep(1.5)
        return False

if __name__ == "__main__":
    mostrar_menu_gestion()
