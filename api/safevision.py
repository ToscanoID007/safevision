#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO: Menú SafeVision Principal
DESCRIPCIÓN: Enrutador modular para submenús de planificación, validación y operación.
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

def menu_safevision():
    while True:
        limpiar_pantalla()
        print("=========================================================")
        print("       🛡️ MISIONES SAFEVISION (SISTEMA INTEGRADO)       ")
        print("=========================================================")
        print(" 1. ⚙️  Planificación: Crear / Editar Rutas de Patrullaje")
        print(" 2. 🧪  Validación: Diagnóstico y Simulación")
        print(" 3. 🚀  Operación: Ejecutar misiones")
        print(" 4. 🔙  Salida: Regresar al Menú Principal")
        print("=========================================================")
        
        opcion = input("\nSelecciona una opción (1-4): ").strip()

        if opcion == '1':
            ejecutar_script("menu_planificacion.py")
        elif opcion == '2':
            ejecutar_script("menu_validacion.py")
        elif opcion == '3':
            ejecutar_script("menu_operacion.py")
        elif opcion == '4':
            break
        else:
            print("\n⚠️ Opción inválida. Intenta de nuevo.")
            input("Presiona Enter para continuar...")

if __name__ == "__main__":
    menu_safevision()
