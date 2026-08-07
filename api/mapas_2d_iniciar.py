#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import time

# --- CONFIGURACIÓN ---
MAPS_DIR = "/home/pi/robot_custom/mapping/maps"
LAPTOP_USER = "toscano"
LAPTOP_IP = "192.168.1.76"

def verificar_y_sincronizar_modelo(laptop_user, laptop_ip):
    """
    Verifica si el paquete del modelo 3D existe en la PC remota.
    Si no existe, lo transfiere automáticamente vía SCP y lo compila.
    """
    print("\n🔍 [Verificación] Comprobando el modelo del robot en la PC remota...")
    
    check_cmd = f'ssh {laptop_user}@{laptop_ip} "[ -d ~/yahboomcar_ws/src/yahboomcar_description ]"'
    res = subprocess.run(check_cmd, shell=True)
    
    if res.returncode != 0:
        print("📦 Modelo no encontrado en la PC. Iniciando transferencia automática...")
        
        subprocess.run(f'ssh {laptop_user}@{laptop_ip} "mkdir -p ~/yahboomcar_ws/src"', shell=True)
        
        ruta_local_modelo = "~/yahboomcar_ws/src/yahboomcar_description"
        scp_cmd = f"scp -r {ruta_local_modelo} {laptop_user}@{laptop_ip}:~/yahboomcar_ws/src/"
        
        print("⏳ Transfiriendo archivos (esto puede tardar unos segundos)...")
        scp_res = subprocess.run(scp_cmd, shell=True)
        
        if scp_res.returncode == 0:
            print("⚙️ Archivos copiados. Compilando el espacio de trabajo en la PC...")
            build_cmd = f'ssh {laptop_user}@{laptop_ip} "bash -c \'source /opt/ros/melodic/setup.bash && cd ~/yahboomcar_ws && catkin_make\'"'
            subprocess.run(build_cmd, shell=True, stdout=subprocess.DEVNULL)
            print("✅ Modelo sincronizado y registrado con éxito en la PC.")
        else:
            print("❌ Error al intentar transferir el modelo. Verifica la conexión a internet/red.")
    else:
        print("✅ El modelo ya está configurado en la PC.")

