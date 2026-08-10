#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import math
import threading
from pathlib import Path

import actionlib
import rospy

from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PoseWithCovarianceStamped
from move_base_msgs.msg import MoveBaseAction
from move_base_msgs.msg import MoveBaseGoal
from nav_msgs.srv import GetPlan
from std_msgs.msg import String
from std_srvs.srv import SetBool


ACTIVE_MAP_FILE = Path(
    "/tmp/safevision_active_map.json"
)


class SafeVisionNavQueue:
    def __init__(self):
        self.lock = threading.RLock()

        self.queue = []
        self.completed = []

        self.queue_map = None
        self.current = None

        self.state = "idle"
        self.message = "Cola vacía"

        self.running = False

        self.cancel_event = threading.Event()

        self.goal_timeout = float(
            rospy.get_param(
                "~goal_timeout",
                120.0
            )
        )

        self.status_pub = rospy.Publisher(
            "/safevision/nav/status",
            String,
            queue_size=1,
            latch=True
        )

        rospy.Subscriber(
            "/safevision/nav/command",
            String,
            self.command_callback,
            queue_size=10
        )

        self.move_base = actionlib.SimpleActionClient(
            "/move_base",
            MoveBaseAction
        )

        self.set_mode = rospy.ServiceProxy(
            "/safevision/set_navigation_mode",
            SetBool
        )

        self.make_plan = rospy.ServiceProxy(
            "/move_base/make_plan",
            GetPlan
        )

        self.publish_status()

        rospy.loginfo(
            "SafeVision nav queue lista"
        )

    def active_map(self):
        try:
            data = json.loads(
                ACTIVE_MAP_FILE.read_text()
            )

            name = data.get(
                "name"
            )

            if isinstance(name, str):
                return name

        except Exception:
            pass

        return None

    def status_data(self):
        with self.lock:
            return {
                "state": self.state,
                "message": self.message,
                "map": self.queue_map,
                "active_map": self.active_map(),
                "running": self.running,
                "current": (
                    dict(self.current)
                    if self.current
                    else None
                ),
                "remaining": [
                    dict(point)
                    for point in self.queue
                ],
                "completed": [
                    dict(point)
                    for point in self.completed
                ],
                "remaining_count": len(
                    self.queue
                ),
                "completed_count": len(
                    self.completed
                )
            }

    def publish_status(self):
        data = self.status_data()

        self.status_pub.publish(
            String(
                data=json.dumps(
                    data,
                    sort_keys=True
                )
            )
        )

    def reject(self, message):
        with self.lock:
            self.message = message

        rospy.logwarn(
            message
        )

        self.publish_status()

    def validate_point(self, raw, index):
        if not isinstance(raw, dict):
            raise ValueError(
                "Punto {} inválido".format(
                    index + 1
                )
            )

        try:
            x = float(
                raw["x"]
            )

            y = float(
                raw["y"]
            )

        except Exception:
            raise ValueError(
                "Punto {} sin X/Y válidos".format(
                    index + 1
                )
            )

        if not (
            math.isfinite(x)
            and math.isfinite(y)
        ):
            raise ValueError(
                "Punto {} contiene valores no finitos".format(
                    index + 1
                )
            )

        yaw = raw.get(
            "yaw"
        )

        if yaw is not None:
            try:
                yaw = float(
                    yaw
                )
            except Exception:
                raise ValueError(
                    "Yaw inválido en punto {}".format(
                        index + 1
                    )
                )

            if not math.isfinite(
                yaw
            ):
                raise ValueError(
                    "Yaw no finito en punto {}".format(
                        index + 1
                    )
                )

        point_id = raw.get(
            "id",
            chr(
                ord("A")
                + index
            )
            if index < 26
            else str(index + 1)
        )

        point_id = str(
            point_id
        )

        return {
            "id": point_id,
            "x": x,
            "y": y,
            "yaw": yaw
        }

    def load_queue(self, data):
        with self.lock:
            if self.running:
                self.reject(
                    "No se puede cargar una cola durante navegación"
                )
                return

        queue_map = data.get(
            "map"
        )

        if not isinstance(
            queue_map,
            str
        ) or not queue_map:
            self.reject(
                "Falta mapa de la cola"
            )
            return

        points = data.get(
            "points"
        )

        if not isinstance(
            points,
            list
        ) or not points:
            self.reject(
                "La cola no contiene puntos"
            )
            return

        if len(points) > 50:
            self.reject(
                "La cola supera 50 puntos"
            )
            return

        try:
            validated = [
                self.validate_point(
                    point,
                    index
                )
                for index, point
                in enumerate(points)
            ]

        except ValueError as exc:
            self.reject(
                str(exc)
            )
            return

        with self.lock:
            self.queue = validated
            self.completed = []

            self.queue_map = queue_map
            self.current = None

            self.state = "ready"
            self.message = (
                "Cola cargada"
            )

            self.cancel_event.clear()

        self.publish_status()

    def clear_queue(self):
        with self.lock:
            if self.running:
                self.reject(
                    "Cancela la navegación antes de limpiar"
                )
                return

            self.queue = []
            self.completed = []

            self.queue_map = None
            self.current = None

            self.state = "idle"
            self.message = "Cola vacía"

            self.cancel_event.clear()

        self.publish_status()

    def cancel_queue(self):
        with self.lock:
            was_running = self.running

            self.cancel_event.set()

            if was_running:
                self.state = "cancelled"
                self.message = (
                    "Navegación cancelada"
                )

        if was_running:
            self.move_base.cancel_all_goals()

            try:
                rospy.wait_for_service(
                    "/safevision/set_navigation_mode",
                    timeout=2.0
                )

                self.set_mode(
                    False
                )

            except Exception as exc:
                rospy.logwarn(
                    "No se pudo volver a MANUAL: %s",
                    exc
                )

        self.publish_status()

    def start_queue(self):
        with self.lock:
            if self.running:
                self.reject(
                    "La cola ya está en ejecución"
                )
                return

            if not self.queue:
                self.reject(
                    "No hay puntos pendientes"
                )
                return

            active = self.active_map()

            if active != self.queue_map:
                self.state = "error"
                self.message = (
                    "Mapa activo '{}' distinto de cola '{}'".format(
                        active,
                        self.queue_map
                    )
                )

                self.publish_status()
                return

            self.running = True

            self.state = "running"
            self.message = (
                "Iniciando navegación"
            )

            self.cancel_event.clear()

        self.publish_status()

        thread = threading.Thread(
            target=self.execute_queue,
            daemon=True
        )

        thread.start()

    def command_callback(self, msg):
        try:
            data = json.loads(
                msg.data
            )

        except Exception:
            self.reject(
                "Comando JSON inválido"
            )
            return

        if not isinstance(
            data,
            dict
        ):
            self.reject(
                "Comando inválido"
            )
            return

        command = str(
            data.get(
                "command",
                ""
            )
        ).strip().lower()

        if command == "load":
            self.load_queue(
                data
            )

        elif command == "start":
            self.start_queue()

        elif command == "cancel":
            self.cancel_queue()

        elif command == "clear":
            self.clear_queue()

        elif command == "status":
            self.publish_status()

        else:
            self.reject(
                "Comando desconocido: {}".format(
                    command
                )
            )

    def quaternion_yaw(self, q):
        siny_cosp = 2.0 * (
            q.w * q.z
            + q.x * q.y
        )

        cosy_cosp = 1.0 - 2.0 * (
            q.y * q.y
            + q.z * q.z
        )

        return math.atan2(
            siny_cosp,
            cosy_cosp
        )

    def yaw_quaternion(self, yaw):
        half = yaw * 0.5

        return (
            math.sin(half),
            math.cos(half)
        )

    def current_pose(self):
        msg = rospy.wait_for_message(
            "/amcl_pose",
            PoseWithCovarianceStamped,
            timeout=5.0
        )

        return msg.pose.pose

    def resolve_yaw(self, point, pose):
        if point["yaw"] is not None:
            return point["yaw"]

        dx = (
            point["x"]
            - pose.position.x
        )

        dy = (
            point["y"]
            - pose.position.y
        )

        if math.hypot(
            dx,
            dy
        ) < 0.02:
            return self.quaternion_yaw(
                pose.orientation
            )

        return math.atan2(
            dy,
            dx
        )

    def build_pose(self, point, pose):
        yaw = self.resolve_yaw(
            point,
            pose
        )

        z, w = self.yaw_quaternion(
            yaw
        )

        target = PoseStamped()

        target.header.frame_id = "map"
        target.header.stamp = rospy.Time.now()

        target.pose.position.x = point["x"]
        target.pose.position.y = point["y"]
        target.pose.position.z = 0.0

        target.pose.orientation.x = 0.0
        target.pose.orientation.y = 0.0
        target.pose.orientation.z = z
        target.pose.orientation.w = w

        return target

    def plan_exists(self, target, pose):
        start = PoseStamped()

        start.header.frame_id = "map"
        start.header.stamp = rospy.Time.now()

        start.pose = pose

        rospy.wait_for_service(
            "/move_base/make_plan",
            timeout=5.0
        )

        response = self.make_plan(
            start,
            target,
            0.0
        )

        return bool(
            response.plan.poses
        )

    def execute_queue(self):
        try:
            rospy.wait_for_service(
                "/safevision/set_navigation_mode",
                timeout=5.0
            )

            if not self.move_base.wait_for_server(
                rospy.Duration(5.0)
            ):
                raise RuntimeError(
                    "move_base no disponible"
                )

            response = self.set_mode(
                True
            )

            if not response.success:
                raise RuntimeError(
                    response.message
                )

            while not rospy.is_shutdown():
                if self.cancel_event.is_set():
                    return

                with self.lock:
                    if not self.queue:
                        self.state = "completed"
                        self.message = (
                            "Cola completada"
                        )
                        return

                    point = dict(
                        self.queue[0]
                    )

                    self.current = point

                    self.message = (
                        "Navegando hacia {}".format(
                            point["id"]
                        )
                    )

                self.publish_status()

                active = self.active_map()

                if active != self.queue_map:
                    raise RuntimeError(
                        "El mapa activo cambió durante la navegación"
                    )

                pose = self.current_pose()

                target = self.build_pose(
                    point,
                    pose
                )

                if not self.plan_exists(
                    target,
                    pose
                ):
                    raise RuntimeError(
                        "Sin ruta válida hacia {}".format(
                            point["id"]
                        )
                    )

                goal = MoveBaseGoal()

                goal.target_pose = target

                self.move_base.send_goal(
                    goal
                )

                finished = self.move_base.wait_for_result(
                    rospy.Duration(
                        self.goal_timeout
                    )
                )

                if self.cancel_event.is_set():
                    self.move_base.cancel_all_goals()
                    return

                if not finished:
                    self.move_base.cancel_goal()

                    raise RuntimeError(
                        "Timeout navegando hacia {}".format(
                            point["id"]
                        )
                    )

                state = self.move_base.get_state()

                if state != 3:
                    raise RuntimeError(
                        "move_base falló en {} con estado {}".format(
                            point["id"],
                            state
                        )
                    )

                with self.lock:
                    completed = self.queue.pop(
                        0
                    )

                    self.completed.append(
                        completed
                    )

                    self.current = None

                    self.message = (
                        "{} completado".format(
                            completed["id"]
                        )
                    )

                self.publish_status()

        except Exception as exc:
            with self.lock:
                if not self.cancel_event.is_set():
                    self.state = "error"
                    self.message = str(
                        exc
                    )

            rospy.logerr(
                "SafeVision nav queue: %s",
                exc
            )

        finally:
            self.move_base.cancel_all_goals()

            try:
                rospy.wait_for_service(
                    "/safevision/set_navigation_mode",
                    timeout=2.0
                )

                self.set_mode(
                    False
                )

            except Exception as exc:
                rospy.logwarn(
                    "No se pudo volver a MANUAL: %s",
                    exc
                )

            with self.lock:
                self.running = False
                self.current = None

                if self.cancel_event.is_set():
                    self.state = "cancelled"
                    self.message = (
                        "Navegación cancelada"
                    )

            self.publish_status()


def main():
    rospy.init_node(
        "sf_nav_queue"
    )

    SafeVisionNavQueue()

    rospy.spin()


if __name__ == "__main__":
    main()
