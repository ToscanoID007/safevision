#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/.venv"

echo "======================================="
echo "      Grafo - Visualizador"
echo "======================================="

cd "$PROJECT_DIR"

if [ ! -d "$VENV" ]; then
    echo "[1/4] Creando entorno virtual..."
    python3 -m venv .venv
fi

echo "[2/4] Activando entorno..."
source .venv/bin/activate

echo "[3/4] Instalando dependencias..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

echo "[4/4] Iniciando aplicación..."
python3 app.py
