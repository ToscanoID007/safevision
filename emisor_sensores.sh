#!/bin/bash
# =========================================================
# 🤖 EMISOR LIGERO DE SENSORES EN RASPBERRY PI
# =========================================================

PI_IP=$(hostname -I | awk '{print $1}')
[ -z "$PI_IP" ] && PI_IP="192.168.1.75"

export ROS_MASTER_URI=http://${PI_IP}:11311
export ROS_IP=${PI_IP}

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash

echo "🧹 Limpiando procesos antiguos..."
killall -9 roslaunch rviz roscore 2>/dev/null || true
sleep 2

rosparam set use_sim_time false
echo "📐 Cargando modelo URDF..."
rosparam set robot_description -t /home/pi/yahboomcar_ws/src/yahboomcar_description/urdf/yahboomcar_X3.urdf 2>/dev/null || true

echo "⚡ [1/2] Lanzando Chasis y LiDAR..."
roslaunch yahboomcar_nav laser_bringup.launch > /dev/null 2>&1 &
sleep 5

echo "📷 [2/2] Encendiendo Cámara Astra 3D..."
roslaunch astra_camera astrapro.launch > /dev/null 2>&1 &
sleep 4

echo "========================================================="
echo " ✅ SENSORES LISTOS Y TRANSMITIENDO DESDE $PI_IP"
echo " 💻 Ahora ejecuta en tu Laptop Victus: ./rtabmap_pc.sh"
echo "========================================================="
echo ""

echo "🎮 Selecciona control de movimiento:"
echo " 1) Control con Teclado"
echo " 2) Control con Mando / Joystick"
read -p "Opción [1 o 2]: " TELEOP_OPT </dev/tty

if [ "$TELEOP_OPT" == "2" ]; then
    roslaunch yahboomcar_ctrl yahboom_joy.launch
else
    roslaunch yahboomcar_ctrl yahboom_keyboard.launch
fi
