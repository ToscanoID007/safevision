"use strict";


// =========================================================
// SAFEVISION - SIMULADOR LOCAL
// =========================================================

const progSimulation = {
    running: false,
    paused: false,
    actionActive: false,

    token: 0,

    trace: [],
    index: 0,

    stepBudget: 0,
    gateWaiters: [],

    history: [],

    pose: null,
    path: [],

    pointMap: new Map(),

    currentPointId: null,
    referenceYaw: null
};


function ensureProgSimulationCanvas() {

    const scene =
        $p("progMapScene");

    if (!scene) {
        return null;
    }


    let canvas =
        $p("progSimulationCanvas");


    if (!canvas) {

        canvas =
            document.createElement(
                "canvas"
            );

        canvas.id =
            "progSimulationCanvas";

        canvas.style.position =
            "absolute";

        canvas.style.inset =
            "0";

        canvas.style.zIndex =
            "28";

        canvas.style.width =
            "100%";

        canvas.style.height =
            "100%";

        canvas.style.pointerEvents =
            "none";

        canvas.style.userSelect =
            "none";


        scene.appendChild(
            canvas
        );
    }


    return canvas;
}


function renderProgSimulation() {

    const scene =
        $p("progMapScene");

    const image =
        $p("progMapImage");

    const canvas =
        ensureProgSimulationCanvas();

    const layout =
        getProgImageLayout();


    if (
        !scene
        ||
        !image
        ||
        !canvas
        ||
        !layout
        ||
        image.offsetParent === null
    ) {
        return;
    }


    const width =
        scene.clientWidth;

    const height =
        scene.clientHeight;


    if (
        width <= 0
        ||
        height <= 0
    ) {
        return;
    }


    const zoomScale =
        Math.max(
            1,
            Number(
                progMapView.scale || 1
            )
        );

    const deviceScale =
        Math.max(
            1,
            window.devicePixelRatio || 1
        );

    const renderScale =
        Math.min(
            5,
            zoomScale * deviceScale
        );


    const targetWidth =
        Math.max(
            1,
            Math.round(
                width * renderScale
            )
        );

    const targetHeight =
        Math.max(
            1,
            Math.round(
                height * renderScale
            )
        );


    if (
        canvas.width !== targetWidth
    ) {
        canvas.width =
            targetWidth;
    }


    if (
        canvas.height !== targetHeight
    ) {
        canvas.height =
            targetHeight;
    }


    const ctx =
        canvas.getContext(
            "2d"
        );


    if (!ctx) {
        return;
    }


    ctx.setTransform(
        renderScale,
        0,
        0,
        renderScale,
        0,
        0
    );


    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    if (!progSimulation.pose) {
        return;
    }


    const compensation =
        1 /
        Math.max(
            0.01,
            Number(
                progMapView.scale || 1
            )
        );


    const toScreen =
        point => ({
            x:
                layout.left
                +
                Number(point.u)
                *
                layout.width,

            y:
                layout.top
                +
                Number(point.v)
                *
                layout.height
        });


    if (
        progSimulation.path.length >= 2
    ) {

        ctx.beginPath();


        progSimulation.path.forEach(
            (
                point,
                index
            ) => {

                const screen =
                    toScreen(
                        point
                    );


                if (index === 0) {

                    ctx.moveTo(
                        screen.x,
                        screen.y
                    );

                } else {

                    ctx.lineTo(
                        screen.x,
                        screen.y
                    );
                }
            }
        );


        ctx.lineWidth =
            2 * compensation;

        ctx.strokeStyle =
            "#60a5fa";

        ctx.setLineDash([
            6 * compensation,
            4 * compensation
        ]);

        ctx.stroke();

        ctx.setLineDash([]);
    }


    const robot =
        toScreen(
            progSimulation.pose
        );

    const radius =
        7 * compensation;


    ctx.save();

    ctx.translate(
        robot.x,
        robot.y
    );

    ctx.rotate(
        -Number(
            progSimulation.pose.yaw || 0
        )
    );


    ctx.beginPath();

    ctx.arc(
        0,
        0,
        radius,
        0,
        Math.PI * 2
    );

    ctx.fillStyle =
        "#f97316";

    ctx.fill();

    ctx.lineWidth =
        1.5 * compensation;

    ctx.strokeStyle =
        "#ffffff";

    ctx.stroke();


    ctx.beginPath();

    ctx.moveTo(
        radius + 7 * compensation,
        0
    );

    ctx.lineTo(
        radius - 1 * compensation,
        -4 * compensation
    );

    ctx.lineTo(
        radius - 1 * compensation,
        4 * compensation
    );

    ctx.closePath();

    ctx.fillStyle =
        "#ffffff";

    ctx.fill();


    ctx.restore();
}


