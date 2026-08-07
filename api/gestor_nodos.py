# -*- coding: utf-8 -*-
import os
import time
from utils import ejecutar, pausar

def leer_entrada(mensaje):
    try:
        return raw_input(mensaje)
    except NameError:
        return input(mensaje)

# TODO EL ARSENAL DE NODOS DISPONIBLES EN YAHBOOMCAR
NODOS = [
    # --- SENSORES Y BRINGUP ---
    {"nombre": "Base + LiDAR", "pkg": "yahboomcar_nav", "launch": "laser_bringup.launch"},
    {"nombre": "Base + AstraPro (3D)", "pkg": "yahboomcar_nav", "launch": "astrapro_bringup.launch"},
    {"nombre": "Profundidad a Láser", "pkg": "yahboomcar_nav", "launch": "depthimage_to_laserscan.launch"},
    {"nombre": "Visual (Láser a Img)", "pkg": "yahboomcar_visual", "launch": "laser_to_image.launch"},
    
    # --- ALGORITMOS SLAM (2D) ---
    {"nombre": "Mapeo General 2D", "pkg": "yahboomcar_nav", "launch": "yahboomcar_map.launch"},
    {"nombre": "Gmapping (Core)", "pkg": "yahboomcar_nav", "launch": "gmapping.launch"},
    {"nombre": "Karto (Core)", "pkg": "yahboomcar_nav", "launch": "karto.launch"},
    {"nombre": "Hector (Core)", "pkg": "yahboomcar_nav", "launch": "hector.launch"},
    {"nombre": "Cartographer (Core)", "pkg": "yahboomcar_nav", "launch": "cartographer.launch"},
    {"nombre": "Guardar Mapa", "pkg": "yahboomcar_nav", "launch": "map_saver.launch"},
    
    # --- ALGORITMOS SLAM Y NAV (3D) ---
    {"nombre": "RTAB-Map (Mapeo 3D)", "pkg": "yahboomcar_nav", "launch": "yahboomcar_rtabmap.launch"},
    {"nombre": "RTAB-Map (Nav 3D)", "pkg": "yahboomcar_nav", "launch": "yahboomcar_rtabmap_nav.launch"},
    {"nombre": "RTAB-Map (Core)", "pkg": "yahboomcar_nav", "launch": "rtabmap.launch"},
    {"nombre": "Navegación General", "pkg": "yahboomcar_nav", "launch": "yahboomcar_navigation.launch"},
    {"nombre": "AMCL (Localización)", "pkg": "yahboomcar_nav", "launch": "amcl.launch"},
    {"nombre": "Move_Base (Trayect.)", "pkg": "yahboomcar_nav", "launch": "move_base.launch"},
    
    # --- ENJAMBRE / MULTI-ROBOT ---
    {"nombre": "Multi: Base", "pkg": "yahboomcar_multi", "launch": "bringup_multi.launch"},
    {"nombre": "Multi: Base + LiDAR", "pkg": "yahboomcar_multi", "launch": "laser_bringup_multi.launch"},
    {"nombre": "Multi: Base + USB", "pkg": "yahboomcar_multi", "launch": "laser_usb_bringup_multi.launch"},
    {"nombre": "Multi: Base + Astra", "pkg": "yahboomcar_multi", "launch": "laser_astrapro_bringup_multi.launch"},
    {"nombre": "Multi: Navegación", "pkg": "yahboomcar_multi", "launch": "yahboomcar_nav_multi.launch"},
    {"nombre": "App Node", "pkg": "yahboomcar_nav", "launch": "app.launch"},
    
    # --- RVIZ (VISTAS REMOTAS) ---
    {"nombre": "View: Map", "pkg": "yahboomcar_nav", "launch": "view_map.launch"},
    {"nombre": "View: Navigate", "pkg": "yahboomcar_nav", "launch": "view_navigate.launch"},
    {"nombre": "View: Cartographer", "pkg": "yahboomcar_nav", "launch": "view_cartographer.launch"},
    {"nombre": "View: RTAB-Map", "pkg": "yahboomcar_nav", "launch": "view_rtabmap.launch"},
    {"nombre": "View: RTAB-Nav", "pkg": "yahboomcar_nav", "launch": "view_rtabmap_nav.launch"},
    {"nombre": "View: RRT Map", "pkg": "yahboomcar_nav", "launch": "view_rrt_map.launch"}
]

