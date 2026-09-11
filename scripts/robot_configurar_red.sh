#!/usr/bin/env bash
#
# SafeVision — red autonoma del robot (cliente Wi-Fi + punto de acceso propio)
#
# ESTE SCRIPT SE EJECUTA EN LA RASPBERRY PI, NO EN LA PC.
#
# Problema que resuelve
# ---------------------
# El robot cambia de sitio y de red constantemente, y a veces va a lugares sin
# ninguna red. Hasta ahora eso obligaba a reconfigurarlo cada vez.
#
# Como queda despues de ejecutarlo
# --------------------------------
#   1. Si hay una red Wi-Fi conocida al alcance  -> el robot se conecta a ella.
#   2. Si no la hay                               -> el robot crea SU PROPIA red
#      y queda SIEMPRE en la misma direccion:      10.42.0.1
#      (fijada explicitamente, no dejada al azar de NetworkManager)
#   3. El cable Ethernet sigue funcionando como via de rescate.
#
# Es idempotente (se puede repetir) y reversible (ver el final del script).
# Necesita sudo. NO toca los servicios de SafeVision ni ningun fichero del robot
# fuera de NetworkManager y systemd.
#
set -euo pipefail

VERDE=$'\033[1;32m'; AMARILLO=$'\033[1;33m'; ROJO=$'\033[1;31m'
AZUL=$'\033[1;34m'; NEGRITA=$'\033[1m'; NEUTRO=$'\033[0m'
info()  { printf '%s==>%s %s\n' "$AZUL"      "$NEUTRO" "$1"; }
ok()    { printf '%s  OK%s %s\n' "$VERDE"    "$NEUTRO" "$1"; }
aviso() { printf '%s  !!%s %s\n' "$AMARILLO" "$NEUTRO" "$1"; }
fatal() { printf '%s ERROR%s %s\n' "$ROJO"   "$NEUTRO" "$1" >&2; exit 1; }

RAIZ="${SAFEVISION_RAIZ:-/home/pi/robot_custom}"
AP_PERFIL="SafeVision-AP"
AP_SSID="${SAFEVISION_AP_SSID:-SafeVision-Robot}"
AP_CANAL="${SAFEVISION_AP_CANAL:-6}"
IFAZ="wlan0"

WATCHDOG="$RAIZ/misiones/pilotada/robot/sf_red_watchdog.sh"
UNIDAD_ORIGEN="$RAIZ/misiones/pilotada/systemd/safevision-red.service"
UNIDAD_DESTINO="/etc/systemd/system/safevision-red.service"

echo
echo "==========================================================="
echo " SafeVision — red autonoma del robot"
echo "==========================================================="
echo

# ---------------------------------------------------------------
# 1. Comprobaciones
# ---------------------------------------------------------------
info "Comprobaciones previas"

command -v nmcli >/dev/null 2>&1 || fatal "No hay nmcli (NetworkManager)."
[ -f "$WATCHDOG" ]       || fatal "Falta $WATCHDOG. ¿Actualizaste el repositorio con git pull?"
[ -f "$UNIDAD_ORIGEN" ]  || fatal "Falta $UNIDAD_ORIGEN."

ip link show "$IFAZ" >/dev/null 2>&1 || fatal "No existe la interfaz $IFAZ."
ok "NetworkManager y $IFAZ presentes"

# Nota: se evita 'grep -q' dentro de tuberias porque, con 'set -o pipefail',
# grep cierra la tuberia al primer acierto, el productor recibe SIGPIPE y el
# fallo se propaga aunque el patron SI estuviera.
if ! iw list 2>/dev/null | grep -E '^\s+\* AP$' >/dev/null; then
    aviso "No se pudo confirmar que el chip soporte modo AP. Se continua igualmente."
else
    ok "El chip soporta modo punto de acceso"
fi

if ! dpkg -l 2>/dev/null | grep -E '^ii  dnsmasq-base' >/dev/null; then
    fatal "Falta dnsmasq-base, necesario para repartir direcciones en el punto de acceso.
       Instalalo con:  sudo apt install -y dnsmasq-base"
fi
ok "dnsmasq-base instalado"

PERFILES_CLIENTE="$(nmcli -t -f NAME,TYPE connection show \
    | awk -F: '$2=="802-11-wireless" {print $1}' | grep -Fxv "$AP_PERFIL" || true)"

# ---------------------------------------------------------------
# 2. Que se va a hacer
# ---------------------------------------------------------------
echo
echo "${NEGRITA}Se van a realizar estas acciones:${NEUTRO}"
echo
if nmcli -t -f NAME connection show | grep -Fx "$AP_PERFIL" >/dev/null; then
    echo "  [~] Reconfigurar el perfil de punto de acceso '$AP_PERFIL' (ya existe)"
else
    echo "  [+] Crear el perfil de punto de acceso '$AP_PERFIL'"
fi
echo "      SSID '$AP_SSID', banda 2.4 GHz, canal $AP_CANAL, WPA2"
echo "      El robot quedara siempre en 10.42.0.1 cuando este activo"
echo
if [ -n "$PERFILES_CLIENTE" ]; then
    echo "  [~] Dar prioridad de autoconexion a las redes ya guardadas:"
    while IFS= read -r c; do [ -n "$c" ] && echo "         - $c"; done <<< "$PERFILES_CLIENTE"
else
    aviso "No hay ninguna red Wi-Fi guardada todavia."
    aviso "El robot arrancara directamente en modo punto de acceso."
