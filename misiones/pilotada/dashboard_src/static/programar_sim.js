"use strict";


// =========================================================
// SAFEVISION - SIMULADOR LOCAL
// =========================================================

const progSimulation = {
    running: false,
    token: 0,
    trace: [],
    index: 0,
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

    const stop =
        $p("progStopSimulationButton");


    if (simulate) {

        simulate.disabled =
            progSimulation.running;

        simulate.textContent =
            progSimulation.running
                ?
                "Simulando..."
                :
                "Simular";
    }


    if (stop) {

        stop.disabled =
            !progSimulation.running;
    }
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

    progSimulation.pose = null;

    progSimulation.path = [];

    progSimulation.pointMap =
        new Map();

    progSimulation.currentPointId =
        null;

    progSimulation.referenceYaw =
        null;


    renderProgSimulation();
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


async function startProgSimulation() {

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

        progSimulation.token += 1;


        const token =
            progSimulation.token;


        updateProgSimulationButtons();

        renderProgSimulation();


        progLog(
            "Simulación local iniciada · "
            +
            progSimulation.trace.length
            +
            " acciones. Sin comandos al robot."
        );


        for (
            let index = 0;
            index < progSimulation.trace.length;
            index += 1
        ) {

            if (
                !progSimulation.running
                ||
                progSimulation.token !== token
            ) {
                return;
            }


            progSimulation.index =
                index;


            const completed =
                await executeProgSimulationAction(
                    progSimulation.trace[
                        index
                    ],
                    token
                );


            if (!completed) {
                return;
            }
        }


        if (
            progSimulation.running
            &&
            progSimulation.token === token
        ) {

            progSimulation.running = false;

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

        const stop =
            $p("progStopSimulationButton");


        if (simulate) {

            simulate.addEventListener(
                "click",
                startProgSimulation
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
