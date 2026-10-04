#!/usr/bin/env bash
#
# SafeVision — actualizar el codigo del robot desde esta laptop
#
# SE EJECUTA EN LA LAPTOP, NO EN EL ROBOT.
#
# El robot no tiene acceso a GitHub. Este script le lleva la rama wip-handoff
# de esta laptop (un "git bundle" por SSH), la deja como version activa y
# reinicia los servicios de SafeVision para que la usen.
#
# Uso:
#     ./scripts/robot_actualizar.sh               # usa ROBOT_HOST de scripts/robot.env
#     ./scripts/robot_actualizar.sh 10.42.0.1     # o la IP del robot
#
# Pide la contrasena del usuario pi una sola vez.
#
# Efecto en el robot: el reinicio del Robot Server detiene lo que estuviera en
# marcha (driver, LiDAR, navegacion). Despues hay que volver a aplicar el
# perfil desde Pilotada. No toca mapas, modelos ni la configuracion de red.
#
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAMA="wip-handoff"
REPO_ROBOT="/home/pi/robot_custom"
PUERTO=8091

VERDE=$'\033[1;32m'; ROJO=$'\033[1;31m'; AMARILLO=$'\033[1;33m'; AZUL=$'\033[1;34m'; NEUTRO=$'\033[0m'
info()  { printf '%s==>%s %s\n' "$AZUL" "$NEUTRO" "$1"; }
ok()    { printf '%s  OK%s %s\n' "$VERDE" "$NEUTRO" "$1"; }
aviso() { printf '%s  !!%s %s\n' "$AMARILLO" "$NEUTRO" "$1"; }
fatal() { printf '%s ERROR%s %s\n' "$ROJO" "$NEUTRO" "$1" >&2; exit 1; }

cd "$RAIZ"

# ---------------------------------------------------------------
# 1. Comprobaciones locales
# ---------------------------------------------------------------
info "1/5  Comprobando esta copia del repositorio"
[ "$(git rev-parse --abbrev-ref HEAD)" = "$RAMA" ] || \
    fatal "Estas en la rama '$(git rev-parse --abbrev-ref HEAD)'. Cambia a $RAMA:  git checkout $RAMA"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    fatal "Hay cambios sin guardar en el repositorio. Guardalos o descartalos antes de actualizar el robot."
fi
LOCAL="$(git rev-parse HEAD)"
ok "Rama $RAMA en $(git log --oneline -1 | cut -c1-60)"

# ---------------------------------------------------------------
# 2. Direccion del robot
# ---------------------------------------------------------------
info "2/5  Buscando el robot"
DESTINO="${1:-}"
if [ -z "$DESTINO" ]; then
    [ -f scripts/robot.env ] && . scripts/robot.env
    DESTINO="${ROBOT_HOST:-yahboom.local}"
