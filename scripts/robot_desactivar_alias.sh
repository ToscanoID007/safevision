#!/usr/bin/env bash
#
# SafeVision — desactiva en el robot los alias que destruyen el runtime
#
# ESTE SCRIPT SE EJECUTA EN LA RASPBERRY PI, NO EN LA PC.
#
# Problema que resuelve
# ---------------------
# ~/.bashrc del robot define alias heredados de la generacion anterior. Dos de
# ellos ejecutan scripts que empiezan por:
#
#     killall -9 roslaunch rviz roscore
#
# Si alguien los teclea por costumbre con los servicios de SafeVision activos,
# mata el roscore gestionado por systemd. systemd lo reinicia, pero el Robot
# Server queda hablando con un ROS Master nuevo y el estado en /tmp queda
# obsoleto: todo deja de responder sin un error claro.
#
# Que hace
# --------
#   1. Copia de seguridad de ~/.bashrc con fecha y hora.
#   2. COMENTA (no borra) los dos alias destructivos, dejando una nota.
#   3. Muestra el diff.
#
# Es idempotente y reversible: los alias siguen en el fichero, comentados, y la
# copia de seguridad permite volver atras.
#
# NO toca los scripts, NO desinstala nada, NO necesita sudo.
#
set -euo pipefail

VERDE=$'\033[1;32m'; AMARILLO=$'\033[1;33m'; ROJO=$'\033[1;31m'
AZUL=$'\033[1;34m'; NEGRITA=$'\033[1m'; NEUTRO=$'\033[0m'

info()  { printf '%s==>%s %s\n' "$AZUL"      "$NEUTRO" "$1"; }
ok()    { printf '%s  OK%s %s\n' "$VERDE"    "$NEUTRO" "$1"; }
aviso() { printf '%s  !!%s %s\n' "$AMARILLO" "$NEUTRO" "$1"; }
fatal() { printf '%s ERROR%s %s\n' "$ROJO"   "$NEUTRO" "$1" >&2; exit 1; }

BASHRC="${HOME}/.bashrc"
MARCA_D="# [SafeVision] desactivado: mata el roscore gestionado por systemd"
MARCA_C="# [SafeVision] desactivado: lanza LiDAR y chasis y compite con el runtime"

# Nivel 1 - destructivos: sus scripts ejecutan 'killall -9 ... roscore'
ALIAS_DESTRUCTIVOS=(mapeo_denso sensores)

# Nivel 2 - conflictivos: no matan roscore, pero lanzan por su cuenta nodos que
# se disputan el LiDAR y el chasis con el runtime.
ALIAS_CONFLICTIVOS=(mapeo_ligero mapear)

# Ambos niveles se desactivan.
ALIAS_TODOS=("${ALIAS_DESTRUCTIVOS[@]}" "${ALIAS_CONFLICTIVOS[@]}")

echo
echo "==========================================================="
echo " SafeVision — desactivar alias peligrosos del robot"
echo "==========================================================="
echo

[ -f "$BASHRC" ] || fatal "No existe $BASHRC"

# ------------------------------------------------------------------
# 1. Que se va a cambiar
# ------------------------------------------------------------------
info "Analizando $BASHRC"

PENDIENTES=()
for a in "${ALIAS_TODOS[@]}"; do
    if grep -qE "^[[:space:]]*alias[[:space:]]+${a}=" "$BASHRC"; then
        PENDIENTES+=("$a")
        nivel="conflictivo"
        for d in "${ALIAS_DESTRUCTIVOS[@]}"; do [ "$d" = "$a" ] && nivel="DESTRUCTIVO"; done
        printf "      [a desactivar] alias %-14s (%s)\n" "$a" "$nivel"
    elif grep -qE "^[[:space:]]*#[[:space:]]*alias[[:space:]]+${a}=" "$BASHRC"; then
        echo "      [ya desactivado] alias ${a}"
    else
        echo "      [no existe] alias ${a}"
    fi
done

if [ "${#PENDIENTES[@]}" -eq 0 ]; then
    echo
    ok "No hay nada que hacer: los alias ya estan desactivados o no existen."
    echo
    exit 0
fi

echo
echo "${NEGRITA}Se comentaran ${#PENDIENTES[@]} alias. No se borra nada.${NEUTRO}"
echo "Copia de seguridad previa en ${BASHRC}.safevision-<fecha>.bak"
echo
printf '%s¿Continuar? [s/N]: %s' "$NEGRITA" "$NEUTRO"
read -r RESPUESTA
case "${RESPUESTA,,}" in
    s|si|sí|y|yes) ;;
    *) echo; echo "Cancelado. No se ha modificado nada."; exit 0 ;;
esac
echo

# ------------------------------------------------------------------
# 2. Copia de seguridad
# ------------------------------------------------------------------
COPIA="${BASHRC}.safevision-$(date +%Y%m%d_%H%M%S).bak"
cp -a "$BASHRC" "$COPIA"
ok "Copia de seguridad: $COPIA"

# ------------------------------------------------------------------
# 3. Comentar
# ------------------------------------------------------------------
info "Comentando alias"
for a in "${PENDIENTES[@]}"; do
    marca="$MARCA_C"
    for d in "${ALIAS_DESTRUCTIVOS[@]}"; do [ "$d" = "$a" ] && marca="$MARCA_D"; done
    # Inserta la nota justo antes y comenta la linea del alias.
    sed -i -E "s|^([[:space:]]*)(alias[[:space:]]+${a}=.*)$|\1${marca}\n\1# \2|" "$BASHRC"
    ok "alias ${a} desactivado"
done

# ------------------------------------------------------------------
# 4. Diff
# ------------------------------------------------------------------
echo
info "Cambios aplicados"
echo
if diff -u "$COPIA" "$BASHRC" | sed -n '3,$p'; then
    :
fi

# ------------------------------------------------------------------
# 5. Avisos y siguiente paso
# ------------------------------------------------------------------
echo
aviso "Los scripts siguen ahi y se pueden ejecutar a mano por su ruta completa."
aviso "Lo que se ha quitado es el atajo, no la herramienta."

echo
echo "==========================================================="
echo "${VERDE} LISTO${NEUTRO}"
echo "==========================================================="
echo
echo " Aplica los cambios a tu sesion actual:"
echo
echo "     source ~/.bashrc"
echo
echo " Para revertir:"
echo
echo "     cp '$COPIA' ~/.bashrc && source ~/.bashrc"
echo