function updateProgSimulationButtons() {

    const simulate =
        $p("progSimulateButton");

    const restart =
        $p("progRestartSimulationButton");

    const previous =
        $p("progPreviousSimulationButton");

    const pause =
        $p("progPauseSimulationButton");

    const step =
        $p("progStepSimulationButton");

    const stop =
        $p("progStopSimulationButton");


    if (simulate) {

        simulate.disabled =
            (
                progSimulation.running
                &&
                !progSimulation.paused
            );

        simulate.textContent =
            (
                progSimulation.running
                &&
                !progSimulation.paused
            )
                ?
                "Simulando..."
                :
                "Simular";
    }


    if (restart) {

        restart.disabled =
            progSimulation.actionActive;
    }


    if (previous) {

        previous.disabled =
            progSimulation.actionActive;
    }


    if (pause) {

        pause.disabled =
            !progSimulation.running;

        pause.textContent =
            progSimulation.paused
                ?
                "Reanudar"
                :
                "Pausar";
    }


    if (step) {

        step.disabled =
            (
                progSimulation.actionActive
                ||
                (
                    progSimulation.running
                    &&
                    !progSimulation.paused
                )
            );
    }


    if (stop) {

        stop.disabled =
            !progSimulation.running;
    }
}


function wakeProgSimulationGate() {

    const waiters =
        progSimulation.gateWaiters.splice(
            0,
            progSimulation.gateWaiters.length
        );


    waiters.forEach(
        resolve => {
            resolve();
        }
    );
}


async function waitProgSimulationPermission(
    token
) {

    while (
        progSimulation.running
        &&
        progSimulation.token === token
    ) {

        if (!progSimulation.paused) {

            return {
                ok: true,
                stepped: false
            };
        }


        if (
            progSimulation.stepBudget > 0
        ) {

            progSimulation.stepBudget -= 1;


            updateProgSimulationButtons();


            return {
                ok: true,
                stepped: true
            };
        }


        await new Promise(
            resolve => {

                progSimulation.gateWaiters.push(
                    resolve
                );
            }
        );
    }


    return {
        ok: false,
        stepped: false
    };
}


function toggleProgSimulationPause() {

    if (!progSimulation.running) {
        return;
    }


    if (progSimulation.paused) {

        progSimulation.paused =
            false;

        progSimulation.stepBudget =
            0;


        wakeProgSimulationGate();

        updateProgSimulationButtons();


        progLog(
            "▶ Simulación reanudada."
        );

        return;
    }


    progSimulation.paused =
        true;

    progSimulation.stepBudget =
        0;


    updateProgSimulationButtons();


    progLog(
        "⏸ Pausa solicitada · se aplicará al terminar la acción actual."
    );
}


async function stepProgSimulation() {

    if (progSimulation.actionActive) {

        progLog(
            "✗ Paso no disponible: hay una acción en ejecución."
        );

        return;
    }


    if (!progSimulation.running) {

        await startProgSimulation(
            true,
            true,
            "step"
        );

        return;
    }


    if (!progSimulation.paused) {

        progLog(
            "✗ Paso no disponible: pausa primero la simulación."
        );

        return;
    }


    progSimulation.stepBudget +=
        1;


    wakeProgSimulationGate();

    updateProgSimulationButtons();
}


function progSimulationActionDescription(
    action
) {

    if (!action) {
        return "acción";
    }


    if (action.name === "ir") {

        return (
            "ir → "
            +
            (
                action.target_id
                ||
                action.target
                ||
                "?"
            )
        );
    }


    if (action.name === "girar") {

        return (
            "girar "
            +
            action.angle
            +
            "°"
        );
    }


    if (action.name === "orientar") {

        return (
            "orientar "
            +
            action.angle
            +
            "°"
        );
    }


    if (action.name === "esperar") {

        return (
            "esperar "
            +
            action.seconds
            +
            " s"
        );
    }


    if (action.name === "relocalizar") {

        return "relocalizar";
    }


    return String(
        action.name
        ||
        "acción"
    );
}


