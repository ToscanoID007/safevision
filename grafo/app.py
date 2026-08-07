#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, send_from_directory, request, Response
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from scanner import scan_project
import socket


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path.home() / "robot_custom"

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static")
)

TEXT_EXTENSIONS = {
    ".py",
    ".sh",
    ".bat",
    ".ps1",
    ".js",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".cfg",
    ".ini"
}

MAX_TEXT_SIZE = 1024 * 1024  # 1 MB


# =========================================================
# RED
# =========================================================

def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()

    return ip


# =========================================================
# SEGURIDAD DE RUTAS
# =========================================================

def resolver_archivo(relative_id):

    if not relative_id:
        return None

    root = PROJECT_ROOT.resolve()

    try:
        target = (PROJECT_ROOT / relative_id).resolve()
        target.relative_to(root)
    except Exception:
        return None

    if not target.is_file():
        return None

    return target


# =========================================================
# GENERADOR DE RESUMEN TXT
# =========================================================

def construir_resumen_txt(graph):

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    nodos_por_id = {
        n.get("id"): n
        for n in nodes
    }

    salientes = defaultdict(list)
    entrantes = defaultdict(list)

    for edge in edges:

        source = edge.get("source")
        target = edge.get("target")
        tipo = edge.get("type", "reference")

        salientes[source].append({
            "target": target,
            "type": tipo
        })

        entrantes[target].append({
            "source": source,
            "type": tipo
        })

    extensiones = Counter(
        n.get("ext") or "(sin extensión)"
        for n in nodes
    )

    tipos_relacion = Counter(
        e.get("type", "reference")
        for e in edges
    )

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lineas = []

    lineas.append("=" * 78)
    lineas.append("RESUMEN DE ARQUITECTURA - ROBOT_CUSTOM")
    lineas.append("Herramienta: Grafo del Proyecto")
    lineas.append("=" * 78)
    lineas.append("")
    lineas.append(f"Generado        : {ahora}")
    lineas.append(f"Proyecto        : {PROJECT_ROOT}")
    lineas.append(f"Archivos        : {len(nodes)}")
    lineas.append(f"Relaciones      : {len(edges)}")
    lineas.append("")

    lineas.append("=" * 78)
    lineas.append("1. ARCHIVOS POR TIPO")
    lineas.append("=" * 78)

    for ext, cantidad in sorted(
        extensiones.items(),
        key=lambda x: (-x[1], x[0])
    ):
        lineas.append(
            f"{ext:<20} {cantidad:>5}"
        )

    lineas.append("")
    lineas.append("=" * 78)
    lineas.append("2. RELACIONES POR TIPO")
    lineas.append("=" * 78)

    for tipo, cantidad in sorted(
        tipos_relacion.items(),
        key=lambda x: (-x[1], x[0])
    ):
        lineas.append(
            f"{tipo:<30} {cantidad:>5}"
        )

    lineas.append("")
    lineas.append("=" * 78)
    lineas.append("3. LISTA DE ARCHIVOS")
    lineas.append("=" * 78)

    for nodo in sorted(
        nodes,
        key=lambda x: x.get("id", "").lower()
    ):

        node_id = nodo.get("id", "")
        nombre = nodo.get("name", "")
        extension = nodo.get("ext", "")
        tamano = nodo.get("size", 0)
        modificado = nodo.get("modified", "")

        lineas.append("")
        lineas.append("-" * 78)
        lineas.append(f"ARCHIVO      : {nombre}")
        lineas.append(f"ID           : {node_id}")
        lineas.append(f"EXTENSIÓN    : {extension}")
        lineas.append(f"TAMAÑO       : {tamano} bytes")
        lineas.append(f"MODIFICADO   : {modificado}")

        sal = salientes.get(node_id, [])
        ent = entrantes.get(node_id, [])

        lineas.append(
            f"REL. SALIENTES: {len(sal)}"
        )

        if sal:
            for rel in sorted(
                sal,
                key=lambda r: r["target"]
            ):
                destino = nodos_por_id.get(
                    rel["target"],
                    {}
                ).get(
                    "name",
                    rel["target"]
                )

                lineas.append(
                    f"   -> {destino} [{rel['type']}]"
                )
        else:
            lineas.append(
                "   -> Ninguna detectada"
            )

        lineas.append(
            f"REL. ENTRANTES: {len(ent)}"
        )

        if ent:
            for rel in sorted(
                ent,
                key=lambda r: r["source"]
            ):
                origen = nodos_por_id.get(
                    rel["source"],
                    {}
                ).get(
                    "name",
                    rel["source"]
                )

                lineas.append(
                    f"   <- {origen} [{rel['type']}]"
                )
        else:
            lineas.append(
                "   <- Ninguna detectada"
            )

    lineas.append("")
    lineas.append("=" * 78)
    lineas.append("4. TODAS LAS RELACIONES")
    lineas.append("=" * 78)
    lineas.append("")

    for edge in sorted(
        edges,
        key=lambda x: (
            x.get("source", ""),
            x.get("target", ""),
            x.get("type", "")
        )
    ):

        lineas.append(
            "{} --[{}]--> {}".format(
                edge.get("source", ""),
                edge.get("type", "reference"),
                edge.get("target", "")
            )
        )

    lineas.append("")
    lineas.append("=" * 78)
    lineas.append("FIN DEL RESUMEN")
    lineas.append("=" * 78)
    lineas.append("")
    lineas.append(
        "Nota: las relaciones son detectadas automáticamente "
        "por análisis estático del proyecto."
    )

    return "\n".join(lineas)


