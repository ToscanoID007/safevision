#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO: Menú Operación
DESCRIPCIÓN: Submenú de SafeVision para lanzar misiones manuales o automáticas.
"""

import os
import sys
import subprocess

def limpiar_pantalla():
    os.system('clear' if os.name == 'posix' else 'cls')

def ejecutar_script(script_name):
    ruta_script = os.path.join(os.path.dirname(__file__), script_name)
    if os.path.exists(ruta_script):
        subprocess.run([sys.executable, ruta_script])
    else:
        print(f"\n❌ Error: El módulo '{script_name}' aún no ha sido creado.")
        input("\nPresiona Enter para continuar...")

def menu_operacion():
    while True:
        limpiar_pantalla()
        print("=========================================================")
        print("                🚀 MISIONES DE PATRULLAJE               ")
        print("=========================================================")
        print(" 1. 🕹️   Mision Pilotada")
        print(" 2. 🤖  Mision Con Piloto Automatico y rutas configuradas.")
        print(" 3. 🔙  Regresar al Menú Anterior")
        print("=========================================================")
        
        opcion = input("\nSelecciona una opción (1-3): ").strip()

        if opcion == '1':
            ejecutar_script("sf_mision_pilotada.py")
        elif opcion == '2':
            ejecutar_script("sf_mision_automatica.py")
        elif opcion == '3':
            break
        else:
            print("\n⚠️ Opción inválida. Intenta de nuevo.")
            input("Presiona Enter para continuar...")

if __name__ == "__main__":
    menu_operacion()