def iniciar_mapeo_interactivo():
    os.system('clear')
    print("=========================================================")
    print("       🚀 ASISTENTE DE MAPEO 2D INTERACTIVO              ")
    print("=========================================================")
    
    # Asegurarnos de que el directorio de mapas exista
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)
        
    print("\n🛡️  Deteniendo cualquier nodo residual por seguridad...")
    subprocess.run("pkill -INT -f 'yahboomcar_map.launch' >/dev/null 2>&1", shell=True)
    subprocess.run("pkill -INT -f 'laser_bringup.launch' >/dev/null 2>&1", shell=True)
    time.sleep(2)

    # 1. Iniciar Nodos Base y SLAM
    print("\n⚡ [1/3] Iniciando Chasis, LiDAR y SLAM (Gmapping)...")
    cmd_base_slam = (
        "bash -c 'source /opt/ros/melodic/setup.bash && "
        "source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null && "
        "roslaunch yahboomcar_nav laser_bringup.launch > /dev/null 2>&1 & sleep 5 && "
        "roslaunch yahboomcar_nav yahboomcar_map.launch > /dev/null 2>&1 &' &"
    )
    subprocess.Popen(cmd_base_slam, shell=True)
    time.sleep(7) 
    
    # 2. Verificación de Modelo y Exportación de RViz
    print("\n💻 [2/3] Preparando entorno visual en la PC remota...")
    verificar_y_sincronizar_modelo(LAPTOP_USER, LAPTOP_IP)
    
    print("🖥️ Abriendo RViz en la computadora de control...")
    cmd_rviz = f'ssh -f {LAPTOP_USER}@{LAPTOP_IP} "export DISPLAY=:0; export ROS_MASTER_URI=http://192.168.1.75:11311; export ROS_IP={LAPTOP_IP}; source ~/yahboomcar_ws/devel/setup.bash; rviz -d ~/yahboomcar_ws/src/yahboomcar_description/rviz/mapeo_yahboom.rviz" > /dev/null 2>&1 &'
    subprocess.Popen(cmd_rviz, shell=True)
    time.sleep(2)

    # 3. Seleccionar Control
    print("\n🎮 [3/3] SELECCIONA EL MÓDULO DE CONTROL:")
    print(" 1) Control con Mando / Joystick")
    print(" 2) Control con Teclado")
    
    ctrl_opt = input(" Elige una opción (1 o 2): ").strip()
    
    if ctrl_opt == "2":
        print("\n⌨️  Iniciando Control por Teclado...")
        subprocess.Popen("bash -c 'source /opt/ros/melodic/setup.bash && roslaunch yahboomcar_ctrl yahboom_keyboard.launch > /dev/null 2>&1 &' &", shell=True)
    else:
        print("\n🎮 Iniciando Control por Mando...")
        subprocess.Popen("bash -c 'source /opt/ros/melodic/setup.bash && roslaunch yahboomcar_ctrl yahboom_joy.launch > /dev/null 2>&1 &' &", shell=True)

    # 4. Esperar a que el usuario termine
    print("\n=========================================================")
    print(" 🛰️  MAPEO EN PROCESO. Mueve el robot para explorar.")
    print("=========================================================")
    input("\n 🛑 PRESIONA [ENTER] CUANDO TERMINES DE MAPEAR PARA DETENER... ")

    # 5. Detener procesos para poder guardar con seguridad o descartar
    print("\nDeteniendo nodos de mapeo y control visual...")
    subprocess.run("pkill -INT -f 'yahboom_keyboard.launch' >/dev/null 2>&1", shell=True)
    subprocess.run("pkill -INT -f 'yahboom_joy.launch' >/dev/null 2>&1", shell=True)
    # Nota: No matamos el nodo de gmapping aún para que la RAM conserve el mapa temporalmente.
    time.sleep(2)
    
    # 6. Ciclo para Guardar el Mapa
    while True:
        os.system('clear')
        print("=========================================================")
        print("                  💾 GUARDAR MAPA                        ")
        print("=========================================================")
        print(" 1. Guardar mapa actual")
        print(" 2. Descartar y salir")
        print("=========================================================")
        
        opc = input(" Selecciona una opción: ").strip()
        
        if opc == "1":
            map_name = input("\n Ingresa el nombre para el mapa (sin espacios ni extensión): ").strip()
            
            if not map_name:
                print("❌ Nombre no válido. Intenta de nuevo.")
                time.sleep(2)
                continue
                
            full_path = os.path.join(MAPS_DIR, map_name)
            
            if os.path.exists(f"{full_path}.yaml") or os.path.exists(f"{full_path}.pgm"):
                print(f"⚠️  CUIDADO: Ya existe un mapa llamado '{map_name}'.")
                print(" Por favor, elige otro nombre para no sobrescribirlo.")
                time.sleep(3)
                continue
                
            print(f"\n💾 Guardando mapa en la Raspberry Pi ({full_path})...")
            cmd_save = f"bash -c 'source /opt/ros/melodic/setup.bash && rosrun map_server map_saver -f {full_path}'"
            res = subprocess.run(cmd_save, shell=True)

            if res.returncode == 0:
                print(f"\n✅ ¡Mapa '{map_name}' guardado exitosamente!")
                input("\nPresiona ENTER para salir al menú principal...")
                break
            else:
                print("\n⚠️ Error al guardar. Verifica que el robot siga encendido y ROS activo.")
                time.sleep(3)
                
        elif opc == "2":
            print("\n🗑️ Mapa descartado.")
            time.sleep(1)
            break
            
    # Limpieza final absoluta al salir
    subprocess.run("pkill -INT -f 'yahboomcar_map.launch' >/dev/null 2>&1", shell=True)
    subprocess.run("pkill -INT -f 'laser_bringup.launch' >/dev/null 2>&1", shell=True)

if __name__ == "__main__":
    iniciar_mapeo_interactivo()