# =========================================================
# RUTAS WEB
# =========================================================

@app.route("/")
def index():

    return send_from_directory(
        str(BASE_DIR / "static"),
        "index.html"
    )


@app.route("/files")
def files():

    return jsonify(
        scan_project()
    )


@app.route("/code")
def code():

    relative_id = request.args.get(
        "id",
        ""
    ).strip()

    target = resolver_archivo(
        relative_id
    )

    if target is None:

        return jsonify({
            "ok": False,
            "error": "Archivo no encontrado o ruta no permitida."
        }), 404

    extension = target.suffix.lower()

    if extension not in TEXT_EXTENSIONS:

        return jsonify({
            "ok": True,
            "readable": False,
            "id": relative_id,
            "extension": extension,
            "code": "",
            "message":
                "Archivo binario o no configurado para visualización textual."
        })

    try:
        size = target.stat().st_size
    except Exception:
        size = 0

    if size > MAX_TEXT_SIZE:

        return jsonify({
            "ok": True,
            "readable": False,
            "id": relative_id,
            "extension": extension,
            "code": "",
            "message":
                "El archivo supera el límite de 1 MB para visualización."
        })

    try:

        contenido = target.read_text(
            encoding="utf-8",
            errors="replace"
        )

    except Exception as e:

        return jsonify({
            "ok": False,
            "error":
                f"No fue posible leer el archivo: {e}"
        }), 500

    return jsonify({
        "ok": True,
        "readable": True,
        "id": relative_id,
        "extension": extension,
        "code": contenido
    })


@app.route("/summary.txt")
def summary_txt():

    graph = scan_project()

    contenido = construir_resumen_txt(
        graph
    )

    return Response(
        contenido,
        mimetype="text/plain; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=robot_custom_grafo_resumen.txt"
        }
    )


# =========================================================
# INICIO
# =========================================================

if __name__ == "__main__":

    puerto = 8080

    print()
    print("=" * 60)
    print(" Grafo - Visualizador del proyecto")
    print("=" * 60)
    print()

    graph = scan_project()

    print(
        f"Archivos encontrados : "
        f"{len(graph['nodes'])}"
    )

    print(
        f"Relaciones detectadas: "
        f"{len(graph['edges'])}"
    )

    print()
    print("Abra en su navegador:")
    print()
    print(
        f"http://{obtener_ip()}:{puerto}"
    )
    print()

    app.run(
        host="0.0.0.0",
        port=puerto,
        debug=False,
        use_reloader=False
    )
