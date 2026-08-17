#!/usr/bin/env python3

import os
import signal
import subprocess
import threading
import time
from pathlib import Path

import rospy
from std_srvs.srv import SetBool


# =========================================================
# SAFEVISION - GESTOR DE MAPEO 2D
# =========================================================

LOCK = threading.Lock()
OPERATION_LOCK = threading.Lock()

ROBOT_DIR = Path(__file__).resolve().parent

GMAPPING_LAUNCH = (
    ROBOT_DIR
    /
    "sf_mapeo_gmapping.launch"
)

RESTORE_LAUNCH = (
    ROBOT_DIR
    /
    "sf_localizacion_mapa.launch"
)

MAPS_DIR = None
CANCEL_NAVIGATION = None

GMAPPING_PROCESS = None
RESTORE_PROCESS = None

STATE = {
    "state": "idle",
    "mapping": False,
    "name": None,
    "restore_map": None,
    "started_at": None,
    "message": "Mapeo detenido",
}


def configure(
    maps_dir,
    cancel_navigation
):
    global MAPS_DIR
    global CANCEL_NAVIGATION

    MAPS_DIR = Path(
        maps_dir
    )

    CANCEL_NAVIGATION = (
        cancel_navigation
    )


def _set_state(
    **values
):
    with LOCK:
        STATE.update(
            values
        )


def _run(
    command,
    timeout=4
):
    try:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout
        )

    except Exception:
        return None


def _ros_nodes():

    result = _run(
        [
            "rosnode",
            "list",
        ],
        timeout=3
    )

    if (
        result is None
        or
        result.returncode != 0
    ):
        return set()

    return {
        line.strip()
        for line
        in result.stdout.splitlines()
        if line.strip()
    }


def _node_exists(
    name
):
    return (
        name
        in
        _ros_nodes()
    )


def _wait_node(
    name,
    expected,
    timeout=8.0
):
    deadline = (
        time.time()
        +
        timeout
    )

    while time.time() < deadline:

        exists = _node_exists(
            name
        )

        if exists == expected:
            return True

        time.sleep(
            0.20
        )

    return False


def _map_has_publisher(
    expected
):
    result = _run(
        [
            "rostopic",
            "info",
            "/map",
        ],
        timeout=3
    )

    if (
        result is None
        or
        result.returncode != 0
    ):
        return False

    return (
        expected
        in
        result.stdout
    )


def _wait_map_publisher(
    expected,
    timeout=10.0
):
    deadline = (
        time.time()
        +
        timeout
    )

    while time.time() < deadline:

        if _map_has_publisher(
            expected
        ):
            return True

        time.sleep(
            0.20
        )

    return False


def _name_valid(
    name
):
    if not isinstance(
        name,
        str
    ):
        return False

    name = name.strip()

    if (
        not name
        or
        len(name) > 80
    ):
        return False

    if (
        "/" in name
        or
        "\\" in name
        or
        ".." in name
        or
        name.startswith(".")
    ):
        return False

    return True


def _current_map():

    result = _run(
        [
            "rosnode",
            "info",
            "/sf_map_server",
        ],
        timeout=3
    )

    if (
        result is None
        or
        result.returncode != 0
    ):
        return None

    node_pid = None

    for line in result.stdout.splitlines():

        if not line.startswith(
            "Pid:"
        ):
            continue

        try:
            node_pid = int(
                line.split(
                    ":",
                    1
                )[1].strip()
            )

        except Exception:
            node_pid = None

        break

    if node_pid is None:
        return None

    cmdline = Path(
        "/proc/{}/cmdline".format(
            node_pid
        )
    )

    try:
        args = [
            item
            for item
            in cmdline.read_bytes().split(
                b"\0"
            )
            if item
        ]

    except Exception:
        return None

    for raw in args:

        try:
            value = raw.decode(
                "utf-8"
            )

        except Exception:
            continue

        if not value.endswith(
            ".yaml"
        ):
            continue

        candidate = Path(
            value
        )

        if candidate.exists():
            return candidate

    return None


def _core_status():

    nodes = _ros_nodes()

    required = [
        "/rplidarNode",
        "/ekf_localization",
        "/odometry_publisher",
    ]

    missing = [
        name
        for name
        in required
        if name not in nodes
    ]

    return {
        "ok": not missing,
        "missing": missing,
    }


def _start_process(
    launch_path,
    extra_args=None
):
    if not launch_path.exists():
        raise RuntimeError(
            "Launch no encontrado: {}"
            .format(launch_path)
        )

    command = [
        "roslaunch",
        str(
            launch_path
        ),
    ]

    if extra_args:
        command.extend(
            extra_args
        )

    return subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )


def _stop_process(
    process
):
    if process is None:
        return

    if process.poll() is not None:
        return

    try:
        os.killpg(
            os.getpgid(
                process.pid
            ),
            signal.SIGINT
        )

        process.wait(
            timeout=5
        )

        return

    except Exception:
        pass

    try:
        os.killpg(
            os.getpgid(
                process.pid
            ),
            signal.SIGTERM
        )

        process.wait(
            timeout=3
        )

    except Exception:
        pass


def status():

    with LOCK:
        result = dict(
            STATE
        )

    result["configured"] = (
        MAPS_DIR is not None
        and
        CANCEL_NAVIGATION is not None
    )

    result["slam_gmapping"] = (
        _node_exists(
            "/slam_gmapping"
        )
    )

    result["map_server"] = (
        _node_exists(
            "/sf_map_server"
        )
    )

    result["amcl"] = (
        _node_exists(
            "/amcl"
        )
    )

    result["map_from_gmapping"] = (
        _map_has_publisher(
            "/slam_gmapping"
        )
    )

    result["map_from_server"] = (
        _map_has_publisher(
            "/sf_map_server"
        )
    )

    result["core"] = (
        _core_status()
    )

    current_map = (
        _current_map()
    )

    result["current_map"] = (
        str(current_map)
        if current_map is not None
        else None
    )

    return result
