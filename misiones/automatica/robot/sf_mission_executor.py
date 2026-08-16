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


def normalize_yaw(
    yaw
):
    return math.atan2(
        math.sin(
            yaw
        ),
        math.cos(
            yaw
        )
    )


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

    reference_point_id = (
        initial_point_id
        or
        None
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

            reference_point_id = (
                target_id
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

        elif action_name == "orientar":
            angle = finite_number(
                raw_action.get(
                    "angle"
                ),
                "orientar.angle"
            )

            if (
                "velocity"
                in raw_action
            ):
                raise MissionPlanError(
                    (
                        "orientar() con velocidad "
                        "todavía no está habilitado"
                    )
                )

            if not reference_point_id:
                raise MissionPlanError(
                    (
                        "orientar() requiere un "
                        "punto de referencia"
                    )
                )

            reference_point = points.get(
                reference_point_id
            )

            if reference_point is None:
                raise MissionPlanError(
                    (
                        "El punto de referencia {} "
                        "no existe"
                    ).format(
                        reference_point_id
                    )
                )

            reference_yaw = (
                reference_point.get(
                    "yaw"
                )
            )

            if reference_yaw is None:
                raise MissionPlanError(
                    (
                        "orientar() requiere yaw "
                        "numérico en el punto {}"
                    ).format(
                        reference_point_id
                    )
                )

            target_yaw = normalize_yaw(
                reference_yaw
                +
                math.radians(
                    angle
                )
            )

            action[
                "angle"
            ] = angle

            action[
                "reference_id"
            ] = reference_point_id

            action[
                "reference_yaw"
            ] = reference_yaw

            action[
                "target_yaw"
            ] = target_yaw

        elif action_name == "girar":
            action[
                "angle"
            ] = finite_number(
                raw_action.get(
                    "angle"
                ),
                "girar.angle"
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
                    "girar.velocity"
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


    def start(
        self,
        action_executor=None,
        executor_actions=None
    ):
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


            supported = {
                "esperar",
                "ir",
                "orientar"
            }

            unsupported = [
                action["name"]
                for action in self.plan["actions"]
                if action["name"] not in supported
            ]

            if unsupported:
                raise MissionPlanError(
                    (
                        "Acción todavía no habilitada: {}"
                    ).format(
                        unsupported[0]
                    )
                )


            external_actions = {
                action["name"]
                for action in self.plan["actions"]
                if action["name"] in {
                    "ir",
                    "orientar"
                }
            }


            #
            # El punto inicial es una fase previa,
            # pero físicamente utiliza el mismo ir().
            #/
            if self.plan["initial_point_id"]:
                external_actions.add(
                    "ir"
                )


            if external_actions:
                if not callable(
                    action_executor
                ):
                    raise MissionPlanError(
                        (
                            "La misión requiere "
                            "ejecutor de acciones"
                        )
                    )

                if executor_actions is None:
                    declared_actions = {
                        "ir"
                    }

                else:
                    declared_actions = set(
                        executor_actions
                    )

                missing_actions = sorted(
                    external_actions
                    -
                    declared_actions
                )

                if missing_actions:
                    raise MissionPlanError(
                        (
                            "El ejecutor no soporta "
                            "la acción: {}"
                        ).format(
                            missing_actions[0]
                        )
                    )


            self.cancel_event.clear()

            initial_point_id = (
                self.plan[
                    "initial_point_id"
                ]
            )


            self.running = True

            self.action_index = 0
            self.current_action = None


            if initial_point_id:
                self.state = (
                    "positioning_initial"
                )

                self.message = (
                    "Posicionando en punto inicial {}".format(
                        initial_point_id
                    )
                )

            else:
                self.state = "running"

                self.message = (
                    "Misión iniciada"
                )


            worker = threading.Thread(
                target=self._run_actions,
                args=(
                    action_executor,
                ),
                name="safevision-mission",
                daemon=True
            )

            worker.start()


        return self.status()


    def _run_actions(
        self,
        action_executor
    ):
        try:
            actions = list(
                self.plan["actions"]
            )


            initial_point_id = (
                self.plan[
                    "initial_point_id"
                ]
            )


            # =================================================
            # FASE PREVIA OBLIGATORIA
            # =================================================

            if initial_point_id:

                initial_point = (
                    self.plan[
                        "points"
                    ].get(
                        initial_point_id
                    )
                )


                if initial_point is None:
                    raise MissionPlanError(
                        (
                            "El punto inicial {} "
                            "no existe"
                        ).format(
                            initial_point_id
                        )
                    )


                initial_action = {
                    "index": -1,
                    "name": "ir",
                    "line": 0,
                    "target_id":
                        initial_point_id,
                    "point": dict(
                        initial_point
                    ),
                    "phase": "initial"
                }


                with self.lock:
                    self.action_index = 0
                    self.current_action = None

                    self.state = (
                        "positioning_initial"
                    )

                    self.message = (
                        "Posicionando en punto inicial {}".format(
                            initial_point_id
                        )
                    )


                def report_initial(
                    _state,
                    message
                ):
                    with self.lock:
                        if (
                            self.cancel_event.is_set()
                        ):
                            return

                        #
                        # Durante toda esta navegación
                        # conservamos un estado distinto
                        # de las acciones del programa.
                        #/
                        self.state = (
                            "positioning_initial"
                        )

                        self.message = (
                            "Punto inicial {}: {}".format(
                                initial_point_id,
                                str(
                                    message
                                )
                            )
                        )


                action_executor(
                    dict(
                        initial_action
                    ),
                    self.cancel_event,
                    report_initial
                )


                if self.cancel_event.is_set():

                    with self.lock:
                        self.state = (
                            "cancelled"
                        )

                        self.message = (
                            "Misión cancelada"
                        )

                    return


                with self.lock:
                    self.state = "running"

                    self.message = (
                        (
                            "Punto inicial {} alcanzado. "
                            "Ejecutando misión"
                        ).format(
                            initial_point_id
                        )
                    )


            # =================================================
            # CÓDIGO DE LA MISIÓN
            # =================================================

            for index, action in enumerate(
                actions
            ):
                if self.cancel_event.is_set():
                    break


                action_name = action[
                    "name"
                ]


                with self.lock:
                    self.action_index = index

                    self.current_action = dict(
                        action
                    )


                if action_name == "esperar":
                    with self.lock:
                        self.state = "waiting"

                        self.message = (
                            "Esperando {:.3f} s".format(
                                action["seconds"]
                            )
                        )


                    cancelled = (
                        self.cancel_event.wait(
                            action["seconds"]
                        )
                    )

                    if cancelled:
                        break


                elif action_name == "ir":
                    target_id = action[
                        "target_id"
                    ]


                    with self.lock:
                        self.state = "navigating"

                        self.message = (
                            "Navegando hacia {}".format(
                                target_id
                            )
                        )


                    def report(
                        state,
                        message
                    ):
                        with self.lock:
                            if (
                                self.cancel_event.is_set()
                            ):
                                return

                            self.state = str(
                                state
                            )

                            self.message = str(
                                message
                            )


                    action_executor(
                        dict(
                            action
                        ),
                        self.cancel_event,
                        report
                    )


                    if self.cancel_event.is_set():
                        break


                elif action_name == "orientar":
                    with self.lock:
                        self.state = "orienting"

                        self.message = (
                            "Orientando respecto a {}".format(
                                action[
                                    "reference_id"
                                ]
                            )
                        )


                    def report(
                        state,
                        message
                    ):
                        with self.lock:
                            if (
                                self.cancel_event.is_set()
                            ):
                                return

                            self.state = str(
                                state
                            )

                            self.message = str(
                                message
                            )


                    action_executor(
                        dict(
                            action
                        ),
                        self.cancel_event,
                        report
                    )


                    if self.cancel_event.is_set():
                        break


                else:
                    raise MissionPlanError(
                        (
                            "Acción no soportada "
                            "por runtime: {}"
                        ).format(
                            action_name
                        )
                    )


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
                if self.cancel_event.is_set():
                    self.state = "cancelled"

                    self.message = (
                        "Misión cancelada"
                    )

                else:
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
