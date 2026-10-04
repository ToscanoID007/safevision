# Generador del reporte final en Word

Convierte `docs/reporte-final.md` en `docs/entrega/reporte-final.docx` (y su PDF) con
portada, índice con números de página, encabezado, numeración, tablas, notas, figuras con
pie y bloque de firmas.

```bash
cd scripts/reporte_docx
npm install          # una vez: instala la librería docx
./generar.sh         # necesita LibreOffice (soffice) y poppler-utils (pdftotext)
```

Si cambias el reporte, vuelve a ejecutar `./generar.sh`. Las imágenes se toman de
`docs/evidencias/` y de `docs/entrega/img/` (allí están los diagramas renderizados y las
capturas convertidas de `.webp` a `.png`, que Word no siempre muestra). Las dimensiones de cada
imagen están en `docs/entrega/img/dimensiones.json`; si añades una imagen, añádela también ahí.

Los datos de la portada y de las firmas (nombres, números de control, asesor, fechas) están en
`generar_reporte.js`, funciones `portada()` y `firmas()`.
