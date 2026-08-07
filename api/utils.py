import os
import subprocess
import time

def ejecutar(comando):
    """Ejecuta un comando en bash y devuelve el texto limpio."""
    try:
        salida = subprocess.check_output(comando, shell=True, stderr=subprocess.STDOUT)
        return salida.decode('utf-8', errors='ignore').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return str(e)

def pausar():
    try:
        raw_input("\nPresiona ENTER para continuar...")
    except NameError:
        input("\nPresiona ENTER para continuar...")

def ros_master_activo():
    """Comprueba si roscore / ros master está respondiendo."""
    res = ejecutar("bash -c 'source /opt/ros/melodic/setup.bash && rostopic list 2>/dev/null'")
    return "/rosout" in res

def mando_conectado():
    """Comprueba si existe algún joystick en /dev/input/js*"""
    return os.path.exists("/dev/input/js0")

def detener_mando_seguridad():
    """Mata cualquier nodo de joystick/mando activo para evitar movimientos accidentales."""
    ejecutar("pkill -f joy_node 2>/dev/null; pkill -f yahboomcar_joy 2>/dev/null; pkill -f teleop_twist_joy 2>/dev/null")

def asegurar_ros_master():
    """Verifica el master y ofrece encenderlo si está apagado."""
    if not ros_master_activo():
        print("\n⚠️  ATENCIÓN: ROS Master / Driver Base NO está iniciado.")
        print("   Para mover los motores, se necesita iniciar el nodo base de Yahboom.")
        
        try:
            iniciar = raw_input("\n ¿Deseas iniciar la base del robot ahora en segundo plano? (s/n): ").strip().lower()
        except NameError:
            iniciar = input("\n ¿Deseas iniciar la base del robot ahora en segundo plano? (s/n): ").strip().lower()
        
        if iniciar == 's':
            print("\n🚀 Iniciando roscore y driver de Yahboom en segundo plano...")
            os.system("bash -c 'source /opt/ros/melodic/setup.bash && source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null; nohup roslaunch yahboomcar_bringup bringup.launch > /dev/null 2>&1 &' &")
            print(" Esperando 5 segundos a que la base responda...")
            time.sleep(5)
            detener_mando_seguridad()
            return True
        else:
            print("\n No se inició la base. Es posible que el robot no responda.")
            return False
    return True
