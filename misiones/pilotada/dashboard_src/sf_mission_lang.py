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

VARIABLE_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*$"
)

# Acciones que el robot ejecuta realmente.
ALLOWED_COMMANDS = {
    "ir",
    "esperar",
    "orientar"
}

# Acciones que el lenguaje reconocia pero que el ejecutor nunca llego a
# implementar: sf_mission_executor.py solo admite {esperar, ir, orientar} y
# rechaza la mision entera al arrancar. Se retiran del validador para que el
# error aparezca al escribir y no despues de preparar la mision.
RETIRED_COMMANDS = {
    "girar": (
        "girar() no esta implementada: el robot no la ejecuta. "
        "Para cambiar la orientacion usa orientar()."
    ),
    "relocalizar": (
        "relocalizar() no esta implementada: el robot no la ejecuta. "
        "Fija la pose inicial desde el dashboard antes de lanzar la mision."
    )
}

RESERVED_NAMES = (
    ALLOWED_COMMANDS
    |
    set(RETIRED_COMMANDS)
    |
    {
        "range",
        "True",
        "False",
        "None"
    }
)

ALLOWED_BIN_OPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod
)

ALLOWED_AUG_OPS = ALLOWED_BIN_OPS

ALLOWED_COMPARE_OPS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE
)

MAX_RANGE_ITERATIONS = 10000
MAX_RANGE_ARGUMENT = 100000


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


def _integer_literal(
    node
):
    value = _number_literal(
        node
    )

    if (
        value is None
        or
        not math.isfinite(
            value
        )
        or
        int(
            value
        )
        !=
        value
    ):
        return None

    return int(
        value
    )


def _bool_literal(
    node
):
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
            bool
        )
    ):
        return node.value

    name_constant = getattr(
        ast,
        "NameConstant",
        None
    )

    if (
        name_constant is not None
        and
        isinstance(
            node,
            name_constant
        )
        and
        isinstance(
            node.value,
            bool
        )
    ):
        return node.value

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