function logProgSimulationAction(
    action,
    index,
    stepped
) {

    const line =
        Number(
            action.line
        );


    progLog(
        (
            stepped
                ?
                "▶ Paso "
                :
                "▶ Acción "
        )
        +
        (
            index + 1
        )
        +
        "/"
        +
        progSimulation.trace.length
        +
        (
            Number.isFinite(line)
            &&
            line > 0
                ?
                " · línea "
                +
                line
                :
                ""
        )
        +
        " · "
        +
        progSimulationActionDescription(
            action
        )
    );
}


function captureProgSimulationState(
    index
) {

    return {
        index:
            index,

        pose:
            progSimulation.pose
                ?
                {
                    ...progSimulation.pose
                }
                :
                null,

        path:
            progSimulation.path.map(
                point => ({
                    ...point
                })
            ),

        currentPointId:
            progSimulation.currentPointId,

        referenceYaw:
            progSimulation.referenceYaw
    };
}


function restoreProgSimulationState(
    snapshot
) {

    progSimulation.pose =
        snapshot.pose
            ?
            {
                ...snapshot.pose
            }
            :
            null;


    progSimulation.path =
        snapshot.path.map(
            point => ({
                ...point
            })
        );


    progSimulation.currentPointId =
        snapshot.currentPointId;

    progSimulation.referenceYaw =
        snapshot.referenceYaw;

    progSimulation.index =
        snapshot.index;


    renderProgSimulation();

    updateProgSimulationButtons();
}


function previousProgSimulationStep() {

    if (progSimulation.actionActive) {

        progLog(
            "✗ Paso anterior no disponible: hay una acción en ejecución."
        );

        return;
    }


    if (
        !progSimulation.running
        ||
        !progSimulation.paused
    ) {

        if (
            progSimulation.history.length === 0
        ) {

            progLog(
                "✗ Paso anterior: ya estás en el inicio de la simulación."
            );

            return;
        }


        progLog(
            "✗ Paso anterior: pausa primero la simulación."
        );

        return;
    }


    if (
        progSimulation.history.length === 0
    ) {

        progLog(
            "✗ Paso anterior: ya estás en el inicio de la simulación."
        );

        return;
    }


    progSimulation.stepBudget =
        0;


    const snapshot =
        progSimulation.history.pop();


    restoreProgSimulationState(
        snapshot
    );


    progLog(
        "◀ Paso anterior · acción "
        +
        (
            snapshot.index + 1
        )
        +
        "/"
        +
        progSimulation.trace.length
        +
        " deshecha."
    );
}


async function restartProgSimulation() {

    if (progSimulation.actionActive) {

        progLog(
            "✗ Reiniciar no disponible: espera a que termine la acción actual."
        );

        return;
    }


    stopProgSimulation(
        true
    );


    await new Promise(
        resolve => {

            window.setTimeout(
                resolve,
                20
            );
        }
    );


    await startProgSimulation(
        true,
        false,
        "restart"
    );
}




function normalizeProgSimulationAngle(
    angle
) {

    let value =
        Number(angle || 0);


    while (
        value > Math.PI
    ) {

        value -=
            Math.PI * 2;
    }


    while (
        value < -Math.PI
    ) {

        value +=
            Math.PI * 2;
    }


    return value;
}


function progSimulationWait(
    milliseconds,
    token
) {

    return new Promise(
        resolve => {

            window.setTimeout(
                () => {

                    resolve(
                        progSimulation.running
                        &&
                        progSimulation.token === token
                    );

                },
                Math.max(
                    0,
                    Number(milliseconds || 0)
                )
            );
        }
    );
}


