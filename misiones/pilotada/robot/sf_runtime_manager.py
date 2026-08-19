#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SafeVision Runtime Manager.

Etapa 1:
- inspecciona el runtime ROS real;
- describe perfiles futuros;
- no inicia ni detiene procesos todavia.
"""

import os
import socket
import xmlrpc.client


ROS_MASTER_URI = os.environ.get(
    "ROS_MASTER_URI",
    "http://127.0.0.1:11311"
)


class SafeVisionXmlRpcTransport(
    xmlrpc.client.Transport
):
    def __init__(
        self,
        timeout=1.5
    ):
        super().__init__()
        self.timeout = timeout

    def make_connection(
        self,
        host
    ):
        connection = super().make_connection(
            host
        )

        connection.timeout = self.timeout
        return connection


PROFILE_BASE = {
    "ros_master",
    "robot_server",
    "camera",
}


PROFILE_REQUIREMENTS = {
    "libre": {
        "driver",
        "core",
        "selector",
    },

    "pilotada": {
        "driver",
        "core",
        "lidar",
        "localization",
        "pose_exporter",
        "selector",
        "navigation",
        "nav_queue",
    },

    "automatica": {
        "driver",
        "core",
        "lidar",
        "localization",
        "pose_exporter",
        "selector",
        "navigation",
        "nav_queue",
    },

    "mapear": {
        "driver",
        "core",
        "lidar",
        "localization",
        "selector",
    },
}


def _master_state():

    try:
        master = xmlrpc.client.ServerProxy(
            ROS_MASTER_URI,
            transport=SafeVisionXmlRpcTransport(
                timeout=1.5
            ),
            allow_none=True
        )

        code, _message, state = (
            master.getSystemState(
                "/safevision_runtime_manager"
            )
        )

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


def _device_camera():

    return bool(
        os.path.exists("/dev/video0")
        or
        os.path.exists("/dev/video1")
    )


def _device_joystick():

    return os.path.exists(
        "/dev/input/js0"
    )


def _resource(
    active,
    **extra
):

    result = {
        "active": bool(active),
        "state": (
            "active"
            if active
            else "inactive"
        ),
    }

    result.update(extra)
    return result


def infer_profile(
    resources
):

    if resources["mapping"]["active"]:
        return "mapear"

    if (
        resources["localization"]["active"]
        and
        resources["navigation"]["active"]
    ):
        # Pilotada y Automatica comparten infraestructura.
        return "navegacion"

    if (
        resources["driver"]["active"]
        and
        resources["core"]["active"]
    ):
        return "libre"

    if resources["ros_master"]["active"]:
        return "base"

    return "off"


def status(
    control_mode=None
):

    ros, nodes, topics, services = (
        _master_state()
    )

    core_nodes = {
        "/odometry_publisher",
        "/imu_filter_madgwick",
        "/ekf_localization",
    }

    localization_nodes = {
        "/sf_map_server",
        "/amcl",
    }

    resources = {

        "ros_master":
            _resource(ros),

        "robot_server":
            _resource(
                True,
                port=8091
            ),

        "camera":
            _resource(
                _device_camera()
            ),

        "driver":
            _resource(
                "/driver_node"
                in nodes
            ),

        "core":
            _resource(
                core_nodes.issubset(nodes),
                nodes=sorted(core_nodes)
            ),

        "lidar":
            _resource(
                (
                    "/rplidarNode"
                    in nodes
                )
                and
                (
                    "/scan"
                    in topics
                )
            ),

        "localization":
            _resource(
                localization_nodes.issubset(
                    nodes
                ),
                map_server=(
                    "/sf_map_server"
                    in nodes
                ),
                amcl=(
                    "/amcl"
                    in nodes
                )
            ),

        "pose_exporter":
            _resource(
                "/safevision_pose_exporter"
                in nodes
            ),

        "selector":
            _resource(
                (
                    "/sf_cmd_vel_selector"
                    in nodes
                )
                and
                (
                    "/safevision/set_navigation_mode"
                    in services
                )
            ),

        "navigation":
            _resource(
                (
                    "/move_base"
                    in nodes
                )
                and
                (
                    "/move_base/make_plan"
                    in services
                )
            ),

        "nav_queue":
            _resource(
                "/sf_nav_queue"
                in nodes
            ),

        "mando":
            _resource(
                (
                    "/joy_node"
                    in nodes
                )
                and
                (
                    "/yahboom_joy"
                    in nodes
                ),
                connected=(
                    _device_joystick()
                )
            ),

        "teclado":
            _resource(
                "/yahboom_keyboard"
                in nodes,
                implementation="legacy_pi_tty"
            ),

        "mapping":
            _resource(
                (
                    "/slam_gmapping"
                    in nodes
                )
                and
                (
                    "/map"
                    in topics
                )
            ),
    }

    return {
        "ok": True,
        "manager_version": 1,
        "mode": "observe_only",
        "ros_master_uri": ROS_MASTER_URI,
        "hostname": socket.gethostname(),

        "control_mode":
            control_mode
            or
            "desactivado",

        "profile": {
            "requested": None,
            "inferred": infer_profile(
                resources
            ),
        },

        "profiles": {
            name:
                sorted(
                    PROFILE_BASE
                    |
                    requirements
                )

            for name, requirements
            in PROFILE_REQUIREMENTS.items()
        },

        "resources":
            resources,
    }
