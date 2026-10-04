#!/usr/bin/env bash
# Genera docs/entrega/reporte-final.docx y .pdf desde docs/reporte-final.md.
# Dos pasadas: la primera calcula en que pagina cae cada titulo (renderizando con
# LibreOffice) y la segunda escribe el indice con esos numeros.
# Requiere: node + 'npm install' en esta carpeta, LibreOffice (soffice) y poppler-utils.
set -euo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ENTREGA=../../docs/entrega
SOFFICE="${SOFFICE:-soffice}"   # comando de LibreOffice; se puede cambiar con la variable SOFFICE
node generar_reporte.js
"$SOFFICE" --headless --convert-to pdf --outdir "$TMP" "$ENTREGA/reporte-final.docx" >/dev/null
python3 verificar_paginas.py "$TMP/reporte-final.pdf" titulos.json "$TMP/indice.json"
node generar_reporte.js "$TMP/indice.json"
"$SOFFICE" --headless --convert-to pdf --outdir "$ENTREGA" "$ENTREGA/reporte-final.docx" >/dev/null
python3 verificar_paginas.py "$ENTREGA/reporte-final.pdf" titulos.json "$TMP/indice2.json" >/dev/null
python3 - "$TMP/indice.json" "$TMP/indice2.json" <<'PY'
import json, sys
a, b = (json.load(open(f)) for f in sys.argv[1:3])
cambios = [k for k in a if a[k] != b.get(k)]
print("Indice estable." if not cambios else "AVISO: cambian las paginas de %s; vuelve a ejecutar." % cambios)
PY
echo "Listo: $ENTREGA/reporte-final.docx y reporte-final.pdf"