function animateProgSimulationYaw(
    targetYaw,
    duration,
    token
) {

    return new Promise(
        resolve => {

            if (
                !progSimulation.pose
                ||
                !progSimulation.running
                ||
                progSimulation.token !== token
            ) {

                resolve(false);
                return;
            }


            const startYaw =
                Number(
                    progSimulation.pose.yaw || 0
                );

            const delta =
                normalizeProgSimulationAngle(
                    targetYaw - startYaw
                );

            const startTime =
                performance.now();

            const total =
                Math.max(
                    80,
                    Number(duration || 300)
                );


            const frame =
                now => {

                    if (
                        !progSimulation.running
                        ||
                        progSimulation.token !== token
                    ) {

                        resolve(false);
                        return;
                    }


                    const progress =
                        Math.min(
                            1,
                            (
                                now - startTime
                            )
                            /
                            total
                        );


                    progSimulation.pose.yaw =
                        normalizeProgSimulationAngle(
                            startYaw
                            +
                            delta * progress
                        );


                    renderProgSimulation();


                    if (
                        progress >= 1
                    ) {

                        resolve(true);
                        return;
                    }


                    window.requestAnimationFrame(
                        frame
                    );
                };


            window.requestAnimationFrame(
                frame
            );
        }
    );
}


function animateProgSimulationMove(
    target,
    duration,
    token
) {

    return new Promise(
        resolve => {

            if (
                !progSimulation.pose
                ||
                !progSimulation.running
                ||
                progSimulation.token !== token
            ) {

                resolve(false);
                return;
            }


            const start = {
                u:
                    Number(
                        progSimulation.pose.u
                    ),

                v:
                    Number(
                        progSimulation.pose.v
                    ),

                x:
                    Number(
                        progSimulation.pose.x
                    ),

                y:
                    Number(
                        progSimulation.pose.y
                    )
            };


            const startTime =
                performance.now();

            const total =
                Math.max(
                    120,
                    Number(duration || 800)
                );


            const frame =
                now => {

                    if (
                        !progSimulation.running
                        ||
                        progSimulation.token !== token
                    ) {

                        resolve(false);
                        return;
                    }


                    const progress =
                        Math.min(
                            1,
                            (
                                now - startTime
                            )
                            /
                            total
                        );


                    progSimulation.pose.u =
                        start.u
                        +
                        (
                            Number(target.u)
                            -
                            start.u
                        )
                        *
                        progress;

                    progSimulation.pose.v =
                        start.v
                        +
                        (
                            Number(target.v)
                            -
                            start.v
                        )
                        *
                        progress;


                    if (
                        Number.isFinite(start.x)
                        &&
                        Number.isFinite(
                            Number(target.x)
                        )
                    ) {

                        progSimulation.pose.x =
                            start.x
                            +
                            (
                                Number(target.x)
                                -
                                start.x
                            )
                            *
                            progress;
                    }


                    if (
                        Number.isFinite(start.y)
                        &&
                        Number.isFinite(
                            Number(target.y)
                        )
                    ) {

                        progSimulation.pose.y =
                            start.y
                            +
                            (
                                Number(target.y)
                                -
                                start.y
                            )
                            *
                            progress;
                    }


                    renderProgSimulation();


                    if (
                        progress >= 1
                    ) {

                        resolve(true);
                        return;
                    }


                    window.requestAnimationFrame(
                        frame
                    );
                };


            window.requestAnimationFrame(
                frame
            );
        }
    );
}


function progSimulationTurnDuration(
    angleRadians,
    velocity
) {

    const radians =
        Math.abs(
            Number(angleRadians || 0)
        );

    const speed =
        Number(velocity);


    if (
        Number.isFinite(speed)
        &&
        speed > 0
    ) {

        return Math.min(
            2200,
            Math.max(
                120,
                (
                    radians / speed
                )
                *
                350
            )
        );
    }


    return Math.min(
        1200,
        Math.max(
            180,
            250 + radians * 260
        )
    );
}


function progSimulationMoveDuration(
    target
) {

    if (!progSimulation.pose) {
        return 700;
    }


    const x1 =
        Number(
            progSimulation.pose.x
        );

    const y1 =
        Number(
            progSimulation.pose.y
        );

    const x2 =
        Number(
            target.x
        );

    const y2 =
        Number(
            target.y
        );


    if (
        Number.isFinite(x1)
        &&
        Number.isFinite(y1)
        &&
        Number.isFinite(x2)
        &&
        Number.isFinite(y2)
    ) {

        const distance =
            Math.hypot(
                x2 - x1,
                y2 - y1
            );


        return Math.min(
            1800,
            Math.max(
                400,
                300 + distance * 300
            )
        );
    }


    return 800;
}


