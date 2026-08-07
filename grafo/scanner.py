#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import re


# =========================================================
# CONFIGURACIÓN
# =========================================================

PROJECT_ROOT = Path.home() / "robot_custom"

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "grafo",
    "node_modules"
}


# Archivos que queremos mostrar como nodos
VALID_EXT = {
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
    ".ini",
    ".pt",
    ".torchscript",
    ".onnx"
}


# Archivos cuyo contenido sí tiene sentido analizar como texto
TEXT_EXT = {
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


# =========================================================
# ÍNDICES
# =========================================================

def build_indexes(nodes):
    """
    Crea varios índices.

    Permite buscar un archivo por:

        main_menu.py

        api/main_menu.py

        /home/pi/robot_custom/api/main_menu.py

    También permite varios archivos con el mismo nombre.
    """

    by_name = defaultdict(list)
    by_id = {}
    by_abs = {}

    for node in nodes:

        by_name[
            node["name"]
        ].append(node)

        by_id[
            node["id"].replace("\\", "/")
        ] = node

        by_abs[
            node["path"].replace("\\", "/")
        ] = node


    return {
        "by_name": by_name,
        "by_id": by_id,
        "by_abs": by_abs
    }


# =========================================================
# AGREGAR RELACIONES
# =========================================================

def add_edge(
    edges,
    seen,
    source_id,
    target_id,
    relation_type
):

    if not target_id:
        return

    # No conectar un archivo consigo mismo
    if source_id == target_id:
        return


    # Evita repetir exactamente:
    #
    # A -> B [reference]
    # A -> B [reference]
    #
    # Pero SÍ permite:
    #
    # A -> B [import]
    # A -> B [reference]

    key = (
        source_id,
        target_id,
        relation_type
    )


    if key in seen:
        return


    seen.add(key)


    edges.append({
        "source": source_id,
        "target": target_id,
        "type": relation_type
    })


# =========================================================
# NORMALIZAR REFERENCIAS
# =========================================================

def normalize_reference(value):

    value = str(
        value or ""
    ).strip()


    if not value:
        return ""


    value = value.strip(
        "\"'`"
    )


    value = value.replace(
        "\\",
        "/"
    )


    value = value.rstrip(
        "),;]}"
    )


    if value.startswith(
        "file://"
    ):

        value = value[7:]


    return value


# =========================================================
# RESOLVER REFERENCIA A ARCHIVO
# =========================================================

def resolve_reference(
    value,
    indexes
):

    ref = normalize_reference(
        value
    )


    if not ref:
        return []


    results = []

    used_ids = set()


    def push(node):

        if not node:
            return


        if node["id"] in used_ids:
            return


        used_ids.add(
            node["id"]
        )


        results.append(
            node
        )


    by_name = indexes[
        "by_name"
    ]

    by_id = indexes[
        "by_id"
    ]

    by_abs = indexes[
        "by_abs"
    ]


    # -----------------------------------------------------
    # 1. Ruta absoluta
    # -----------------------------------------------------

    if ref in by_abs:

        push(
            by_abs[ref]
        )


    # -----------------------------------------------------
    # 2. Convertir posibles rutas a ruta relativa
    # -----------------------------------------------------

    relative = ref


    root_text = str(
        PROJECT_ROOT
    ).replace(
        "\\",
        "/"
    )


    # /home/pi/robot_custom/api/main_menu.py

    if relative.startswith(
        root_text + "/"
    ):

        relative = relative[
            len(root_text) + 1:
        ]


    # ~/robot_custom/api/main_menu.py

    if relative.startswith(
        "~/robot_custom/"
    ):

        relative = relative[
            len("~/robot_custom/"):
        ]


    # cualquier/cosa/robot_custom/api/main_menu.py

    if "/robot_custom/" in relative:

        relative = relative.split(
            "/robot_custom/",
            1
        )[1]


    relative = relative.lstrip(
        "./"
    )


    if relative in by_id:

        push(
            by_id[relative]
        )


    # -----------------------------------------------------
    # 3. Nombre simple
    # -----------------------------------------------------

    name = Path(
        ref
    ).name


    if name in by_name:

        for node in by_name[name]:

            push(
                node
            )


    return results


# =========================================================
# RESOLVER IMPORT DE PYTHON
# =========================================================

def resolve_module(
    module_name,
    indexes
):

    module_name = str(
        module_name or ""
    ).strip()


    if not module_name:
        return []


    # import modulo as alias

    module_name = module_name.split(
        " as ",
        1
    )[0].strip()


    module_name = module_name.lstrip(
        "."
    )


    if not module_name:
        return []


    results = []

    used_ids = set()


    def push(node):

        if not node:
            return


        if node["id"] in used_ids:
            return


        used_ids.add(
            node["id"]
        )


        results.append(
            node
        )


    by_name = indexes[
        "by_name"
    ]

    by_id = indexes[
        "by_id"
    ]


    # -----------------------------------------------------
    # Ejemplo:
    #
    # dashboard_pc_src.sf_motor_inferencia
    #
    # se convierte en:
    #
    # dashboard_pc_src/sf_motor_inferencia.py
    # -----------------------------------------------------

    module_path = (
        module_name.replace(
            ".",
            "/"
        )
        +
        ".py"
    )


    if module_path in by_id:

        push(
            by_id[module_path]
        )


    # También buscar rutas que TERMINEN en ese módulo.
    #
    # Por ejemplo:
    #
    # api/dashboard_pc_src/sf_motor_inferencia.py

    suffix = (
        "/" +
        module_path
    )


    for node_id, node in by_id.items():

        if node_id.endswith(
            suffix
        ):

            push(
                node
            )


    # -----------------------------------------------------
    # Fallback por nombre
    # -----------------------------------------------------

    filename = (
        module_name
        .split(".")[-1]
        +
        ".py"
    )


    if filename in by_name:

        for node in by_name[
            filename
        ]:

            push(
                node
            )


    return results


# =========================================================
# DETECTAR NOMBRE DE ARCHIVO EN TEXTO
# =========================================================

def filename_mentioned(
    text,
    filename
):

    """
    Evita falsos positivos simples.

    Por ejemplo:

        app.py

    no debe coincidir accidentalmente con:

        sf_app.py
    """


    pattern = (
        r'(?<![A-Za-z0-9_.-])'
        +
        re.escape(
            filename
        )
        +
        r'(?![A-Za-z0-9_.-])'
    )


    return (
        re.search(
            pattern,
            text
        )
        is not None
    )


# =========================================================
# DETECTAR RELACIONES
# =========================================================

def detect_relations(
    node,
    indexes
):

    edges = []

    seen = set()


    path = Path(
        node["path"]
    )


    # Modelos .pt / .onnx aparecen como nodos,
    # pero no intentamos leerlos como texto.

    if node["ext"] not in TEXT_EXT:

        return edges


    try:

        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception:

        return edges


    source_id = node[
        "id"
    ]


    # =====================================================
    # 1. IMPORT PYTHON
    #
    # import safevision
    # import os, sys
    # import modulo as alias
    # =====================================================

    imports = re.findall(
        r'^\s*import\s+([A-Za-z0-9_., \t]+)',
        text,
        re.MULTILINE
    )


    for block in imports:

        for module in block.split(
            ","
        ):

            module = module.strip()


            if not module:
                continue


            for target in resolve_module(
                module,
                indexes
            ):

                add_edge(
                    edges,
                    seen,
                    source_id,
                    target["id"],
                    "import"
                )


    # =====================================================
    # 2. FROM ... IMPORT ...
    #
    # from utils import pausar
    # from dashboard.modulo import Clase
    # =====================================================

    from_imports = re.findall(
        r'^\s*from\s+([A-Za-z0-9_.]+)\s+import\b',
        text,
        re.MULTILINE
    )


    for module in from_imports:

        for target in resolve_module(
            module,
            indexes
        ):

            add_edge(
                edges,
                seen,
                source_id,
                target["id"],
                "from"
            )


    # =====================================================
    # 3. OPEN()
    #
    # open("config.json")
    # open("/home/pi/robot_custom/config.json")
    # =====================================================

    opened_files = re.findall(
        r'open\s*\(\s*(?:r|u|b|f|fr|rf|br|rb)?["\']([^"\']+)["\']',
        text
    )


    for reference in opened_files:

        for target in resolve_reference(
            reference,
            indexes
        ):

            add_edge(
                edges,
                seen,
                source_id,
                target["id"],
                "open"
            )


    # =====================================================
    # 4. EJECUCIÓN DIRECTA
    #
    # python archivo.py
    # python3 archivo.py
    # bash archivo.sh
    # sh archivo.sh
    # source archivo.sh
    # =====================================================

    command_refs = re.findall(
        r'(?<![A-Za-z0-9_])'
        r'(?:python3?|bash|sh|source)\s+'
        r'["\']?'
        r'([^"\'\s;&|]+?\.(?:py|sh|bat|ps1))'
        r'(?=["\'\s;&|]|$)',
        text,
        re.IGNORECASE
    )


    for reference in command_refs:

        for target in resolve_reference(
            reference,
            indexes
        ):

            add_edge(
                edges,
                seen,
                source_id,
                target["id"],
                "execute"
            )


    # =====================================================
    # 5. os.system / subprocess
    #
    # os.system("python3 script.py")
    #
    # subprocess.run("python3 script.py", ...)
    #
    # subprocess.Popen("bash script.sh", ...)
    # =====================================================

    command_strings = re.findall(
        r'(?:os\.system|subprocess\.(?:run|Popen|call|check_call|check_output))'
        r'\s*\(\s*(?:f|r|u|b|fr|rf|br|rb)?["\']([^"\']+)["\']',
        text
    )


    for command_text in command_strings:

        for target_name, target_nodes in indexes[
            "by_name"
        ].items():

            if filename_mentioned(
                command_text,
                target_name
            ):

                for target in target_nodes:

                    add_edge(
                        edges,
                        seen,
                        source_id,
                        target["id"],
                        "execute"
                    )


    # =====================================================
    # 6. ARCHIVOS CONSOLIDADOS
    #
    # Especialmente útil para:
    #
    # codigo_proyecto.txt
    #
    # Detecta:
    #
    # 📄 ARCHIVO: /home/pi/robot_custom/api/main_menu.py
    #
    # ARCHIVO: api/main_menu.py
    #
    # y crea:
    #
    # codigo_proyecto.txt
    #       |
    #       +---- contains ---> main_menu.py
    # =====================================================

    exported_headers = re.findall(
        r'^\s*(?:📄\s*)?ARCHIVO:\s*(.+?)\s*$',
        text,
        re.MULTILINE
    )


    for reference in exported_headers:

        for target in resolve_reference(
            reference,
            indexes
        ):

            add_edge(
                edges,
                seen,
                source_id,
                target["id"],
                "contains"
            )


    # =====================================================
    # 7. REFERENCIAS GENERALES
    #
    # Busca las cuatro formas:
    #
    # main_menu.py
    #
    # api/main_menu.py
    #
    # /home/pi/robot_custom/api/main_menu.py
    #
    # ~/robot_custom/api/main_menu.py
    # =====================================================

    for target in indexes[
        "by_id"
    ].values():


        if target["id"] == source_id:
            continue


        target_id = target[
            "id"
        ].replace(
            "\\",
            "/"
        )


        target_path = target[
            "path"
        ].replace(
            "\\",
            "/"
        )


        target_name = target[
            "name"
        ]


        explicit_paths = (

            target_id,

            target_path,

            (
                "~/robot_custom/"
                +
                target_id
            ),

            (
                "robot_custom/"
                +
                target_id
            )
        )


        matched = any(

            reference in text

            for reference
            in explicit_paths

        )


        # Si no encontramos la ruta,
        # buscar el nombre exacto.

        if not matched:

            matched = filename_mentioned(
                text,
                target_name
            )


        if matched:

            add_edge(
                edges,
                seen,
                source_id,
                target["id"],
                "reference"
            )


    return edges


# =========================================================
# ESCANEAR PROYECTO
# =========================================================

def scan_project():

    nodes = []


    for path in PROJECT_ROOT.rglob(
        "*"
    ):


        if not path.is_file():
            continue


        if any(

            part in IGNORE_DIRS

            for part
            in path.parts

        ):

            continue


        if (
            path.suffix.lower()
            not in VALID_EXT
        ):

            continue


        try:

            stat = path.stat()

        except Exception:

            continue


        nodes.append({

            "id":
                str(
                    path.relative_to(
                        PROJECT_ROOT
                    )
                ).replace(
                    "\\",
                    "/"
                ),

            "name":
                path.name,

            "path":
                str(path),

            "ext":
                path.suffix.lower(),

            "size":
                stat.st_size,

            "modified":
                datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        })


    nodes.sort(
        key=lambda x:
            x["id"]
    )


    indexes = build_indexes(
        nodes
    )


    edges = []


    for node in nodes:

        edges.extend(

            detect_relations(
                node,
                indexes
            )

        )


    return {
        "nodes": nodes,
        "edges": edges
    }


# =========================================================
# PRUEBA DESDE TERMINAL
# =========================================================

if __name__ == "__main__":

    graph = scan_project()


    print()

    print(
        "=" * 60
    )

    print(
        " SCANNER DE RELACIONES - ROBOT_CUSTOM"
    )

    print(
        "=" * 60
    )

    print()


    print(
        "Archivos    :",
        len(
            graph["nodes"]
        )
    )


    print(
        "Relaciones  :",
        len(
            graph["edges"]
        )
    )


    print()


    counts = Counter(

        edge["type"]

        for edge
        in graph["edges"]

    )


    print(
        "Relaciones por tipo:"
    )

    print(
        "-" * 35
    )


    for relation_type, amount in sorted(

        counts.items(),

        key=lambda item: (
            -item[1],
            item[0]
        )

    ):

        print(

            "{:<12} {}".format(

                relation_type,
                amount

            )

        )


    print()

    print(
        "=" * 60
    )