def _valid_variable_name(
    name
):
    return (
        isinstance(
            name,
            str
        )
        and
        VARIABLE_RE.match(
            name
        )
        is not None
        and
        name not in RESERVED_NAMES
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

        id_key = point_id.casefold()

        if id_key in ids:
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
            ids[
                id_key
            ] = point_id

        alias = str(
            point.get(
                "alias",
                ""
            )
            or
            ""
        ).strip()

        if not alias:
            continue

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

            continue

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


def _validate_expression(
    node,
    variables,
    errors
):
    if _number_literal(
        node
    ) is not None:
        return True

    if _bool_literal(
        node
    ) is not None:
        return True

    if isinstance(
        node,
        ast.Name
    ):
        if node.id not in variables:
            errors.append(
                _error(
                    node,
                    (
                        "Variable no definida: {}."
                        .format(
                            node.id
                        )
                    )
                )
            )

            return False

        return True

    if isinstance(
        node,
        ast.UnaryOp
    ):
        if not isinstance(
            node.op,
            (
                ast.UAdd,
                ast.USub,
                ast.Not
            )
        ):
            errors.append(
                _error(
                    node,
                    "Operador unario no permitido."
                )
            )

            return False

        return _validate_expression(
            node.operand,
            variables,
            errors
        )

    if isinstance(
        node,
        ast.BinOp
    ):
        if not isinstance(
            node.op,
            ALLOWED_BIN_OPS
        ):
            errors.append(
                _error(
                    node,
                    "Operación matemática no permitida."
                )
            )

            return False

        left_ok = _validate_expression(
            node.left,
            variables,
            errors
        )

        right_ok = _validate_expression(
            node.right,
            variables,
            errors
        )

        if isinstance(
            node.op,
            (
                ast.Div,
                ast.FloorDiv,
                ast.Mod
            )
        ):
            divisor = _number_literal(
                node.right
            )

            if divisor == 0:
                errors.append(
                    _error(
                        node.right,
                        "División entre cero."
                    )
                )

                right_ok = False

        return (
            left_ok
            and
            right_ok
        )

    if isinstance(
        node,
        ast.BoolOp
    ):
        if not isinstance(
            node.op,
            (
                ast.And,
                ast.Or
            )
        ):
            errors.append(
                _error(
                    node,
                    "Operador lógico no permitido."
                )
            )

            return False

        ok = True

        for value in node.values:
            if not _validate_expression(
                value,
                variables,
                errors
            ):
                ok = False

        return ok

    if isinstance(
        node,
        ast.Compare
    ):
        ok = _validate_expression(
            node.left,
            variables,
            errors
        )

        for operator in node.ops:
            if not isinstance(
                operator,
                ALLOWED_COMPARE_OPS
            ):
                errors.append(
                    _error(
                        node,
                        "Comparación no permitida."
                    )
                )

                ok = False

        for comparator in node.comparators:
            if not _validate_expression(
                comparator,
                variables,
                errors
            ):
                ok = False

        return ok

    errors.append(
        _error(
            node,
            (
                "Expresión no permitida: {}."
                .format(
                    type(
                        node
                    ).__name__
                )
            )
        )
    )

    return False


def _validate_range(
    node,
    variables,
    errors
):
    if (
        not isinstance(
            node,
            ast.Call
        )
        or
        not isinstance(
            node.func,
            ast.Name
        )
        or
        node.func.id != "range"
    ):
        errors.append(
            _error(
                node,
                "El for solo permite range(...)."
            )
        )

        return False

    if node.keywords:
        errors.append(
            _error(
                node,
                "range() no acepta parámetros nombrados."
            )
        )

        return False

    if not (
        1
        <=
        len(
            node.args
        )
        <=
        3
    ):
        errors.append(
            _error(
                node,
                "range() acepta de 1 a 3 enteros."
            )
        )

        return False

    values = []

    for argument in node.args:
        value = _integer_literal(
            argument
        )

        if value is None:
            errors.append(
                _error(
                    argument,
                    "range() solo acepta enteros literales."
                )
            )

            return False

        if abs(
            value
        ) > MAX_RANGE_ARGUMENT:
            errors.append(
                _error(
                    argument,
                    "Valor de range() demasiado grande."
                )
            )

            return False

        values.append(
            value
        )

    if (
        len(
            values
        )
        == 3
        and
        values[2] == 0
    ):
        errors.append(
            _error(
                node.args[2],
                "El paso de range() no puede ser 0."
            )
        )

        return False

    try:
        iterations = len(
            range(
                *values
            )
        )

    except Exception:
        errors.append(
            _error(
                node,
                "range() inválido."
            )
        )

        return False

    if iterations > MAX_RANGE_ITERATIONS:
        errors.append(
            _error(
                node,
                (
                    "El for supera el límite de {} iteraciones."
                    .format(
                        MAX_RANGE_ITERATIONS
                    )
                )
            )
        )

        return False

    return True


def _validate_velocity_call(
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

        return False

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
                "El ángulo debe ser un número literal."
            )
        )

        return False

    if len(
        call.keywords
    ) > 1:
        errors.append(
            _error(
                call,
                "Solo se permite el parámetro velocidad."
            )
        )

        return False

    ok = True

    for keyword in call.keywords:
        if keyword.arg != "velocidad":
            errors.append(
                _error(
                    call,
                    (
                        "Parámetro no permitido: {}."
                        .format(
                            keyword.arg
                            if keyword.arg
                            else
                            "**kwargs"
                        )
                    )
                )
            )

            ok = False

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

            ok = False

    return ok


