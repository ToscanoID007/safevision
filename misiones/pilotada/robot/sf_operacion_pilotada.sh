#!/bin/bash

CONTROL="$1"
MAP_NAME="${2:-HAB2}"

ROOT="/home/pi/robot_custom/misiones/pilotada"
ROBOT_DIR="$ROOT/robot"
LOG_DIR="$ROOT/logs"

MAPS_DIR="/home/pi/robot_custom/mapping/maps"
MAP_FILE="$MAPS_DIR/${MAP_NAME}.yaml"
ACTIVE_MAP_FILE="/tmp/safevision_active_map.json"

mkdir -p "$LOG_DIR"

if [ "$CONTROL" != "teclado" ] && \
   [ "$CONTROL" != "mando" ]; then
    echo "Uso: $0 teclado|mando [mapa]"
    exit 1
fi

if [[ -z "$MAP_NAME" ]] ||    [[ "$MAP_NAME" == *"/"* ]] ||    [[ "$MAP_NAME" == *"\\"* ]] ||    [[ "$MAP_NAME" == *".."* ]]; then
    echo "ERROR: nombre de mapa inválido."
    exit 1
fi

PI_IP="$(hostname -I | awk '{print $1}')"
[ -z "$PI_IP" ] && PI_IP="127.0.0.1"

export ROS_MASTER_URI="http://${PI_IP}:11311"
export ROS_IP="$PI_IP"
export ROBOT_TYPE="X3"
export SAFEVISION_MAP_NAME="$MAP_NAME"

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash

ROSCORE_PID=""
DRIVER_PID=""
LOCALIZACION_PID=""
EXPORTER_PID=""
SERVER_PID=""
SELECTOR_PID=""
NAV_PID=""
QUEUE_PID=""
CONTROL_PID=""
CERRANDO=0

cerrar_pid() {
    PID="$1"

    if [ -z "$PID" ]; then
        return
    fi

    if kill -0 "$PID" 2>/dev/null; then
        kill -INT "$PID" 2>/dev/null || true
    fi
}

terminar_pid() {
    PID="$1"

    if [ -z "$PID" ]; then
        return
    fi

    if ! kill -0 "$PID" 2>/dev/null; then
        return
    fi

    kill -TERM "$PID" 2>/dev/null || true

    for I in $(seq 1 10); do
        if ! kill -0 "$PID" 2>/dev/null; then
            return
        fi

        sleep 0.2
    done

    if kill -0 "$PID" 2>/dev/null; then
        echo "[WARN] PID $PID no respondió a SIGTERM; usando SIGKILL."
        kill -KILL "$PID" 2>/dev/null || true
    fi
}

cerrar() {
    trap '' INT TERM

    if [ "$CERRANDO" -eq 1 ]; then
        return
    fi

    CERRANDO=1

    echo ""
    echo "========================================================="
    echo " Finalizando misión pilotada..."
    echo "========================================================="

    cerrar_pid "$CONTROL_PID"
    cerrar_pid "$QUEUE_PID"
    cerrar_pid "$NAV_PID"
    cerrar_pid "$SELECTOR_PID"
    cerrar_pid "$SERVER_PID"
    cerrar_pid "$EXPORTER_PID"
    cerrar_pid "$LOCALIZACION_PID"
    cerrar_pid "$DRIVER_PID"

    sleep 3

    terminar_pid "$CONTROL_PID"
    terminar_pid "$QUEUE_PID"
    terminar_pid "$NAV_PID"
    terminar_pid "$SELECTOR_PID"
    terminar_pid "$SERVER_PID"
    terminar_pid "$EXPORTER_PID"
    terminar_pid "$LOCALIZACION_PID"
    terminar_pid "$DRIVER_PID"

    if [ -n "$ROSCORE_PID" ]; then
        cerrar_pid "$ROSCORE_PID"
        sleep 2
        terminar_pid "$ROSCORE_PID"
    fi

    rm -f "$ACTIVE_MAP_FILE"

echo "Operación finalizada."
}

