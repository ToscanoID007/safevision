#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/melodic/setup.bash
source /home/pi/yahboomcar_ws/devel/setup.bash

resolve_ip() {
    local ip=""

    ip="$(
        ip -4 -o addr show dev wlan0 scope global 2>/dev/null \
            | awk 'NR==1 {split($4,a,"/"); print a[1]}'
    )"

    if [ -z "$ip" ]; then
        ip="$(
            hostname -I 2>/dev/null \
                | awk '{for(i=1;i<=NF;i++) if($i ~ /^[0-9]+\./){print $i; exit}}'
        )"
    fi

    printf '%s' "$ip"
}

ROBOT_IP=""

for _ in $(seq 1 120); do
    ROBOT_IP="$(resolve_ip)"

    if [ -n "$ROBOT_IP" ]; then
        break
    fi

    sleep 0.5
done

if [ -z "$ROBOT_IP" ]; then
    echo "ERROR: no se pudo resolver IPv4 del robot." >&2
    exit 1
fi

export ROS_IP="$ROBOT_IP"
export ROS_MASTER_URI="http://${ROBOT_IP}:11311"
export ROBOT_TYPE="X3"

echo "SafeVision ROS Master"
echo "ROS_IP=${ROS_IP}"
echo "ROS_MASTER_URI=${ROS_MASTER_URI}"

exec /opt/ros/melodic/bin/roscore -p 11311