function stopProgSimulation(
    silent = false
) {

    const wasRunning =
        progSimulation.running;


    progSimulation.token += 1;

    progSimulation.running =
        false;

    progSimulation.paused =
        false;

    progSimulation.actionActive =
        false;

    progSimulation.stepBudget =
        0;


    wakeProgSimulationGate();


    updateProgSimulationButtons();

    renderProgSimulation();


    if (
        wasRunning
        &&
        !silent
    ) {

        progLog(
            "Simulación detenida."
        );
    }
}


function clearProgSimulation(
    silent = true
) {

    stopProgSimulation(
        silent
    );


    progSimulation.trace = [];

    progSimulation.index = 0;

    progSimulation.paused =
        false;

    progSimulation.actionActive =
        false;

    progSimulation.stepBudget =
        0;

    progSimulation.gateWaiters =
        [];

    progSimulation.history =
        [];

    progSimulation.pose = null;

    progSimulation.path = [];

    progSimulation.pointMap =
        new Map();

    progSimulation.currentPointId =
        null;

    progSimulation.referenceYaw =
        null;


    renderProgSimulation();

    updateProgSimulationButtons();
}


async function executeProgSimulationAction(
    action,
    token
) {

    if (
        !progSimulation.running
        ||
        progSimulation.token !== token
    ) {

        return false;
    }


    if (
        action.name === "ir"
    ) {

        const target =
            progSimulation.pointMap.get(
                action.target_id
            );


        if (!target) {

            throw new Error(
                "Punto no disponible: "
                +
                action.target_id
            );
        }


        const du =
            Number(target.u)
            -
            Number(
                progSimulation.pose.u
            );

        const dv =
            Number(target.v)
            -
            Number(
                progSimulation.pose.v
            );


        if (
            Math.hypot(
                du,
                dv
            ) > 0.00001
        ) {

            const travelYaw =
                Math.atan2(
                    -dv,
                    du
                );


            if (
                !await animateProgSimulationYaw(
                    travelYaw,
                    220,
                    token
                )
            ) {
                return false;
            }
        }


        if (
            !await animateProgSimulationMove(
                target,
                progSimulationMoveDuration(
                    target
                ),
                token
            )
        ) {
            return false;
        }


        progSimulation.path.push({
            u:
                Number(target.u),

            v:
                Number(target.v)
        });


        progSimulation.currentPointId =
            target.id;


        const hasYaw =
            (
                target.yaw !== null
                &&
                target.yaw !== undefined
                &&
                Number.isFinite(
                    Number(target.yaw)
                )
            );


        if (hasYaw) {

            const targetYaw =
                Number(target.yaw);


            if (
                !await animateProgSimulationYaw(
                    targetYaw,
                    350,
                    token
                )
            ) {
                return false;
            }


            progSimulation.referenceYaw =
                targetYaw;

        } else {

            progSimulation.referenceYaw =
                null;
        }


        renderProgSimulation();

        return true;
    }


    if (
        action.name === "girar"
    ) {

        const angle =
            Number(action.angle)
            *
            Math.PI
            /
            180;

        const targetYaw =
            normalizeProgSimulationAngle(
                Number(
                    progSimulation.pose.yaw || 0
                )
                +
                angle
            );


        return await animateProgSimulationYaw(
            targetYaw,
            progSimulationTurnDuration(
                angle,
                action.velocity
            ),
            token
        );
    }


    if (
        action.name === "orientar"
    ) {

        if (
            progSimulation.referenceYaw === null
            ||
            progSimulation.referenceYaw === undefined
        ) {

            throw new Error(
                "orientar() requiere un punto actual con orientación guardada."
            );
        }


        const angle =
            Number(action.angle)
            *
            Math.PI
            /
            180;

        const targetYaw =
            normalizeProgSimulationAngle(
                Number(
                    progSimulation.referenceYaw
                )
                +
                angle
            );


        return await animateProgSimulationYaw(
            targetYaw,
            progSimulationTurnDuration(
                angle,
                action.velocity
            ),
            token
        );
    }


    if (
        action.name === "esperar"
    ) {

        const milliseconds =
            Math.min(
                2500,
                Math.max(
                    0,
                    Number(
                        action.seconds || 0
                    )
                    *
                    350
                )
            );


        return await progSimulationWait(
            milliseconds,
            token
        );
    }


    if (
        action.name === "relocalizar"
    ) {

        return await progSimulationWait(
            450,
            token
        );
    }


    return true;
}


