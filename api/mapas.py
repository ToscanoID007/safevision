#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time

def menu_nodos_mapas():
    while True:
        os.system('clear')
        print("=========================================================")
        print("       🗺️   GESTOR DE MAPAS Y NAVEGACIÓN DEL ROBOT       ")
        print("=========================================================")
        print(" --- MAPAS 2D ---")
        print(" [1] 🚀 Iniciar Mapeo 2D")
        print(" [2] 💾 Guardar Mapa 2D actual")
        print(" [3] 👁️  Ver y Gestionar Mapas 2D")
        print(" [4] 🎨 Editar Mapa 2D")
        print(" [5] 🧭 Navegación Autónoma 2D")
        print("")
        print(" --- MAPAS 3D ---")
        print(" [6] 🌌 Iniciar Mapeo 3D")
        print(" [7] 🛸 Navegación Autónoma 3D")
        print(" [8] 🎨 Edicion de mapas 3D")
        print("")
        print(" [0] 🔙 Volver al Menú Principal")
        print("=========================================================")
        
        opcion = input(" Selecciona una opción (0-8): ").strip()
        
        # Rutas a los scripts independientes
        base_path = "/home/pi/robot_custom/api"
        
        if opcion == "1":
            script = os.path.join(base_path, "mapas_2d_iniciar.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script de Iniciar Mapeo 2D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")
                
        elif opcion == "2":
            script = os.path.join(base_path, "mapas_2d_guardar.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script para Guardar Mapas 2D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")
                
        elif opcion == "3":
            script = os.path.join(base_path, "mapas_2d_ver.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script para Ver Mapas 2D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")
                
        elif opcion == "4":
            script = os.path.join(base_path, "mapas_2d_editar.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script para Editar Mapas 2D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")

        elif opcion == "5":
            script = os.path.join(base_path, "navegacion_2d.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script de Navegación Autónoma 2D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")
                
        elif opcion == "6":
            script = os.path.join(base_path, "mapas_3d_iniciar.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script de Iniciar Mapeo 3D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")

        elif opcion == "7":
            script = os.path.join(base_path, "mapas_3d_navegacion.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script de Navegación Autónoma 3D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")

        elif opcion == "8":
            script = os.path.join(base_path, "mapas_3d_editar.py")
            if os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("\n⚠️  El script para Editar Mapas 3D aún no ha sido creado.")
                input("Presiona ENTER para continuar...")
                
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida. Inténtalo de nuevo.")
            time.sleep(1)

if __name__ == "__main__":
    menu_nodos_mapas()
