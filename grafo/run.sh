#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/.venv"
PYTHON="$VENV/bin/python3"
PIP="$VENV/bin/pip"

echo ""
echo "======================================="
echo "      Grafo - Visualizador"
echo "======================================="
echo ""

cd "$PROJECT_DIR"

# =========================================================
# 1. ENTORNO VIRTUAL
# =========================================================

if [ ! -x "$PYTHON" ]; then
    echo "[1/3] Creando entorno virtual..."
    python3 -m venv "$VENV"

    echo "[2/3] Instalando dependencias..."
    "$PIP" install -r "$PROJECT_DIR/requirements.txt"
else
    echo "[1/3] Entorno virtual listo."

    # Solo instalar si falta una dependencia necesaria.
    if ! "$PYTHON" -c "import flask" >/dev/null 2>&1; then
        echo "[2/3] Faltan dependencias. Instalando..."
        "$PIP" install -r "$PROJECT_DIR/requirements.txt"
    else
        echo "[2/3] Dependencias listas."
    fi
fi

# =========================================================
# 2. INICIAR APLICACIÓN
# =========================================================

echo "[3/3] Iniciando aplicación..."
echo ""

exec "$PYTHON" "$PROJECT_DIR/app.py"
