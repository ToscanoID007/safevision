#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

# Importaciones modulares originales + Nueva de Redes
from utils import detener_mando_seguridad
from safevision import menu_safevision
from redes import menu_redes  # <-- AQUÍ IMPORTAMOS TU NUEVO MENÚ
from navegacion import menu_navegacion_manual
from wifi import menu_wifi
from mapas import menu_nodos_mapas
from sistema import menu_archivos
from gestor_nodos import menu_gestor_nodos

def menu_principal():
    detener_mando_seguridad()
    
    while True:
        os.system('clear')
        print("=========================================================")
        print("       🤖 YAHBOOM ROBOT - PANEL DE CONTROL CENTRAL       ")
        print("=========================================================")
        print(" 1. 🛡️  Iniciar Misión SafeVision (IA + Navegación)")
        print(" 2. 🧠  Gestión de Modelos IA (Redes Neuronales)")
        print(" 3. 🕹️  Navegación Manual (Teclado / Mando)")
        print(" 4. 🗺️  Gestión de Mapas (Crear, Ver, Usar)")
        print(" 5. 🛠️  Gestión de Nodos ROS (Control Manual / Lab)")
        print(" 6. 📶 Gestión de Redes Wi-Fi")
        print(" 7. 📁 Explorador de Archivos y Sistema")
        print(" 8. 🖥️  Preparar y Sincronizar PC Remota")
        print(" 9. 🚪 Salir al sistema")
        print("=========================================================")
        
        try:
            opcion = raw_input(" Selecciona una opción (1-9): ").strip()
        except NameError:
            opcion = input(" Selecciona una opción (1-9): ").strip()
        
        if opcion == '1':
            menu_safevision()
        elif opcion == '2':
            menu_redes()
        elif opcion == '3':
            menu_navegacion_manual()
        elif opcion == '4':
            menu_nodos_mapas()
        elif opcion == '5':
            menu_gestor_nodos()
        elif opcion == '6':
            menu_wifi()
        elif opcion == '7':
            menu_archivos()
        elif opcion == '8':
            pass # <-- ¡AQUÍ ESTÁ LA CORRECCIÓN!
        elif opcion == '9':
            detener_mando_seguridad()
            os.system('clear')
            print("¡Hasta luego!\n")
            break

if __name__ == '__main__':
    try:
        menu_principal()
    except KeyboardInterrupt:
        detener_mando_seguridad()
        os.system('clear')
        print("\nPrograma terminado por el usuario (Ctrl+C).\n")
        sys.exit(0)
