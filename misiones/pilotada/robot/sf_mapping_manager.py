#!/usr/bin/env python3

import os
import signal
import subprocess
import threading
import time
import xmlrpc.client
from pathlib import Path

import rosgraph
import rosnode
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

NORMALIZE_MAP_NAME = None
MAP_NAME_OCCUPIED = None
MAP_COMPLETE = None
MAP_PATHS = None

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
    cancel_navigation,
    normalize_map_name,
    map_name_occupied,
    map_complete,
    map_paths
):
    global MAPS_DIR
    global CANCEL_NAVIGATION
    global NORMALIZE_MAP_NAME
    global MAP_NAME_OCCUPIED
    global MAP_COMPLETE
    global MAP_PATHS

    MAPS_DIR = Path(
        maps_dir
    )

    CANCEL_NAVIGATION = (
        cancel_navigation
    )

    NORMALIZE_MAP_NAME = (
        normalize_map_name
    )

    MAP_NAME_OCCUPIED = (
        map_name_occupied
    )

    MAP_COMPLETE = (
        map_complete
    )

    MAP_PATHS = (
        map_paths
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


def _current_map_direct(
    master
):
    if master is None:
        return None

    try:
        uri = rosnode.get_api_uri(
            master,
            "/sf_map_server",
            skip_cache=True
        )

    except Exception:
        return None

    if not uri:
        return None

    try:
        proxy = xmlrpc.client.ServerProxy(
            uri
        )

        code, _message, node_pid = (
            proxy.getPid(
                "/safevision_mapping_manager"
            )
        )

        if code != 1:
            return None

        node_pid = int(
            node_pid
        )

    except Exception:
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
        and
        NORMALIZE_MAP_NAME is not None
        and
        MAP_NAME_OCCUPIED is not None
        and
        MAP_COMPLETE is not None
        and
        MAP_PATHS is not None
    )

    nodes = set()
    map_publishers = []
    master = None

    try:
        master = rosgraph.Master(
            "/safevision_mapping_manager"
        )

        nodes = set(
            rosnode.get_node_names()
        )

        system_state = (
            master.getSystemState()
        )

        for topic, publishers in system_state[0]:
            if topic == "/map":
                map_publishers = list(
                    publishers
                )
                break

    except Exception:
        nodes = set()
        map_publishers = []

    result["slam_gmapping"] = (
        "/slam_gmapping"
        in nodes
    )

    result["map_server"] = (
        "/sf_map_server"
        in nodes
    )

    result["amcl"] = (
        "/amcl"
        in nodes
    )

    required = [
        "/rplidarNode",
        "/ekf_localization",
        "/odometry_publisher",
    ]

    missing = [
        name
        for name in required
        if name not in nodes
    ]

    result["core"] = {
        "ok": not missing,
        "missing": missing,
    }

    result["map_from_gmapping"] = (
        "/slam_gmapping"
        in map_publishers
    )

    result["map_from_server"] = (
        "/sf_map_server"
        in map_publishers
    )

    current_map = None

    if result["map_server"]:
        current_map = (
            _current_map_direct(
                master
            )
        )

    result["current_map"] = (
        str(current_map)
        if current_map is not None
        else None
    )

    return result


# =========================================================
# HELPERS DE TRANSICION ROS
# =========================================================

def _kill_node(
    name
):
    if not _node_exists(
        name
    ):
        return True

    result = _run(
        [
            "rosnode",
            "kill",
            name,
        ],
        timeout=5
    )

    if result is None:
        return False

    return _wait_node(
        name,
        False,
        timeout=5.0
    )