salir_por_senal() {
    CODIGO="$1"

    trap '' INT TERM

    cerrar

    trap - EXIT
    exit "$CODIGO"
}

trap cerrar EXIT
trap 'salir_por_senal 130' INT
trap 'salir_por_senal 143' TERM

clear

echo "========================================================="
echo " SAFEVISION - PREPARANDO MISIÓN PILOTADA"
echo "========================================================="
echo " IP      : $PI_IP"
echo " Robot   : $ROBOT_TYPE"
echo " Control : ${CONTROL^^}"
echo " Mapa    : $MAP_NAME"
echo " Nivel   : 2"
echo "========================================================="

if [ ! -f "$MAP_FILE" ]; then
    echo ""
    echo "ERROR: no existe el mapa:"
    echo "$MAP_FILE"
    exit 1
fi

python3 - "$MAP_NAME" "$MAP_FILE" "$ACTIVE_MAP_FILE" <<'PYMAP'
import json
import sys
from pathlib import Path

nombre = sys.argv[1]
yaml_path = sys.argv[2]
destino = Path(sys.argv[3])

temporal = Path(
    str(destino) + ".tmp"
)

temporal.write_text(
    json.dumps(
        {
            "name": nombre,
            "yaml": yaml_path
        },
        sort_keys=True
    )
)

temporal.replace(
    destino
)
PYMAP

echo ""
echo "[1/9] Preparando ROS Master..."

if rosnode list >/dev/null 2>&1; then
    echo "[OK] ROS Master ya está activo."
else
    roscore \
        > "$LOG_DIR/roscore.log" 2>&1 &

    ROSCORE_PID=$!

    ROS_OK=0

    for I in $(seq 1 20); do
        if rosnode list >/dev/null 2>&1; then
            ROS_OK=1
            break
        fi

        sleep 0.5
    done

    if [ "$ROS_OK" -ne 1 ]; then
        echo "ERROR: ROS Master no inició."
        exit 1
    fi

    echo "[OK] ROS Master iniciado."
fi

echo ""
echo "[2/9] Iniciando driver Yahboom..."

if rosnode list 2>/dev/null \
    | grep -Fx "/driver_node" >/dev/null; then
    echo "ERROR: /driver_node ya está activo."
    echo "Cierra el runtime anterior antes de iniciar la misión."
    exit 1
fi

rosrun \
yahboomcar_bringup \
Mcnamu_driver.py \
/pub_vel:=/vel_raw \
/pub_imu:=/imu/imu_raw \
/pub_mag:=/mag/mag_raw \
> "$LOG_DIR/driver.log" 2>&1 &

DRIVER_PID=$!

DRIVER_OK=0

for I in $(seq 1 30); do
    if rosnode list 2>/dev/null \
        | grep -Fx "/driver_node" >/dev/null; then
        DRIVER_OK=1
        break
    fi

    sleep 0.25
done

if [ "$DRIVER_OK" -ne 1 ]; then
    echo "ERROR: driver Yahboom no inició."
    echo "Revisa:"
    echo "$LOG_DIR/driver.log"
    exit 1
fi

echo "[OK] Driver Yahboom."

echo ""
echo "[3/9] Iniciando localización $MAP_NAME..."
echo ""
echo "NO MUEVAS EL ROBOT."
echo "Esperando calibración de IMU y arranque de AMCL..."
echo ""

roslaunch \
"$ROBOT_DIR/sf_localizacion.launch" \
map_file:="$MAP_FILE" \
> "$LOG_DIR/localizacion.log" 2>&1 &

LOCALIZACION_PID=$!

LOCALIZACION_OK=0