fi
echo
echo "  [+] Instalar y habilitar el servicio safevision-red.service"
echo "      (vigila la conexion y levanta el punto de acceso si hace falta)"
echo
echo "  ${NEGRITA}NO se cambia la conexion actual.${NEUTRO} Todo surte efecto al reiniciar,"
echo "  o cuando wlan0 se quede sin red."
echo
# SAFEVISION_SI=1 salta la confirmacion (uso desatendido).
if [ "${SAFEVISION_SI:-0}" = "1" ]; then
    echo "${AMARILLO}  Modo desatendido (SAFEVISION_SI=1): se continua sin preguntar.${NEUTRO}"
else
    printf '%s¿Continuar? [s/N]: %s' "$NEGRITA" "$NEUTRO"
    read -r RESPUESTA
    case "${RESPUESTA,,}" in
        s|si|sí|y|yes) ;;
        *) echo; echo "Cancelado. No se ha modificado nada."; exit 0 ;;
    esac
fi
echo

# ---------------------------------------------------------------
# 3. Clave del punto de acceso
# ---------------------------------------------------------------
info "Clave del punto de acceso"
echo "      Minimo 8 caracteres. Es la que escribiras en la laptop para"
echo "      conectarte a '$AP_SSID'. No se guarda en el repositorio."
echo
# Se puede pasar por entorno para uso desatendido:
#     SAFEVISION_AP_PSK='...' ./robot_configurar_red.sh
AP_PSK="${SAFEVISION_AP_PSK:-}"

if [ -n "$AP_PSK" ]; then
    [ "${#AP_PSK}" -ge 8 ] || fatal "SAFEVISION_AP_PSK tiene ${#AP_PSK} caracteres; WPA2 exige 8 como minimo."
    ok "Clave tomada de SAFEVISION_AP_PSK (${#AP_PSK} caracteres)"
else
    while [ "${#AP_PSK}" -lt 8 ]; do
        read -rsp "      Clave (8+ caracteres): " AP_PSK; echo
        if [ "${#AP_PSK}" -lt 8 ]; then
            aviso "Demasiado corta (${#AP_PSK}). WPA2 exige 8 como minimo."
        fi
    done
    read -rsp "      Repitela: " AP_PSK2; echo
    [ "$AP_PSK" = "$AP_PSK2" ] || fatal "Las claves no coinciden."
    ok "Clave aceptada"
fi
echo

# ---------------------------------------------------------------
# 4. Perfil del punto de acceso
# ---------------------------------------------------------------
info "Configurando el punto de acceso"

if ! nmcli -t -f NAME connection show | grep -Fx "$AP_PERFIL" >/dev/null; then
    sudo nmcli connection add type wifi ifname "$IFAZ" con-name "$AP_PERFIL" \
        autoconnect no ssid "$AP_SSID" >/dev/null
    ok "Perfil '$AP_PERFIL' creado"
fi

sudo nmcli connection modify "$AP_PERFIL" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.channel "$AP_CANAL" \
    802-11-wireless.ssid "$AP_SSID" \
    ipv4.method shared \
    ipv4.addresses 10.42.0.1/24 \
    ipv6.method ignore \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.proto rsn \
    wifi-sec.pairwise ccmp \
    wifi-sec.group ccmp \
    wifi-sec.psk "$AP_PSK" \
    connection.autoconnect no
ok "Punto de acceso configurado (SSID '$AP_SSID', canal $AP_CANAL)"

unset AP_PSK AP_PSK2

# ---------------------------------------------------------------
# 5. Prioridad de las redes conocidas
# ---------------------------------------------------------------
if [ -n "$PERFILES_CLIENTE" ]; then
    info "Priorizando las redes conocidas sobre el punto de acceso"
    while IFS= read -r c; do
        [ -z "$c" ] && continue
        sudo nmcli connection modify "$c" \
            connection.autoconnect yes \
            connection.autoconnect-priority 10 2>/dev/null \
            && ok "$c  (autoconnect, prioridad 10)"
    done <<< "$PERFILES_CLIENTE"
fi

# ---------------------------------------------------------------
# 6. Servicio vigilante
# ---------------------------------------------------------------
info "Instalando el servicio vigilante"
sudo chmod +x "$WATCHDOG"
sudo install -m 0644 -o root -g root "$UNIDAD_ORIGEN" "$UNIDAD_DESTINO"
sudo systemctl daemon-reload
sudo systemctl enable safevision-red.service >/dev/null 2>&1
ok "safevision-red.service instalado y habilitado"

# ---------------------------------------------------------------
# 7. Resumen
# ---------------------------------------------------------------
echo
echo "==========================================================="
echo "${VERDE} CONFIGURACION COMPLETADA${NEUTRO}"
echo "==========================================================="
echo
echo " A partir del proximo reinicio, el robot:"
echo
echo "   1. Intenta conectarse a una red Wi-Fi conocida."
echo "   2. Si no hay ninguna al alcance, crea la suya:"
echo
echo "        Red:        ${NEGRITA}$AP_SSID${NEUTRO}"
echo "        Robot en:   ${NEGRITA}http://10.42.0.1:8091${NEUTRO}"
echo
echo " Para arrancarlo ahora sin reiniciar:"
echo "        sudo systemctl start safevision-red.service"
echo
echo " Para volver a una red concreta estando en modo punto de acceso:"
echo "        sudo nmcli connection up \"<NOMBRE_DE_LA_RED>\""
echo
echo " Para anadir una red nueva (te pedira la clave sin dejar rastro):"
echo "        sudo nmcli dev wifi connect \"<SSID>\" --ask"
echo
echo " ${NEGRITA}Para deshacer todo esto:${NEUTRO}"
echo "        sudo systemctl disable --now safevision-red.service"
echo "        sudo rm $UNIDAD_DESTINO"
echo "        sudo systemctl daemon-reload"
echo "        sudo nmcli connection delete \"$AP_PERFIL\""
echo