function simulateProgSimulation() {

    if (
        progSimulation.running
        &&
        progSimulation.paused
        &&
        !progSimulation.actionActive
    ) {

        progSimulation.paused =
            false;

        progSimulation.stepBudget =
            0;


        wakeProgSimulationGate();

        updateProgSimulationButtons();


        progLog(
            "▶ Simulación automática iniciada desde el paso actual."
        );

        return;
    }


    if (progSimulation.running) {
        return;
    }


    startProgSimulation(
        false,
        false,
        "simulate"
    );
}


async function startProgSimulation(
    startPaused = false,
    initialStep = false,
    startMode = "simulate"
) {

    if (
        progSimulation.running
    ) {
        return;
    }


    const codeElement =
        $p("progCode");

    const code =
        codeElement
            ?
            codeElement.value
            :
            "";


    if (!code.trim()) {

        progLog(
            "No se puede simular: programa vacío."
        );

        return;
    }


    if (
        !progPlanner.map
        ||
        !progPlanner.meta
    ) {

        progLog(
            "No se puede simular: carga un mapa."
        );

        return;
    }


    if (
        !progPlanner.initialPointId
    ) {

        progLog(
            "No se puede simular: define un punto ★ Inicial."
        );

        return;
    }


    const snapshot =
        progPlanner.points.map(
            point => ({
                id:
                    point.id,

                alias:
                    point.alias || "",

                x:
                    Number(point.x),

                y:
                    Number(point.y),

                yaw:
                    (
                        point.yaw === null
                        ||
                        point.yaw === undefined
                    )
                        ?
                        null
                        :
                        Number(point.yaw),

                u:
                    Number(point.u),

                v:
                    Number(point.v)
            })
        );


    const initial =
        snapshot.find(
            point =>
                point.id
                ===
                progPlanner.initialPointId
        );


    if (!initial) {

        progLog(
            "No se puede simular: el punto inicial no existe."
        );

        return;
    }


    clearProgSimulation(
        true
    );


    try {

        const response =
            await fetch(
                "/programar/simulate",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            code:
                                code,

                            points:
                                snapshot.map(
                                    point => ({
                                        id:
                                            point.id,

                                        alias:
                                            point.alias
                                    })
                                )
                        })
                }
            );


        const data =
            await response.json();


        if (
            !response.ok
            ||
            !data.ok
        ) {

            const errors =
                data.errors || [];


            progLog(
                "Simulación no iniciada.\n"
                +
                errors.map(
                    item =>
                        "✗ "
                        +
                        (
                            item.line
                                ?
                                "Línea "
                                +
                                item.line
                                +
                                ": "
                                :
                                ""
                        )
                        +
                        item.message
                ).join("\n")
            );

            return;
        }


        progSimulation.pointMap =
            new Map(
                snapshot.map(
                    point => [
                        point.id,
                        point
                    ]
                )
            );

        progSimulation.trace =
            data.trace || [];

        progSimulation.index = 0;

        progSimulation.currentPointId =
            initial.id;


        const hasInitialYaw =
            (
                initial.yaw !== null
                &&
                Number.isFinite(
                    Number(initial.yaw)
                )
            );


        progSimulation.pose = {
            u:
                initial.u,

            v:
                initial.v,

            x:
                initial.x,

            y:
                initial.y,

            yaw:
                hasInitialYaw
                    ?
                    Number(initial.yaw)
                    :
                    0
        };


        progSimulation.referenceYaw =
            hasInitialYaw
                ?
                Number(initial.yaw)
                :
                null;


        progSimulation.path = [{
            u:
                initial.u,

            v:
                initial.v
        }];


        progSimulation.running = true;

        progSimulation.paused =
            Boolean(
                startPaused
            );

        progSimulation.actionActive =
            false;

        progSimulation.stepBudget =
            initialStep
                ?
                1
                :
                0;

        progSimulation.gateWaiters =
            [];

        progSimulation.history =
            [];

        progSimulation.token += 1;


        const token =
            progSimulation.token;


        updateProgSimulationButtons();

        renderProgSimulation();


        if (startMode === "restart") {

            progLog(
                "↺ Simulación reiniciada · "
                +
                progSimulation.trace.length
                +
                " acciones · detenida en el inicio."
            );

        } else if (startMode === "step") {

            progLog(
                "Simulación preparada paso a paso · "
                +
                progSimulation.trace.length
                +
                " acciones."
            );

        } else {

            progLog(
                "Simulación automática iniciada · "
                +
                progSimulation.trace.length
                +
                " acciones. Sin comandos al robot."
            );
        }


        while (
            progSimulation.index
            <
            progSimulation.trace.length
        ) {

            if (
                !progSimulation.running
                ||
                progSimulation.token !== token
            ) {
                return;
            }


            const permission =
                await waitProgSimulationPermission(
                    token
                );


            if (!permission.ok) {
                return;
            }


            const index =
                progSimulation.index;

            const action =
                progSimulation.trace[
                    index
                ];


            const snapshot =
                captureProgSimulationState(
                    index
                );


            logProgSimulationAction(
                action,
                index,
                permission.stepped
            );


            progSimulation.actionActive =
                true;

            updateProgSimulationButtons();


            const completed =
                await executeProgSimulationAction(
                    action,
                    token
                );


            progSimulation.actionActive =
                false;


            if (!completed) {

                updateProgSimulationButtons();

                return;
            }


            progSimulation.history.push(
                snapshot
            );


            progSimulation.index =
                index + 1;


            updateProgSimulationButtons();
        }


        if (
            progSimulation.running
            &&
            progSimulation.token === token
        ) {

            progSimulation.running = false;

            progSimulation.paused =
                false;

            progSimulation.actionActive =
                false;

            progSimulation.stepBudget =
                0;

            wakeProgSimulationGate();


            progSimulation.index =
                progSimulation.trace.length;


            updateProgSimulationButtons();

            renderProgSimulation();


            progLog(
                "✓ Simulación completada · "
                +
                progSimulation.trace.length
                +
                " acciones."
            );
        }

    } catch (error) {

        stopProgSimulation(
            true
        );


        progLog(
            "Simulación detenida por error: "
            +
            error.message
        );
    }
}