for I in $(seq 1 80); do
    NODOS="$(rosnode list 2>/dev/null)"

    if echo "$NODOS" \
        | grep -Fx "/amcl" >/dev/null && \
       echo "$NODOS" \
        | grep -Fx "/ekf_localization" >/dev/null && \
       echo "$NODOS" \
        | grep -Fx "/imu_filter_madgwick" >/dev/null && \
       echo "$NODOS" \
        | grep -Fx "/rplidarNode" >/dev/null; then

        LOCALIZACION_OK=1
        break
    fi

    sleep 0.5
done

if [ "$LOCALIZACION_OK" -ne 1 ]; then
    echo "ERROR: localización no inició completamente."
    echo "Revisa:"
    echo "$LOG_DIR/localizacion.log"
    exit 1
fi

echo "Esperando calibración física de IMU..."
sleep 7

if ! kill -0 "$LOCALIZACION_PID" 2>/dev/null; then
    echo "ERROR: sf_localizacion.launch terminó inesperadamente."
    echo "Revisa:"
    echo "$LOG_DIR/localizacion.log"
    exit 1
fi

echo "Comprobando datos de IMU..."

if ! timeout 15     rostopic echo -n 1 /imu/imu_data     >/dev/null 2>&1; then

    echo "ERROR: /imu/imu_data no entregó datos."
    echo "Revisa:"
    echo "$LOG_DIR/localizacion.log"
    exit 1
fi

echo "[OK] IMU calibrada y publicando."

echo "Comprobando LiDAR..."

if ! timeout 15     rostopic echo -n 1 /scan     >/dev/null 2>&1; then

    echo "ERROR: /scan no entregó datos."
    echo "Revisa:"
    echo "$LOG_DIR/localizacion.log"
    exit 1
fi

echo "[OK] LiDAR publicando."

echo "[OK] IMU + EKF + LiDAR + $MAP_NAME + AMCL."

echo ""
echo "[4/9] Iniciando exportador de pose..."

rm -f /tmp/safevision_map_pose.json

/usr/bin/python \
"$ROBOT_DIR/sf_pose_exporter.py" \
> "$LOG_DIR/pose_exporter.log" 2>&1 &

EXPORTER_PID=$!

EXPORTER_OK=0

for I in $(seq 1 30); do
    if rosnode list 2>/dev/null \
        | grep -Fx "/safevision_pose_exporter" >/dev/null; then

        EXPORTER_OK=1
        break
    fi

    sleep 0.25
done

if [ "$EXPORTER_OK" -ne 1 ]; then
    echo "ERROR: Pose Exporter no inició."
    echo "Revisa:"
    echo "$LOG_DIR/pose_exporter.log"
    exit 1
fi

echo "[OK] Pose Exporter."

echo ""
echo "[5/9] Iniciando cámara y Robot Server..."

python3 \
"$ROBOT_DIR/sf_robot_server.py" \
--control "$CONTROL" \
> "$LOG_DIR/robot_server.log" 2>&1 &

SERVER_PID=$!

SERVER_OK=0

for I in $(seq 1 40); do
    if curl -sS --max-time 1 \
        "http://127.0.0.1:8080/" \
        >/dev/null 2>&1; then

        SERVER_OK=1
        break
    fi

    sleep 0.25
done

if [ "$SERVER_OK" -ne 1 ]; then
    echo "ERROR: Robot Server no respondió en puerto 8080."
    echo "Revisa:"
    echo "$LOG_DIR/robot_server.log"
    exit 1
fi

echo "[OK] Robot Server."

echo ""
echo "========================================================="
echo " RUNTIME SAFEVISION NIVEL 2 PREPARADO"
echo "========================================================="
echo " ROS Master   : OK"
echo " Driver       : OK"
echo " IMU / EKF    : OK"
echo " LiDAR        : OK"
echo " Mapa / AMCL  : $MAP_NAME / OK"
echo " Pose Export  : OK"
echo " Robot Server : OK"
echo "========================================================="
echo ""
echo " Robot Server:"
echo " http://${PI_IP}:8080"
echo ""

