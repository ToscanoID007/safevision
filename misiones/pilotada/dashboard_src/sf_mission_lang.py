#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import math
import re


POINT_ID_RE = re.compile(
    r"^0[xX][0-9A-Fa-f]{3}$"
)

ALIAS_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)

ALLOWED_COMMANDS = {
    "ir",
    "esperar",
    "orientar",
    "girar",
    "relocalizar"
}


def _error(
    node,
    message
):
    return {
        "line": int(
            getattr(
                node,
                "lineno",
                0
            )
            or
            0
        ),
        "column": int(
            getattr(
                node,
                "col_offset",
                0
            )
            or
            0
        )
        +
        1,
        "message": message
    }


def _number_literal(
    node
):
    if isinstance(
        node,
        ast.Num
    ):
        value = node.n

        if isinstance(
            value,
            bool
        ):
            return None

        return float(
            value
        )

    constant_type = getattr(
        ast,
        "Constant",
        None
    )

    if (
        constant_type is not None
        and
        isinstance(
            node,
            constant_type
        )
    ):
        value = node.value

        if (
            isinstance(
                value,
                bool
            )
            or
            not isinstance(
                value,
                (
                    int,
                    float
                )
            )
        ):
            return None

        return float(
            value
        )

    if (
        isinstance(
            node,
            ast.UnaryOp
        )
        and
        isinstance(
            node.op,
            (
                ast.USub,
                ast.UAdd
            )
        )
    ):
        value = _number_literal(
            node.operand
        )

        if value is None:
            return None

        if isinstance(
            node.op,
            ast.USub
        ):
            return -value

        return value

    return None


def _string_literal(
    node
):
    if isinstance(
        node,
        ast.Str
    ):
        return node.s

    constant_type = getattr(
        ast,
        "Constant",
        None
    )

    if (
        constant_type is not None
        and
        isinstance(
            node,
            constant_type
        )
        and
        isinstance(
            node.value,
            str
        )
    ):
        return node.value

    return None


def _canonical_point_id(
    value
):
    if not isinstance(
        value,
        str
    ):
        return None

    text = value.strip()

    if not POINT_ID_RE.match(
        text
    ):
        return None

    number = int(
        text[2:],
        16
    )

    return (
        "0x"
        +
        format(
            number,
            "03X"
        )
    )


def _build_point_context(
    points
):
    errors = []

    ids = {}
    aliases = {}

    if not isinstance(
        points,
        list
    ):
        return ids, aliases, [{
            "line": 0,
            "column": 0,
            "message": "La lista de puntos no es válida."
        }]

    for index, point in enumerate(
        points
    ):
        if not isinstance(
            point,
            dict
        ):
            errors.append({
                "line": 0,
                "column": 0,
                "message": (
                    "El punto {} no es válido."
                    .format(
                        index + 1
                    )
                )
            })
            continue

        point_id = _canonical_point_id(
            point.get(
                "id"
            )
        )

        if point_id is None:
            errors.append({
                "line": 0,
                "column": 0,
                "message": (
                    "El punto {} tiene un ID inválido."
                    .format(
                        index + 1
                    )
                )
            })
            continue

        key = point_id.casefold()

        if key in ids:
            errors.append({
                "line": 0,
                "column": 0,
                "message": (
                    "El ID {} está duplicado."
                    .format(
                        point_id
                    )
                )
            })

        else:
            ids[key] = point_id

        alias = str(
            point.get(
                "alias",
                ""
            )
            or
            ""
        ).strip()

        if alias:

            if not ALIAS_RE.match(
                alias
            ):
                errors.append({
                    "line": 0,
                    "column": 0,
                    "message": (
                        "El alias '{}' no es válido."
                        .format(
                            alias
                        )
                    )
                })

            else:
                alias_key = alias.casefold()

                if alias_key in aliases:
                    errors.append({
                        "line": 0,
                        "column": 0,
                        "message": (
                            "El alias '{}' está duplicado."
                            .format(
                                alias
                            )
                        )
                    })

                else:
                    aliases[
                        alias_key
                    ] = point_id

    return ids, aliases, errors


def _validate_velocity(
    call,
    errors
):
    if len(
        call.args
    ) != 1:
        errors.append(
            _error(
                call,
                "Debe recibir exactamente un ángulo."
            )
        )
        return

    angle = _number_literal(
        call.args[0]
    )

    if (
        angle is None
        or
        not math.isfinite(
            angle
        )
    ):
        errors.append(
            _error(
                call.args[0],
                "El ángulo debe ser un número."
            )
        )

    if len(
        call.keywords
    ) > 1:
        errors.append(
            _error(
                call,
                "Solo se permite el parámetro velocidad."
            )
        )
        return

    for keyword in call.keywords:

        if keyword.arg != "velocidad":
            errors.append(
                _error(
                    call,
                    "Parámetro no permitido: {}.".format(
                        keyword.arg
                        if keyword.arg
                        else "**kwargs"
                    )
                )
            )
            continue

        velocity = _number_literal(
            keyword.value
        )

        if (
            velocity is None
            or
            not math.isfinite(
                velocity
            )
            or
            velocity <= 0
        ):
            errors.append(
                _error(
                    keyword.value,
                    "velocidad debe ser un número mayor que 0."
                )
            )


