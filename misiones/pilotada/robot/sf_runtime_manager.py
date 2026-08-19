#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shlex
import signal
import socket
import subprocess
import threading
import time
import xmlrpc.client
from pathlib import Path

ROOT = Path("/home/pi/robot_custom")
ROBOT_DIR = ROOT / "misiones" / "pilotada" / "robot"
LOG_DIR = Path(
    "/tmp/safevision_runtime_logs"
)

MAPS_DIR = ROOT / "mapping" / "maps"
ACTIVE_MAP_FILE = Path("/tmp/safevision_active_map.json")
STATE_FILE = Path("/tmp/safevision_runtime_state.json")
_LOCK = threading.RLock()


class TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout=1.5):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host):
        connection = super().make_connection(host)
        connection.timeout = self.timeout
        return connection


def _empty_state():
    return {
        "requested_profile": None,
        "map_name": None,
        "control_mode": None,
        "owned": {},
    }


def _load_state():
    try:
        data = json.loads(STATE_FILE.read_text())
        if not isinstance(data, dict):
            return _empty_state()
        result = _empty_state()
        result.update(data)
        if not isinstance(result.get("owned"), dict):
            result["owned"] = {}
        return result
    except Exception:
        return _empty_state()


def _save_state(state):
    temp = Path(str(STATE_FILE) + ".tmp")
    temp.write_text(json.dumps(state, sort_keys=True))
    temp.replace(STATE_FILE)


def _robot_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _ros_prefix():
    ip = _robot_ip()
    return (
        "source /opt/ros/melodic/setup.bash >/dev/null 2>&1; "
        "source /home/pi/yahboomcar_ws/devel/setup.bash >/dev/null 2>&1; "
        "export ROS_MASTER_URI=" + shlex.quote("http://{}:11311".format(ip)) + "; "
        "export ROS_IP=" + shlex.quote(ip) + "; "
        "export ROBOT_TYPE=X3; "
    )


