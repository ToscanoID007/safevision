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
# Lista de redes vista antes de levantar el AP; la lee el dashboard (pagina Wi-Fi)
# porque en modo AP no se puede escanear sin tirar a los clientes.
CACHE_ESCANEO="/tmp/safevision_redes_wifi.txt"
# El dashboard lo crea mientras cambia de red; el vigilante no interviene.
CERROJO="/tmp/safevision_red_ocupada"
CERROJO_TTL=90

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
    # Guarda la lista completa para el dashboard y devuelve solo los SSID.
    local lista
    # Formas compatibles con NetworkManager 1.10 (Ubuntu 18.04): sin --rescan.
    nmcli device wifi rescan >/dev/null 2>&1 && sleep 4
    lista="$(nmcli -t -e yes -f SSID,SIGNAL,SECURITY,FREQ device wifi list 2>/dev/null)"
    if [ -n "$lista" ]; then
        printf '%s\n' "$lista" > "${CACHE_ESCANEO}.tmp" && mv -f "${CACHE_ESCANEO}.tmp" "$CACHE_ESCANEO"
        chmod 644 "$CACHE_ESCANEO" 2>/dev/null || true
    fi
    printf '%s\n' "$lista" | sed 's/\\:/\x01/g' | cut -d: -f1 | sed 's/\x01/:/g; s/\\\\/\\/g' | grep -v '^$' | sort -u
}

cerrojo_vigente() {
    [ -f "$CERROJO" ] || return 1
    local edad=$(( $(date +%s) - $(stat -c %Y "$CERROJO" 2>/dev/null || echo 0) ))
    [ "$edad" -lt "$CERROJO_TTL" ]
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
    if cerrojo_vigente; then
        sleep "$INTERVALO"
        continue
    fi
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