def _force_manual():

    if CANCEL_NAVIGATION is None:
        raise RuntimeError(
            "Gestor de mapeo no configurado"
        )

    try:
        cancelled = (
            CANCEL_NAVIGATION()
        )

        if cancelled is False:
            raise RuntimeError(
                "Cola de navegación no disponible"
            )

    except Exception as exc:
        raise RuntimeError(
            "No se pudo cancelar navegación: {}"
            .format(exc)
        )

    try:
        rospy.wait_for_service(
            "/safevision/set_navigation_mode",
            timeout=2.0
        )

        service = rospy.ServiceProxy(
            "/safevision/set_navigation_mode",
            SetBool
        )

        response = service(
            False
        )

        if not response.success:
            raise RuntimeError(
                response.message
                or
                "Selector rechazó modo manual"
            )

    except Exception as exc:
        raise RuntimeError(
            "No se pudo forzar modo manual: {}"
            .format(exc)
        )


def _stop_restore_process():
    global RESTORE_PROCESS

    _stop_process(
        RESTORE_PROCESS
    )

    RESTORE_PROCESS = None


def _stop_gmapping():
    global GMAPPING_PROCESS

    _stop_process(
        GMAPPING_PROCESS
    )

    GMAPPING_PROCESS = None

    if _node_exists(
        "/slam_gmapping"
    ):
        _kill_node(
            "/slam_gmapping"
        )

    return _wait_node(
        "/slam_gmapping",
        False,
        timeout=5.0
    )


# =========================================================
# RESTAURACION MAP_SERVER + AMCL
# =========================================================

def _restore_localization(
    map_path
):
    global RESTORE_PROCESS

    map_path = Path(
        map_path
    )

    if not map_path.exists():
        raise RuntimeError(
            "Mapa de retorno no encontrado: {}"
            .format(map_path)
        )

    if not map_path.is_file():
        raise RuntimeError(
            "Mapa de retorno inválido: {}"
            .format(map_path)
        )

    if map_path.suffix.lower() != ".yaml":
        raise RuntimeError(
            "El mapa de retorno debe ser YAML"
        )

    if _node_exists(
        "/slam_gmapping"
    ):
        raise RuntimeError(
            "No se puede restaurar mientras Gmapping siga activo"
        )

    core = _core_status()

    if not core["ok"]:
        raise RuntimeError(
            "Núcleo ROS incompleto: {}"
            .format(
                ", ".join(
                    core["missing"]
                )
            )
        )

    # Evita mantener un roslaunch de restauración
    # anterior antes de crear uno nuevo.
    _stop_restore_process()

    # Dejamos una pareja limpia para evitar duplicados
    # si una transición anterior quedó a medias.
    if not _kill_node(
        "/amcl"
    ):
        raise RuntimeError(
            "No se pudo limpiar AMCL antes de restaurar"
        )

    if not _kill_node(
        "/sf_map_server"
    ):
        raise RuntimeError(
            "No se pudo limpiar sf_map_server antes de restaurar"
        )

    try:
        RESTORE_PROCESS = _start_process(
            RESTORE_LAUNCH,
            [
                "map_file:={}".format(
                    map_path
                )
            ]
        )

        if not _wait_node(
            "/sf_map_server",
            True,
            timeout=8.0
        ):
            raise RuntimeError(
                "sf_map_server no volvió a iniciar"
            )

        if not _wait_node(
            "/amcl",
            True,
            timeout=8.0
        ):
            raise RuntimeError(
                "AMCL no volvió a iniciar"
            )

        if not _wait_map_publisher(
            "/sf_map_server",
            timeout=8.0
        ):
            raise RuntimeError(
                "sf_map_server no recuperó /map"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Núcleo ROS incompleto después de restaurar: {}"
                .format(
                    ", ".join(
                        core["missing"]
                    )
                )
            )

        return True

    except Exception:

        _stop_restore_process()

        _kill_node(
            "/amcl"
        )

        _kill_node(
            "/sf_map_server"
        )

        raise



# =========================================================
# INICIO DE SESION DE MAPEO
# =========================================================

