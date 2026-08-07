# -*- coding: utf-8 -*-
import os
from utils import detener_mando_seguridad, asegurar_ros_master, mando_conectado, pausar

def menu_navegacion_manual():
    while True:
        os.system('clear')
        print("=========================================================")
        print("            🕹️  NAVEGACIÓN MANUAL DEL ROBOT             ")
        print("=========================================================")
        print(" 1. ⌨️  Control por TECLADO (teleop_twist_keyboard)")
        print(" 2. 🎮 Control por MANDO / JOYSTICK (USB / Bluetooth)")
        print(" 3. Volver al menú principal")
        print("=========================================================")
        
        try:
            opcion = raw_input(" Selecciona una opción (1-3): ").strip()
        except NameError:
            opcion = input(" Selecciona una opción (1-3): ").strip()
        
        if opcion == '1':
            detener_mando_seguridad()
            os.system('clear')
            print("=========================================================")
            print("           ⌨️  CONTROL DE NAVEGACIÓN POR TECLADO          ")
            print("=========================================================")
            
            if asegurar_ros_master():
                print("\n INSTRUCCIONES DE USO:")
                print("   • i : Avanzar  |  , : Retroceder  |  k : Detener")
                print("   • j : Izquierda|  l : Derecha")
                print("   • Ctrl + C : Salir del modo manual")
                
                try:
                    raw_input("\n Presiona ENTER para tomar el control...")
                except NameError:
                    input("\n Presiona ENTER para tomar el control...")
                
                # Carga el entorno y ejecuta el teclado como funcionaba antes
                cmd_teleop = (
                    "bash -c 'source /opt/ros/melodic/setup.bash && "
                    "source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null; "
                    "rosrun teleop_twist_keyboard teleop_twist_keyboard.py || "
                    "roslaunch yahboomcar_teleop yahboomcar_teleop_key.launch'"
                )
                os.system(cmd_teleop)
            
            print("\n Control por teclado finalizado.")
            pausar()

        elif opcion == '2':
            os.system('clear')
            print("=========================================================")
            print("         🎮 CONTROL DE NAVEGACIÓN POR MANDO             ")
            print("=========================================================")
            
            if not mando_conectado():
                print("❌ ERROR: No se detecta ningún mando en '/dev/input/js0'.")
                pausar()
                continue
            
            if asegurar_ros_master():
                print("\n 🔒 MODO MANDO ACTIVADO:")
                print("   • Ya puedes controlar el robot.")
                print("   • Presiona Ctrl + C para BLOQUEAR el mando y salir.")
                
                try:
                    raw_input("\n Presiona ENTER para ACTIVAR el mando...")
                except NameError:
                    input("\n Presiona ENTER para ACTIVAR el mando...")
                
                print("\n 🎮 Mando en uso... (Logs ocultos para mantener la pantalla limpia)")
                
                # Agregamos "> /dev/null 2>&1" al final para silenciar completamente los logs de ROS
                cmd_joy = (
                    "bash -c 'source /opt/ros/melodic/setup.bash && "
                    "source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null; "
                    "roslaunch yahboomcar_ctrl yahboom_joy.launch > /dev/null 2>&1'"
                )
                
                try:
                    os.system(cmd_joy)
                finally:
                    detener_mando_seguridad()
                    print("\n🛑 MANDO DESACTIVADO Y BLOQUEADO.")
            
            pausar()

        elif opcion == '3':
            detener_mando_seguridad()
            break