def validate_program(
    code,
    points
):
    result = {
        "ok": False,
        "errors": [],
        "commands": [],
        "command_count": 0
    }

    if not isinstance(
        code,
        str
    ):
        result["errors"].append({
            "line": 0,
            "column": 0,
            "message": "El programa debe ser texto."
        })

        return result

    if not code.strip():
        result["errors"].append({
            "line": 0,
            "column": 0,
            "message": "Programa vacío."
        })

        return result

    try:
        tree = ast.parse(
            code,
            mode="exec"
        )

    except SyntaxError as exc:
        result["errors"].append({
            "line": int(
                exc.lineno
                or
                0
            ),
            "column": int(
                exc.offset
                or
                0
            ),
            "message": (
                "Error de sintaxis: "
                +
                str(
                    exc.msg
                )
            )
        })

        return result

    ids, aliases, context_errors = (
        _build_point_context(
            points
        )
    )

    result["errors"].extend(
        context_errors
    )

    if not tree.body:
        result["errors"].append({
            "line": 0,
            "column": 0,
            "message": "El programa no contiene instrucciones."
        })

        return result

    for statement in tree.body:

        if not isinstance(
            statement,
            ast.Expr
        ):
            result["errors"].append(
                _error(
                    statement,
                    (
                        "Instrucción todavía no permitida: {}."
                        .format(
                            type(
                                statement
                            ).__name__
                        )
                    )
                )
            )
            continue

        call = statement.value

        if not isinstance(
            call,
            ast.Call
        ):
            result["errors"].append(
                _error(
                    statement,
                    "Solo se permiten llamadas a instrucciones SafeVision."
                )
            )
            continue

        if not isinstance(
            call.func,
            ast.Name
        ):
            result["errors"].append(
                _error(
                    call,
                    "Solo se permiten instrucciones SafeVision directas."
                )
            )
            continue

        command = call.func.id

        if command not in ALLOWED_COMMANDS:
            result["errors"].append(
                _error(
                    call,
                    (
                        "Instrucción no permitida: {}."
                        .format(
                            command
                        )
                    )
                )
            )
            continue

        command_info = {
            "line": int(
                getattr(
                    statement,
                    "lineno",
                    0
                )
                or
                0
            ),
            "name": command
        }

        if command == "ir":

            if (
                len(
                    call.args
                )
                !=
                1
                or
                call.keywords
            ):
                result["errors"].append(
                    _error(
                        call,
                        'Uso: ir("0x000") o ir("alias").'
                    )
                )
                continue

            target = _string_literal(
                call.args[0]
            )

            if target is None:
                result["errors"].append(
                    _error(
                        call.args[0],
                        "La referencia de ir() debe ser texto."
                    )
                )
                continue

            target = target.strip()

            point_id = _canonical_point_id(
                target
            )

            resolved_id = None

            if point_id is not None:
                resolved_id = ids.get(
                    point_id.casefold()
                )

            else:
                resolved_id = aliases.get(
                    target.casefold()
                )

            if resolved_id is None:
                result["errors"].append(
                    _error(
                        call.args[0],
                        (
                            "El punto '{}' no existe en esta misión."
                            .format(
                                target
                            )
                        )
                    )
                )
                continue

            command_info[
                "target"
            ] = target

            command_info[
                "target_id"
            ] = resolved_id

        elif command == "esperar":

            if (
                len(
                    call.args
                )
                !=
                1
                or
                call.keywords
            ):
                result["errors"].append(
                    _error(
                        call,
                        "Uso: esperar(segundos)."
                    )
                )
                continue

            seconds = _number_literal(
                call.args[0]
            )

            if (
                seconds is None
                or
                not math.isfinite(
                    seconds
                )
                or
                seconds < 0
            ):
                result["errors"].append(
                    _error(
                        call.args[0],
                        "El tiempo debe ser un número mayor o igual a 0."
                    )
                )
                continue

            command_info[
                "seconds"
            ] = seconds

        elif command in (
            "orientar",
            "girar"
        ):

            before = len(
                result["errors"]
            )

            _validate_velocity(
                call,
                result["errors"]
            )

            if (
                len(
                    result["errors"]
                )
                !=
                before
            ):
                continue

            command_info[
                "angle"
            ] = _number_literal(
                call.args[0]
            )

            if call.keywords:
                command_info[
                    "velocity"
                ] = _number_literal(
                    call.keywords[0].value
                )

        elif command == "relocalizar":

            if (
                call.args
                or
                call.keywords
            ):
                result["errors"].append(
                    _error(
                        call,
                        "Uso: relocalizar()."
                    )
                )
                continue

        result["commands"].append(
            command_info
        )

    result["command_count"] = len(
        result["commands"]
    )

    result["ok"] = (
        len(
            result["errors"]
        )
        ==
        0
    )

    return result
