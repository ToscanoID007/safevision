#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from importar_modelo import iniciar_portal
from ver_modelos import mostrar_modelos
from ver_parametros import ver_parametros_modelo
from editar_nombre import editar_nombre_modelo
from editar_metadatos import editar_metadatos_modelo
from eliminar_modelo import eliminar_modelo_ia
from exportar_modelo import exportar_modelo_ia
from probar_red import probar_red_neuronal

def menu_redes():
    while True:
        os.system('clear')
        print("=========================================================")
        print("       🧠 GESTIÓN DE MODELOS IA (REDES NEURONALES)       ")
        print("=========================================================")
        print(" 1. 👁️  Probar red neuronal (Benchmark y Cámara)")
        print(" 2. 📋  Ver modelos instalados")
        print(" 3. 📥  Importar nuevo modelo (.zip)")
        print(" 4. 📤  Exportar modelo")
        print(" 5. 📊  Ver parámetros y clases del modelo (.json)")
        print(" 6. 🏷️  Editar nombre del modelo")
        print(" 7. 📝  Editar metadatos y clases (.json)")
        print(" 8. 🗑️  Eliminar modelo y metadatos")
        print(" 9. 🔙  Regresar al Menú Principal")
        print("=========================================================")
        
        opcion = input(" Selecciona una opción (1-9): ").strip()
        
        if opcion == '9':
            break 
        elif opcion == '1':
            probar_red_neuronal()
        elif opcion == '2':
            mostrar_modelos()
        elif opcion == '3':
            iniciar_portal()
        elif opcion == '4':
            exportar_modelo_ia()
        elif opcion == '5':
            ver_parametros_modelo()
        elif opcion == '6':
            editar_nombre_modelo()
        elif opcion == '7':
            editar_metadatos_modelo()
        elif opcion == '8':
            eliminar_modelo_ia()
        else:
            print("\n[INFO] Esta función aún está en desarrollo.\n")
            
        if opcion != '9':
            input("\nPresiona Enter para continuar...")
