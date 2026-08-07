#!/bin/bash

# --- CONFIGURACIÓN ---
TARGET_DIR="/home/pi/robot_custom"
OUTPUT_FILE="/tmp/codigo_proyecto.txt"
CONFIG_FILE="/home/pi/robot_custom/api/.pc_config"

echo "========================================================="
echo "       📦 EXPORTADOR DE CÓDIGO (robot_custom)            "
echo "========================================================="

# 1. Vaciar el archivo si ya existe
> "$OUTPUT_FILE"

echo "🔍 [1/3] Recopilando código..."
# Encuentra archivos .py, .yaml, .json, .sh ignorando carpetas basura como __pycache__ o .git
find "$TARGET_DIR" -type d \( -name "__pycache__" -o -name ".git" \) -prune -o -type f \( -name "*.py" -o -name "*.sh" -o -name "*.yaml" -o -name "*.json" \) -print | while read -r file; do
    echo "=========================================================" >> "$OUTPUT_FILE"
    echo "📄 ARCHIVO: $file" >> "$OUTPUT_FILE"
    echo "=========================================================" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
done

echo "   ✅ Código consolidado correctamente."

# 2. Detectar IP y Usuario de la PC
if [ -n "$SSH_CLIENT" ]; then
    PC_IP=$(echo $SSH_CLIENT | awk '{print $1}')
else
    PC_IP="192.168.1.76" # Fallback por si lo corres directo en la Pi
fi

if [ -f "$CONFIG_FILE" ]; then
    PC_USER=$(cat "$CONFIG_FILE")
else
    echo ""
    read -p "👉 Ingresa tu usuario de la PC (ej: toscano, admin, ubuntu): " PC_USER
    echo "$PC_USER" > "$CONFIG_FILE"
fi

echo "🚀 [2/3] Conectando con tu PC ($PC_USER@$PC_IP)..."

# Detectar si tu PC usa la carpeta "Desktop" o "Escritorio"
DEST_PATH=$(ssh -o ConnectTimeout=5 "$PC_USER@$PC_IP" "if [ -d 'Desktop' ]; then echo 'Desktop'; elif [ -d 'Escritorio' ]; then echo 'Escritorio'; else echo '.'; fi" 2>/dev/null)

if [ -z "$DEST_PATH" ]; then
    echo "❌ Error: No se pudo conectar a tu PC por SSH. Verifica que tu PC esté encendida y acepte conexiones."
    exit 1
fi

echo "🔄 [3/3] Transfiriendo archivo al $DEST_PATH..."

# 3. Enviar el archivo mediante SCP
scp -q "$OUTPUT_FILE" "$PC_USER@$PC_IP:~/$DEST_PATH/codigo_proyecto.txt"

if [ $? -eq 0 ]; then
    echo "🎉 ¡Éxito! El archivo 'codigo_proyecto.txt' está actualizado en el $DEST_PATH de tu PC."
    echo "========================================================="
else
    echo "❌ Error al transferir el archivo a tu PC."
fi