def _run_ros(command, timeout=8):
    try:
        return subprocess.run(
            ["/bin/bash", "-lc", _ros_prefix() + command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return subprocess.CompletedProcess(command, 99, "", str(exc))


def _master_state():
    try:
        uri = "http://{}:11311".format(_robot_ip())
        master = xmlrpc.client.ServerProxy(
            uri,
            transport=TimeoutTransport(1.5),
            allow_none=True,
        )
        code, _message, state = master.getSystemState("/safevision_runtime_manager")
        if code != 1:
            return False, set(), set(), set()
        publishers, subscribers, services = state
        nodes = set()
        topics = set()
        service_names = set()
        for topic, owners in publishers + subscribers:
            topics.add(topic)
            nodes.update(owners)
        for service, owners in services:
            service_names.add(service)
            nodes.update(owners)
        return True, nodes, topics, service_names
    except Exception:
        return False, set(), set(), set()


def _resource(active, **extra):
    result = {
        "active": bool(active),
        "state": "active" if active else "inactive",
    }
    result.update(extra)
    return result


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def _remember_process(name, process, command):
    state = _load_state()
    state["owned"][name] = {
        "pid": process.pid,
        "command": command,
        "started_at": time.time(),
    }
    _save_state(state)


def _forget_process(name):
    state = _load_state()
    state["owned"].pop(name, None)
    _save_state(state)


def _spawn(name, command):
    state = _load_state()
    current = state.get("owned", {}).get(name)
    if isinstance(current, dict) and _pid_alive(current.get("pid")):
        return int(current["pid"])

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "{}.log".format(name)
    log_handle = open(str(log_path), "ab", buffering=0)

    process = subprocess.Popen(
        ["/bin/bash", "-lc", _ros_prefix() + "exec " + command],
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    log_handle.close()
    _remember_process(name, process, command)
    return process.pid


def _terminate_owned(name):
    state = _load_state()
    item = state.get("owned", {}).get(name)
    if not isinstance(item, dict):
        return
    pid = item.get("pid")
    if not _pid_alive(pid):
        _forget_process(name)
        return

    for sig, wait_time in [
        (signal.SIGINT, 2.0),
        (signal.SIGTERM, 1.5),
        (signal.SIGKILL, 0.2),
    ]:
        if not _pid_alive(pid):
            break
        try:
            os.killpg(os.getpgid(int(pid)), sig)
        except Exception:
            pass
        deadline = time.time() + wait_time
        while time.time() < deadline and _pid_alive(pid):
            time.sleep(0.1)

    _forget_process(name)


def _rosnode_kill(*names):
    existing = _master_state()[1]
    targets = [name for name in names if name in existing]
    if targets:
        _run_ros(
            "rosnode kill " + " ".join(shlex.quote(name) for name in targets),
            timeout=8,
        )


def _wait(predicate, timeout, interval=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return bool(predicate())


def _node_alive(node):
    # Un registro en ROS Master no basta:
    # el nodo debe responder realmente a getPid().
    try:
        uri = "http://{}:11311".format(_robot_ip())

        master = xmlrpc.client.ServerProxy(
            uri,
            transport=TimeoutTransport(1.0),
            allow_none=True,
        )

        code, _message, node_uri = master.lookupNode(
            "/safevision_runtime_manager",
            node,
        )

        if code != 1 or not node_uri:
            return False

        node_api = xmlrpc.client.ServerProxy(
            node_uri,
            transport=TimeoutTransport(1.0),
            allow_none=True,
        )

        code, _message, pid = node_api.getPid(
            "/safevision_runtime_manager"
        )

        return bool(
            code == 1
            and int(pid) > 0
        )

    except Exception:
        return False


def _nodes_present(names):
    return all(
        _node_alive(node)
        for node in names
    )


def _nodes_absent(names):
    return not any(
        _node_alive(node)
        for node in names
    )


def _topic_present(name):
    return name in _master_state()[2]


def _service_present(name):
    return name in _master_state()[3]


def _set_selector_manual():
    if not _service_present("/safevision/set_navigation_mode"):
        return False
    result = _run_ros(
        'rosservice call /safevision/set_navigation_mode "data: false"',
        timeout=5,
    )
    return result.returncode == 0


def _safe_map(name):
    name = str(name or "").strip()
    if not name or "/" in name or "\\" in name or ".." in name:
        raise ValueError("Nombre de mapa invalido.")
    path = MAPS_DIR / "{}.yaml".format(name)
    if not path.is_file():
        raise FileNotFoundError("No existe el mapa {}.".format(name))
    return name, path


def _write_active_map(name, path):
    temp = Path(str(ACTIVE_MAP_FILE) + ".tmp")
    temp.write_text(json.dumps({"name": name, "yaml": str(path)}, sort_keys=True))
    temp.replace(ACTIVE_MAP_FILE)


def _clear_active_map():
    try:
        ACTIVE_MAP_FILE.unlink()
    except Exception:
        pass


def _stop_nav_queue():
    _rosnode_kill("/sf_nav_queue")
    _terminate_owned("nav_queue")
    return _wait(lambda: _nodes_absent({"/sf_nav_queue"}), 5)


def _stop_navigation():
    _set_selector_manual()
    _rosnode_kill("/move_base")
    _terminate_owned("navigation")
    return _wait(lambda: _nodes_absent({"/move_base"}), 7)


def _stop_pose_exporter():
    _rosnode_kill("/safevision_pose_exporter")
    _terminate_owned("pose_exporter")
    try:
        Path("/tmp/safevision_map_pose.json").unlink()
    except Exception:
        pass
    return _wait(lambda: _nodes_absent({"/safevision_pose_exporter"}), 5)


def _stop_localization():
    _rosnode_kill("/amcl", "/sf_map_server")
    _terminate_owned("localization")
    return _wait(lambda: _nodes_absent({"/amcl", "/sf_map_server"}), 7)


def _stop_lidar():
    _rosnode_kill("/rplidarNode", "/base_link_to_laser")
    _terminate_owned("lidar")
    return _wait(lambda: _nodes_absent({"/rplidarNode", "/base_link_to_laser"}), 7)


def _ensure_lidar():
    if _nodes_present({"/rplidarNode"}) and _topic_present("/scan"):
        return True
    launch = ROBOT_DIR / "sf_runtime_lidar.launch"
    _spawn("lidar", "roslaunch " + shlex.quote(str(launch)))
    return _wait(
        lambda: _nodes_present({"/rplidarNode"}) and _topic_present("/scan"),
        15,
    )


def _ensure_localization(map_path):
    if _nodes_present({"/amcl", "/sf_map_server"}) and _topic_present("/map"):
        return True
    launch = ROBOT_DIR / "sf_localizacion_mapa.launch"
    command = (
        "roslaunch " + shlex.quote(str(launch))
        + " map_file:=" + shlex.quote(str(map_path))
    )
    _spawn("localization", command)
    return _wait(
        lambda: _nodes_present({"/amcl", "/sf_map_server"}) and _topic_present("/map"),
        15,
    )


def _ensure_pose_exporter():
    if _nodes_present({"/safevision_pose_exporter"}):
        return True
    script = ROBOT_DIR / "sf_pose_exporter.py"
    _spawn("pose_exporter", "/usr/bin/python " + shlex.quote(str(script)))
    return _wait(lambda: _nodes_present({"/safevision_pose_exporter"}), 8)


def _ensure_navigation():
    if _nodes_present({"/move_base"}) and _service_present("/move_base/make_plan"):
        return True
    launch = ROBOT_DIR / "sf_navegacion.launch"
    _spawn("navigation", "roslaunch " + shlex.quote(str(launch)))
    return _wait(
        lambda: _nodes_present({"/move_base"}) and _service_present("/move_base/make_plan"),
        18,
    )


def _ensure_nav_queue():
    if _nodes_present({"/sf_nav_queue"}):
        return True
    script = ROBOT_DIR / "sf_nav_queue.py"
    _spawn("nav_queue", "python3 " + shlex.quote(str(script)))
    return _wait(lambda: _nodes_present({"/sf_nav_queue"}), 8)


def _topic_has_message(
    topic,
    timeout=10
):

    result = _run_ros(
        (
            "timeout "
            + str(int(timeout))
            + " rostopic echo -n 1 "
            + shlex.quote(topic)
            + " >/dev/null 2>&1"
        ),
        timeout=(
            int(timeout)
            + 2
        )
    )

    return (
        result.returncode
        ==
        0
    )


def _ensure_driver():

    if _nodes_present(
        {
            "/driver_node"
        }
    ):
        return True

    _spawn(
        "driver",
        (
            "rosrun "
            "yahboomcar_bringup "
            "Mcnamu_driver.py "
            "/pub_vel:=/vel_raw "
            "/pub_imu:=/imu/imu_raw "
            "/pub_mag:=/mag/mag_raw"
        )
    )

    return _wait(
        lambda:
            _nodes_present(
                {
                    "/driver_node"
                }
            ),
        10
    )


def _ensure_core():

    required = {
        "/odometry_publisher",
        "/imu_filter_madgwick",
        "/ekf_localization",
    }

    if (
        _nodes_present(required)
        and
        _topic_has_message(
            "/imu/imu_data",
            timeout=3
        )
    ):
        return True

    launch = (
        ROBOT_DIR
        /
        "sf_runtime_core.launch"
    )

    _spawn(
        "core",
        (
            "roslaunch "
            +
            shlex.quote(
                str(launch)
            )
        )
    )

    nodes_ok = _wait(
        lambda:
            _nodes_present(
                required
            ),
        20
    )

    if not nodes_ok:
        return False

    return _topic_has_message(
        "/imu/imu_data",
        timeout=15
    )


def _ensure_selector():

    if (
        _nodes_present(
            {
                "/sf_cmd_vel_selector"
            }
        )
        and
        _service_present(
            "/safevision/set_navigation_mode"
        )
    ):
        return True

    script = (
        ROBOT_DIR
        /
        "sf_cmd_vel_selector.py"
    )

    _spawn(
        "selector",
        (
            "python3 "
            +
            shlex.quote(
                str(script)
            )
        )
    )

    return _wait(
        lambda:
            (
                _nodes_present(
                    {
                        "/sf_cmd_vel_selector"
                    }
                )
                and
                _service_present(
                    "/safevision/set_navigation_mode"
                )
            ),
        10
    )


def _stop_mando():

    _rosnode_kill(
        "/yahboom_joy",
        "/joy_node"
    )

    _terminate_owned(
        "mando"
    )

    return _wait(
        lambda:
            _nodes_absent(
                {
                    "/yahboom_joy",
                    "/joy_node"
                }
            ),
        7
    )


def _ensure_mando():

    if not os.path.exists("/dev/input/js0"):
        return False

    if _nodes_present(
        {
            "/joy_node",
            "/yahboom_joy"
        }
    ):
        return True

    launch = (
        ROBOT_DIR
        /
        "sf_control_mando.launch"
    )

    _spawn(
        "mando",
        (
            "roslaunch "
            +
            shlex.quote(
                str(launch)
            )
        )
    )

    return _wait(
        lambda:
            _nodes_present(
                {
                    "/joy_node",
                    "/yahboom_joy"
                }
            ),
        10
    )


def set_control_mode(
    mode
):

    mode = str(
        mode
        or
        ""
    ).strip().lower()

    if mode not in (
        "mando",
        "teclado"
    ):
        return _result(
            False,
            "Control invalido."
        )

    with _LOCK:

        _set_selector_manual()

        if mode == "mando":

            if not _ensure_mando():
                return _result(
                    False,
                    (
                        "No se pudo activar el mando "
                        "o no existe /dev/input/js0."
                    ),
                    status=status()
                )

        else:

            if not _stop_mando():
                return _result(
                    False,
                    "No se pudo desactivar el mando.",
                    status=status()
                )

        state = _load_state()

        state[
            "control_mode"
        ] = mode

        _save_state(
            state
        )

        final = status(
            mode
        )

        if mode == "mando":
            ok = bool(
                final[
                    "resources"
                ][
                    "mando"
                ][
                    "active"
                ]
            )
        else:
            ok = bool(
                final[
                    "resources"
                ][
                    "teclado"
                ][
                    "active"
                ]
                and
                not final[
                    "resources"
                ][
                    "mando"
                ][
                    "active"
                ]
            )

        return _result(
            ok,
            (
                "Control {} activo.".format(
                    mode.upper()
                )
                if ok
                else
                "No se pudo confirmar el control."
            ),
            status=final
        )


def _ensure_base(
    control_mode=None
):

    ros = _master_state()[0]

    if not ros:
        return _result(
            False,
            "ROS Master no esta disponible."
        )

    requested_control = (
        str(
            control_mode
            or
            _load_state().get(
                "control_mode"
            )
            or
            "mando"
        )
        .strip()
        .lower()
    )

    steps = []

    for name, action in [
        (
            "driver",
            _ensure_driver
        ),
        (
            "core",
            _ensure_core
        ),
        (
            "selector",
            _ensure_selector
        ),
    ]:

        ok = bool(
            action()
        )

        steps.append({
            "resource": name,
            "ok": ok,
        })

        if not ok:
            return _result(
                False,
                (
                    "No se pudo iniciar "
                    +
                    name
                ),
                steps=steps,
                status=status(
                    requested_control
                )
            )

    control_result = set_control_mode(
        requested_control
    )

    steps.append({
        "resource":
            "control",

        "mode":
            requested_control,

        "ok":
            bool(
                control_result.get(
                    "ok"
                )
            ),
    })

    if not control_result.get(
        "ok"
    ):
        return _result(
            False,
            control_result.get(
                "message",
                "No se pudo activar control."
            ),
            steps=steps,
            status=status(
                requested_control
            )
        )

    return _result(
        True,
        "Base SafeVision lista.",
        steps=steps,
        status=status(
            requested_control
        )
    )


def infer_profile(resources):
    if resources["mapping"]["active"]:
        return "mapear"
    if resources["localization"]["active"] and resources["navigation"]["active"]:
        return "navegacion"
    if resources["driver"]["active"] and resources["core"]["active"]:
        return "libre"
    if resources["ros_master"]["active"]:
        return "base"
    return "off"


def status(control_mode=None):
    ros, nodes, topics, services = _master_state()
    state = _load_state()

    core_nodes = {
        "/odometry_publisher",
        "/imu_filter_madgwick",
        "/ekf_localization",
    }

    localization_nodes = {
        "/sf_map_server",
        "/amcl",
    }

    effective_control = (
        state.get("control_mode")
        or control_mode
        or "desactivado"
    )

    resources = {
        "ros_master": _resource(ros),

        "robot_server": _resource(
            True,
            port=8091,
        ),

        "camera": _resource(
            os.path.exists("/dev/video0")
            or os.path.exists("/dev/video1")
        ),

        "driver": _resource(
            _node_alive("/driver_node")
        ),

        "core": _resource(
            all(
                _node_alive(node)
                for node in core_nodes
            ),
            nodes=sorted(core_nodes),
        ),

        "lidar": _resource(
            _node_alive("/rplidarNode")
            and "/scan" in topics
        ),

        "localization": _resource(
            all(
                _node_alive(node)
                for node in localization_nodes
            ),
            map_server=_node_alive("/sf_map_server"),
            amcl=_node_alive("/amcl"),
        ),

        "pose_exporter": _resource(
            _node_alive("/safevision_pose_exporter")
        ),

        "selector": _resource(
            _node_alive("/sf_cmd_vel_selector")
            and "/safevision/set_navigation_mode" in services
        ),

        "navigation": _resource(
            _node_alive("/move_base")
            and "/move_base/make_plan" in services
        ),

        "nav_queue": _resource(
            _node_alive("/sf_nav_queue")
        ),

        "mando": _resource(
            _node_alive("/joy_node")
            and _node_alive("/yahboom_joy"),
            connected=os.path.exists("/dev/input/js0"),
        ),

        "teclado": _resource(
            effective_control == "teclado",
            implementation="dashboard_keyboard",
        ),

        "mapping": _resource(
            _node_alive("/slam_gmapping")
            and "/map" in topics
        ),
    }

    return {
        "ok": True,
        "manager_version": 4,
        "mode": "active_profiles",
        "hostname": socket.gethostname(),
        "ros_master_uri": (
            "http://{}:11311".format(_robot_ip())
        ),
        "control_mode": effective_control,
        "profile": {
            "requested": state.get("requested_profile"),
            "inferred": infer_profile(resources),
            "map": state.get("map_name"),
        },
        "resources": resources,
    }



def _result(ok, message, **extra):
    result = {"ok": bool(ok), "message": message}
    result.update(extra)
    return result


def apply_profile(profile, map_name=None, control_mode=None):
    profile = str(profile or "").strip().lower()
    if profile not in (
        "libre",
        "pilotada",
        "automatica",
    ):
        return _result(
            False,
            "Perfil no soportado: {}".format(profile),
        )

    with _LOCK:
        base = _ensure_base(control_mode)

        if not base.get("ok"):
            return _result(
                False,
                base.get(
                    "message",
                    "No se pudo preparar la base."
                ),
                base=base,
                status=status(control_mode),
            )

        before = status(control_mode)

        _set_selector_manual()

        if profile == "libre":
            steps = []
            for name, action in [
                ("nav_queue", _stop_nav_queue),
                ("navigation", _stop_navigation),
                ("pose_exporter", _stop_pose_exporter),
                ("localization", _stop_localization),
                ("lidar", _stop_lidar),
            ]:
                ok = bool(action())
                steps.append({"resource": name, "ok": ok})
                if not ok:
                    return _result(
                        False,
                        "No se pudo detener " + name,
                        steps=steps,
                        status=status(control_mode),
                    )

            _clear_active_map()
            state = _load_state()
            state["requested_profile"] = "libre"
            state["map_name"] = None
            if control_mode:
                state["control_mode"] = control_mode
            _save_state(state)

            final = status(control_mode)
            expected_off = ["lidar", "localization", "pose_exporter", "navigation", "nav_queue"]
            bad = [name for name in expected_off if final["resources"][name]["active"]]
            if bad:
                return _result(
                    False,
                    "Libre incompleto; siguen activos: " + ", ".join(bad),
                    steps=steps,
                    status=final,
                )
            return _result(True, "Modo Libre listo.", steps=steps, status=final)

        safe_name, map_path = _safe_map(map_name)
        _write_active_map(safe_name, map_path)

        steps = []
        for name, action in [
            ("lidar", _ensure_lidar),
            ("localization", lambda: _ensure_localization(map_path)),
            ("pose_exporter", _ensure_pose_exporter),
            ("navigation", _ensure_navigation),
            ("nav_queue", _ensure_nav_queue),
        ]:
            ok = bool(action())
            steps.append({"resource": name, "ok": ok})
            if not ok:
                return _result(
                    False,
                    "No se pudo iniciar " + name,
                    steps=steps,
                    status=status(control_mode),
                )

        state = _load_state()
        state["requested_profile"] = profile
        state["map_name"] = safe_name
        if control_mode:
            state["control_mode"] = control_mode
        _save_state(state)

        final = status(control_mode)
        expected_on = ["lidar", "localization", "pose_exporter", "navigation", "nav_queue"]
        bad = [name for name in expected_on if not final["resources"][name]["active"]]
        if bad:
            return _result(
                False,
                "Pilotada incompleta; faltan: " + ", ".join(bad),
                steps=steps,
                status=final,
            )

        profile_label = (
            "Mision Automatica"
            if profile == "automatica"
            else "Mision Pilotada"
        )

        return _result(
            True,
            "{} lista con mapa {}.".format(
                profile_label,
                safe_name,
            ),
            steps=steps,
            status=final,
        )
