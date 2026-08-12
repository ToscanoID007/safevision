#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import threading


ALLOWED_ACTIONS = {
    "ir",
    "esperar",
    "orientar",
    "girar",
    "relocalizar"
}


class MissionPlanError(ValueError):
    pass


def finite_number(
    value,
    label
):
    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError
    ):
        raise MissionPlanError(
            "{} no es numérico".format(
                label
            )
        )

    if not math.isfinite(
        number
    ):
        raise MissionPlanError(
            "{} no es finito".format(
                label
            )
        )

    return number


def normalized_point(
    raw
):
    if not isinstance(
        raw,
        dict
    ):
        raise MissionPlanError(
            "Punto inválido"
        )

    point_id = str(
        raw.get(
            "id",
            ""
        )
    ).strip()

    if not point_id:
        raise MissionPlanError(
            "Punto sin id"
        )

    x = finite_number(
        raw.get("x"),
        "{}.x".format(
            point_id
        )
    )

    y = finite_number(
        raw.get("y"),
        "{}.y".format(
            point_id
        )
    )

    raw_yaw = raw.get(
        "yaw"
    )

    if raw_yaw is None:
        yaw = None

    else:
        yaw = finite_number(
            raw_yaw,
            "{}.yaw".format(
                point_id
            )
        )

    return {
        "id": point_id,
        "alias": str(
            raw.get(
                "alias",
                ""
            )
            or
            ""
        ).strip(),
        "x": x,
        "y": y,
        "yaw": yaw
    }


def build_execution_plan(
    mission,
    trace
):
    if not isinstance(
        mission,
        dict
    ):
        raise MissionPlanError(
            "Misión inválida"
        )

    if not isinstance(
        trace,
        list
    ):
        raise MissionPlanError(
            "Trace inválido"
        )

    mission_name = str(
        mission.get(
            "name",
            ""
        )
    ).strip()

    map_name = str(
        mission.get(
            "map",
            ""
        )
    ).strip()

    if not mission_name:
        raise MissionPlanError(
            "La misión no tiene nombre"
        )

    if not map_name:
        raise MissionPlanError(
            "La misión no tiene mapa"
        )

    raw_points = mission.get(
        "points"
    )

    if not isinstance(
        raw_points,
        list
    ):
        raise MissionPlanError(
            "La misión no contiene una lista de puntos"
        )

    points = {}

    for raw in raw_points:
        point = normalized_point(
            raw
        )

        point_id = point[
            "id"
        ]

        if point_id in points:
            raise MissionPlanError(
                "ID de punto repetido: {}".format(
                    point_id
                )
            )

        points[
            point_id
        ] = point

    initial_point_id = mission.get(
        "initial_point_id"
    )

    if initial_point_id is not None:
        initial_point_id = str(
            initial_point_id
        ).strip()

        if (
            initial_point_id
            and
            initial_point_id
            not in points
        ):
            raise MissionPlanError(
                (
                    "El punto inicial {} "
                    "no existe"
                ).format(
                    initial_point_id
                )
            )

    actions = []

    for index, raw_action in enumerate(
        trace
    ):
        if not isinstance(
            raw_action,
            dict
        ):
            raise MissionPlanError(
                "Acción {} inválida".format(
                    index + 1
                )
            )

        action_name = str(
            raw_action.get(
                "name",
                ""
            )
        ).strip().lower()

        if action_name not in ALLOWED_ACTIONS:
            raise MissionPlanError(
                "Acción no soportada: {}".format(
                    action_name
                )
            )

        action = {
            "index": index,
            "name": action_name,
            "line": int(
                raw_action.get(
                    "line",
                    0
                )
                or
                0
            )
        }

        if action_name == "ir":
            target_id = str(
                raw_action.get(
                    "target_id",
                    ""
                )
            ).strip()

            if target_id not in points:
                raise MissionPlanError(
                    (
                        "La acción ir() referencia "
                        "un punto inexistente: {}"
                    ).format(
                        target_id
                    )
                )

            point = points[
                target_id
            ]

            action[
                "target_id"
            ] = target_id

            action[
                "point"
            ] = dict(
                point
            )

        elif action_name == "esperar":
            seconds = finite_number(
                raw_action.get(
                    "seconds"
                ),
                "esperar.seconds"
            )

            if seconds < 0:
                raise MissionPlanError(
                    "esperar() no puede usar tiempo negativo"
                )

            action[
                "seconds"
            ] = seconds

        elif action_name in (
            "orientar",
            "girar"
        ):
            action[
                "angle"
            ] = finite_number(
                raw_action.get(
                    "angle"
                ),
                "{}.angle".format(
                    action_name
                )
            )

            if (
                "velocity"
                in raw_action
            ):
                action[
                    "velocity"
                ] = finite_number(
                    raw_action.get(
                        "velocity"
                    ),
                    "{}.velocity".format(
                        action_name
                    )
                )

        actions.append(
            action
        )

    return {
        "name": mission_name,
        "map": map_name,
        "initial_point_id": (
            initial_point_id
            or
            None
        ),
        "point_count": len(
            points
        ),
        "action_count": len(
            actions
        ),
        "points": points,
        "actions": actions
    }