// =========================================================
// ENVOLTURAS SOBRE EL PROGRAMADOR EXISTENTE
// =========================================================

const originalRenderProgPlanner =
    renderProgPlanner;

renderProgPlanner =
    function() {

        originalRenderProgPlanner();

        renderProgSimulation();
    };


const originalApplyProgMapView =
    applyProgMapView;

applyProgMapView =
    function() {

        originalApplyProgMapView();

        renderProgSimulation();
    };


const originalResetProgramDraft =
    resetProgramDraft;

resetProgramDraft =
    function() {

        clearProgSimulation(
            true
        );

        return originalResetProgramDraft();
    };


const originalApplyMissionData =
    applyMissionData;

applyMissionData =
    function(
        mission
    ) {

        clearProgSimulation(
            true
        );

        return originalApplyMissionData(
            mission
        );
    };


const originalShowProgMap =
    showProgMap;

showProgMap =
    function() {

        clearProgSimulation(
            true
        );

        return originalShowProgMap.apply(
            this,
            arguments
        );
    };


// =========================================================
// DOM
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        ensureProgSimulationCanvas();

        updateProgSimulationButtons();


        const simulate =
            $p("progSimulateButton");

        const restart =
            $p("progRestartSimulationButton");

        const previous =
            $p("progPreviousSimulationButton");

        const pause =
            $p("progPauseSimulationButton");

        const step =
            $p("progStepSimulationButton");

        const stop =
            $p("progStopSimulationButton");


        if (simulate) {

            simulate.addEventListener(
                "click",
                simulateProgSimulation
            );
        }


        if (restart) {

            restart.addEventListener(
                "click",
                restartProgSimulation
            );
        }


        if (previous) {

            previous.addEventListener(
                "click",
                previousProgSimulationStep
            );
        }


        if (pause) {

            pause.addEventListener(
                "click",
                toggleProgSimulationPause
            );
        }


        if (step) {

            step.addEventListener(
                "click",
                stepProgSimulation
            );
        }


        if (stop) {

            stop.addEventListener(
                "click",
                () => {

                    stopProgSimulation(
                        false
                    );
                }
            );
        }


        window.addEventListener(
            "resize",
            renderProgSimulation
        );
    }
);