fi
IP="$DESTINO"
if ! [[ "$IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    IP="$(getent ahostsv4 "$DESTINO" 2>/dev/null | awk 'NR==1 {print $1}')" || true
    if [ -z "$IP" ] && grep -qi microsoft /proc/version 2>/dev/null && command -v powershell.exe >/dev/null; then
        IP="$(powershell.exe -NoProfile -NonInteractive -Command "[System.Net.Dns]::GetHostAddresses('$DESTINO') | Where-Object { \$_.AddressFamily -eq 'InterNetwork' } | Select-Object -First 1 | ForEach-Object { \$_.IPAddressToString }" 2>/dev/null | tr -d '\r' | head -1)" || true
    fi
fi
[ -n "$IP" ] || fatal "No se pudo resolver '$DESTINO'. Pasa la IP:  $0 10.42.0.1"
curl -s --max-time 4 -o /dev/null "http://$IP:$PUERTO/" || \
    fatal "El robot no responde en $IP. ¿Esta encendido y en la misma red que esta laptop?"
ok "Robot en $IP"

# Una sola conexion SSH reutilizada: la contrasena se pide una vez.
CTL="$(mktemp -u /tmp/sv-ssh-XXXXXX)"
SSH_OPC=(-o ControlMaster=auto -o ControlPath="$CTL" -o ControlPersist=120 -o StrictHostKeyChecking=accept-new)
cerrar() { ssh "${SSH_OPC[@]}" -O exit "pi@$IP" >/dev/null 2>&1 || true; rm -f "$BUNDLE" 2>/dev/null || true; }
BUNDLE="$(mktemp /tmp/sv-robot-XXXXXX.bundle)"
trap cerrar EXIT
rsh() { ssh "${SSH_OPC[@]}" "pi@$IP" "$@"; }

info "      Contrasena del usuario pi del robot:"
ROBOT_HEAD="$(rsh "cd $REPO_ROBOT && git rev-parse HEAD && test -z \"\$(git status --porcelain --untracked-files=no)\" && echo LIMPIO || echo SUCIO")"
ROBOT_COMMIT="$(printf '%s\n' "$ROBOT_HEAD" | sed -n 1p)"
[ "$(printf '%s\n' "$ROBOT_HEAD" | sed -n 2p)" = "LIMPIO" ] || \
    fatal "La copia del robot tiene cambios locales sin guardar. Revisalos antes ($REPO_ROBOT)."
ok "Robot en $(printf '%s' "$ROBOT_COMMIT" | cut -c1-7)"

if [ "$ROBOT_COMMIT" = "$LOCAL" ]; then
    ok "El robot ya tiene esta version. Nada que hacer."
    exit 0
fi

# ---------------------------------------------------------------
# 3. Paquete con lo que le falta al robot
# ---------------------------------------------------------------
info "3/5  Preparando el paquete"
if git merge-base --is-ancestor "$ROBOT_COMMIT" "$LOCAL" 2>/dev/null; then
    git bundle create "$BUNDLE" "$ROBOT_COMMIT..$RAMA" --tags >/dev/null 2>&1 || git bundle create "$BUNDLE" "$RAMA" --tags >/dev/null
else
    aviso "El robot tiene una version que esta laptop no conoce; se envia la rama completa."
    git bundle create "$BUNDLE" "$RAMA" --tags >/dev/null
fi
ok "Paquete de $(du -h "$BUNDLE" | cut -f1)"

# ---------------------------------------------------------------
# 4. Instalar en el robot
# ---------------------------------------------------------------
info "4/5  Instalando en el robot"
scp -q "${SSH_OPC[@]}" "$BUNDLE" "pi@$IP:/tmp/sv-actualizacion.bundle"
rsh "set -e; cd $REPO_ROBOT
     git fetch -q /tmp/sv-actualizacion.bundle '+refs/heads/$RAMA:refs/remotes/laptop/$RAMA' '+refs/tags/*:refs/tags/*'
     git checkout -q -B $RAMA laptop/$RAMA
     rm -f /tmp/sv-actualizacion.bundle
     echo \"  version: \$(git log --oneline -1 | cut -c1-60)\""
ok "Codigo actualizado"

# ---------------------------------------------------------------
# 5. Reiniciar servicios
# ---------------------------------------------------------------
info "5/5  Reiniciando los servicios de SafeVision"
rsh "sudo -n systemctl restart safevision-robot-server && (systemctl list-unit-files safevision-red.service >/dev/null 2>&1 && sudo -n systemctl restart safevision-red || true)" \
    || fatal "No se pudieron reiniciar los servicios (¿sudo pide contrasena?)."
for _ in $(seq 1 30); do
    curl -s --max-time 2 -o /dev/null "http://$IP:$PUERTO/" && break
    sleep 2
done
curl -s --max-time 3 -o /dev/null "http://$IP:$PUERTO/" || fatal "El Robot Server no volvio a responder. Revisa: journalctl -u safevision-robot-server"
ok "El Robot Server responde"

echo
echo "======================================================="
echo "${VERDE} ROBOT ACTUALIZADO${NEUTRO} a $(git log --oneline -1 | cut -c1-50)"
echo "======================================================="
echo " Si el robot estaba operando, vuelve a aplicar el perfil"
echo " desde la pagina Pilotada."
echo
