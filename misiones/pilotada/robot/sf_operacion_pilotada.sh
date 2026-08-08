#!/bin/bash

CONTROL="$1"

ROOT="/home/pi/robot_custom/misiones/pilotada"
ROBOT_DIR="$ROOT/robot"
LOG_DIR="$ROOT/logs"

mkdir -p "$LOG_DIR"

if [ "$CONTROL" != "teclado" ] && \
   [ "$CONTROL" != "mando" ]; then
    echo "Uso: $0 teclado|mando"
    exit 1
fi


PI_IP=$(hostname -I | awk '{print $1}')
[ -z "$PI_IP" ] && PI_IP="127.0.0.1"

export ROS_MASTER_URI="http://${PI_IP}:11311"
export ROS_IP="$PI_IP"

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash


BASE_PID=""
CONTROL_PID=""
SERVER_PID=""


cerrar() {
    echo ""
    echo "Finalizando misión pilotada..."

    [ -n "$CONTROL_PID" ] && kill -INT "$CONTROL_PID" 2>/dev/null || true
    [ -n "$SERVER_PID" ] && kill -INT "$SERVER_PID" 2>/dev/null || true
    [ -n "$BASE_PID" ] && kill -INT "$BASE_PID" 2>/dev/null || true

    sleep 2

    [ -n "$CONTROL_PID" ] && kill -TERM "$CONTROL_PID" 2>/dev/null || true
    [ -n "$SERVER_PID" ] && kill -TERM "$SERVER_PID" 2>/dev/null || true
    [ -n "$BASE_PID" ] && kill -TERM "$BASE_PID" 2>/dev/null || true

    echo "Operación finalizada."
}

trap cerrar EXIT


clear

echo "========================================================="
echo " SAFEVISION - PREPARANDO MISIÓN PILOTADA"
echo "========================================================="
echo " IP      : $PI_IP"
echo " Control : ${CONTROL^^}"
echo "========================================================="


echo ""
echo "[1/3] Iniciando chasis y LiDAR..."

roslaunch \
yahboomcar_bringup \
yahboomcar.launch \
> "$LOG_DIR/base.log" 2>&1 &

BASE_PID=$!

sleep 5


echo ""
echo "[2/3] Iniciando cámara y servidor..."

python3 \
"$ROBOT_DIR/sf_robot_server.py" \
--control "$CONTROL" \
> "$LOG_DIR/robot_server.log" 2>&1 &

SERVER_PID=$!

sleep 2


if [ "$CONTROL" = "mando" ]; then

    echo ""
    echo "[3/3] Iniciando mando..."

    if [ ! -e /dev/input/js0 ]; then
        echo "ERROR: no se detectó /dev/input/js0"
        exit 1
    fi

    roslaunch \
    yahboomcar_ctrl \
    yahboom_joy.launch \
    > "$LOG_DIR/control.log" 2>&1 &

    CONTROL_PID=$!

    sleep 2

    python3 \
    "$ROBOT_DIR/sf_modo_espera.py" \
    mando

else

    echo ""
    echo "[3/3] Sistema preparado para teclado."

    #
    # Primero dejamos al operador revisar el diagnóstico.
    #
    python3 \
    "$ROBOT_DIR/sf_modo_espera.py" \
    teclado

    clear

    echo "========================================================="
    echo " SAFEVISION - CONTROL POR TECLADO"
    echo "========================================================="
    echo ""
    echo " El Dashboard puede permanecer abierto en la PC."
    echo " Esta terminal controla el Rosmaster."
    echo ""
    echo " Para salir utiliza el comando de salida del"
    echo " controlador Yahboom o Ctrl+C."
    echo "========================================================="
    echo ""

    #
    # IMPORTANTE:
    # no background, no redirección.
    # yahboom_keyboard necesita este TTY.
    #
    roslaunch \
    yahboomcar_ctrl \
    yahboom_keyboard.launch

fi
