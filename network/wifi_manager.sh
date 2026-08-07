#!/bin/bash
COMMAND="$1"
SSID="$2"
PASS="$3"

case "$COMMAND" in
    scan)
        # Truco del doble escaneo (para despertar la antena y ver a los vecinos)
        sudo nmcli dev wifi rescan > /dev/null 2>&1
        sleep 3
        sudo nmcli dev wifi rescan > /dev/null 2>&1
        sleep 2
        sudo nmcli -t -f SSID dev wifi list | grep -v '^$' | sort -u
        ;;
        
    saved)
        sudo nmcli -t -f NAME,TYPE connection show | grep "802-11-wireless" | cut -d: -f1 | sort -u
        ;;

    connect_new)
        sudo nmcli connection delete "$SSID" > /dev/null 2>&1
        OUTPUT=$(sudo nmcli dev wifi connect "$SSID" password "$PASS" 2>&1)
        if echo "$OUTPUT" | grep -q "successfully activated"; then
            echo "SUCCESS"
        else
            sudo nmcli connection delete "$SSID" > /dev/null 2>&1
            echo "ERROR"
        fi
        ;;

    connect_saved)
        OUTPUT=$(sudo nmcli connection up "$SSID" 2>&1)
        if echo "$OUTPUT" | grep -q "successfully activated"; then
            echo "SUCCESS"
        else
            echo "ERROR"
        fi
        ;;

    forget)
        sudo nmcli connection delete "$SSID" > /dev/null 2>&1
        echo "SUCCESS"
        ;;

    restart)
        sudo systemctl restart NetworkManager
        sleep 3
        echo "SUCCESS"
        ;;

    status)
        WLAN_IP=$(ip -4 addr show wlan0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        ETH_IP=$(ip -4 addr show eth0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        CURR_SSID=$(iwgetid -r 2>/dev/null)
        
        echo "WLAN_IP=${WLAN_IP:-Desconectado}"
        echo "ETH_IP=${ETH_IP:-Desconectado}"
        echo "SSID=${CURR_SSID:-Ninguna}"
        ;;
esac