class MissionRuntime:

    def __init__(self):
        self.lock = threading.RLock()
        self.cancel_event = threading.Event()

        self.plan = None

        self.state = "idle"
        self.running = False

        self.action_index = 0
        self.current_action = None

        self.message = "Sin misión preparada"


    def status(self):
        with self.lock:
            if self.plan is None:
                mission_name = None
                map_name = None
                initial_point_id = None
                action_count = 0

            else:
                mission_name = self.plan["name"]
                map_name = self.plan["map"]

                initial_point_id = (
                    self.plan["initial_point_id"]
                )

                action_count = (
                    self.plan["action_count"]
                )


            current_action = None

            if isinstance(
                self.current_action,
                dict
            ):
                current_action = dict(
                    self.current_action
                )

                if isinstance(
                    current_action.get("point"),
                    dict
                ):
                    current_action["point"] = dict(
                        current_action["point"]
                    )


            return {
                "state": self.state,
                "running": self.running,

                "mission": mission_name,
                "map": map_name,

                "initial_point_id":
                    initial_point_id,

                "action_index":
                    self.action_index,

                "action_count":
                    action_count,

                "current_action":
                    current_action,

                "message":
                    self.message
            }


    def prepare(
        self,
        mission,
        trace
    ):
        plan = build_execution_plan(
            mission,
            trace
        )

        with self.lock:
            if self.running:
                raise MissionPlanError(
                    "Hay una misión en ejecución"
                )

            self.cancel_event.clear()

            self.plan = plan

            self.state = "ready"
            self.running = False

            self.action_index = 0
            self.current_action = None

            self.message = "Misión preparada"

        return self.status()


    def start(self):
        with self.lock:
            if self.running:
                raise MissionPlanError(
                    "La misión ya está en ejecución"
                )

            if self.plan is None:
                raise MissionPlanError(
                    "No hay una misión preparada"
                )

            if self.state != "ready":
                raise MissionPlanError(
                    "La misión no está en estado ready"
                )


            unsupported = [
                action["name"]
                for action in self.plan["actions"]
                if action["name"] != "esperar"
            ]

            if unsupported:
                raise MissionPlanError(
                    (
                        "Runtime de prueba: solo se admite "
                        "esperar(). Acción no habilitada: {}"
                    ).format(
                        unsupported[0]
                    )
                )


            self.cancel_event.clear()

            self.running = True
            self.state = "running"

            self.action_index = 0
            self.current_action = None

            self.message = (
                "Misión iniciada"
            )


            worker = threading.Thread(
                target=self._run_wait_only,
                name="safevision-mission-wait",
                daemon=True
            )

            worker.start()


        return self.status()


    def _run_wait_only(self):
        try:
            actions = list(
                self.plan["actions"]
            )

            for index, action in enumerate(
                actions
            ):
                if self.cancel_event.is_set():
                    break


                with self.lock:
                    self.action_index = index

                    self.current_action = dict(
                        action
                    )

                    self.state = "waiting"

                    self.message = (
                        "Esperando {:.3f} s".format(
                            action["seconds"]
                        )
                    )


                cancelled = self.cancel_event.wait(
                    action["seconds"]
                )

                if cancelled:
                    break


            with self.lock:
                if self.cancel_event.is_set():
                    self.state = "cancelled"

                    self.message = (
                        "Misión cancelada"
                    )

                else:
                    self.state = "completed"

                    self.action_index = len(
                        actions
                    )

                    self.message = (
                        "Misión completada"
                    )


        except Exception as exc:
            with self.lock:
                self.state = "error"

                self.message = str(
                    exc
                )


        finally:
            with self.lock:
                self.running = False
                self.current_action = None


    def cancel(self):
        with self.lock:
            self.cancel_event.set()

            if self.running:
                self.message = (
                    "Cancelación solicitada"
                )

            elif self.plan is not None:
                self.state = "cancelled"

                self.message = (
                    "Misión cancelada"
                )

            else:
                self.state = "idle"

                self.message = (
                    "Sin misión preparada"
                )

        return self.status()
