#!/usr/bin/env bash
#
# SafeVision — arranque del Dashboard en la PC
#
# Lee la direccion del robot de la variable de entorno ROBOT_HOST o de
# scripts/robot.env, comprueba que el robot responde, activa el entorno
# virtual y arranca el dashboard.
#
# NO hay ninguna IP escrita en este script.
#
# Uso:
#     ./scripts/run_dashboard.sh
#     ROBOT_HOST=192.168.1.50 ./scripts/run_dashboard.sh
#
set -euo pipefail

AZUL=$'\033[1;34m'; VERDE=$'\033[1;32m'; AMARILLO=$'\033[1;33m'
ROJO=$'\033[1;31m'; NEGRITA=$'\033[1m'; NEUTRO=$'\033[0m'

info()  { printf '%s==>%s %s\n' "$AZUL"      "$NEUTRO" "$1"; }
ok()    { printf '%s  OK%s %s\n' "$VERDE"    "$NEUTRO" "$1"; }
aviso() { printf '%s  !!%s %s\n' "$AMARILLO" "$NEUTRO" "$1"; }
fatal() { printf '%s ERROR%s %s\n' "$ROJO"   "$NEUTRO" "$1" >&2; exit 1; }

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASH="$RAIZ/misiones/pilotada/dashboard_src"
VENV="$DASH/.venv"
ENV_FILE="$RAIZ/scripts/robot.env"
ENV_EJEMPLO="$RAIZ/scripts/robot.env.example"

echo
echo "======================================================="
echo " SafeVision — Dashboard"
echo "======================================================="

# ---------------------------------------------------------------
# 1. Configuracion
# ---------------------------------------------------------------
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a
    ok "Configuracion leida de scripts/robot.env"
elif [ -f "$ENV_EJEMPLO" ]; then
    aviso "No existe scripts/robot.env; se crea a partir del ejemplo"
    cp "$ENV_EJEMPLO" "$ENV_FILE"
    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a
    aviso "Revisa scripts/robot.env si tu robot no responde a yahboom.local"
fi

ROBOT_HOST="${ROBOT_HOST:-yahboom.local}"
ROBOT_PORT="${ROBOT_PORT:-8091}"

info "Robot configurado: $ROBOT_HOST:$ROBOT_PORT"

# ---------------------------------------------------------------
# 2. Entorno virtual
# ---------------------------------------------------------------
if [ ! -x "$VENV/bin/python" ]; then
    fatal "No hay entorno virtual en $VENV
       Ejecuta primero:  ./scripts/install_dashboard.sh"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
ok "Entorno virtual activado"

# ---------------------------------------------------------------
# 3. Resolucion de la IP del robot
# ---------------------------------------------------------------
info "Resolviendo la direccion del robot"

