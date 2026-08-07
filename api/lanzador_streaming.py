import os
import socket
import subprocess
import time

def obtener_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

ip_local = obtener_ip()
script_camara = "/home/pi/robot_custom/api/transmisor_camara_pi.py"

os.system('clear' if os.name == 'posix' else 'cls')
print("\033[1;36m" + "="*65)
print(" 📡 TRANSMISIÓN DE VIDEO ACTIVA (MODO LIGERO)")
print("="*65 + "\033[0m")
print("\033[1;33m La Raspberry Pi ahora solo envía el video en bruto por red.\033[0m")
print(" En el script de Python de tu PC, usa esta dirección:\n")
print(f"\033[1;32m      👉   http://{ip_local}:5000/video   👈\033[0m\n")
print("\033[1;36m" + "="*65 + "\033[0m")
print("\033[1;31m 🛑  Presiona CTRL + C para apagar la cámara y regresar al menú.\033[0m")
print("\033[1;36m" + "="*65 + "\033[0m\n")

if os.path.exists(script_camara):
    proceso = subprocess.Popen(["python3", script_camara], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\033[1;33m[INFO] Deteniendo transmisión de cámara...\033[0m")
        proceso.terminate()
        time.sleep(1)
else:
    print(f"\033[1;31m[ERROR] No se encontró el archivo: {script_camara}\033[0m")
    time.sleep(3)
