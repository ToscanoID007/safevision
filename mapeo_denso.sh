#!/bin/bash

# =========================================================
# 🔴 MAPEO DENSO 3D (RTAB-MAP DIRECT DEPTH FIX)
# =========================================================

PI_IP=$(hostname -I | awk '{print $1}')
[ -z "$PI_IP" ] && PI_IP="192.168.1.75"

PC_IP=$(echo $SSH_CLIENT | awk '{print $1}')
[ -z "$PC_IP" ] && PC_IP="192.168.1.76"

echo "========================================================="
echo " 🛰️ MODO: MAPEO DENSO 3D (TIMESTAMP & NO-SYNC FIX)"
echo " 🤖 IP Raspberry Pi : $PI_IP"
echo " 💻 IP Laptop (PC)  : $PC_IP"
echo "========================================================="

# 1. LIMPIEZA DE PROCESOS PREVIOS
killall -9 roslaunch rviz roscore 2>/dev/null || true
sleep 2

# 2. ENTORNO ROS LOCAL
export ROS_MASTER_URI=http://${PI_IP}:11311
export ROS_IP=${PI_IP}

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash

rosparam set use_sim_time false

# 3. CARGAR MODELO URDF EN ROS MASTER
echo "📐 Cargando modelo URDF en ROS Master..."
rosparam set robot_description -t /home/pi/yahboomcar_ws/src/yahboomcar_description/urdf/yahboomcar_X3.urdf 2>/dev/null || true

# 4. LANZAR CHASIS Y LIDAR
echo "⚡ [1/3] Lanzando Chasis y LiDAR..."
roslaunch yahboomcar_nav laser_bringup.launch > /dev/null 2>&1 &
sleep 5

# 5. LANZAR CÁMARA ASTRA
echo "📷 [2/3] Encendiendo Cámara Astra 3D..."
roslaunch astra_camera astrapro.launch > /dev/null 2>&1 &
sleep 5

# 6. LANZAR RTAB-MAP DIRECTO (BYPASS RGBD_SYNC)
echo "🧠 [3/3] Lanzando RTAB-Map SLAM..."
roslaunch rtabmap_ros rtabmap.launch \
    rtabmap_args:="--delete_db_on_start" \
    subscribe_rgbd:=false \
    subscribe_depth:=true \
    depth_topic:=/camera/depth_registered/image_raw \
    rgb_topic:=/camera/rgb/image_raw \
    camera_info_topic:=/camera/rgb/camera_info \
    frame_id:=base_footprint \
    approx_sync:=true \
    approx_sync_max_interval:=0.1 \
    queue_size:=100 \
    rviz:=false \
    rtabmapviz:=false \
    > /dev/null 2>&1 &

sleep 5

# 7. ABRIR RVIZ EN LA PC REMOTA
echo "💻 Abriendo RViz en Laptop PC..."
ssh -t toscano@${PC_IP} "export DISPLAY=:0; export ROS_MASTER_URI=http://${PI_IP}:11311; export ROS_IP=${PC_IP}; source ~/yahboomcar_ws/devel/setup.bash; rviz -d ~/yahboomcar_ws/src/yahboomcar_description/rviz/mapeo_yahboom.rviz" &

sleep 2

# 8. SELECCIÓN DE CONTROL
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