echo ""
echo "[6/9] Iniciando selector de movimiento..."

python3 "$ROBOT_DIR/sf_cmd_vel_selector.py" > "$LOG_DIR/cmd_vel_selector.log" 2>&1 &

SELECTOR_PID=$!

SELECTOR_OK=0

for I in $(seq 1 20); do
    if rosnode list 2>/dev/null         | grep -Fx "/sf_cmd_vel_selector" >/dev/null; then
        SELECTOR_OK=1
        break
    fi

    sleep 0.25
done

if [ "$SELECTOR_OK" -ne 1 ]; then
    echo "ERROR: sf_cmd_vel_selector no inició."
    tail -n 30 "$LOG_DIR/cmd_vel_selector.log" 2>/dev/null || true
    exit 1
fi

echo "[OK] Selector en modo MANUAL."

echo ""
echo "[7/9] Iniciando navegación Nivel 3..."

roslaunch "$ROBOT_DIR/sf_navegacion.launch" > "$LOG_DIR/navegacion.log" 2>&1 &

NAV_PID=$!

NAV_OK=0

for I in $(seq 1 30); do
    if rosnode list 2>/dev/null         | grep -Fx "/move_base" >/dev/null; then
        NAV_OK=1
        break
    fi

    sleep 0.5
done

if [ "$NAV_OK" -ne 1 ]; then
    echo "ERROR: move_base no inició."
    tail -n 40 "$LOG_DIR/navegacion.log" 2>/dev/null || true
    exit 1
fi

echo "[OK] move_base activo sin objetivo."

echo ""
echo "[8/9] Iniciando ejecutor de cola..."

python3 "$ROBOT_DIR/sf_nav_queue.py" > "$LOG_DIR/nav_queue.log" 2>&1 &

QUEUE_PID=$!

QUEUE_OK=0

for I in $(seq 1 20); do
    if rosnode list 2>/dev/null \
        | grep -Fx "/sf_nav_queue" >/dev/null; then
        QUEUE_OK=1
        break
    fi

    sleep 0.25
done

if [ "$QUEUE_OK" -ne 1 ]; then
    echo "ERROR: sf_nav_queue no inició."
    tail -n 40 "$LOG_DIR/nav_queue.log" 2>/dev/null || true
    exit 1
fi

echo "[OK] Ejecutor de cola activo."

if [ "$CONTROL" = "mando" ]; then
    echo "[9/9] Preparando control por mando..."

    if [ ! -e /dev/input/js0 ]; then
        echo "ERROR: no se detectó /dev/input/js0"
        exit 1
    fi

    roslaunch \
    "$ROBOT_DIR/sf_control_mando.launch" \
    > "$LOG_DIR/control.log" 2>&1 &

    CONTROL_PID=$!

    sleep 2

    python3 \
    "$ROBOT_DIR/sf_modo_espera.py" \
    mando

    ESPERA_RC=$?

    if [ "$ESPERA_RC" -ne 0 ]; then
        exit "$ESPERA_RC"
    fi

    wait "$CONTROL_PID"

else
    echo "[9/9] Sistema preparado para teclado."

    python3 \
    "$ROBOT_DIR/sf_modo_espera.py" \
    teclado

    clear

    echo "========================================================="
    echo " SAFEVISION - CONTROL POR TECLADO"
    echo "========================================================="
    echo ""
    echo " Robot Server : http://${PI_IP}:8080"
    echo " Mapa         : $MAP_NAME"
    echo " Localización : AMCL"
    echo ""
    echo " El Dashboard puede permanecer abierto en la PC."
    echo " Esta terminal controla el Rosmaster."
    echo ""
    echo " Para salir utiliza el comando de salida del"
    echo " controlador Yahboom o Ctrl+C."
    echo "========================================================="
    echo ""

    roslaunch \
    "$ROBOT_DIR/sf_control_teclado.launch"
fi
