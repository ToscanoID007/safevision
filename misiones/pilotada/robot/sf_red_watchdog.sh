#!/usr/bin/env bash
#
# SafeVision — vigilante de conectividad de wlan0
#
# Se ejecuta EN EL ROBOT como servicio systemd (safevision-red.service).
#
# Que hace
# --------
# NetworkManager ya intenta por su cuenta las redes Wi-Fi guardadas. Este
# vigilante solo actua cuando eso falla:
#
#   - Si wlan0 esta conectada  ->  no hace nada.
#   - Si wlan0 NO esta conectada:
#       * busca entre las redes guardadas alguna que este al alcance
#         (usando el escaneo que NetworkManager mantiene) y la activa;
#       * si no hay ninguna al alcance, levanta el punto de acceso propio.
#
# Con el punto de acceso activo el robot SIEMPRE esta en la misma direccion:
#
#       10.42.0.1
#
# Mientras el punto de acceso este activo NO se vuelve a escanear: el chip
# brcmfmac de la Raspberry Pi no escanea de forma fiable mientras hace de AP,
# y un escaneo tiraria a los clientes conectados. Para volver a modo cliente,
# reinicia el robot o ejecuta:
#
#       sudo nmcli connection up "<NOMBRE_DE_LA_RED>"
#
set -uo pipefail

AP_NOMBRE="${SAFEVISION_AP_NOMBRE:-SafeVision-AP}"
ESPERA_INICIAL="${SAFEVISION_RED_ESPERA:-20}"
INTERVALO="${SAFEVISION_RED_INTERVALO:-20}"
IFAZ="wlan0"

log() { echo "[sf-red] $*"; }

# ---------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------
estado_wlan() {
    nmcli -t -f DEVICE,STATE device status 2>/dev/null \
        | awk -F: -v d="$IFAZ" '$1==d {print $2}'
}

conexion_activa() {
    nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null \
        | awk -F: -v d="$IFAZ" '$2==d {print $1}'
}

# Perfiles Wi-Fi guardados, excluyendo el del punto de acceso
perfiles_cliente() {
    nmcli -t -f NAME,TYPE connection show 2>/dev/null \
        | awk -F: '$2=="802-11-wireless" {print $1}' \
        | grep -Fxv "$AP_NOMBRE"
}

ssid_de_perfil() {
    nmcli -g 802-11-wireless.ssid connection show "$1" 2>/dev/null
}

ssids_al_alcance() {
    nmcli -t -f SSID device wifi list 2>/dev/null | grep -v '^$' | sort -u
}

# ---------------------------------------------------------------
# Logica principal
# ---------------------------------------------------------------
intentar_red_conocida() {
    local en_rango perfil ssid
    en_rango="$(ssids_al_alcance)"
    [ -z "$en_rango" ] && return 1

    while IFS= read -r perfil; do
        [ -z "$perfil" ] && continue
        ssid="$(ssid_de_perfil "$perfil")"
        [ -z "$ssid" ] && continue
        if printf '%s\n' "$en_rango" | grep -Fx "$ssid" >/dev/null; then
            log "red conocida al alcance: '$ssid' (perfil '$perfil'); conectando"
            if nmcli -w 25 connection up "$perfil" >/dev/null 2>&1; then
                log "conectado a '$ssid'"
                return 0
            fi
            log "fallo la conexion a '$ssid'"
        fi
    done < <(perfiles_cliente)
    return 1
}

levantar_ap() {
    if ! nmcli -t -f NAME connection show 2>/dev/null | grep -Fx "$AP_NOMBRE" >/dev/null; then
        log "ERROR: no existe el perfil '$AP_NOMBRE'."
        log "Ejecuta scripts/robot_configurar_red.sh para crearlo."
        return 1
    fi
    log "ninguna red conocida al alcance; levantando punto de acceso '$AP_NOMBRE'"
    if nmcli -w 30 connection up "$AP_NOMBRE" >/dev/null 2>&1; then
        log "punto de acceso activo. El robot responde en 10.42.0.1"
        return 0
    fi
    log "no se pudo levantar el punto de acceso"
    return 1
}

# ---------------------------------------------------------------
log "iniciando; espera inicial ${ESPERA_INICIAL}s"
sleep "$ESPERA_INICIAL"

while true; do
    estado="$(estado_wlan)"
    activa="$(conexion_activa)"

    if [ "$estado" = "connected" ]; then
        if [ "$activa" = "$AP_NOMBRE" ]; then
            # Punto de acceso en marcha: no escanear, se cortaria el servicio.
            :
        fi
    else
        log "wlan0 sin conexion (estado: ${estado:-desconocido})"
        if ! intentar_red_conocida; then
            levantar_ap || true
        fi
    fi

    sleep "$INTERVALO"
done
