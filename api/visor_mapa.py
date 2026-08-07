#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import yaml
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def visualizar_mapa(ruta_yaml):
    if not os.path.exists(ruta_yaml):
        print(f"❌ Error: No se encontró el archivo YAML: {ruta_yaml}")
        sys.exit(1)

    with open(ruta_yaml, 'r') as f:
        datos_yaml = yaml.safe_load(f)

    rel_img = datos_yaml.get('image', '')
    dir_yaml = os.path.dirname(os.path.abspath(ruta_yaml))
    nombre_base_pgm = os.path.basename(rel_img)
    
    # Intenta resolver la imagen en la ruta original, o en la carpeta local (/tmp)
    posibles_rutas = [
        rel_img,
        os.path.join(dir_yaml, nombre_base_pgm),
        os.path.join(dir_yaml, os.path.splitext(os.path.basename(ruta_yaml))[0] + ".pgm")
    ]

    ruta_pgm = None
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            ruta_pgm = ruta
            break

    if not ruta_pgm:
        print(f"❌ Error: No se encontró la imagen .pgm del mapa en ninguna de estas rutas:")
        for r in posibles_rutas:
            print(f"   - {r}")
        sys.exit(1)

    resolucion = datos_yaml.get('resolution', 0.05)
    origen = datos_yaml.get('origin', [0.0, 0.0, 0.0])

    img = mpimg.imread(ruta_pgm)
    h, w = img.shape[:2]
    extent = [
        origen[0], 
        origen[0] + w * resolucion, 
        origen[1], 
        origen[1] + h * resolucion
    ]

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img, cmap='gray', origin='lower', extent=extent)
    ax.set_title(f"Mapa 2D: {os.path.basename(ruta_yaml)}", fontsize=14, fontweight='bold')
    ax.set_xlabel("X (Metros)")
    ax.set_ylabel("Y (Metros)")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    print("✅ Visualizador activo en pantalla. Cierra la ventana gráfica para continuar.")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 visor_mapa.py <ruta_al_archivo_yaml>")
        sys.exit(1)
    visualizar_mapa(sys.argv[1])