def start(name):
    global GMAPPING_PROCESS

    if not OPERATION_LOCK.acquire(
        blocking=False
    ):
        return {
            "ok": False,
            "error": "Hay otra operación de mapeo en curso",
        }

    restore_map = None
    localization_touched = False
    gmapping_started = False

    try:
        if (
            MAPS_DIR is None
            or CANCEL_NAVIGATION is None
            or NORMALIZE_MAP_NAME is None
            or MAP_NAME_OCCUPIED is None
            or MAP_COMPLETE is None
            or MAP_PATHS is None
        ):
            raise RuntimeError(
                "Gestor de mapeo no configurado"
            )

        name = NORMALIZE_MAP_NAME(
            name
        )

        if name is None:
            raise RuntimeError(
                "Nombre de mapa inválido"
            )

        with LOCK:
            if STATE.get("mapping"):
                raise RuntimeError(
                    "Ya existe una sesión activa"
                )

        occupied = MAP_NAME_OCCUPIED(
            name
        )

        if occupied is not None:
            raise RuntimeError(
                "Ya existe un mapa con ese nombre: {}"
                .format(
                    occupied
                )
            )

        yaml_path, pgm_path = (
            MAP_PATHS(
                name
            )
        )

        if (
            yaml_path.exists()
            or
            pgm_path.exists()
        ):
            raise RuntimeError(
                "Ya existe un archivo para ese mapa"
            )

        if _node_exists("/slam_gmapping"):
            raise RuntimeError(
                "slam_gmapping ya está activo"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Núcleo ROS incompleto: {}".format(
                    ", ".join(core["missing"])
                )
            )

        if not _node_exists("/sf_map_server"):
            raise RuntimeError(
                "sf_map_server no está activo"
            )

        if not _node_exists("/amcl"):
            raise RuntimeError(
                "AMCL no está activo"
            )

        if not _map_has_publisher(
            "/sf_map_server"
        ):
            raise RuntimeError(
                "sf_map_server no controla /map"
            )

        restore_map = _current_map()

        if restore_map is None:
            raise RuntimeError(
                "No se pudo identificar el mapa activo"
            )

        _set_state(
            state="starting",
            mapping=False,
            name=name,
            restore_map=str(restore_map),
            started_at=time.time(),
            message="Preparando Gmapping",
        )

        # Cancela navegación y fuerza MANUAL
        # antes de modificar localización.
        _force_manual()

        localization_touched = True

        # Si venimos de una restauración anterior,
        # cerramos primero su roslaunch.
        _stop_restore_process()

        if not _kill_node("/amcl"):
            raise RuntimeError(
                "No se pudo detener AMCL"
            )

        if not _kill_node("/sf_map_server"):
            raise RuntimeError(
                "No se pudo detener sf_map_server"
            )

        if _node_exists("/amcl"):
            raise RuntimeError(
                "AMCL continúa activo"
            )

        if _node_exists("/sf_map_server"):
            raise RuntimeError(
                "sf_map_server continúa activo"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Núcleo ROS incompleto tras transición: {}".format(
                    ", ".join(core["missing"])
                )
            )

        GMAPPING_PROCESS = _start_process(
            GMAPPING_LAUNCH
        )

        gmapping_started = True

        if not _wait_node(
            "/slam_gmapping",
            True,
            timeout=10.0
        ):
            raise RuntimeError(
                "slam_gmapping no inició"
            )

        if not _wait_map_publisher(
            "/slam_gmapping",
            timeout=10.0
        ):
            raise RuntimeError(
                "Gmapping no tomó control de /map"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Núcleo ROS incompleto con Gmapping: {}".format(
                    ", ".join(core["missing"])
                )
            )

        _set_state(
            state="mapping",
            mapping=True,
            message="Mapeando",
        )

        return {
            "ok": True,
            "mapping": True,
            "name": name,
            "restore_map": restore_map.stem,
        }

    except Exception as exc:
        error = str(exc)
        rollback_errors = []

        if (
            gmapping_started
            or GMAPPING_PROCESS is not None
        ):
            try:
                if not _stop_gmapping():
                    rollback_errors.append(
                        "Gmapping no terminó completamente"
                    )
            except Exception as stop_exc:
                rollback_errors.append(
                    "Error deteniendo Gmapping: {}".format(
                        stop_exc
                    )
                )

        if (
            localization_touched
            and restore_map is not None
        ):
            try:
                _restore_localization(
                    restore_map
                )
            except Exception as restore_exc:
                rollback_errors.append(
                    "Error restaurando localización: {}".format(
                        restore_exc
                    )
                )

        rollback_error = (
            "; ".join(rollback_errors)
            if rollback_errors
            else None
        )

        message = error

        if rollback_error:
            message += (
                " | ROLLBACK: "
                + rollback_error
            )

        _set_state(
            state="error",
            mapping=False,
            message=message,
        )

        return {
            "ok": False,
            "error": error,
            "rollback_ok": not rollback_errors,
            "rollback_error": rollback_error,
        }

    finally:
        OPERATION_LOCK.release()



