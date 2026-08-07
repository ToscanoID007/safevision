#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
from utils import ejecutar, pausar, detener_mando_seguridad

MAPS_DIR = "/home/pi/robot_custom/mapping/maps"
LAPTOP_USER = "toscano"

def leer_entrada(mensaje):
    try:
        return input(mensaje)
    except NameError:
        return raw_input(mensaje)

def obtener_ip_local():
    ip = ejecutar("hostname -I | awk '{print $1}'").strip()
    return ip if ip else "192.168.1.75"

def obtener_ip_laptop():
    ssh_client = os.environ.get('SSH_CLIENT', '')
    if ssh_client:
        return ssh_client.split()[0]
    return "192.168.1.76"

def limpiar_procesos_previos():
    print("🧹 Limpiando procesos ROS previos...")
    ejecutar("pkill -9 -f roslaunch 2>/dev/null")
    ejecutar("pkill -9 -f roscore 2>/dev/null")
    ejecutar("pkill -9 -f rosmaster 2>/dev/null")
    time.sleep(1.5)

def verificar_conexion_laptop(laptop_ip):
    print("🌐 Verificando conexión SSH con Laptop (" + laptop_ip + ")...")
    cmd = "ssh -o ConnectTimeout=3 " + LAPTOP_USER + "@" + laptop_ip + " 'echo OK' 2>/dev/null"
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if "OK" in res.stdout:
        print("✅ Conexión SSH correcta.")
        return True
    else:
        print("❌ Error: No se pudo conectar a " + LAPTOP_USER + "@" + laptop_ip)
        return False

def sincronizar_modelos_3d_pc(laptop_ip):
    print("🔄 Sincronizando paquetes ROS y modelos 3D con la Laptop...")
    path_pc = "/home/" + LAPTOP_USER + "/yahboomcar_ws/src"
    cmd_mkdir = "ssh " + LAPTOP_USER + "@" + laptop_ip + " 'mkdir -p " + path_pc + "'"
    subprocess.run(cmd_mkdir, shell=True)
    
    cmd_sync = (
        "rsync -az --quiet "
        "~/yahboomcar_ws/src/yahboomcar_nav "
        "~/yahboomcar_ws/src/yahboomcar_description "
        + LAPTOP_USER + "@" + laptop_ip + ":" + path_pc + "/ 2>/dev/null"
    )
    subprocess.run(cmd_sync, shell=True)
    print("✅ Recursos y modelos 3D validados/actualizados en Laptop.")

def abrir_rviz_remoto(pi_ip, laptop_ip):
    print("🖥️ Desplegando RViz en la pantalla de la Laptop...")
    cmd_rviz = (
        "ssh -f " + LAPTOP_USER + "@" + laptop_ip + " "
        "\"export DISPLAY=${DISPLAY:-:0}; "
        "export ROS_MASTER_URI=http://" + pi_ip + ":11311; "
        "export ROS_IP=" + laptop_ip + "; "
        "source /opt/ros/melodic/setup.bash 2>/dev/null; "
        "source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null; "
        "roslaunch yahboomcar_nav view_navigate.launch > /tmp/rviz_nav.log 2>&1 &\""
    )
    subprocess.Popen(cmd_rviz, shell=True)
    print("🚀 RViz iniciado en la Laptop.")

def iniciar_navegacion_2d():
    detener_mando_seguridad()
    limpiar_procesos_previos()
    os.system('clear')
    print("=========================================================")
    print("               🧭 NAVEGACIÓN AUTÓNOMA 2D                 ")
    print("=========================================================")
    
    mapas_yaml = sorted([f for f in os.listdir(MAPS_DIR) if f.endswith('.yaml')]) if os.path.exists(MAPS_DIR) else []
    
    if not mapas_yaml:
        print("❌ No hay mapas (.yaml) guardados en: " + MAPS_DIR)
        pausar()
        return

    print(" Selección de mapa para la navegación:\n")
    for idx, m in enumerate(mapas_yaml, 1):
        print(" [{}] 🗺️  {}".format(idx, m))
    print(" [0] Cancelar")
    print("=========================================================")
    
    choice = leer_entrada(" Elige el número del mapa a usar: ").strip()
    if choice == "0" or not choice.isdigit() or not (1 <= int(choice) <= len(mapas_yaml)):
        print(" Navegación cancelada.")
        pausar()
        return

    mapa_seleccionado = mapas_yaml[int(choice) - 1]
    ruta_yaml_completa = os.path.join(MAPS_DIR, mapa_seleccionado)

    pi_ip = obtener_ip_local()
    laptop_ip = obtener_ip_laptop()

    print("\n🚀 Preparando entorno de Navegación Autónoma...")
    print(" 📍 Mapa elegido: " + mapa_seleccionado)
    print(" 🤖 IP Robot : " + pi_ip)
    print(" 💻 IP Laptop: " + laptop_ip)
    print("---------------------------------------------------------")

    if not verificar_conexion_laptop(laptop_ip):
        pausar()
        return

    sincronizar_modelos_3d_pc(laptop_ip)

    print("\n⚡ Encendiendo motores, LiDAR, AMCL y move_base...")
    
    # Se agrega --wait en yahboomcar_navigation para alinearse al run_id existente
    cmd_nav = (
        "bash -c 'source /opt/ros/melodic/setup.bash && "
        "source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null && "
        "roslaunch yahboomcar_nav laser_bringup.launch & "
        "sleep 5 && "
        "roslaunch --wait yahboomcar_nav yahboomcar_navigation.launch map_file:=" + ruta_yaml_completa + " open_rviz:=false rviz:=false use_rviz:=false'"
    )
    
    proc_pi = subprocess.Popen(cmd_nav, shell=True)

    print("⏳ Esperando estabilización del sistema ROS (7 segundos)...")
    time.sleep(7)

    abrir_rviz_remoto(pi_ip, laptop_ip)

    print("\n=========================================================")
    print("👉 En RViz usa '2D Pose Estimate' para fijar posición inicial.")
    print("👉 En RViz usa '2D Nav Goal' para indicar destino.")
    print("👉 Presiona [Ctrl + C] para DETENER la navegación.")
    print("=========================================================")

    try:
        proc_pi.wait()
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo Navegación Autónoma...")
    finally:
        ejecutar("pkill -INT -f 'roslaunch'")
        ejecutar("pkill -9 -f 'roslaunch'")
        detener_mando_seguridad()
        print("✅ Navegación 2D finalizada.")
        pausar()

if __name__ == "__main__":
    iniciar_navegacion_2d()
