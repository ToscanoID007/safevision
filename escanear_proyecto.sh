#!/bin/bash

CARPETA_BASE="/home/pi/robot_custom"
ARCHIVO_SALIDA="$CARPETA_BASE/codigo_completo.txt"

echo "=== REPORTE DE CÓDIGO: ROBOT CUSTOM ===" > "$ARCHIVO_SALIDA"
echo "Fecha de escaneo: $(date)" >> "$ARCHIVO_SALIDA"
echo "" >> "$ARCHIVO_SALIDA"

# Buscar archivos .py y .sh, ignorando pycache y compilados
find "$CARPETA_BASE" -type f \( -name "*.py" -o -name "*.sh" \) | grep -v "__pycache__" | sort | while read -r archivo; do
    echo -e "\n\n======================================================================" >> "$ARCHIVO_SALIDA"
    echo "📁 ARCHIVO: $archivo" >> "$ARCHIVO_SALIDA"
    echo "======================================================================" >> "$ARCHIVO_SALIDA"
    cat "$archivo" >> "$ARCHIVO_SALIDA"
done

echo "✅ Escaneo completado. Archivo generado en: $ARCHIVO_SALIDA"
