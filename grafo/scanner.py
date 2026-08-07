from pathlib import Path
from datetime import datetime
import re

PROJECT_ROOT = Path.home() / "robot_custom"

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "grafo",
    "node_modules"
}

# Extensiones que queremos visualizar
VALID_EXT = {
    ".py",".sh",".bat",".ps1",".js",".html",".css",
    ".json",".yaml",".yml",".txt",".cfg",".ini",
    ".pt",".torchscript",".onnx"
}


def build_index(nodes):
    """
    Crea un índice:
    robot.py -> nodo
    """
    index = {}

    for node in nodes:
        index[node["name"]] = node

    return index


def detect_relations(node, index):

    edges = []

    path = Path(node["path"])

    try:
        text = path.read_text(errors="ignore")
    except:
        return edges

    # ----------------------------
    # import xxx
    # ----------------------------

    for m in re.findall(r'^\s*import\s+([a-zA-Z0-9_, ]+)', text, re.MULTILINE):

        mods = [x.strip() for x in m.split(",")]

        for mod in mods:

            filename = mod.split(".")[0] + ".py"

            if filename in index:

                edges.append({
                    "source":node["id"],
                    "target":index[filename]["id"],
                    "type":"import"
                })

    # ----------------------------
    # from xxx import
    # ----------------------------

    for mod in re.findall(r'^\s*from\s+([a-zA-Z0-9_.]+)', text, re.MULTILINE):

        filename = mod.split(".")[0] + ".py"

        if filename in index:

            edges.append({
                "source":node["id"],
                "target":index[filename]["id"],
                "type":"from"
            })

    # ----------------------------
    # open("archivo")
    # ----------------------------

    for f in re.findall(r'open\s*\(\s*["\']([^"\']+)', text):

        name = Path(f).name

        if name in index:

            edges.append({
                "source":node["id"],
                "target":index[name]["id"],
                "type":"open"
            })

    # ----------------------------
    # Referencias por nombre
    # ----------------------------

    for filename in index:

        if filename == node["name"]:
            continue

        if filename in text:

            edges.append({
                "source":node["id"],
                "target":index[filename]["id"],
                "type":"reference"
            })

    return edges


def scan_project():

    nodes = []

    for path in PROJECT_ROOT.rglob("*"):

        if not path.is_file():
            continue

        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        if path.suffix.lower() not in VALID_EXT:
            continue

        try:
            stat = path.stat()
        except:
            continue

        nodes.append({

            "id":str(path.relative_to(PROJECT_ROOT)),

            "name":path.name,

            "path":str(path),

            "ext":path.suffix.lower(),

            "size":stat.st_size,

            "modified":datetime.fromtimestamp(
                stat.st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S")
        })

    nodes.sort(key=lambda x:x["id"])

    index = build_index(nodes)

    edges = []

    for node in nodes:

        edges.extend(detect_relations(node,index))

    return {

        "nodes":nodes,

        "edges":edges

    }


if __name__ == "__main__":

    g = scan_project()

    print()

    print("Archivos :",len(g["nodes"]))

    print("Relaciones :",len(g["edges"]))

    print()

    for e in g["edges"][:30]:

        print(e)
