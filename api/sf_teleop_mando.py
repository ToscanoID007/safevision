#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import time

def obtener_ip_local():
    """Detecta automáticamente la IP activa de la Pi en la red local."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

ip_local = obtener_ip_local()
print(f"[MANDO ROS] 🎮 Detectada IP dinámica de la Pi: {ip_local}")

if not os.path.exists("/dev/input/js0"):
    print("❌ ERROR: No se detecta ningún mando físico en /dev/input/js0")
    exit(1)

cmd_joy = (
    f"bash -c 'source /opt/ros/melodic/setup.bash && "
    f"source ~/yahboomcar_ws/devel/setup.bash 2>/dev/null && "
    f"export ROS_MASTER_URI=http://{ip_local}:11311 && "
    f"export ROS_IP={ip_local} && "
    f"roslaunch yahboomcar_ctrl yahboomcar_joy.launch > /dev/null 2>&1 &'"
)

os.system(cmd_joy)
time.sleep(2)
print("✅ Nodos ROS de Mando iniciados correctamente con IP automática.")
