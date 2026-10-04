#!/usr/bin/env python3
"""Calcula en que pagina cae cada titulo del reporte renderizado a PDF.

    python3 verificar_paginas.py reporte-final.pdf ../../docs/entrega/titulos.json indice.json

La portada no se numera: la pagina impresa es la del PDF menos uno. Se ignoran
las paginas del propio indice (las primeras despues de la portada).
"""
import json, subprocess, sys, re, unicodedata

def norm(t):
    t = unicodedata.normalize("NFKC", t)
    return re.sub(r"\s+", " ", t).strip().lower()

pdf, titulos_json, salida = sys.argv[1:4]
titulos = json.load(open(titulos_json))
paginas = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
textos = []
for p in range(1, paginas + 1):
    t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", pdf, "-"], capture_output=True, text=True).stdout
    textos.append([norm(l) for l in t.splitlines() if l.strip()])
# Donde empieza el cuerpo: primera pagina, tras el indice, cuyo texto incluye el primer titulo como linea propia
inicio = next(i for i in range(2, paginas) if any(l.startswith(norm(titulos[0])) for l in textos[i][:6]))
resultado, faltan, desde = {}, [], inicio
for t in titulos:
    n = norm(t)
    pagina = next((i for i in range(desde, paginas) if any(l == n or l.startswith(n) for l in textos[i])), None)
    if pagina is None:
        faltan.append(t); continue
    resultado[t] = pagina          # indice 0 = portada -> pagina impresa = indice
    desde = pagina
json.dump(resultado, open(salida, "w"), ensure_ascii=False, indent=1)
print("titulos con pagina: %d de %d" % (len(resultado), len(titulos)))
if faltan: print("sin encontrar:", faltan)
