# -*- coding: utf-8 -*-
import os
from utils import detener_mando_seguridad, pausar

def leer_entrada(mensaje):
    """Manejo seguro de inputs para Python 2 y 3"""
    try:
        return raw_input(mensaje)
    except NameError:
        return input(mensaje)

def explorador_archivos():
    # Empezamos en la carpeta principal del usuario (/home/ubuntu o similar)
    ruta_actual = os.path.expanduser('~')
    
    while True:
        os.system('clear')
        print("=========================================================")
        print(" 📁 EXPLORADOR DE ARCHIVOS")
        print(" 📍 Ruta actual: " + ruta_actual)
        print("=========================================================")
        
        elementos = []
        try:
            # Leer el contenido de la carpeta actual
            elementos = os.listdir(ruta_actual)
            # Ordenar: primero carpetas, luego archivos, alfabéticamente
            elementos.sort(key=lambda x: (not os.path.isdir(os.path.join(ruta_actual, x)), x.lower()))
            
            if not elementos:
                print(" (Carpeta vacía)")
            else:
                for i, el in enumerate(elementos):
                    ruta_completa = os.path.join(ruta_actual, el)
                    icono = "📁" if os.path.isdir(ruta_completa) else "📄"
                    # Usamos .format para compatibilidad con Python 2
                    print(" {0:2d}. {1} {2}".format(i+1, icono, el))
        except OSError: # En Python 2 no existe PermissionError, se usa OSError
            print(" ❌ No tienes permisos para leer esta carpeta.")
        except Exception as e:
            print(" ❌ Error al leer carpeta: " + str(e))

        print("---------------------------------------------------------")
        print(" C. Cambiar de ruta manualmente (ej. /etc)")
        print(" A. Subir de nivel (ir a la carpeta anterior)")
        print(" R. Regresar al menú de Sistema")
        print("=========================================================")
        
        opcion = leer_entrada(" Elige un número para abrir/leer, 'A' para subir, 'R' para salir: ").strip().lower()
        
        if opcion == 'r':
            break
        elif opcion == 'a':
            ruta_actual = os.path.dirname(ruta_actual)
        elif opcion == 'c':
            nueva_ruta = leer_entrada(" Ingresa la ruta absoluta: ").strip()
            # Convertir a ruta absoluta y validar
            ruta_eval = os.path.abspath(os.path.join(ruta_actual, nueva_ruta))
            if os.path.isdir(ruta_eval):
                ruta_actual = ruta_eval
            else:
                print(" ❌ Ruta inválida o no es una carpeta.")
                pausar()
        elif opcion.isdigit():
            idx = int(opcion) - 1
            if 0 <= idx < len(elementos):
                seleccion = os.path.join(ruta_actual, elementos[idx])
                
                # Si es carpeta, entramos
                if os.path.isdir(seleccion):
                    ruta_actual = seleccion
                # Si es archivo, lo leemos
                else:
                    os.system('clear')
                    print("--- Leyendo: " + elementos[idx] + " ---\n")
                    try:
                        with open(seleccion, 'r') as f:
                            contenido = f.read(2500) # Límite para no saturar terminal
                            print(contenido)
                            if len(contenido) == 2500:
                                print("\n[... Archivo muy largo, se truncó para previsualización ...]")
                    except Exception as e:
                        print(" ❌ No se puede mostrar como texto o es un archivo binario.")
                        print(" Detalle del error: " + str(e))
                    pausar()

def menu_archivos():
    detener_mando_seguridad()
    while True:
        os.system('clear')
        print("=========================================================")
        print("          📁 EXPLORADOR DE SISTEMA Y HARDWARE           ")
        print("=========================================================")
        print(" 1. 🔍 Navegador de archivos interactivo")
        print(" 2. 💾 Ver estado de Disco (Almacenamiento)")
        print(" 3. 🧠 Ver estado de Memoria RAM")
        print(" 4. Volver al menú principal")
        print("=========================================================")
        
        opcion = leer_entrada(" Selecciona una opción (1-4): ").strip()
        
        if opcion == '1':
            explorador_archivos()
        elif opcion == '2':
            os.system('clear')
            print("--- Uso de Almacenamiento (Disco) ---\n")
            os.system("df -h / | grep -v 'Filesystem'")
            pausar()
        elif opcion == '3':
            os.system('clear')
            print("--- Uso de Memoria RAM ---\n")
            os.system("free -h")
            pausar()
        elif opcion == '4':
            break