# =========================================================
# DESCARTAR SESION DE MAPEO
# =========================================================

def discard():

    if not OPERATION_LOCK.acquire(
        blocking=False
    ):
        return {
            "ok": False,
            "error": (
                "Hay otra operación de mapeo en curso"
            ),
        }

    try:
        with LOCK:
            mapping = bool(
                STATE.get("mapping")
            )

            name = STATE.get(
                "name"
            )

            restore_value = STATE.get(
                "restore_map"
            )

        with LOCK:
            state = STATE.get(
                "state"
            )

        recoverable = (
            mapping
            or
            (
                state == "error"
                and restore_value
            )
        )

        if not recoverable:
            raise RuntimeError(
                "No hay una sesión de mapeo activa"
            )

        if not restore_value:
            raise RuntimeError(
                "La sesión no tiene mapa de retorno"
            )

        restore_map = Path(
            restore_value
        )

        _set_state(
            state="stopping",
            mapping=True,
            message="Descartando mapa",
        )

        if not _stop_gmapping():
            raise RuntimeError(
                "No se pudo detener Gmapping completamente"
            )

        if _node_exists(
            "/slam_gmapping"
        ):
            raise RuntimeError(
                "slam_gmapping continúa activo"
            )

        _restore_localization(
            restore_map
        )

        if not _node_exists(
            "/sf_map_server"
        ):
            raise RuntimeError(
                "sf_map_server no quedó activo"
            )

        if not _node_exists(
            "/amcl"
        ):
            raise RuntimeError(
                "AMCL no quedó activo"
            )

        if not _map_has_publisher(
            "/sf_map_server"
        ):
            raise RuntimeError(
                "sf_map_server no recuperó /map"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Núcleo ROS incompleto tras descartar: {}".format(
                    ", ".join(
                        core["missing"]
                    )
                )
            )

        restored_name = (
            restore_map.stem
        )

        _set_state(
            state="idle",
            mapping=False,
            name=None,
            restore_map=None,
            started_at=None,
            message="Mapeo detenido",
        )

        return {
            "ok": True,
            "mapping": False,
            "discarded": name,
            "restored_map": restored_name,
        }

    except Exception as exc:

        error = str(
            exc
        )

        _set_state(
            state="error",
            mapping=_node_exists(
                "/slam_gmapping"
            ),
            message=error,
        )

        return {
            "ok": False,
            "error": error,
        }

    finally:
        OPERATION_LOCK.release()



# =========================================================
# GUARDAR SESION DE MAPEO
# =========================================================

