#!/bin/bash

# =========================================================
# 🤖 LAUNCHER AUTOMÁTICO DE MAPEO (ROBOT + RVIZ REMOTO)
# =========================================================

# 1. AUTODETECCIÓN DE IPs
PI_IP=$(hostname -I | awk '{print $1}')
[ -z "$PI_IP" ] && PI_IP="192.168.1.75"

# Detectar la IP de la laptop desde la sesión SSH
PC_IP=$(echo $SSH_CLIENT | awk '{print $1}')
[ -z "$PC_IP" ] && PC_IP="192.168.1.76"

echo "========================================================="
echo " 🤖 IP Raspberry Pi : $PI_IP"
echo " 💻 IP Laptop (PC)  : $PC_IP"
echo "========================================================="

# 2. ENTORNO ROS LOCAL
export ROS_MASTER_URI=http://${PI_IP}:11311
export ROS_IP=${PI_IP}

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash

# 3. CARGAR MODELO URDF EN ROS MASTER
echo "📐 Cargando modelo URDF 3D en ROS Master..."
rosparam set robot_description -t /home/pi/yahboomcar_ws/src/yahboomcar_description/urdf/yahboomcar_X3.urdf 2>/dev/null || true

# 4. LANZAR CHASIS Y LIDAR
echo "⚡ [1/3] Lanzando Chasis y LiDAR..."
roslaunch yahboomcar_nav laser_bringup.launch > /dev/null 2>&1 &
sleep 5

# 5. LANZAR MAPEO SLAM (GMAPPING)
echo "🧠 [2/3] Lanzando Algoritmo de Mapeo..."
roslaunch yahboomcar_nav yahboomcar_map.launch > /dev/null 2>&1 &
sleep 3

# 6. LANZAR RVIZ EN LA PC REMOTA (Ingresa tu clave de la Laptop si te la solicita)
echo "💻 [3/3] Abriendo RViz en tu laptop Victus (te pedirá tu contraseña de PC)..."
ssh -t toscano@${PC_IP} "export DISPLAY=:0; export ROS_MASTER_URI=http://${PI_IP}:11311; export ROS_IP=${PC_IP}; source ~/yahboomcar_ws/devel/setup.bash; rviz -d ~/yahboomcar_ws/src/yahboomcar_description/rviz/mapeo_yahboom.rviz" &

sleep 2

# 7. SELECCIÓN DE CONTROL (MANDO VS TECLADO)
echo ""
echo "---------------------------------------------------------"
echo "🎮 SELECCIONA EL MÓDULO DE CONTROL:"
echo " 1) Control con Mando / Joystick (yahboom_joy.launch)"
echo " 2) Control con Teclado (yahboom_keyboard.launch)"
echo "---------------------------------------------------------"

read -p "Elige una opción [1 o 2]: " TELEOP_OPT </dev/tty

if [ "$TELEOP_OPT" == "2" ]; then
    echo "⌨️ Iniciando Control por Teclado..."
    roslaunch yahboomcar_ctrl yahboom_keyboard.launch
else
    echo "🎮 Iniciando Control por Mando / Joystick..."
    roslaunch yahboomcar_ctrl yahboom_joy.launch
fi

