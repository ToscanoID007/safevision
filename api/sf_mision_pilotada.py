#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import signal

def limpiar_pantalla():
    os.system('clear' if os.name == 'posix' else 'cls')

def ejecutar_script(script_name):
    ruta_script = os.path.join(os.path.dirname(__file__), script_name)
    if os.path.exists(ruta_script):
        # Protegemos el submenú de interrupciones
        handler_original = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            subprocess.run([sys.executable, ruta_script])
        finally:
            signal.signal(signal.SIGINT, handler_original)
    else:
        print(f"\n❌ Error: El script '{script_name}' no existe en el directorio.")
        input("\nPresiona Enter para continuar...")

def menu_pilotada():
    while True:
        limpiar_pantalla()
        print("=========================================================")
        print("              🚁 MISIÓN PILOTADA (SUBMENÚ)               ")
        print("=========================================================")
        print(" 1. 📥 Habilitar Descarga del Dashboard (PC)")
        print(" 2. ⏳ Iniciar Modo Espera (Conexión Remota)")
        print(" 3. 🔙 Regresar al Menú Operación")
        print("=========================================================")
        
        opcion = input("\nSelecciona una opción (1-3): ").strip()

        if opcion == '1':
            ejecutar_script("sf_servidor_descarga.py")
        elif opcion == '2':
            ejecutar_script("sf_modo_espera.py")
        elif opcion == '3':
            print("\n[INFO] Regresando...")
            sys.exit(0)
        else:
            print("\n⚠️ Opción inválida. Intenta de nuevo.")
            input("Presiona Enter para continuar...")

if __name__ == "__main__":
    try:
        menu_pilotada()
    except KeyboardInterrupt:
        sys.exit(0)
