#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time

def obtener_input(mensaje):
    try:
        return raw_input(mensaje).strip()
    except NameError:
        return input(mensaje).strip()

def probar_red_neuronal():
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
            try:
                import orquestador_ccn_pi
                orquestador_ccn_pi.ejecutar_cnn_pi()
            except ImportError:
                print("❌ No se encontró 'orquestador_ccn_pi.py'. Revisa la instalación.")
                time.sleep(2)
            
        elif opcion == '2':
            print("\n[INFO] Redirigiendo al módulo de PC (Procesamiento Remoto)...")
            time.sleep(1)
            try:
                pass
            except ImportError:
                time.sleep(2)
            
        else:
            print("\n[ERROR] Opción inválida. Por favor, elige 1, 2 o 3.")
            time.sleep(1)

if __name__ == "__main__":
    probar_red_neuronal()