def _validate_command(
    statement,
    call,
    ids,
    aliases,
    errors,
    commands
):
    if not isinstance(
        call.func,
        ast.Name
    ):
        errors.append(
            _error(
                call,
                "Solo se permiten instrucciones SafeVision directas."
            )
        )

        return

    command = call.func.id

    if command in RETIRED_COMMANDS:
        errors.append(
            _error(
                call,
                RETIRED_COMMANDS[command]
            )
        )

        return

    if command not in ALLOWED_COMMANDS:
        errors.append(
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

        return

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

    before = len(
        errors
    )

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
            errors.append(
                _error(
                    call,
                    'Uso: ir("0x000") o ir("alias").'
                )
            )

        else:
            target = _string_literal(
                call.args[0]
            )

            if target is None:
                errors.append(
                    _error(
                        call.args[0],
                        "La referencia de ir() debe ser texto."
                    )
                )

            else:
                target = target.strip()

                point_id = _canonical_point_id(
                    target
                )

                if point_id is not None:
                    resolved_id = ids.get(
                        point_id.casefold()
                    )

                else:
                    resolved_id = aliases.get(
                        target.casefold()
                    )

                if resolved_id is None:
                    errors.append(
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

                else:
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
            errors.append(
                _error(
                    call,
                    "Uso: esperar(segundos)."
                )
            )

        else:
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
                errors.append(
                    _error(
                        call.args[0],
                        "El tiempo debe ser un número literal mayor o igual a 0."
                    )
                )

            else:
                command_info[
                    "seconds"
                ] = seconds

    elif command in (
        "orientar",
        "girar"
    ):
        if _validate_velocity_call(
            call,
            errors
        ):
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
            errors.append(
                _error(
                    call,
                    "Uso: relocalizar()."
                )
            )

    if len(
        errors
    ) == before:
        commands.append(
            command_info
        )


def _validate_assignment(
    statement,
    variables,
    errors
):
    if len(
        statement.targets
    ) != 1:
        errors.append(
            _error(
                statement,
                "Solo se permite asignar una variable a la vez."
            )
        )

        return

    target = statement.targets[0]

    if not isinstance(
        target,
        ast.Name
    ):
        errors.append(
            _error(
                target,
                "Solo se permiten variables simples."
            )
        )

        return

    if not _valid_variable_name(
        target.id
    ):
        errors.append(
            _error(
                target,
                (
                    "Nombre de variable no permitido: {}."
                    .format(
                        target.id
                    )
                )
            )
        )

        return

    if _validate_expression(
        statement.value,
        variables,
        errors
    ):
        variables.add(
            target.id
        )


def _validate_aug_assignment(
    statement,
    variables,
    errors
):
    if not isinstance(
        statement.target,
        ast.Name
    ):
        errors.append(
            _error(
                statement.target,
                "Solo se permiten variables simples."
            )
        )

        return

    name = statement.target.id

    if name not in variables:
        errors.append(
            _error(
                statement.target,
                (
                    "Variable no definida: {}."
                    .format(
                        name
                    )
                )
            )
        )

        return

    if not isinstance(
        statement.op,
        ALLOWED_AUG_OPS
    ):
        errors.append(
            _error(
                statement,
                "Operación de asignación no permitida."
            )
        )

        return

    _validate_expression(
        statement.value,
        variables,
        errors
    )


def _validate_block(
    statements,
    variables,
    ids,
    aliases,
    errors,
    commands,
    loop_depth=0
):
    for statement in statements:

        if isinstance(
            statement,
            ast.Expr
        ):
            if not isinstance(
                statement.value,
                ast.Call
            ):
                errors.append(
                    _error(
                        statement,
                        "Solo se permiten llamadas a instrucciones SafeVision."
                    )
                )

                continue

            _validate_command(
                statement,
                statement.value,
                ids,
                aliases,
                errors,
                commands
            )

            continue

        if isinstance(
            statement,
            ast.Assign
        ):
            _validate_assignment(
                statement,
                variables,
                errors
            )

            continue

        if isinstance(
            statement,
            ast.AugAssign
        ):
            _validate_aug_assignment(
                statement,
                variables,
                errors
            )

            continue

        if isinstance(
            statement,
            ast.If
        ):
            _validate_expression(
                statement.test,
                variables,
                errors
            )

            base_variables = set(
                variables
            )

            body_variables = set(
                base_variables
            )

            _validate_block(
                statement.body,
                body_variables,
                ids,
                aliases,
                errors,
                commands,
                loop_depth
            )

            if statement.orelse:
                else_variables = set(
                    base_variables
                )

                _validate_block(
                    statement.orelse,
                    else_variables,
                    ids,
                    aliases,
                    errors,
                    commands,
                    loop_depth
                )

                guaranteed = (
                    body_variables
                    &
                    else_variables
                )

            else:
                guaranteed = base_variables

            variables.clear()

            variables.update(
                guaranteed
            )

            continue

        if isinstance(
            statement,
            ast.For
        ):
            if not isinstance(
                statement.target,
                ast.Name
            ):
                errors.append(
                    _error(
                        statement.target,
                        "La variable del for debe ser un nombre simple."
                    )
                )

                continue

            loop_name = statement.target.id

            if not _valid_variable_name(
                loop_name
            ):
                errors.append(
                    _error(
                        statement.target,
                        (
                            "Nombre de variable no permitido: {}."
                            .format(
                                loop_name
                            )
                        )
                    )
                )

                continue

            range_ok = _validate_range(
                statement.iter,
                variables,
                errors
            )

            if statement.orelse:
                errors.append(
                    _error(
                        statement,
                        "for ... else todavía no está permitido."
                    )
                )

            body_variables = set(
                variables
            )

            body_variables.add(
                loop_name
            )

            if range_ok:
                _validate_block(
                    statement.body,
                    body_variables,
                    ids,
                    aliases,
                    errors,
                    commands,
                    loop_depth + 1
                )

            continue

        if isinstance(
            statement,
            ast.While
        ):
            _validate_expression(
                statement.test,
                variables,
                errors
            )

            if statement.orelse:
                errors.append(
                    _error(
                        statement,
                        "while ... else todavía no está permitido."
                    )
                )

            body_variables = set(
                variables
            )

            _validate_block(
                statement.body,
                body_variables,
                ids,
                aliases,
                errors,
                commands,
                loop_depth + 1
            )

            continue

        if isinstance(
            statement,
            ast.Break
        ):
            if loop_depth <= 0:
                errors.append(
                    _error(
                        statement,
                        "break solo puede usarse dentro de for o while."
                    )
                )

            continue

        if isinstance(
            statement,
            ast.Pass
        ):
            continue

        errors.append(
            _error(
                statement,
                (
                    "Instrucción no permitida: {}."
                    .format(
                        type(
                            statement
                        ).__name__
                    )
                )
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

    variables = set()

    _validate_block(
        tree.body,
        variables,
        ids,
        aliases,
        result["errors"],
        result["commands"],
        0
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



# =========================================================
# EVALUADOR SEGURO PARA SIMULACION
# =========================================================

MAX_SIMULATION_STEPS = 2000
MAX_SIMULATION_ACTIONS = 1000


class _SimulationRuntimeError(
    Exception
):
    def __init__(
        self,
        node,
        message
    ):
        super().__init__(
            message
        )

        self.node = node
        self.message = message


class _SimulationBreak(
    Exception
):
    pass


def _simulation_tick(
    state,
    node
):
    state["steps"] += 1

    if (
        state["steps"]
        >
        state["max_steps"]
    ):
        raise _SimulationRuntimeError(
            node,
            (
                "La simulación superó el límite de {} pasos."
                .format(
                    state["max_steps"]
                )
            )
        )


def _simulation_binary(
    operator,
    left,
    right,
    node
):
    try:
        if isinstance(
            operator,
            ast.Add
        ):
            return left + right

        if isinstance(
            operator,
            ast.Sub
        ):
            return left - right

        if isinstance(
            operator,
            ast.Mult
        ):
            return left * right

        if isinstance(
            operator,
            ast.Div
        ):
            return left / right

        if isinstance(
            operator,
            ast.FloorDiv
        ):
            return left // right

        if isinstance(
            operator,
            ast.Mod
        ):
            return left % right

    except ZeroDivisionError:
        raise _SimulationRuntimeError(
            node,
            "División entre cero durante la simulación."
        )

    except Exception:
        raise _SimulationRuntimeError(
            node,
            "No se pudo evaluar la operación matemática."
        )

    raise _SimulationRuntimeError(
        node,
        "Operación matemática no permitida."
    )


def _simulation_compare(
    operator,
    left,
    right,
    node
):
    try:
        if isinstance(
            operator,
            ast.Eq
        ):
            return left == right

        if isinstance(
            operator,
            ast.NotEq
        ):
            return left != right

        if isinstance(
            operator,
            ast.Lt
        ):
            return left < right

        if isinstance(
            operator,
            ast.LtE
        ):
            return left <= right

        if isinstance(
            operator,
            ast.Gt
        ):
            return left > right

        if isinstance(
            operator,
            ast.GtE
        ):
            return left >= right

    except Exception:
        raise _SimulationRuntimeError(
            node,
            "No se pudo evaluar la comparación."
        )

    raise _SimulationRuntimeError(
        node,
        "Comparación no permitida."
    )


def _simulation_expression(
    node,
    variables
):
    number = _number_literal(
        node
    )

    if number is not None:
        return number

    boolean = _bool_literal(
        node
    )

    if boolean is not None:
        return boolean

    if isinstance(
        node,
        ast.Name
    ):
        if node.id not in variables:
            raise _SimulationRuntimeError(
                node,
                (
                    "Variable no definida durante la simulación: {}."
                    .format(
                        node.id
                    )
                )
            )

        return variables[
            node.id
        ]

    if isinstance(
        node,
        ast.UnaryOp
    ):
        value = _simulation_expression(
            node.operand,
            variables
        )

        if isinstance(
            node.op,
            ast.UAdd
        ):
            return +value

        if isinstance(
            node.op,
            ast.USub
        ):
            return -value

        if isinstance(
            node.op,
            ast.Not
        ):
            return not bool(
                value
            )

        raise _SimulationRuntimeError(
            node,
            "Operador unario no permitido."
        )

    if isinstance(
        node,
        ast.BinOp
    ):
        left = _simulation_expression(
            node.left,
            variables
        )

        right = _simulation_expression(
            node.right,
            variables
        )

        return _simulation_binary(
            node.op,
            left,
            right,
            node
        )

    if isinstance(
        node,
        ast.BoolOp
    ):
        if isinstance(
            node.op,
            ast.And
        ):
            for value_node in node.values:
                value = _simulation_expression(
                    value_node,
                    variables
                )

                if not bool(
                    value
                ):
                    return False

            return True

        if isinstance(
            node.op,
            ast.Or
        ):
            for value_node in node.values:
                value = _simulation_expression(
                    value_node,
                    variables
                )

                if bool(
                    value
                ):
                    return True

            return False

        raise _SimulationRuntimeError(
            node,
            "Operador lógico no permitido."
        )

    if isinstance(
        node,
        ast.Compare
    ):
        left = _simulation_expression(
            node.left,
            variables
        )

        for operator, comparator in zip(
            node.ops,
            node.comparators
        ):
            right = _simulation_expression(
                comparator,
                variables
            )

            if not _simulation_compare(
                operator,
                left,
                right,
                node
            ):
                return False

            left = right

        return True

    raise _SimulationRuntimeError(
        node,
        (
            "Expresión no soportada durante simulación: {}."
            .format(
                type(
                    node
                ).__name__
            )
        )
    )


def _simulation_range(
    node
):
    values = []

    for argument in node.args:
        value = _integer_literal(
            argument
        )

        if value is None:
            raise _SimulationRuntimeError(
                argument,
                "range() requiere enteros literales."
            )

        values.append(
            value
        )

    try:
        return range(
            *values
        )

    except Exception:
        raise _SimulationRuntimeError(
            node,
            "range() inválido."
        )


def _simulation_add_action(
    trace,
    state,
    action,
    node
):
    if (
        len(
            trace
        )
        >=
        state["max_actions"]
    ):
        raise _SimulationRuntimeError(
            node,
            (
                "La simulación superó el límite de {} acciones."
                .format(
                    state["max_actions"]
                )
            )
        )

    trace.append(
        action
    )


def _simulation_command(
    statement,
    call,
    ids,
    aliases,
    trace,
    state
):
    command = call.func.id

    action = {
        "name": command,
        "line": int(
            getattr(
                statement,
                "lineno",
                0
            )
            or
            0
        )
    }

    if command == "ir":
        target = (
            _string_literal(
                call.args[0]
            )
            or
            ""
        ).strip()

        point_id = _canonical_point_id(
            target
        )

        if point_id is not None:
            resolved_id = ids.get(
                point_id.casefold()
            )

        else:
            resolved_id = aliases.get(
                target.casefold()
            )

        if resolved_id is None:
            raise _SimulationRuntimeError(
                call,
                (
                    "El punto '{}' no existe."
                    .format(
                        target
                    )
                )
            )

        action["target"] = target
        action["target_id"] = resolved_id

    elif command == "esperar":
        action["seconds"] = _number_literal(
            call.args[0]
        )

    elif command in (
        "orientar",
        "girar"
    ):
        action["angle"] = _number_literal(
            call.args[0]
        )

        if call.keywords:
            action["velocity"] = _number_literal(
                call.keywords[0].value
            )

    _simulation_add_action(
        trace,
        state,
        action,
        statement
    )


def _simulation_assign(
    statement,
    variables
):
    target = statement.targets[
        0
    ]

    variables[
        target.id
    ] = _simulation_expression(
        statement.value,
        variables
    )


def _simulation_aug_assign(
    statement,
    variables
):
    name = statement.target.id

    left = variables[
        name
    ]

    right = _simulation_expression(
        statement.value,
        variables
    )

    variables[
        name
    ] = _simulation_binary(
        statement.op,
        left,
        right,
        statement
    )


def _simulation_block(
    statements,
    variables,
    ids,
    aliases,
    trace,
    state,
    loop_depth=0
):
    for statement in statements:
        _simulation_tick(
            state,
            statement
        )

        if isinstance(
            statement,
            ast.Expr
        ):
            _simulation_command(
                statement,
                statement.value,
                ids,
                aliases,
                trace,
                state
            )

            continue

        if isinstance(
            statement,
            ast.Assign
        ):
            _simulation_assign(
                statement,
                variables
            )

            continue

        if isinstance(
            statement,
            ast.AugAssign
        ):
            _simulation_aug_assign(
                statement,
                variables
            )

            continue

        if isinstance(
            statement,
            ast.If
        ):
            condition = _simulation_expression(
                statement.test,
                variables
            )

            branch = (
                statement.body
                if bool(
                    condition
                )
                else
                statement.orelse
            )

            _simulation_block(
                branch,
                variables,
                ids,
                aliases,
                trace,
                state,
                loop_depth
            )

            continue

        if isinstance(
            statement,
            ast.For
        ):
            loop_name = statement.target.id

            for value in _simulation_range(
                statement.iter
            ):
                _simulation_tick(
                    state,
                    statement
                )

                variables[
                    loop_name
                ] = value

                try:
                    _simulation_block(
                        statement.body,
                        variables,
                        ids,
                        aliases,
                        trace,
                        state,
                        loop_depth + 1
                    )

                except _SimulationBreak:
                    break

            continue

        if isinstance(
            statement,
            ast.While
        ):
            while True:
                _simulation_tick(
                    state,
                    statement
                )

                condition = _simulation_expression(
                    statement.test,
                    variables
                )

                if not bool(
                    condition
                ):
                    break

                try:
                    _simulation_block(
                        statement.body,
                        variables,
                        ids,
                        aliases,
                        trace,
                        state,
                        loop_depth + 1
                    )

                except _SimulationBreak:
                    break

            continue

        if isinstance(
            statement,
            ast.Break
        ):
            raise _SimulationBreak()

        if isinstance(
            statement,
            ast.Pass
        ):
            continue

        raise _SimulationRuntimeError(
            statement,
            (
                "Instrucción no soportada durante simulación: {}."
                .format(
                    type(
                        statement
                    ).__name__
                )
            )
        )


def simulate_program(
    code,
    points,
    max_steps=MAX_SIMULATION_STEPS,
    max_actions=MAX_SIMULATION_ACTIONS
):
    validation = validate_program(
        code,
        points
    )

    result = {
        "ok": False,
        "errors": [],
        "trace": [],
        "action_count": 0,
        "steps": 0
    }

    if not validation["ok"]:
        result["errors"] = validation[
            "errors"
        ]

        return result

    ids, aliases, context_errors = (
        _build_point_context(
            points
        )
    )

    if context_errors:
        result["errors"] = context_errors
        return result

    try:
        tree = ast.parse(
            code,
            mode="exec"
        )

        variables = {}

        state = {
            "steps": 0,
            "max_steps": int(
                max_steps
            ),
            "max_actions": int(
                max_actions
            )
        }

        trace = []

        _simulation_block(
            tree.body,
            variables,
            ids,
            aliases,
            trace,
            state,
            0
        )

        result["ok"] = True
        result["trace"] = trace
        result["action_count"] = len(
            trace
        )
        result["steps"] = state[
            "steps"
        ]

        return result

    except _SimulationRuntimeError as exc:
        result["errors"] = [
            _error(
                exc.node,
                exc.message
            )
        ]

        if "state" in locals():
            result["steps"] = state[
                "steps"
            ]

        if "trace" in locals():
            result["trace"] = trace
            result["action_count"] = len(
                trace
            )

        return result

    except _SimulationBreak:
        result["errors"] = [{
            "line": 0,
            "column": 0,
            "message": "break fuera de un ciclo durante simulación."
        }]

        return result
