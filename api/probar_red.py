#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time

def obtener_input(mensaje):
    """Maneja el input compatible con Python 2 y 3."""
    try:
        return raw_input(mensaje).strip()
    except NameError:
        return input(mensaje).strip()

def probar_red_neuronal():
    """Menú principal para rutear la ejecución de la red neuronal."""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=========================================================")
        print(" 👁️  PRUEBA DE RED NEURONAL (INFERENCIA)")
        print("=========================================================")
        print(" 1. 🍓 Correr la CNN en la Raspberry Pi (Local optimizado)")
        print(" 2. 💻 Correr la CNN en la PC (Procesamiento Remoto)")
        print(" 3. 🔙 Volver al menú principal")
        print("=========================================================")
        
        opcion = obtener_input(" Selecciona una opción (1-3): ")
        
        if opcion == '3':
            print("\n[INFO] Regresando al menú anterior...")
            time.sleep(1)
            break
            
        elif opcion == '1':
            print("\n[INFO] Redirigiendo al orquestador de Raspberry Pi...")
            time.sleep(1)
            # Importamos y ejecutamos el orquestador local
            import orquestador_ccn_pi
            orquestador_ccn_pi.ejecutar_cnn_pi()
            
        elif opcion == '2':
            print("\n[INFO] Redirigiendo al módulo de PC (Procesamiento Remoto)...")
            time.sleep(1)
            # Ejecutamos el orquestador que levanta la interfaz web de descarga
            os.system('python3 /home/pi/robot_custom/api/orquestador_ccn_pc.py')
            
        else:
            print("\n[ERROR] Opción inválida. Por favor, elige 1, 2 o 3.")
            time.sleep(1)

if __name__ == "__main__":
    probar_red_neuronal()
