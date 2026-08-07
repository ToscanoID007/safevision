#!/bin/bash

# 1. EL BLINDAJE: Esta función se ejecutará siempre al final, pase lo que pase.
cleanup() {
    echo -e "\n======================================================"
    echo " [4/4] APAGANDO SISTEMA Y TRANSFIRIENDO ARCHIVO..."
    echo "======================================================"
    
    # Apagar sensores suavemente
    kill -INT $PID_BAG 2>/dev/null
    sleep 3
    kill -INT $PID_CAM 2>/dev/null
    kill -INT $PID_BASE 2>/dev/null
    sleep 2

    echo "Enviando datos_3d.bag a tu Laptop (toscano)..."
    echo "--> Por favor, ingresa tu contraseña si te la pide:"
    scp /home/pi/datos_3d.bag toscano@192.168.1.76:/home/toscano/

    echo "======================================================"
    echo " ¡PROCESO COMPLETADO! Ya puedes usar 'ver_mapa' en tu PC."
    echo "======================================================"
    exit 0
}

# 2. Le decimos a Linux que atrape el Ctrl+C y ejecute el blindaje
trap cleanup EXIT SIGINT

echo "=========================================="
echo " INICIANDO SISTEMA DE MAPEO OFFLINE"
echo "=========================================="

export ROS_MASTER_URI=http://192.168.1.75:11311
export ROS_IP=192.168.1.75

echo "[1/4] Encendiendo base y Lidar..."
roslaunch yahboomcar_bringup bringup.launch &
PID_BASE=$!
sleep 5

echo "[2/4] Encendiendo cámara Astra..."
roslaunch astra_camera astra.launch color_width:=320 color_height:=240 depth_width:=320 depth_height:=240 color_fps:=15 depth_fps:=15 &
PID_CAM=$!
sleep 5

echo "[3/4] Grabando datos (RAM extra activada para la SD)..."
rosbag record -b 512 -O /home/pi/datos_3d.bag /odom /tf /tf_static /camera/depth_registered/image_raw /camera/color/image_raw /camera/rgb/image_raw /camera/color/camera_info /camera/rgb/camera_info /scan &
PID_BAG=$!
sleep 3

echo "======================================================"
echo " [CONTROL ACTIVADO] Usa las teclas (i, j, k, l) para moverte."
echo " PRESIONA [Ctrl + C] CUANDO TERMINES DE MAPEAR."
echo "======================================================"

rosrun teleop_twist_keyboard teleop_twist_keyboard.py
