#!/usr/bin/env python3
"""Pagina de cada titulo, subtitulo y figura del informe renderizado a PDF.
    python3 paginas_informe.py informe.pdf titulos_informe.json salida.json"""
import json, re, subprocess, sys

pdf, entrada, salida = sys.argv[1:4]
t = json.load(open(entrada, encoding="utf-8"))
info = subprocess.run(["pdfinfo", pdf], stdout=subprocess.PIPE, universal_newlines=True).stdout
n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
paginas = []
for p in range(1, n + 1):
    txt = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), pdf, "-"], stdout=subprocess.PIPE,
                         universal_newlines=True).stdout
    paginas.append([re.sub(r"\s+", " ", l).strip() for l in txt.splitlines() if l.strip()])
res, desde = {}, 2
for titulo in t["titulos"] + [t["firmas"]]:
    for p in range(desde, n + 1):
        if titulo in paginas[p - 1]:
            res[titulo] = p; desde = p; break
inicio = res.get(t["titulos"][1], 3)
for sub in t["subtitulos"]:
    for p in range(inicio, n + 1):
        if sub in paginas[p - 1]:
            res[sub] = p; break
for fig in t["figuras"]:
    for p in range(inicio, n + 1):
        if any(l.startswith(fig + " ") for l in paginas[p - 1]):
            res[fig] = p; break
json.dump(res, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
faltan = [x for x in t["titulos"] + t["subtitulos"] + t["figuras"] + [t["firmas"]] if x not in res]
print("paginas: %d | encontrados %d | faltan %s" % (n, len(res), faltan or "ninguno"))
