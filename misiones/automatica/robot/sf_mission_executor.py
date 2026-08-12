#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math


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
