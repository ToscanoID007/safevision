#!/bin/bash

# =========================================================
# 🟢 MAPEO LIGERO 2D (Chasis + LiDAR + Gmapping 2D)
# =========================================================

PI_IP=$(hostname -I | awk '{print $1}')
[ -z "$PI_IP" ] && PI_IP="192.168.1.75"

PC_IP=$(echo $SSH_CLIENT | awk '{print $1}')
[ -z "$PC_IP" ] && PC_IP="192.168.1.76"

echo "========================================================="
echo " ⚡ MODO: MAPEO LIGERO 2D"
echo " 🤖 IP Raspberry Pi : $PI_IP"
echo " 💻 IP Laptop (PC)  : $PC_IP"
echo "========================================================="

export ROS_MASTER_URI=http://${PI_IP}:11311
export ROS_IP=${PI_IP}

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash

# Cargar modelo 3D URDF
echo "📐 Cargando modelo URDF en ROS Master..."
rosparam set robot_description -t /home/pi/yahboomcar_ws/src/yahboomcar_description/urdf/yahboomcar_X3.urdf 2>/dev/null || true

# 1. Chasis y LiDAR
echo "⚡ [1/3] Lanzando Chasis y LiDAR..."
roslaunch yahboomcar_nav laser_bringup.launch > /dev/null 2>&1 &
sleep 5

# 2. SLAM 2D (Gmapping)
echo "🧠 [2/3] Lanzando Algoritmo SLAM 2D (Gmapping)..."
roslaunch yahboomcar_nav yahboomcar_map.launch > /dev/null 2>&1 &
sleep 3

# 3. RViz en Laptop Victus
echo "💻 [3/3] Abriendo RViz en Laptop PC..."
ssh -f toscano@${PC_IP} "export DISPLAY=:0; export ROS_MASTER_URI=http://${PI_IP}:11311; export ROS_IP=${PC_IP}; source ~/yahboomcar_ws/devel/setup.bash; rviz -d ~/yahboomcar_ws/src/yahboomcar_description/rviz/mapeo_yahboom.rviz" > /dev/null 2>&1 &

sleep 2

# 4. Seleccionar Mando o Teclado
echo ""
echo "---------------------------------------------------------"
echo "🎮 SELECCIONA EL MÓDULO DE CONTROL:"
echo " 1) Control con Mando / Joystick (yahboom_joy.launch)"
echo " 2) Control con Teclado (yahboom_keyboard.launch)"
echo "---------------------------------------------------------"

read -p "Elige una opción [1 o 2]: " TELEOP_OPT </dev/tty

if [ "$TELEOP_OPT" == "2" ]; then
    echo "⌨️ Iniciando Control por Teclado..."
    roslaunch yahboomcar_ctrl yahboom_keyboard.launch &
else
    echo "🎮 Iniciando Control por Mando / Joystick..."
    roslaunch yahboomcar_ctrl yahboom_joy.launch > /dev/null 2>&1 &
fi

echo "✅ Mapeo y controles iniciados correctamente en segundo plano."
sleep 2
