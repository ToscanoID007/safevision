#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import subprocess
from flask import Flask, request, jsonify

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

# Captura dinámica de red para ROS
IP_ACTUAL = obtener_ip_local()
os.environ["ROS_MASTER_URI"] = f"http://{IP_ACTUAL}:11311"
os.environ["ROS_IP"] = IP_ACTUAL

print(f"[TELEOP TECLADO] 🌐 Configurando ROS en la IP dinámica: {IP_ACTUAL}")

app = Flask(__name__)

def inicializar_ros_node():
    try:
        res = subprocess.check_output(
            "bash -c 'source /opt/ros/melodic/setup.bash && rostopic list 2>/dev/null'", 
            shell=True
        ).decode('utf-8')
        return "/rosout" in res
    except Exception:
        return False

try:
    import rospy
    from geometry_msgs.msg import Twist
    
    if not rospy.core.is_initialized():
        rospy.init_node('sf_teleop_web_node', anonymous=True)
    pub_cmd = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    ROS_DISPONIBLE = True
except Exception as e:
    ROS_DISPONIBLE = False
    print(f"[WARN] ROS no disponible directamente en Python: {e}")

VEL_LINEAL = 0.2
VEL_ANGULAR = 0.5

@app.route('/mover', methods=['POST'])
def mover():
    data = request.json or {}
    comando = data.get('direccion', 'stop')
    
    twist = Twist()
    if comando == 'w':
        twist.linear.x = VEL_LINEAL
    elif comando == 's':
        twist.linear.x = -VEL_LINEAL
    elif comando == 'a':
        twist.angular.z = VEL_ANGULAR
    elif comando == 'd':
        twist.angular.z = -VEL_ANGULAR
    elif comando == 'stop':
        twist.linear.x = 0.0
        twist.angular.z = 0.0

    if ROS_DISPONIBLE and inicializar_ros_node():
        pub_cmd.publish(twist)
        print(f"[ROS /cmd_vel] Command: {comando}")
    else:
        print(f"[SIMULACIÓN ROS] /cmd_vel -> Linear: {twist.linear.x}, Angular: {twist.angular.z}")

    return jsonify({"status": "ok", "comando": comando})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, threaded=True)