def estado_nodo(launch_file):
    # Se usa [r]oslaunch para evitar que pgrep se capture a sí mismo
    # Usamos os.popen directo para mayor fiabilidad al capturar el output
    salida = os.popen("pgrep -f '[r]oslaunch.*" + launch_file + "'").read().strip()
    return bool(salida)

def format_item(idx, nodo):
    activo = estado_nodo(nodo['launch'])
    # Uso de colores ANSI para la consola (Verde = ON, Rojo = OFF)
    estado = "\033[92m[ON ]\033[0m" if activo else "\033[91m[OFF]\033[0m"
    # Aseguramos que el nombre tenga exactamente 22 caracteres para que las columnas alineen
    nombre_padded = nodo['nombre'][:22].ljust(22)
    num = str(idx).rjust(2)
    return " " + num + ". " + estado + " " + nombre_padded

def alternar_nodo(nodo):
    activo = estado_nodo(nodo['launch'])
    os.system('clear')
    
    if activo:
        print("\n🛑 Apagando " + nodo['nombre'] + " (" + nodo['launch'] + ")...")
        os.system("pkill -INT -f '" + nodo['launch'] + "'")
        time.sleep(2)
        print("✅ Nodo detenido correctamente.")
    else:
        print("\n🚀 Iniciando " + nodo['nombre'] + " (" + nodo['launch'] + ")...")
        
        # 1. Lanzamos el proceso 100% desconectado de esta terminal, guardando su log
        comando_ros = (
            "nohup bash -c 'source /opt/ros/melodic/setup.bash && "
            "source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null && "
            "stdbuf -oL roslaunch " + nodo['pkg'] + " " + nodo['launch'] + "' > /tmp/ros_nodo_actual.log 2>&1 &"
        )
        os.system(comando_ros)
        
        # 2. Intentamos abrir una nueva ventana de terminal gráfica (lxterminal) para ver el log.
        # Si no hay entorno gráfico activo (ej. SSH sin X11), fallará silenciosamente pero el log seguirá guardándose.
        comando_term = (
            "export DISPLAY=:0 && "
            "lxterminal -t 'LOGS: " + nodo['nombre'] + "' -e 'tail -f /tmp/ros_nodo_actual.log' >/dev/null 2>&1 &"
        )
        os.system(comando_term)

        print("⏳ Lanzando procesos (espera 3-5 seg)...")
        time.sleep(4)
        print("✅ Comando enviado con éxito al sistema.")
        print("🖥️  (Si usas VNC/Pantalla, se abrió una ventana con los logs).")
        print("📂 (Si usas SSH sin pantalla, abre otra terminal en tu PC y pon: tail -f /tmp/ros_nodo_actual.log)")

    pausar()

def menu_gestor_nodos():
    while True:
        os.system('clear')
        print("===============================================================================")
        print("                   🛠️  LABORATORIO DE PRUEBAS: GESTIÓN DE NODOS                ")
        print("===============================================================================")
        
        # Imprimir en 2 columnas para aprovechar el espacio
        for i in range(0, len(NODOS), 2):
            columna_1 = format_item(i + 1, NODOS[i])
            if i + 1 < len(NODOS):
                columna_2 = format_item(i + 2, NODOS[i+1])
            else:
                columna_2 = ""
            print(columna_1 + "   |   " + columna_2)
        
        print("===============================================================================")
        print(" T. ☠️  Apagar TODOS los nodos ROS          R. Volver al menú")
        print("===============================================================================")
        
        opcion = leer_entrada(" Selecciona el número del nodo a Encender/Apagar: ").strip().lower()
        
        if opcion == 'r':
            break
        elif opcion == 't':
            os.system('clear')
            print("\n🛑 Apagando agresivamente todos los procesos de ROS...")
            os.system("pkill -INT -f 'roslaunch'")
            time.sleep(2)
            os.system("pkill -9 -f 'roslaunch' 2>/dev/null")
            print("✅ Todo el hardware ha sido detenido.")
            pausar()
        elif opcion.isdigit():
            idx = int(opcion) - 1
            if 0 <= idx < len(NODOS):
                alternar_nodo(NODOS[idx])

if __name__ == "__main__":
    menu_gestor_nodos()
