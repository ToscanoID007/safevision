#!/usr/bin/env bash
#
# SafeVision — instalacion del Dashboard en la PC
#
# Destino: Ubuntu 22.04 / 24.04 (tambien funciona en 20.04 con Python >= 3.8).
# Crea un entorno virtual aislado en misiones/pilotada/dashboard_src/.venv,
# instala las dependencias y verifica que se pueden importar.
#
# Es idempotente: se puede ejecutar las veces que haga falta.
# NO toca el robot. NO necesita sudo (salvo que falte python3-venv).
#
# Uso:  ./scripts/install_dashboard.sh
#
set -euo pipefail

PYTHON_MINIMO="3.8"

AZUL=$'\033[1;34m'; VERDE=$'\033[1;32m'; AMARILLO=$'\033[1;33m'
ROJO=$'\033[1;31m'; NEUTRO=$'\033[0m'

info()  { printf '%s==>%s %s\n' "$AZUL"     "$NEUTRO" "$1"; }
ok()    { printf '%s  OK%s %s\n' "$VERDE"   "$NEUTRO" "$1"; }
aviso() { printf '%s  !!%s %s\n' "$AMARILLO" "$NEUTRO" "$1"; }
fatal() { printf '%s ERROR%s %s\n' "$ROJO"  "$NEUTRO" "$1" >&2; exit 1; }

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASH="$RAIZ/misiones/pilotada/dashboard_src"
VENV="$DASH/.venv"
REQ="$DASH/requirements.txt"

echo
echo "======================================================="
echo " SafeVision — instalacion del Dashboard (PC)"
echo "======================================================="
echo " Repositorio : $RAIZ"
echo " Dashboard   : $DASH"
echo

# ---------------------------------------------------------------
# 1. Comprobaciones previas
# ---------------------------------------------------------------
info "1/6  Comprobando el repositorio"

[ -d "$DASH" ] || fatal "No existe $DASH. Ejecuta el script desde el repositorio clonado."
[ -f "$REQ" ]  || fatal "No existe $REQ."
[ -f "$DASH/sf_app_dashboard.py" ] || fatal "No existe sf_app_dashboard.py en $DASH."
ok "Estructura del repositorio correcta"

# ---------------------------------------------------------------
# 2. Python
# ---------------------------------------------------------------
info "2/6  Comprobando Python (se requiere >= $PYTHON_MINIMO)"

command -v python3 >/dev/null 2>&1 || fatal "No hay python3. Instalalo con: sudo apt install python3"

PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,8) else 1)'; then
    fatal "Python $PY_VER es demasiado antiguo. Se requiere >= $PYTHON_MINIMO."
fi
ok "Python $PY_VER en $(command -v python3)"

if ! python3 -c 'import venv' 2>/dev/null; then
    fatal "Falta el modulo venv. Instalalo con: sudo apt install python3-venv"
fi
ok "Modulo venv disponible"

# ---------------------------------------------------------------
# 3. Entorno virtual
# ---------------------------------------------------------------
info "3/6  Preparando el entorno virtual"

if [ -d "$VENV" ] && [ -x "$VENV/bin/python" ]; then
    ok "Ya existe un entorno virtual; se reutiliza ($VENV)"
else
    [ -e "$VENV" ] && [ ! -x "$VENV/bin/python" ] && \
        fatal "Existe $VENV pero esta incompleto. Borralo y vuelve a ejecutar: rm -rf '$VENV'"
    python3 -m venv "$VENV"
    ok "Entorno virtual creado en $VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
ok "Entorno activado ($(python --version 2>&1))"

# ---------------------------------------------------------------
# 4. Dependencias
# ---------------------------------------------------------------
info "4/6  Instalando dependencias (puede tardar varios minutos)"

echo
aviso "Se instalara PyTorch en su version para CPU."
aviso "Es lo correcto: la inferencia YOLO corre en la PC y no requiere GPU."
aviso "Si tu equipo tiene GPU NVIDIA y quieres usarla, instala despues la"
aviso "variante CUDA siguiendo https://pytorch.org/get-started/locally/"
echo

python -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || \
    aviso "No se pudo actualizar pip; se continua igualmente"
ok "pip actualizado"

info "      Instalando torch (CPU) desde el indice oficial"
python -m pip install --quiet \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchvision \
    || fatal "Fallo la instalacion de torch. Revisa tu conexion a Internet."
ok "torch (CPU) instalado"

info "      Instalando el resto de $REQ"
python -m pip install --quiet -r "$REQ" \
    || fatal "Fallo la instalacion de las dependencias de requirements.txt"
ok "Dependencias instaladas"

# ---------------------------------------------------------------
# 5. Verificacion de importaciones
# ---------------------------------------------------------------
info "5/6  Verificando que las dependencias se importan"

python - <<'PYCHECK' || fatal "Alguna dependencia no se pudo importar. La instalacion NO esta completa."
import importlib, sys

modulos = [
    ("flask",       "Flask"),
    ("requests",    "requests"),
    ("cv2",         "OpenCV"),
    ("numpy",       "NumPy"),
    ("torch",       "PyTorch"),
    ("ultralytics", "Ultralytics YOLO"),
]

fallos = []
for modulo, nombre in modulos:
    try:
        m = importlib.import_module(modulo)
        v = getattr(m, "__version__", "?")
        print("      %-20s %s" % (nombre, v))
    except Exception as exc:
        fallos.append("%s (%s): %s" % (nombre, modulo, exc))

if fallos:
    print("\n      NO SE PUDIERON IMPORTAR:")
    for f in fallos:
        print("        - " + f)
    sys.exit(1)

try:
    print("      torch usa CUDA:      %s" % torch.cuda.is_available())
except Exception:
    pass
PYCHECK
ok "Todas las dependencias se importan correctamente"

# ---------------------------------------------------------------
# 6. Configuracion de red
# ---------------------------------------------------------------
info "6/6  Comprobando la configuracion de red"

if [ -f "$RAIZ/scripts/robot.env" ]; then
    ok "Existe scripts/robot.env"
else
    aviso "No existe scripts/robot.env (se creara al ejecutar run_dashboard.sh,"
    aviso "o puedes copiarlo ahora: cp scripts/robot.env.example scripts/robot.env)"
fi

echo
echo "======================================================="
echo "${VERDE} INSTALACION COMPLETADA${NEUTRO}"
echo "======================================================="
echo
echo " Siguiente paso:"
echo
echo "     ./scripts/run_dashboard.sh"
echo
echo " Ese script arranca el dashboard en http://127.0.0.1:5000"
echo " y te dira que IP escribir para conectar con el robot."
echo
echo " Documentacion: docs/instalacion-pc.md"
echo
