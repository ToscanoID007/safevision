#!/usr/bin/env bash
#
# SafeVision — instalacion de los servicios systemd EN EL ROBOT
#
# ESTE SCRIPT SE EJECUTA EN LA RASPBERRY PI, NO EN LA PC.
#
# Copia las dos unidades a /etc/systemd/system, recarga systemd y las habilita
# para que arranquen solas al encender el robot.
#
# Muestra exactamente lo que va a hacer y pide confirmacion antes de tocar nada.
# NO arranca los servicios: eso lo decide la persona, despues de revisar.
#
# Uso (en el robot):
#     cd ~/robot_custom
#     ./misiones/pilotada/systemd/install_services.sh
#
set -euo pipefail

AZUL=$'\033[1;34m'; VERDE=$'\033[1;32m'; AMARILLO=$'\033[1;33m'
ROJO=$'\033[1;31m'; NEGRITA=$'\033[1m'; NEUTRO=$'\033[0m'

info()  { printf '%s==>%s %s\n' "$AZUL"      "$NEUTRO" "$1"; }
ok()    { printf '%s  OK%s %s\n' "$VERDE"    "$NEUTRO" "$1"; }
aviso() { printf '%s  !!%s %s\n' "$AMARILLO" "$NEUTRO" "$1"; }
fatal() { printf '%s ERROR%s %s\n' "$ROJO"   "$NEUTRO" "$1" >&2; exit 1; }

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROBOT_DIR="$(cd "$AQUI/../robot" && pwd)"
DESTINO="/etc/systemd/system"

UNIDADES=(safevision-roscore.service safevision-robot-server.service)
LANZADORES=(sf_roscore_service.sh sf_robot_server_service.sh)

echo
echo "==========================================================="
echo " SafeVision — instalacion de servicios systemd"
echo "==========================================================="
echo

# ---------------------------------------------------------------
# Comprobaciones previas
# ---------------------------------------------------------------
info "Comprobaciones previas"

[ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "armv7l" ] || {
    aviso "Este equipo no es ARM ($(uname -m))."
    aviso "Este script esta pensado para la Raspberry Pi del robot."
    aviso "Si lo ejecutas en la PC por error, contesta 'n' abajo."
}

command -v systemctl >/dev/null 2>&1 || fatal "No hay systemctl en este sistema."

for u in "${UNIDADES[@]}"; do
    [ -f "$AQUI/$u" ] || fatal "Falta la unidad $AQUI/$u"
done
for l in "${LANZADORES[@]}"; do
    [ -f "$ROBOT_DIR/$l" ] || fatal "Falta el lanzador $ROBOT_DIR/$l"
    [ -x "$ROBOT_DIR/$l" ] || aviso "$l no tiene permiso de ejecucion (se corregira)"
done
ok "Unidades y lanzadores presentes"

# Las unidades llevan rutas absolutas: avisar si el repositorio no esta donde esperan.
RUTA_ESPERADA="/home/pi/robot_custom"
RAIZ_REAL="$(cd "$AQUI/../../.." && pwd)"
if [ "$RAIZ_REAL" != "$RUTA_ESPERADA" ]; then
    aviso "El repositorio esta en $RAIZ_REAL"
    aviso "pero las unidades apuntan a $RUTA_ESPERADA"
    aviso "Los servicios NO arrancaran hasta que coincidan."
    aviso "Mueve el repositorio a $RUTA_ESPERADA o edita las unidades."
fi

# ---------------------------------------------------------------
# Que se va a hacer
# ---------------------------------------------------------------
echo
echo "${NEGRITA}Se van a realizar estas acciones:${NEUTRO}"
echo
for u in "${UNIDADES[@]}"; do
    if [ -f "$DESTINO/$u" ]; then
        if diff -q "$AQUI/$u" "$DESTINO/$u" >/dev/null 2>&1; then
            echo "  [=] $u ya esta instalada y es identica (se reinstala igualmente)"
        else
            echo "  ${AMARILLO}[~]${NEUTRO} $u ya existe y ES DISTINTA — se SOBRESCRIBIRA"
            echo "      (se guardara copia en $DESTINO/$u.bak)"
        fi
    else
        echo "  [+] $u se copiara a $DESTINO/"
    fi
done
echo "  [+] chmod +x sobre los lanzadores en $ROBOT_DIR"
echo "  [+] systemctl daemon-reload"
echo "  [+] systemctl enable ${UNIDADES[*]}"
echo
echo "  ${NEGRITA}NO se arrancaran los servicios.${NEUTRO} Para hacerlo despues:"
echo "      sudo systemctl start ${UNIDADES[*]}"
echo
echo "  Se usara sudo. Puede pedirte tu contrasena."
echo

# ---------------------------------------------------------------
# Confirmacion
# ---------------------------------------------------------------
printf '%s¿Continuar? [s/N]: %s' "$NEGRITA" "$NEUTRO"
read -r RESPUESTA
case "${RESPUESTA,,}" in
    s|si|sí|y|yes) ;;
    *) echo; echo "Cancelado. No se ha modificado nada."; exit 0 ;;
esac
echo

# ---------------------------------------------------------------
# Instalacion
# ---------------------------------------------------------------
info "Instalando unidades"
for u in "${UNIDADES[@]}"; do
    if [ -f "$DESTINO/$u" ] && ! diff -q "$AQUI/$u" "$DESTINO/$u" >/dev/null 2>&1; then
        sudo cp -a "$DESTINO/$u" "$DESTINO/$u.bak"
        aviso "Copia de seguridad: $DESTINO/$u.bak"
    fi
    sudo install -m 0644 -o root -g root "$AQUI/$u" "$DESTINO/$u"
    ok "$u instalada"
done

info "Asegurando permisos de ejecucion de los lanzadores"
for l in "${LANZADORES[@]}"; do
    chmod +x "$ROBOT_DIR/$l" 2>/dev/null || sudo chmod +x "$ROBOT_DIR/$l"
    ok "$l ejecutable"
done

info "Recargando systemd"
sudo systemctl daemon-reload
ok "daemon-reload completado"

info "Habilitando los servicios para el arranque"
sudo systemctl enable "${UNIDADES[@]}"
ok "Servicios habilitados"

# ---------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------
echo
echo "==========================================================="
echo "${VERDE} INSTALACION COMPLETADA${NEUTRO}"
echo "==========================================================="
echo
systemctl is-enabled "${UNIDADES[@]}" 2>&1 | sed 's/^/      /'
echo
echo " Para arrancarlos ahora (o reinicia el robot):"
echo
echo "     sudo systemctl start ${UNIDADES[*]}"
echo
echo " Para comprobar que funcionan:"
echo
echo "     systemctl status safevision-robot-server"
echo "     curl -s http://127.0.0.1:8091/health"
echo
echo " Recuerda: arrancar los servicios NO deja el robot listo para moverse."
echo " Hay que aplicar un perfil de runtime. Ver docs/manual-operacion.md."
echo