resolver_ipv4() {
    local destino="$1" ip=""
    if [[ "$destino" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        printf '%s' "$destino"; return 0
    fi
    ip="$(getent ahostsv4 "$destino" 2>/dev/null | awk 'NR==1 {print $1}')" || true
    [ -z "$ip" ] && ip="$(getent hosts "$destino" 2>/dev/null | awk 'NR==1 {print $1}')" || true
    printf '%s' "$ip"
}

ROBOT_IP="$(resolver_ipv4 "$ROBOT_HOST")"

# Si el nombre no resuelve (mDNS caido, o el robot cambio de interfaz y de IP),
# barremos la red local buscando quien responda al Robot Server en :8091.
# Asi el script sobrevive a un cambio de Ethernet a Wi-Fi sin tocar nada.
descubrir_robot() {
    local prefijo pid_list=() encontrado=""
    prefijo="$(ip -4 -o addr show scope global 2>/dev/null \
        | awk 'NR==1 {split($4,a,"/"); split(a[1],b,"."); print b[1]"."b[2]"."b[3]}')"
    [ -z "$prefijo" ] && return 1

    local tmp; tmp="$(mktemp -d)"
    for i in $(seq 1 254); do
        (
            if curl -sS --max-time 1 -o /dev/null \
                 "http://${prefijo}.${i}:${ROBOT_PORT}/health" 2>/dev/null; then
                echo "${prefijo}.${i}" > "$tmp/encontrado"
            fi
        ) &
        pid_list+=("$!")
        # no saturar: tandas de 64
        if [ "${#pid_list[@]}" -ge 64 ]; then wait; pid_list=(); fi
    done
    wait
    [ -f "$tmp/encontrado" ] && encontrado="$(cat "$tmp/encontrado")"
    rm -rf "$tmp"
    [ -n "$encontrado" ] && printf '%s' "$encontrado"
}

# Ruta rapida: si el robot esta en modo punto de acceso propio, siempre esta
# en 10.42.0.1 (NetworkManager reparte 10.42.0.0/24 con ipv4.method shared).
if [ -z "$ROBOT_IP" ] && curl -sS --max-time 2 -o /dev/null \
        "http://10.42.0.1:${ROBOT_PORT}/health" 2>/dev/null; then
    ROBOT_IP="10.42.0.1"
    ok "Robot en modo punto de acceso: $ROBOT_IP"
fi

if [ -z "$ROBOT_IP" ]; then
    aviso "No se pudo resolver '$ROBOT_HOST'."
    info "Buscando el robot en la red local (unos 10 s)..."
    ROBOT_IP="$(descubrir_robot || true)"
    if [ -n "$ROBOT_IP" ]; then
        ok "Robot encontrado en $ROBOT_IP"
        aviso "Para fijarlo: echo 'ROBOT_HOST=$ROBOT_IP' > scripts/robot.env"
    else
        aviso "No se encontro ningun robot respondiendo en :$ROBOT_PORT."
        aviso "Comprueba que esta encendido y en la misma red."
        aviso "Ver docs/red.md §6."
    fi
else
    ok "Robot en $ROBOT_IP"
fi

# ---------------------------------------------------------------
# 4. Comprobacion del Robot Server (solo lectura)
# ---------------------------------------------------------------
ROBOT_OK=0
if [ -n "$ROBOT_IP" ] && command -v curl >/dev/null 2>&1; then
    info "Consultando http://$ROBOT_IP:$ROBOT_PORT/health"
    if SALUD="$(curl -sS --max-time 6 "http://$ROBOT_IP:$ROBOT_PORT/health" 2>/dev/null)"; then
        ROBOT_OK=1
        ok "El Robot Server responde"
        python - "$SALUD" <<'PYSALUD' || true
import json, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
marca = lambda v: "si" if v else "NO"
print("      ros_master : %s" % marca(d.get("ros_master")))
print("      driver     : %s" % marca(d.get("driver")))
print("      lidar      : %s" % marca(d.get("lidar")))
print("      camara     : %s" % marca(d.get("camera")))
print("      control    : %s (%s)" % (marca(d.get("control")), d.get("control_mode")))
if not d.get("ok"):
    print()
    print("      AVISO: /health devuelve ok=false.")
    print("      Es NORMAL recien arrancado el robot: todavia no se ha")
    print("      aplicado un perfil de runtime, asi que el robot no se")
    print("      movera. Ver docs/manual-operacion.md, 'Aplicar un perfil'.")
PYSALUD
    else
        aviso "El robot no respondio en http://$ROBOT_IP:$ROBOT_PORT/health"
        aviso "El dashboard arrancara igualmente; podras conectar despues."
    fi
fi

# ---------------------------------------------------------------
# 5. Arranque
# ---------------------------------------------------------------
echo
echo "======================================================="
echo "${NEGRITA} Dashboard:  http://127.0.0.1:5000${NEUTRO}"
if [ -n "$ROBOT_IP" ]; then
echo "${NEGRITA} Robot:      $ROBOT_IP${NEUTRO}"
echo
echo " La pagina Pilotada toma esa IP automaticamente."
echo " Si usas la portada clasica, escribela en la casilla"
echo " 'IP del robot' (solo acepta IPv4, no nombres)."
fi
echo "======================================================="
echo " Para detenerlo: Ctrl+C"
echo

# La pagina /pilotada no expone panel de IP: lee SAFEVISION_ROBOT_IP del
# entorno y, si falta, cae en una IP de respaldo que puede estar obsoleta.
# Se la damos resuelta para que nunca dependa de ese respaldo.
if [ -n "$ROBOT_IP" ]; then
    export SAFEVISION_ROBOT_IP="$ROBOT_IP"
fi

cd "$DASH"
exec python sf_app_dashboard.py