def save():

    if not OPERATION_LOCK.acquire(
        blocking=False
    ):
        return {
            "ok": False,
            "error": (
                "Hay otra operación de mapeo en curso"
            ),
        }

    yaml_path = None
    pgm_path = None
    saved_pair = False
    original_restore = None
    name = None

    try:
        if (
            MAPS_DIR is None
            or NORMALIZE_MAP_NAME is None
            or MAP_NAME_OCCUPIED is None
            or MAP_COMPLETE is None
            or MAP_PATHS is None
        ):
            raise RuntimeError(
                "Gestor de mapeo no configurado"
            )

        with LOCK:
            mapping = bool(
                STATE.get("mapping")
            )

            name = STATE.get(
                "name"
            )

            original_restore = STATE.get(
                "restore_map"
            )

        if not mapping:
            raise RuntimeError(
                "No hay una sesión de mapeo activa"
            )

        name = NORMALIZE_MAP_NAME(
            name
        )

        if name is None:
            raise RuntimeError(
                "La sesión tiene un nombre de mapa inválido"
            )

        if not _node_exists(
            "/slam_gmapping"
        ):
            raise RuntimeError(
                "slam_gmapping no está activo"
            )

        if not _map_has_publisher(
            "/slam_gmapping"
        ):
            raise RuntimeError(
                "Gmapping no controla /map"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Núcleo ROS incompleto: {}".format(
                    ", ".join(
                        core["missing"]
                    )
                )
            )

        occupied = MAP_NAME_OCCUPIED(
            name
        )

        if occupied is not None:
            raise RuntimeError(
                "Ya existe un mapa con ese nombre: {}"
                .format(
                    occupied
                )
            )

        yaml_path, pgm_path = (
            MAP_PATHS(
                name
            )
        )

        if (
            yaml_path.exists()
            or pgm_path.exists()
        ):
            raise RuntimeError(
                "Ya existe un archivo para ese mapa"
            )

        MAPS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        map_saver = Path(
            "/opt/ros/melodic/lib/map_server/map_saver"
        )

        if not map_saver.is_file():
            raise RuntimeError(
                "map_saver no está disponible"
            )

        prefix = (
            MAPS_DIR
            /
            name
        )

        _set_state(
            state="saving",
            mapping=True,
            message="Guardando mapa",
        )

        result = _run(
            [
                str(
                    map_saver
                ),
                "-f",
                str(
                    prefix
                ),
            ],
            timeout=30
        )

        if (
            result is None
            or result.returncode != 0
        ):
            for candidate in (
                yaml_path,
                pgm_path,
            ):
                try:
                    candidate.unlink()

                except FileNotFoundError:
                    pass

                except Exception:
                    pass

            details = ""

            if result is not None:
                details = (
                    result.stderr
                    or result.stdout
                    or ""
                ).strip()

            if len(details) > 300:
                details = details[-300:]

            if details:
                raise RuntimeError(
                    "map_saver falló: {}"
                    .format(
                        details
                    )
                )

            raise RuntimeError(
                "map_saver falló"
            )

        if not MAP_COMPLETE(
            name
        ):
            for candidate in (
                yaml_path,
                pgm_path,
            ):
                try:
                    candidate.unlink()

                except FileNotFoundError:
                    pass

                except Exception:
                    pass

            raise RuntimeError(
                "map_saver no generó el par YAML + PGM"
            )

        saved_pair = True

        # Desde este punto el mapa ya está persistido.
        # Si falla la transición, restore_map apunta al
        # mapa nuevo para poder reintentar recuperación.
        _set_state(
            state="switching",
            mapping=True,
            restore_map=str(
                yaml_path
            ),
            message=(
                "Mapa guardado; restaurando localización"
            ),
        )

        if not _stop_gmapping():
            raise RuntimeError(
                "El mapa se guardó, pero Gmapping no terminó completamente"
            )

        if _node_exists(
            "/slam_gmapping"
        ):
            raise RuntimeError(
                "El mapa se guardó, pero slam_gmapping continúa activo"
            )

        _restore_localization(
            yaml_path
        )

        if not _node_exists(
            "/sf_map_server"
        ):
            raise RuntimeError(
                "El mapa se guardó, pero sf_map_server no quedó activo"
            )

        if not _node_exists(
            "/amcl"
        ):
            raise RuntimeError(
                "El mapa se guardó, pero AMCL no quedó activo"
            )

        if not _map_has_publisher(
            "/sf_map_server"
        ):
            raise RuntimeError(
                "El mapa se guardó, pero sf_map_server no recuperó /map"
            )

        core = _core_status()

        if not core["ok"]:
            raise RuntimeError(
                "Mapa guardado, pero núcleo ROS incompleto: {}".format(
                    ", ".join(
                        core["missing"]
                    )
                )
            )

        _set_state(
            state="idle",
            mapping=False,
            name=None,
            restore_map=None,
            started_at=None,
            message="Mapeo detenido",
        )

        return {
            "ok": True,
            "mapping": False,
            "saved": name,
            "restored_map": name,
            "yaml": str(
                yaml_path
            ),
            "pgm": str(
                pgm_path
            ),
        }

    except Exception as exc:

        error = str(
            exc
        )

        gmapping_live = _node_exists(
            "/slam_gmapping"
        )

        if saved_pair:
            restore_value = (
                str(yaml_path)
                if yaml_path is not None
                else original_restore
            )

        else:
            restore_value = (
                original_restore
            )

        _set_state(
            state="error",
            mapping=gmapping_live,
            restore_map=restore_value,
            message=error,
        )

        return {
            "ok": False,
            "error": error,
            "mapping": gmapping_live,
            "saved": saved_pair,
            "name": name,
        }

    finally:
        OPERATION_LOCK.release()



