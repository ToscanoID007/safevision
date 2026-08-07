# -*- coding: utf-8 -*-
import os
import time
from utils import detener_mando_seguridad, ejecutar, pausar

def leer_entrada(mensaje):
    """Manejo seguro de inputs para Python 2 y 3"""
    try:
        return raw_input(mensaje)
    except NameError:
        return input(mensaje)

def menu_wifi():
    detener_mando_seguridad()
    script_sh = "~/robot_custom/network/wifi_manager.sh"
    
    while True:
        os.system('clear')
        print("=========================================================")
        print("                 📶 GESTOR DE RED WI-FI                  ")
        print("=========================================================")
        
        # Leer estado desde tu script .sh
        estado_raw = ejecutar(script_sh + " status")
        estado = {}
        for linea in estado_raw.split('\n'):
            if "=" in linea:
                partes = linea.split("=", 1)
                estado[partes[0]] = partes[1]
        
        print(" Red Actual       : " + estado.get('SSID', 'Ninguna'))
        print(" IP Inalámbrica   : " + estado.get('WLAN_IP', 'Desconectado'))
        print(" IP Cable (ETH)   : " + estado.get('ETH_IP', 'Desconectado'))
        print("---------------------------------------------------------")
        print(" 1. Conectar a una red GUARDADA")
        print(" 2. Escanear y conectar a una NUEVA red")
        print(" 3. Borrar (olvidar) una red guardada")
        print(" 4. Reiniciar el adaptador de red (Botón de pánico)")
        print(" 5. Volver al menú principal")
        print("=========================================================")
        
        opcion = leer_entrada(" Selecciona una opción (1-5): ").strip()

        if opcion == '1':
            print("\nBuscando perfiles guardados...")
            redes_raw = ejecutar(script_sh + " saved")
            redes = [r for r in redes_raw.split('\n') if r.strip()]
            
            if not redes:
                print("No hay redes guardadas en el sistema.")
                pausar()
                continue
            
            print("\n--- Redes Guardadas ---")
            for i, red in enumerate(redes):
                print(" " + str(i + 1) + ". " + red)
            
            sel = leer_entrada("\n Elige el número de la red (o ENTER para cancelar): ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(redes):
                red_elegida = redes[int(sel) - 1]
                print("\n🔌 Conectando a '" + red_elegida + "'...")
                res = ejecutar(script_sh + ' connect_saved "' + red_elegida + '"')
                if "SUCCESS" in res:
                    print("✅ ¡Conectado con éxito!")
                else:
                    print("❌ Error al conectar. Intenta reiniciar el adaptador (Opción 4).")
            pausar()

        elif opcion == '2':
            print("\n🔍 Escaneando redes cercanas (esperando al adaptador)...")
            # Damos un tiempo de espera para que el adaptador capture el espectro completo
            time.sleep(3)
            redes_raw = ejecutar(script_sh + " scan")
            redes = [r for r in redes_raw.split('\n') if r.strip()]
            
            if not redes:
                print("No se encontraron redes Wi-Fi cercanas.")
                pausar()
                continue
            
            print("\n--- Redes Visibles ---")
            for i, red in enumerate(redes):
                print(" " + str(i + 1) + ". " + red)
            
            sel = leer_entrada("\n Elige el número de la red (o ENTER para cancelar): ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(redes):
                red_elegida = redes[int(sel) - 1]
                password = leer_entrada(" Contraseña para '" + red_elegida + "': ").strip()
                print("\n🔌 Guardando y conectando a '" + red_elegida + "'...")
                res = ejecutar(script_sh + ' connect_new "' + red_elegida + '" "' + password + '"')
                if "SUCCESS" in res:
                    print("✅ ¡Conectado y guardado con éxito!")
                else:
                    print("❌ Error: Contraseña incorrecta o red fuera de alcance.")
            pausar()

        elif opcion == '3':
            print("\nBuscando perfiles guardados...")
            redes_raw = ejecutar(script_sh + " saved")
            redes = [r for r in redes_raw.split('\n') if r.strip()]
            
            if not redes:
                print("No hay redes para borrar.")
                pausar()
                continue
            
            print("\n--- Selecciona la red a BORRAR ---")
            for i, red in enumerate(redes):
                print(" " + str(i + 1) + ". " + red)
            
            sel = leer_entrada("\n Elige el número de la red (o ENTER para cancelar): ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(redes):
                red_elegida = redes[int(sel) - 1]
                ejecutar(script_sh + ' forget "' + red_elegida + '"')
                print("✅ La red '" + red_elegida + "' ha sido borrada del robot.")
            pausar()

        elif opcion == '4':
            print("\n🔄 Reiniciando adaptador Wi-Fi... (espera 5 segundos)")
            ejecutar(script_sh + " restart")
            print("✅ Adaptador reiniciado.")
            pausar()

        elif opcion == '5':
            break