# =========================================================
# CIERRE DEL GESTOR
# Solo procesos roslaunch creados por este modulo.
# No mata nodos ROS por nombre.
# =========================================================

def _signal_owned_process(
    process,
    sig
):
    if process is None:
        return False

    if process.poll() is not None:
        return False

    try:
        os.killpg(
            os.getpgid(
                process.pid
            ),
            sig
        )

        return True

    except Exception:
        return False


def _wait_owned_processes(
    processes,
    timeout
):
    deadline = (
        time.time()
        +
        float(timeout)
    )

    while time.time() < deadline:

        alive = [
            process
            for process in processes
            if (
                process is not None
                and
                process.poll() is None
            )
        ]

        if not alive:
            return True

        time.sleep(
            0.05
        )

    return not any(
        process is not None
        and process.poll() is None
        for process in processes
    )


def shutdown():
    global GMAPPING_PROCESS
    global RESTORE_PROCESS

    processes = []

    for process in (
        GMAPPING_PROCESS,
        RESTORE_PROCESS,
    ):
        if process is None:
            continue

        if any(
            existing.pid == process.pid
            for existing in processes
        ):
            continue

        processes.append(
            process
        )

    # Desde este punto el gestor deja de considerar
    # estos procesos como disponibles para operaciones.
    GMAPPING_PROCESS = None
    RESTORE_PROCESS = None

    if not processes:
        return {
            "ok": True,
            "stopped": 0,
        }

    # Primera oportunidad: cierre ROS normal.
    for process in processes:
        _signal_owned_process(
            process,
            signal.SIGINT
        )

    _wait_owned_processes(
        processes,
        timeout=1.0
    )

    remaining = [
        process
        for process in processes
        if process.poll() is None
    ]

    # Segunda oportunidad: terminar el roslaunch.
    for process in remaining:
        _signal_owned_process(
            process,
            signal.SIGTERM
        )

    _wait_owned_processes(
        remaining,
        timeout=0.4
    )

    remaining = [
        process
        for process in remaining
        if process.poll() is None
    ]

    # Ultimo recurso durante cierre general de Pilotada.
    for process in remaining:
        _signal_owned_process(
            process,
            signal.SIGKILL
        )

    _wait_owned_processes(
        remaining,
        timeout=0.2
    )

    alive = [
        process.pid
        for process in processes
        if process.poll() is None
    ]

    return {
        "ok": not alive,
        "stopped": (
            len(processes)
            -
            len(alive)
        ),
        "alive": alive,
    }
