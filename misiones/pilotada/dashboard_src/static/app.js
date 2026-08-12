const state = {
    connected: false,
    confidenceTimer: null
};


const $ = (id) => document.getElementById(id);


function log(message) {
    const box = $("log");

    const time = new Date()
        .toLocaleTimeString();

    box.textContent =
        `[${time}] ${message}\n`
        +
        box.textContent;
}


function yesNo(value) {
    if (value === true) {
        return "OK";
    }

    if (value === false) {
        return "FAIL";
    }

    return "—";
}


function renderRobot(robot) {
    $("rosStatus").textContent =
        yesNo(robot.ros_master);

    $("driverStatus").textContent =
        yesNo(robot.driver);

    $("lidarStatus").textContent =
        yesNo(robot.lidar);

    const mapEnabled =
        robot.map
        &&
        typeof robot.map.enabled === "boolean"
            ? robot.map.enabled
            : null;

    $("mapStatus").textContent =
        yesNo(mapEnabled);

    $("cameraStatus").textContent =
        yesNo(robot.camera);


    const mode =
        robot.control_mode
        ||
        "desconocido";


    if (robot.control === true) {
        $("controlStatus").textContent =
            `${mode.toUpperCase()} · OK`;
    } else {
        $("controlStatus").textContent =
            mode.toUpperCase();
    }
}


function startVideo() {
    const img =
        $("videoFeed");

    const placeholder =
        $("videoPlaceholder");


    img.src =
        "/video_feed?t="
        +
        Date.now();


    img.hidden = false;
    placeholder.hidden = true;
}


async function connectRobot() {
    const ip =
        $("robotIp")
        .value
        .trim();


    if (!ip) {
        log(
            "Escribe la IP del robot."
        );

        return;
    }


    $("connectButton").disabled = true;

    log(
        `Conectando a ${ip}...`
    );


    try {
        const response = await fetch(
            "/connect",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    ip: ip
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.message
                ||
                "No se pudo conectar."
            );
        }


        state.connected = true;


        $("connectionBadge")
            .textContent =
            "CONECTADO";


        $("connectionBadge")
            .className =
            "badge badge-on";


        renderRobot(
            data.robot
        );


        startVideo();

        await loadMaps();


        log(
            `Robot conectado: ${ip}`
        );


    } catch (error) {
        state.connected = false;


        $("connectionBadge")
            .textContent =
            "DESCONECTADO";


        $("connectionBadge")
            .className =
            "badge badge-off";


        log(
            `Error: ${error.message}`
        );


    } finally {
        $("connectButton").disabled = false;
    }
}


async function uploadModel(event) {
    event.preventDefault();


    const pt =
        $("modelPt").files[0];


    const json =
        $("modelJson").files[0];


    if (!pt) {
        log(
            "Selecciona un archivo .pt."
        );

        return;
    }


    const form =
        new FormData();


    form.append(
        "model_pt",
        pt
    );


    if (json) {
        form.append(
            "model_json",
            json
        );
    }


    log(
        `Cargando modelo ${pt.name}...`
    );


    try {
        const response = await fetch(
            "/upload_model",
            {
                method: "POST",
                body: form
            }
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.message
                ||
                "Error cargando modelo."
            );
        }


        renderModel(
            data.model
        );


        log(
            `Modelo listo: ${data.model.model}`
        );


    } catch (error) {
        log(
            `Error IA: ${error.message}`
        );
    }
}


function renderModel(info) {
    $("modelName").textContent =
        info.model
        ||
        "Ninguno";


    const metadata =
        info.metadata
        ||
        {};


    const parts = [];


    if (metadata.nombre_modelo) {
        parts.push(
            `Nombre: ${metadata.nombre_modelo}`
        );
    }


    if (metadata.version) {
        parts.push(
            `Versión: ${metadata.version}`
        );
    }


    if (info.json) {
        parts.push(
            `JSON: ${info.json}`
        );
    }


    if (parts.length === 0) {
        parts.push(
            `Archivo: ${info.model}`
        );
    }


    $("modelMetadata")
        .textContent =
        parts.join(" · ");


    const classes =
        $("classes");


    classes.innerHTML = "";


    if (
        !info.classes
        ||
        info.classes.length === 0
    ) {
        classes.innerHTML =
            '<span class="muted">'
            +
            'Sin clases disponibles.'
            +
            '</span>';

        return;
    }


    for (
        const className
        of info.classes
    ) {
        const tag =
            document.createElement(
                "span"
            );


        tag.className =
            "class-tag";


        tag.textContent =
            className;


        classes.appendChild(
            tag
        );
    }
}


async function sendConfidence(value) {
    try {
        await fetch(
            "/confidence",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    confidence:
                        value / 100
                })
            }
        );

    } catch (_) {
        // No saturar el log con el slider.
    }
}


async function pollRobot() {
    if (!state.connected) {
        return;
    }


    try {
        const response = await fetch(
            "/robot_status"
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error();
        }


        renderRobot(
            data.robot
        );


    } catch (_) {
        $("connectionBadge")
            .textContent =
            "SIN RESPUESTA";


        $("connectionBadge")
            .className =
            "badge badge-warn";
    }
}


$("connectButton")
    .addEventListener(
        "click",
        connectRobot
    );


$("modelForm")
    .addEventListener(
        "submit",
        uploadModel
    );


$("confidence")
    .addEventListener(
        "input",
        (event) => {
            const value =
                Number(
                    event.target.value
                );


            $("confidenceValue")
                .textContent =
                `${value}%`;


            clearTimeout(
                state.confidenceTimer
            );


            state.confidenceTimer =
                setTimeout(
                    () => {
                        sendConfidence(
                            value
                        );
                    },
                    150
                );
        }
    );


setInterval(
    pollRobot,
    3000
);


// =========================================================
// MAPAS - NIVEL 2A
// =========================================================

async function loadMaps() {
    const select =
        $("mapSelect");

    if (!select) {
        return;
    }

    select.innerHTML =
        '<option value="">Seleccionar mapa...</option>';


    try {
        const response =
            await fetch(
                "/maps"
            );

        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.message
                ||
                "No se pudieron consultar mapas."
            );
        }


        for (const mapa of data.maps || []) {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                mapa.name;

            option.textContent =
                mapa.name;

            select.appendChild(
                option
            );
        }


        log(
            `${(data.maps || []).length} mapa(s) disponible(s).`
        );


    } catch (error) {

        log(
            `Mapas: ${error.message}`
        );
    }
}


function showSelectedMap() {
    const select =
        $("mapSelect");

    const image =
        $("mapImage");

    const scene =
        $("mapScene");

    const placeholder =
        $("mapPlaceholder");


    if (
        !select
        ||
        !image
        ||
        !scene
        ||
        !placeholder
    ) {
        return;
    }


    const nombre =
        select.value;


    if (!nombre) {
        log(
            "Selecciona un mapa."
        );

        return;
    }


    image.onload = () => {
        scene.hidden = false;
        placeholder.hidden = true;

        focusMapView();
    };


    image.src =
        `/map_image/${encodeURIComponent(nombre)}?t=${Date.now()}`;


    log(
        `Mapa mostrado: ${nombre}`
    );
}


const mapButton =
    $("loadMapButton");

if (mapButton) {
    mapButton.addEventListener(
        "click",
        showSelectedMap
    );
}



// =========================================================
// MAP VIEWPORT INTERACTIVO
// =========================================================
// MAP VIEWPORT INTERACTIVO

const mapView = {
    scale: 1,
    x: 0,
    y: 0,
    dragging: false,
    startX: 0,
    startY: 0
};


function applyMapView() {
    const scene =
        $("mapScene");

    if (!scene) {
        return;
    }

    scene.style.transform =
        `translate(${mapView.x}px, ${mapView.y}px) scale(${mapView.scale})`;

    if (
        typeof window.safeVisionNavRenderMarkers
        ===
        "function"
    ) {
        window.requestAnimationFrame(
            window.safeVisionNavRenderMarkers
        );
    }
}


function focusMapView() {
    /*
     * Los mapas actuales tienen bastante área vacía alrededor.
     * Arrancamos un poco acercados para que sean cómodos.
     */
    mapView.scale = 2.5;
    mapView.x = 0;
    mapView.y = 0;

    applyMapView();
}


function resetMapView() {
    if (mapView.locked) {
        return;
    }

    mapView.scale = 1;
    mapView.x = 0;
    mapView.y = 0;

    applyMapView();
}


function zoomMap(factor) {
    if (mapView.locked) {
        return;
    }

    mapView.scale *= factor;

    mapView.scale =
        Math.max(
            0.5,
            Math.min(
                10,
                mapView.scale
            )
        );

    applyMapView();
}


const mapViewport =
    $("mapViewport");

const mapScene =
    $("mapScene");

const mapZoomIn =
    $("mapZoomIn");

const mapZoomOut =
    $("mapZoomOut");

const mapReset =
    $("mapReset");


if (mapZoomIn) {
    mapZoomIn.addEventListener(
        "click",
        () => zoomMap(1.25)
    );
}


if (mapZoomOut) {
    mapZoomOut.addEventListener(
        "click",
        () => zoomMap(0.8)
    );
}


if (mapReset) {
    mapReset.addEventListener(
        "click",
        resetMapView
    );
}


if (mapViewport) {

    mapViewport.addEventListener(
        "wheel",
        (event) => {
            if (
                !$("mapScene")
                ||
                $("mapScene").hidden
            ) {
                return;
            }

            event.preventDefault();

            zoomMap(
                event.deltaY < 0
                    ? 1.15
                    : 0.87
            );
        },
        {
            passive: false
        }
    );


    mapViewport.addEventListener(
        "mousedown",
        (event) => {

            if (
                !mapScene
                ||
                mapScene.hidden
            ) {
                return;
            }

            mapView.dragging = true;

            mapView.startX =
                event.clientX - mapView.x;

            mapView.startY =
                event.clientY - mapView.y;

            mapViewport.classList.add(
                "dragging"
            );
        }
    );


    window.addEventListener(
        "mousemove",
        (event) => {

            if (!mapView.dragging) {
                return;
            }

            mapView.x =
                event.clientX
                - mapView.startX;

            mapView.y =
                event.clientY
                - mapView.startY;

            applyMapView();
        }
    );


    window.addEventListener(
        "mouseup",
        () => {

            mapView.dragging = false;

            if (mapViewport) {
                mapViewport.classList.remove(
                    "dragging"
                );
            }
        }
    );
}



// =========================================================
// SAFEVISION MAP AREA ZOOM + LOCK
// =========================================================
// SAFEVISION MAP AREA ZOOM + LOCK

mapView.locked = false;
mapView.areaSelecting = false;
mapView.selectionDragging = false;

mapView.selectionStartX = 0;
mapView.selectionStartY = 0;


const mapAreaZoomButton =
    $("mapAreaZoom");

const mapLockButton =
    $("mapLock");


let mapSelectionBox = null;


function ensureMapSelectionBox() {

    if (
        mapSelectionBox
        ||
        !mapViewport
    ) {
        return;
    }


    mapSelectionBox =
        document.createElement(
            "div"
        );


    mapSelectionBox.className =
        "map-selection-box";


    mapSelectionBox.hidden =
        true;


    mapViewport.appendChild(
        mapSelectionBox
    );
}


function updateMapLockUI() {

    if (mapLockButton) {

        mapLockButton.textContent =
            mapView.locked
                ? "Desbloquear"
                : "Bloquear";


        mapLockButton.classList.toggle(
            "active",
            mapView.locked
        );
    }


    if (mapViewport) {

        mapViewport.classList.toggle(
            "map-locked",
            mapView.locked
        );
    }
}


function setAreaZoomMode(active) {

    if (
        mapView.locked
        &&
        active
    ) {
        return;
    }


    mapView.areaSelecting =
        Boolean(active);


    if (mapAreaZoomButton) {

        mapAreaZoomButton.classList.toggle(
            "active",
            mapView.areaSelecting
        );
    }


    if (mapViewport) {

        mapViewport.classList.toggle(
            "map-area-selecting",
            mapView.areaSelecting
        );
    }


    if (
        !mapView.areaSelecting
        &&
        mapSelectionBox
    ) {

        mapSelectionBox.hidden =
            true;
    }
}


function clampMapCoordinate(
    value,
    min,
    max
) {

    return Math.max(
        min,
        Math.min(
            max,
            value
        )
    );
}


function finishAreaZoom(
    event
) {

    if (
        !mapView.selectionDragging
        ||
        !mapViewport
        ||
        !mapSelectionBox
    ) {
        return;
    }


    mapView.selectionDragging =
        false;


    const bounds =
        mapViewport.getBoundingClientRect();


    const endX =
        clampMapCoordinate(
            event.clientX - bounds.left,
            0,
            bounds.width
        );


    const endY =
        clampMapCoordinate(
            event.clientY - bounds.top,
            0,
            bounds.height
        );


    const left =
        Math.min(
            mapView.selectionStartX,
            endX
        );


    const top =
        Math.min(
            mapView.selectionStartY,
            endY
        );


    const width =
        Math.abs(
            endX
            -
            mapView.selectionStartX
        );


    const height =
        Math.abs(
            endY
            -
            mapView.selectionStartY
        );


    mapSelectionBox.hidden =
        true;


    if (
        width < 20
        ||
        height < 20
    ) {

        setAreaZoomMode(
            false
        );

        return;
    }


    const factor =
        Math.min(
            bounds.width / width,
            bounds.height / height
        )
        * 0.90;


    const escalaAnterior =
        mapView.scale;


    const escalaNueva =
        Math.max(
            0.5,
            Math.min(
                10,
                escalaAnterior * factor
            )
        );


    const factorReal =
        escalaNueva
        /
        escalaAnterior;


    const centroSeleccionX =
        left
        +
        width / 2;


    const centroSeleccionY =
        top
        +
        height / 2;


    const centroViewportX =
        bounds.width / 2;


    const centroViewportY =
        bounds.height / 2;


    mapView.x =
        (
            centroViewportX
            +
            mapView.x
            -
            centroSeleccionX
        )
        *
        factorReal;


    mapView.y =
        (
            centroViewportY
            +
            mapView.y
            -
            centroSeleccionY
        )
        *
        factorReal;


    mapView.scale =
        escalaNueva;


    applyMapView();


    setAreaZoomMode(
        false
    );


    log(
        "Zoom de área aplicado."
    );
}


ensureMapSelectionBox();


if (mapAreaZoomButton) {

    mapAreaZoomButton.addEventListener(
        "click",
        () => {

            if (mapView.locked) {

                log(
                    "Desbloquea el mapa para cambiar el encuadre."
                );

                return;
            }


            setAreaZoomMode(
                !mapView.areaSelecting
            );


            if (mapView.areaSelecting) {

                log(
                    "Dibuja un rectángulo sobre el área que quieres ampliar."
                );
            }
        }
    );
}


if (mapLockButton) {

    mapLockButton.addEventListener(
        "click",
        () => {

            mapView.locked =
                !mapView.locked;


            mapView.dragging =
                false;


            mapView.selectionDragging =
                false;


            setAreaZoomMode(
                false
            );


            updateMapLockUI();


            log(
                mapView.locked
                    ? "Encuadre del mapa bloqueado."
                    : "Encuadre del mapa desbloqueado."
            );
        }
    );
}


/*
 * Capturamos el evento antes del manejador normal
 * de arrastre del mapa.
 */

if (mapViewport) {

    mapViewport.addEventListener(
        "mousedown",
        (event) => {

            if (mapView.locked) {

                event.preventDefault();

                event.stopImmediatePropagation();

                return;
            }


            if (!mapView.areaSelecting) {
                return;
            }


            event.preventDefault();

            event.stopImmediatePropagation();


            ensureMapSelectionBox();


            const bounds =
                mapViewport.getBoundingClientRect();


            mapView.selectionStartX =
                clampMapCoordinate(
                    event.clientX - bounds.left,
                    0,
                    bounds.width
                );


            mapView.selectionStartY =
                clampMapCoordinate(
                    event.clientY - bounds.top,
                    0,
                    bounds.height
                );


            mapView.selectionDragging =
                true;


            mapSelectionBox.style.left =
                `${mapView.selectionStartX}px`;


            mapSelectionBox.style.top =
                `${mapView.selectionStartY}px`;


            mapSelectionBox.style.width =
                "0px";


            mapSelectionBox.style.height =
                "0px";


            mapSelectionBox.hidden =
                false;
        },
        true
    );


    mapViewport.addEventListener(
        "wheel",
        (event) => {

            if (
                mapView.locked
                ||
                mapView.areaSelecting
            ) {

                event.preventDefault();

                event.stopImmediatePropagation();
            }
        },
        true
    );
}


window.addEventListener(
    "mousemove",
    (event) => {

        if (
            !mapView.selectionDragging
            ||
            !mapViewport
            ||
            !mapSelectionBox
        ) {
            return;
        }


        event.preventDefault();

        event.stopImmediatePropagation();


        const bounds =
            mapViewport.getBoundingClientRect();


        const currentX =
            clampMapCoordinate(
                event.clientX - bounds.left,
                0,
                bounds.width
            );


        const currentY =
            clampMapCoordinate(
                event.clientY - bounds.top,
                0,
                bounds.height
            );


        const left =
            Math.min(
                mapView.selectionStartX,
                currentX
            );


        const top =
            Math.min(
                mapView.selectionStartY,
                currentY
            );


        const width =
            Math.abs(
                currentX
                -
                mapView.selectionStartX
            );


        const height =
            Math.abs(
                currentY
                -
                mapView.selectionStartY
            );


        mapSelectionBox.style.left =
            `${left}px`;


        mapSelectionBox.style.top =
            `${top}px`;


        mapSelectionBox.style.width =
            `${width}px`;


        mapSelectionBox.style.height =
            `${height}px`;
    },
    true
);


window.addEventListener(
    "mouseup",
    (event) => {

        if (
            !mapView.selectionDragging
        ) {
            return;
        }


        event.preventDefault();

        event.stopImmediatePropagation();


        finishAreaZoom(
            event
        );
    },
    true
);


/*
 * Cuando está bloqueado también evitamos
 * los botones normales de cambio de vista.
 */

[
    mapZoomIn,
    mapZoomOut,
    mapReset

].forEach(
    (button) => {

        if (!button) {
            return;
        }


        button.addEventListener(
            "click",
            (event) => {

                if (!mapView.locked) {
                    return;
                }


                event.preventDefault();

                event.stopImmediatePropagation();


                log(
                    "Desbloquea el mapa para cambiar el encuadre."
                );
            },
            true
        );
    }
);


updateMapLockUI();



// =========================================================
// SAFEVISION NIVEL 2B - ROBOT EN MAPA
// =========================================================

const safeVisionMapPose = {
    mapName: null,
    meta: null,
    timer: null,
    busy: false,
    lastPose: null
};


// Huella aproximada ROSMASTER X3 vista desde arriba.
// Yahboom: aproximadamente 24 cm x 20 cm.

const ROSMASTER_X3_LENGTH_M = 0.24;
const ROSMASTER_X3_WIDTH_M = 0.20;


// =========================================================
// SAFEVISION - GUIA DE ALINEACION DEL ROBOT
// =========================================================

const safeVisionAlignmentGuide = {
    rasterMapName: null,
    rasterWidth: 0,
    rasterHeight: 0,
    raster: null,
    visible: true
};


function updateRobotAlignmentGuideToggleUI() {

    const button =
        document.getElementById(
            "mapAlignmentGuideToggle"
        );

    if (!button) {
        return;
    }

    button.textContent =
        safeVisionAlignmentGuide.visible
            ? "Ocultar guía"
            : "Mostrar guía";

    button.classList.toggle(
        "active",
        safeVisionAlignmentGuide.visible
    );
}


function ensureRobotAlignmentGuideToggle() {

    const toolbar =
        document.querySelector(
            ".map-toolbar"
        );

    if (!toolbar) {
        return;
    }


    let button =
        document.getElementById(
            "mapAlignmentGuideToggle"
        );


    if (!button) {

        button =
            document.createElement(
                "button"
            );

        button.id =
            "mapAlignmentGuideToggle";

        button.type =
            "button";

        button.title =
            "Mostrar u ocultar la guía de alineación";


        button.addEventListener(
            "click",
            () => {

                safeVisionAlignmentGuide.visible =
                    !safeVisionAlignmentGuide.visible;

                updateRobotAlignmentGuideToggleUI();


                if (
                    !safeVisionAlignmentGuide.visible
                ) {

                    hideRobotAlignmentGuide();
                    return;
                }


                updateRobotMarker();
            }
        );


        toolbar.appendChild(
            button
        );
    }


    updateRobotAlignmentGuideToggleUI();
}


ensureRobotAlignmentGuideToggle();


// =========================================================
// SAFEVISION - CALIBRACION POR MEDIDAS FISICAS
// =========================================================

function physicalMeasurePrompt(
    label
) {

    const value =
        window.prompt(
            `${label} en metros.\n`
            +
            `Déjalo vacío si no tienes esa medida:`,
            ""
        );


    if (value === null) {
        return {
            cancelled: true,
            value: null
        };
    }


    const text =
        value
        .trim()
        .replace(
            ",",
            "."
        );


    if (!text) {
        return {
            cancelled: false,
            value: null
        };
    }


    const number =
        Number(
            text
        );


    if (
        !Number.isFinite(number)
        ||
        number <= 0
        ||
        number > 4
    ) {

        throw new Error(
            `${label}: medida inválida.`
        );
    }


    return {
        cancelled: false,
        value: number
    };
}


function worldPoseToAlignment(
    x,
    y,
    yaw,
    meta
) {

    const resolution =
        Number(
            meta.resolution
        );

    const width =
        Number(
            meta.width
        );

    const height =
        Number(
            meta.height
        );

    const originX =
        Number(
            meta.origin.x
        );

    const originY =
        Number(
            meta.origin.y
        );

    const originYaw =
        Number(
            meta.origin.yaw
            ||
            0
        );


    const dx =
        x
        -
        originX;

    const dy =
        y
        -
        originY;


    const cosO =
        Math.cos(
            originYaw
        );

    const sinO =
        Math.sin(
            originYaw
        );


    const localX =
        cosO * dx
        +
        sinO * dy;

    const localY =
        -sinO * dx
        +
        cosO * dy;


    return {
        pixelX:
            localX
            /
            resolution,

        pixelY:
            height
            -
            (
                localY
                /
                resolution
            ),

        yawRel:
            yaw
            -
            originYaw,

        resolution,
        width,
        height
    };
}


function evaluatePhysicalPose(
    x,
    y,
    yaw,
    measurements,
    raster,
    meta
) {

    const p =
        worldPoseToAlignment(
            x,
            y,
            yaw,
            meta
        );


    if (
        p.pixelX < 0
        ||
        p.pixelY < 0
        ||
        p.pixelX >= p.width
        ||
        p.pixelY >= p.height
    ) {
        return null;
    }


    const definitions = {
        F: {
            angle:
                p.yawRel,
            offset:
                ROSMASTER_X3_LENGTH_M / 2
        },

        I: {
            angle:
                p.yawRel
                +
                Math.PI / 2,
            offset:
                ROSMASTER_X3_WIDTH_M / 2
        },

        D: {
            angle:
                p.yawRel
                -
                Math.PI / 2,
            offset:
                ROSMASTER_X3_WIDTH_M / 2
        },

        A: {
            angle:
                p.yawRel
                +
                Math.PI,
            offset:
                ROSMASTER_X3_LENGTH_M / 2
        }
    };


    let squaredError =
        0;

    let absoluteError =
        0;

    let count =
        0;

    const predicted =
        {};


    for (
        const key
        of Object.keys(
            measurements
        )
    ) {

        const physical =
            measurements[key];


        if (physical === null) {
            continue;
        }


        const def =
            definitions[key];


        const result =
            measureAlignmentClearance(
                raster,
                p.width,
                p.height,
                p.resolution,
                p.pixelX,
                p.pixelY,
                def.angle,
                def.offset
            );


        if (
            !result
            ||
            result.type !== "wall"
        ) {
            return null;
        }


        const difference =
            result.distance
            -
            physical;


        squaredError +=
            difference
            *
            difference;

        absoluteError +=
            Math.abs(
                difference
            );

        count += 1;

        predicted[key] =
            result.distance;
    }


    if (!count) {
        return null;
    }


    return {
        x,
        y,
        yaw,
        score:
            squaredError
            /
            count,
        meanError:
            absoluteError
            /
            count,
        predicted
    };
}


function searchPhysicalPose(
    current,
    measurements,
    raster,
    meta
) {

    let best =
        null;


    function tryCandidate(
        x,
        y,
        yaw
    ) {

        const candidate =
            evaluatePhysicalPose(
                x,
                y,
                yaw,
                measurements,
                raster,
                meta
            );


        if (
            candidate
            &&
            (
                !best
                ||
                candidate.score
                <
                best.score
            )
        ) {
            best =
                candidate;
        }
    }


    const coarseXY =
        0.025;

    const coarseYaw =
        2
        *
        Math.PI
        /
        180;


    for (
        let ix = -10;
        ix <= 10;
        ix += 1
    ) {

        for (
            let iy = -10;
            iy <= 10;
            iy += 1
        ) {

            for (
                let ia = -6;
                ia <= 6;
                ia += 1
            ) {

                tryCandidate(
                    Number(current.x)
                    +
                    ix * coarseXY,

                    Number(current.y)
                    +
                    iy * coarseXY,

                    Number(current.yaw)
                    +
                    ia * coarseYaw
                );
            }
        }
    }


    if (!best) {
        return null;
    }


    const coarseBest =
        best;

    best =
        null;


    const fineXY =
        0.01;

    const fineYaw =
        Math.PI
        /
        180;


    for (
        let ix = -4;
        ix <= 4;
        ix += 1
    ) {

        for (
            let iy = -4;
            iy <= 4;
            iy += 1
        ) {

            for (
                let ia = -3;
                ia <= 3;
                ia += 1
            ) {

                tryCandidate(
                    coarseBest.x
                    +
                    ix * fineXY,

                    coarseBest.y
                    +
                    iy * fineXY,

                    coarseBest.yaw
                    +
                    ia * fineYaw
                );
            }
        }
    }


    return (
        best
        ||
        coarseBest
    );
}


async function runPhysicalCalibration() {

    try {

        if (
            !safeVisionMapPose.meta
            ||
            !safeVisionMapPose.lastPose
        ) {
            throw new Error(
                "Primero muestra el mapa y espera a que aparezca el robot."
            );
        }


        window.alert(
            "Calibración aproximada por medidas físicas.\n\n"
            +
            "Mide desde el borde del robot hasta las paredes.\n"
            +
            "No es necesario que sean medidas milimétricas.\n"
            +
            "Puedes dejar campos vacíos.\n\n"
            +
            "Se requieren al menos 3 medidas.\n"
            +
            "AMCL e IMU terminarán de estabilizar la estimación al mover el robot."
        );


        const measurements =
            {};


        for (
            const item
            of [
                ["F", "Frente"],
                ["I", "Izquierda"],
                ["D", "Derecha"],
                ["A", "Atrás"]
            ]
        ) {

            const result =
                physicalMeasurePrompt(
                    item[1]
                );


            if (result.cancelled) {
                return;
            }


            measurements[
                item[0]
            ] =
                result.value;
        }


        const available =
            Object.values(
                measurements
            )
            .filter(
                value =>
                    value !== null
            )
            .length;


        if (available < 3) {
            throw new Error(
                "Se requieren al menos 3 medidas físicas."
            );
        }


        const meta =
            safeVisionMapPose.meta;


        const raster =
            getAlignmentRaster(
                Number(meta.width),
                Number(meta.height)
            );


        if (!raster) {
            throw new Error(
                "No pude leer el mapa para calcular el ajuste."
            );
        }


        const current =
            safeVisionMapPose.lastPose;


        const best =
            searchPhysicalPose(
                current,
                measurements,
                raster,
                meta
            );


        if (!best) {
            throw new Error(
                "No encontré una pose compatible con esas medidas."
            );
        }


        const yawDeg =
            best.yaw
            *
            180
            /
            Math.PI;


        const names = {
            F: "Frente",
            I: "Izquierda",
            D: "Derecha",
            A: "Atrás"
        };


        const lines =
            [];


        for (
            const key
            of ["F", "I", "D", "A"]
        ) {

            if (
                measurements[key]
                === null
            ) {
                continue;
            }


            lines.push(
                `${names[key]}: `
                +
                `físico ${measurements[key].toFixed(2)} m`
                +
                ` | mapa ${best.predicted[key].toFixed(2)} m`
            );
        }


        const accepted =
            window.confirm(
                "Pose sugerida\n\n"
                +
                `X: ${best.x.toFixed(3)} m\n`
                +
                `Y: ${best.y.toFixed(3)} m\n`
                +
                `Yaw: ${yawDeg.toFixed(1)}°\n\n`
                +
                `Desajuste medio estimado: ${best.meanError.toFixed(3)} m\n\n`
                +
                lines.join("\n")
                +
                "\n\n"
                +
                "Las medidas son aproximadas.\n"
                +
                "Aceptar para aplicar esta pose."
            );


        if (!accepted) {
            return;
        }


        const response =
            await fetch(
                "/initialpose",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            x: best.x,
                            y: best.y,
                            yaw: best.yaw
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
            throw new Error(
                data.message
                ||
                data.error
                ||
                "No se pudo aplicar la pose."
            );
        }


        log(
            (
                "Calibración por medidas aplicada: "
                +
                `X ${best.x.toFixed(2)} m, `
                +
                `Y ${best.y.toFixed(2)} m, `
                +
                `${yawDeg.toFixed(1)}°, `
                +
                `error aprox. ${best.meanError.toFixed(2)} m`
            ),
            "success"
        );


        window.alert(
            "Pose aplicada.\n\n"
            +
            `Desajuste estimado: ${best.meanError.toFixed(3)} m\n\n`
            +
            "Mueve un poco el robot para que AMCL/IMU terminen de estabilizar la estimación."
        );


    } catch (error) {

        log(
            `Calibración por medidas: ${error.message}`,
            "error"
        );

        window.alert(
            error.message
        );
    }
}


function ensurePhysicalCalibrationButton() {

    const toolbar =
        document.querySelector(
            ".map-toolbar"
        );


    if (
        !toolbar
        ||
        document.getElementById(
            "mapPhysicalCalibration"
        )
    ) {
        return;
    }


    const button =
        document.createElement(
            "button"
        );


    button.id =
        "mapPhysicalCalibration";

    button.type =
        "button";

    button.textContent =
        "Calibrar medidas";

    button.title =
        "Ajustar pose usando distancias físicas aproximadas";


    button.addEventListener(
        "click",
        runPhysicalCalibration
    );


    toolbar.appendChild(
        button
    );
}


ensurePhysicalCalibrationButton();


function hideRobotAlignmentGuide() {

    const canvas =
        document.getElementById(
            "robotAlignmentGuide"
        );

    if (canvas) {
        canvas.hidden = true;
    }
}


function getRobotAlignmentCanvas(
    width,
    height,
    renderScale
) {

    const scene =
        document.getElementById(
            "mapScene"
        );

    if (!scene) {
        return null;
    }


    let canvas =
        document.getElementById(
            "robotAlignmentGuide"
        );


    if (!canvas) {

        canvas =
            document.createElement(
                "canvas"
            );

        canvas.id =
            "robotAlignmentGuide";

        canvas.hidden =
            true;

        scene.appendChild(
            canvas
        );
    }


    const targetWidth =
        Math.max(
            1,
            Math.round(
                width
                *
                renderScale
            )
        );

    const targetHeight =
        Math.max(
            1,
            Math.round(
                height
                *
                renderScale
            )
        );


    if (
        canvas.width
        !==
        targetWidth
    ) {
        canvas.width =
            targetWidth;
    }

    if (
        canvas.height
        !==
        targetHeight
    ) {
        canvas.height =
            targetHeight;
    }


    return canvas;
}


function getAlignmentRaster(
    width,
    height
) {

    const image =
        document.getElementById(
            "mapImage"
        );


    if (
        !image
        ||
        !image.complete
        ||
        !image.naturalWidth
        ||
        !image.naturalHeight
    ) {
        return null;
    }


    if (
        safeVisionAlignmentGuide.raster
        &&
        safeVisionAlignmentGuide.rasterMapName
            === safeVisionMapPose.mapName
        &&
        safeVisionAlignmentGuide.rasterWidth
            === width
        &&
        safeVisionAlignmentGuide.rasterHeight
            === height
    ) {
        return safeVisionAlignmentGuide.raster;
    }


    try {

        const rasterCanvas =
            document.createElement(
                "canvas"
            );

        rasterCanvas.width =
            width;

        rasterCanvas.height =
            height;


        const ctx =
            rasterCanvas.getContext(
                "2d",
                {
                    willReadFrequently: true
                }
            );


        ctx.drawImage(
            image,
            0,
            0,
            width,
            height
        );


        const raster =
            ctx.getImageData(
                0,
                0,
                width,
                height
            ).data;


        safeVisionAlignmentGuide.rasterMapName =
            safeVisionMapPose.mapName;

        safeVisionAlignmentGuide.rasterWidth =
            width;

        safeVisionAlignmentGuide.rasterHeight =
            height;

        safeVisionAlignmentGuide.raster =
            raster;


        return raster;


    } catch (_) {

        return null;
    }
}


function classifyAlignmentPixel(
    raster,
    width,
    height,
    x,
    y
) {

    const px =
        Math.round(x);

    const py =
        Math.round(y);


    if (
        px < 0
        ||
        py < 0
        ||
        px >= width
        ||
        py >= height
    ) {
        return "outside";
    }


    const index =
        (
            py * width
            +
            px
        )
        *
        4;


    const luminance =
        (
            raster[index]
            +
            raster[index + 1]
            +
            raster[index + 2]
        )
        /
        3;


    if (luminance <= 80) {
        return "occupied";
    }


    if (
        luminance >= 150
        &&
        luminance <= 230
    ) {
        return "unknown";
    }


    return "free";
}


function measureAlignmentClearance(
    raster,
    width,
    height,
    resolution,
    pixelX,
    pixelY,
    angle,
    robotOffset
) {

    const maxDistance =
        4.0;

    const maxPixels =
        Math.floor(
            maxDistance
            /
            resolution
        );


    const dx =
        Math.cos(
            angle
        );

    const dy =
        -Math.sin(
            angle
        );


    for (
        let step = 1;
        step <= maxPixels;
        step += 1
    ) {

        const state =
            classifyAlignmentPixel(
                raster,
                width,
                height,
                pixelX + dx * step,
                pixelY + dy * step
            );


        if (state === "occupied") {

            return {
                type: "wall",
                distance:
                    Math.max(
                        0,
                        step * resolution
                        -
                        robotOffset
                    )
            };
        }


        if (
            state === "unknown"
            ||
            state === "outside"
        ) {

            return {
                type: state,
                distance:
                    Math.max(
                        0,
                        step * resolution
                        -
                        robotOffset
                    )
            };
        }
    }


    return {
        type: "far",
        distance: maxDistance
    };
}


function formatAlignmentClearance(
    result
) {

    if (
        result.type === "wall"
    ) {

        return (
            result.distance.toFixed(2)
            +
            " m"
        );
    }


    if (
        result.type === "far"
    ) {

        return (
            ">"
            +
            result.distance.toFixed(1)
            +
            " m"
        );
    }


    return "?";
}


function updateRobotAlignmentGuide(
    pixelX,
    pixelY,
    yawRel,
    resolution,
    width,
    height
) {

    if (
        !safeVisionAlignmentGuide.visible
    ) {

        hideRobotAlignmentGuide();
        return;
    }


    const zoomScale =
        Math.max(
            1,
            Number(
                mapView.scale
            )
            ||
            1
        );


    const deviceScale =
        Math.max(
            1,
            Number(
                window.devicePixelRatio
            )
            ||
            1
        );


    const renderScale =
        Math.min(
            5,
            zoomScale
            *
            deviceScale
        );


    const raster =
        getAlignmentRaster(
            width,
            height
        );


    const canvas =
        getRobotAlignmentCanvas(
            width,
            height,
            renderScale
        );


    if (
        !raster
        ||
        !canvas
        ||
        !resolution
    ) {

        hideRobotAlignmentGuide();
        return;
    }


    const rect =
        canvas.getBoundingClientRect();


    const scaleX =
        rect.width
        /
        width;


    const scaleY =
        rect.height
        /
        height;


    const displayScale =
        Math.max(
            0.05,
            (
                scaleX
                +
                scaleY
            )
            /
            2
        );


    const screenCompensation =
        1.0
        /
        displayScale;


    const ctx =
        canvas.getContext(
            "2d"
        );


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


    const directions = [
        {
            label: "F",
            angle: yawRel,
            robotOffset:
                ROSMASTER_X3_LENGTH_M / 2
        },
        {
            label: "I",
            angle:
                yawRel
                +
                Math.PI / 2,
            robotOffset:
                ROSMASTER_X3_WIDTH_M / 2
        },
        {
            label: "D",
            angle:
                yawRel
                -
                Math.PI / 2,
            robotOffset:
                ROSMASTER_X3_WIDTH_M / 2
        },
        {
            label: "A",
            angle:
                yawRel
                +
                Math.PI,
            robotOffset:
                ROSMASTER_X3_LENGTH_M / 2
        }
    ];


    const guideMeters =
        1.0;

    const guidePixels =
        guideMeters
        /
        resolution;


    ctx.save();

    ctx.strokeStyle =
        "#ff2d2d";

    ctx.fillStyle =
        "#ff2d2d";

    ctx.lineWidth =
        0.65
        *
        screenCompensation;

    ctx.lineCap =
        "round";

    ctx.font =
        `700 ${
            13
            *
            screenCompensation
        }px sans-serif`;

    ctx.textAlign =
        "center";

    ctx.textBaseline =
        "middle";

    ctx.shadowColor =
        "rgba(255, 255, 255, 0.95)";

    ctx.shadowBlur =
        1.5
        *
        screenCompensation;


    for (
        const direction
        of directions
    ) {

        const dx =
            Math.cos(
                direction.angle
            );

        const dy =
            -Math.sin(
                direction.angle
            );


        const endX =
            pixelX
            +
            dx * guidePixels;

        const endY =
            pixelY
            +
            dy * guidePixels;


        ctx.beginPath();

        ctx.moveTo(
            pixelX,
            pixelY
        );

        ctx.lineTo(
            endX,
            endY
        );

        ctx.stroke();


        const perpendicularX =
            -dy;

        const perpendicularY =
            dx;


        for (
            let tick = 0.25;
            tick <= 1.001;
            tick += 0.25
        ) {

            const tickPixels =
                tick
                /
                resolution;


            const tx =
                pixelX
                +
                dx * tickPixels;

            const ty =
                pixelY
                +
                dy * tickPixels;


            const halfTick =
                2.5
                *
                screenCompensation;


            ctx.beginPath();

            ctx.moveTo(
                tx
                -
                perpendicularX
                *
                halfTick,
                ty
                -
                perpendicularY
                *
                halfTick
            );

            ctx.lineTo(
                tx
                +
                perpendicularX
                *
                halfTick,
                ty
                +
                perpendicularY
                *
                halfTick
            );

            ctx.stroke();
        }


        const clearance =
            measureAlignmentClearance(
                raster,
                width,
                height,
                resolution,
                pixelX,
                pixelY,
                direction.angle,
                direction.robotOffset
            );


        const text =
            (
                direction.label
                +
                " "
                +
                formatAlignmentClearance(
                    clearance
                )
            );


        const textOffset =
            11
            *
            screenCompensation;


        let textX =
            endX
            +
            dx
            *
            textOffset;

        let textY =
            endY
            +
            dy
            *
            textOffset;


        textX =
            Math.max(
                35,
                Math.min(
                    width - 35,
                    textX
                )
            );

        textY =
            Math.max(
                10,
                Math.min(
                    height - 10,
                    textY
                )
            );


        ctx.save();

        ctx.lineWidth =
            3
            *
            screenCompensation;

        ctx.strokeStyle =
            "rgba(255, 255, 255, 0.92)";

        ctx.shadowBlur =
            0;

        ctx.strokeText(
            text,
            textX,
            textY
        );

        ctx.fillText(
            text,
            textX,
            textY
        );

        ctx.restore();
    }


    ctx.beginPath();

    ctx.arc(
        pixelX,
        pixelY,
        2.5
        *
        screenCompensation,
        0,
        Math.PI * 2
    );

    ctx.fill();


    ctx.restore();


    canvas.hidden =
        false;
}


async function prepareRobotTracking() {

    const select =
        $("mapSelect");

    const marker =
        $("robotMarker");


    if (
        !select
        ||
        !marker
    ) {
        return;
    }


    const nombre =
        select.value;


    if (!nombre) {
        marker.hidden = true;
        hideRobotAlignmentGuide();
        return;
    }


    try {

        const response =
            await fetch(
                `/map_meta/${encodeURIComponent(nombre)}`
            );

        const data =
            await response.json();


        if (
            !response.ok
            ||
            !data.ok
        ) {
            throw new Error(
                data.message
                ||
                "Metadatos no disponibles."
            );
        }


        safeVisionMapPose.mapName =
            nombre;

        safeVisionMapPose.meta =
            data;


        if (safeVisionMapPose.timer) {
            clearInterval(
                safeVisionMapPose.timer
            );
        }


        await updateRobotMarker();


        safeVisionMapPose.timer =
            setInterval(
                updateRobotMarker,
                150
            );


        log(
            `Localizacion activa sobre mapa: ${nombre}`,
            "success"
        );


    } catch (error) {

        marker.hidden = true;

        hideRobotAlignmentGuide();
        log(
            `Localizacion: ${error.message}`,
            "error"
        );
    }
}


async function updateRobotMarker() {

    if (
        safeVisionMapPose.busy
        ||
        !safeVisionMapPose.meta
    ) {
        return;
    }


    safeVisionMapPose.busy = true;


    try {

        const response =
            await fetch(
                "/map_pose",
                {
                    cache: "no-store"
                }
            );

        const pose =
            await response.json();


        const marker =
            $("robotMarker");


        if (!marker) {
            return;
        }


        if (
            !response.ok
            ||
            !pose.ok
            ||
            !pose.localized
        ) {
            marker.hidden = true;
            hideRobotAlignmentGuide();
            return;
        }


        safeVisionMapPose.lastPose =
            pose;


        const meta =
            safeVisionMapPose.meta;


        const resolution =
            Number(
                meta.resolution
            );

        const width =
            Number(
                meta.width
            );

        const height =
            Number(
                meta.height
            );

        const originX =
            Number(
                meta.origin.x
            );

        const originY =
            Number(
                meta.origin.y
            );

        const originYaw =
            Number(
                meta.origin.yaw || 0
            );


        if (
            !resolution
            ||
            !width
            ||
            !height
        ) {
            marker.hidden = true;
            hideRobotAlignmentGuide();
            return;
        }


        const dx =
            Number(pose.x) - originX;

        const dy =
            Number(pose.y) - originY;


        const cosO =
            Math.cos(originYaw);

        const sinO =
            Math.sin(originYaw);


        const localX =
            cosO * dx
            +
            sinO * dy;

        const localY =
            -sinO * dx
            +
            cosO * dy;


        const pixelX =
            localX / resolution;

        const pixelY =
            height
            -
            (
                localY / resolution
            );


        const leftPct =
            (
                pixelX
                /
                width
            )
            *
            100;

        const topPct =
            (
                pixelY
                /
                height
            )
            *
            100;


        if (
            leftPct < 0
            ||
            leftPct > 100
            ||
            topPct < 0
            ||
            topPct > 100
        ) {
            marker.hidden = true;
            hideRobotAlignmentGuide();
            return;
        }


        const yawRel =
            Number(pose.yaw)
            -
            originYaw;

        const yawDeg =
            yawRel
            *
            180
            /
            Math.PI;


        // Dimensiones físicas completas del mapa.
        const mapWidthMeters =
            width * resolution;

        const mapHeightMeters =
            height * resolution;


        // Huella física aproximada del ROSMASTER X3.
        //
        // HAB2:
        // 0.24 / 40 m = 0.6% del ancho
        // 0.20 / 40 m = 0.5% del alto
        //
        // Equivale aproximadamente a 4.8 x 4 píxeles
        // en un mapa 800x800 a 0.05 m/pixel.
        const robotLengthPct =
            (
                ROSMASTER_X3_LENGTH_M
                /
                mapWidthMeters
            )
            *
            100;

        const robotWidthPct =
            (
                ROSMASTER_X3_WIDTH_M
                /
                mapHeightMeters
            )
            *
            100;


        marker.style.left =
            `${leftPct}%`;

        marker.style.top =
            `${topPct}%`;

        marker.style.width =
            `${robotLengthPct}%`;

        marker.style.height =
            `${robotWidthPct}%`;

        // El frente del robot es +X.
        // Como Y de la imagen crece hacia abajo,
        // el giro visual usa signo negativo.
        marker.style.transform =
            `translate(-50%, -50%) rotate(${-yawDeg}deg)`;

        marker.title =
            `Robot | X ${Number(pose.x).toFixed(2)} m | Y ${Number(pose.y).toFixed(2)} m | ${Number(pose.yaw_deg).toFixed(1)}°`;

        updateRobotAlignmentGuide(
            pixelX,
            pixelY,
            yawRel,
            resolution,
            width,
            height
        );

        marker.hidden = false;


    } catch (_) {

        const marker =
            $("robotMarker");

        if (marker) {
            marker.hidden = true;
            hideRobotAlignmentGuide();
        }


    } finally {

        safeVisionMapPose.busy = false;
    }
}


const safeVisionMapButton =
    $("loadMapButton");


if (safeVisionMapButton) {

    safeVisionMapButton.addEventListener(
        "click",
        () => {

            setTimeout(
                prepareRobotTracking,
                50
            );
        }
    );
}



// =========================================================
// SAFEVISION NIVEL 2B - CALIBRACION AMCL EN MAPA
// =========================================================

(() => {

    if (window.safeVisionCalibrationInstalled) {
        return;
    }

    window.safeVisionCalibrationInstalled = true;


    const calibration = {
        active: false,
        firstPoint: null
    };


    function getScene() {
        return document.getElementById(
            "mapScene"
        );
    }


    function getMapImage() {

        const scene =
            getScene();

        if (!scene) {
            return null;
        }

        return scene.querySelector(
            "img"
        );
    }


    function setCalibrationStatus(
        mensaje,
        tipo = ""
    ) {

        const status =
            document.getElementById(
                "mapCalibrationStatus"
            );

        if (!status) {
            return;
        }

        status.textContent =
            mensaje;

        status.dataset.state =
            tipo;
    }


    function hideCalibrationPoint() {

        const point =
            document.getElementById(
                "mapCalibrationPoint"
            );

        if (point) {
            point.hidden = true;
        }
    }


    function showCalibrationPoint(
        clientX,
        clientY
    ) {

        const scene =
            getScene();

        const image =
            getMapImage();

        const point =
            document.getElementById(
                "mapCalibrationPoint"
            );

        if (
            !scene
            ||
            !image
            ||
            !point
        ) {
            return;
        }


        const imageRect =
            image.getBoundingClientRect();

        const sceneRect =
            scene.getBoundingClientRect();


        const x =
            clientX
            -
            sceneRect.left;

        const y =
            clientY
            -
            sceneRect.top;


        point.style.left =
            `${x}px`;

        point.style.top =
            `${y}px`;

        point.hidden =
            false;
    }


    function screenToMap(
        clientX,
        clientY
    ) {

        if (
            !safeVisionMapPose
            ||
            !safeVisionMapPose.meta
        ) {
            return null;
        }


        const image =
            getMapImage();

        if (!image) {
            return null;
        }


        const rect =
            image.getBoundingClientRect();


        if (
            clientX < rect.left
            ||
            clientX > rect.right
            ||
            clientY < rect.top
            ||
            clientY > rect.bottom
        ) {
            return null;
        }


        const meta =
            safeVisionMapPose.meta;


        const width =
            Number(
                meta.width
            );

        const height =
            Number(
                meta.height
            );

        const resolution =
            Number(
                meta.resolution
            );

        const originX =
            Number(
                meta.origin.x
            );

        const originY =
            Number(
                meta.origin.y
            );

        const originYaw =
            Number(
                meta.origin.yaw || 0
            );


        const u =
            (
                clientX
                -
                rect.left
            )
            /
            rect.width;

        const v =
            (
                clientY
                -
                rect.top
            )
            /
            rect.height;


        const pixelX =
            u * width;

        const pixelY =
            v * height;


        const localX =
            pixelX
            *
            resolution;

        const localY =
            (
                height
                -
                pixelY
            )
            *
            resolution;


        const cosO =
            Math.cos(
                originYaw
            );

        const sinO =
            Math.sin(
                originYaw
            );


        const mapX =
            originX
            +
            cosO * localX
            -
            sinO * localY;

        const mapY =
            originY
            +
            sinO * localX
            +
            cosO * localY;


        return {
            x: mapX,
            y: mapY,
            u,
            v
        };
    }


    function cancelCalibration() {

        calibration.active =
            false;

        calibration.firstPoint =
            null;


        const button =
            document.getElementById(
                "mapCalibrationButton"
            );

        if (button) {
            button.textContent =
                "Calibrar pose";
        }


        const scene =
            getScene();

        if (scene) {
            scene.classList.remove(
                "map-calibrating"
            );
        }


        hideCalibrationPoint();

        setCalibrationStatus(
            ""
        );
    }


    function startCalibration() {

        if (
            !safeVisionMapPose
            ||
            !safeVisionMapPose.meta
        ) {

            log(
                "Primero selecciona un mapa y pulsa Mostrar.",
                "error"
            );

            return;
        }


        calibration.active =
            true;

        calibration.firstPoint =
            null;


        const button =
            document.getElementById(
                "mapCalibrationButton"
            );

        if (button) {
            button.textContent =
                "Cancelar calibración";
        }


        const scene =
            getScene();

        if (scene) {
            scene.classList.add(
                "map-calibrating"
            );
        }


        setCalibrationStatus(
            "1/2: clic donde está el CENTRO del robot.",
            "active"
        );


        log(
            "Calibración AMCL: marca la posición del robot.",
            "info"
        );
    }


    async function sendInitialPose(
        x,
        y,
        yaw
    ) {

        setCalibrationStatus(
            "Aplicando pose a AMCL...",
            "active"
        );


        try {

            const response =
                await fetch(
                    "/initialpose",
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                x,
                                y,
                                yaw
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
                throw new Error(
                    data.message
                    ||
                    data.error
                    ||
                    "No se pudo aplicar la pose."
                );
            }


            const deg =
                yaw
                *
                180
                /
                Math.PI;


            log(
                (
                    `AMCL recalibrado: `
                    +
                    `X ${x.toFixed(2)} m, `
                    +
                    `Y ${y.toFixed(2)} m, `
                    +
                    `${deg.toFixed(1)}°`
                ),
                "success"
            );


            setCalibrationStatus(
                (
                    `Pose aplicada: `
                    +
                    `${x.toFixed(2)}, `
                    +
                    `${y.toFixed(2)}, `
                    +
                    `${deg.toFixed(1)}°`
                ),
                "success"
            );


            calibration.active =
                false;

            calibration.firstPoint =
                null;


            const button =
                document.getElementById(
                    "mapCalibrationButton"
                );

            if (button) {
                button.textContent =
                    "Calibrar pose";
            }


            const scene =
                getScene();

            if (scene) {
                scene.classList.remove(
                    "map-calibrating"
                );
            }


            setTimeout(
                () => {
                    hideCalibrationPoint();
                    updateRobotMarker();
                },
                800
            );


        } catch (error) {

            log(
                `Calibración AMCL: ${error.message}`,
                "error"
            );

            setCalibrationStatus(
                `Error: ${error.message}`,
                "error"
            );
        }
    }


    function handleCalibrationClick(
        event
    ) {

        if (
            !calibration.active
            ||
            event.button !== 0
        ) {
            return;
        }


        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();


        const punto =
            screenToMap(
                event.clientX,
                event.clientY
            );


        if (!punto) {

            setCalibrationStatus(
                "Haz clic dentro de la imagen del mapa.",
                "error"
            );

            return;
        }


        if (!calibration.firstPoint) {

            calibration.firstPoint =
                punto;


            showCalibrationPoint(
                event.clientX,
                event.clientY
            );


            setCalibrationStatus(
                (
                    "2/2: ahora haz clic HACIA DONDE "
                    +
                    "apunta el frente del robot."
                ),
                "active"
            );


            return;
        }


        const dx =
            punto.x
            -
            calibration.firstPoint.x;

        const dy =
            punto.y
            -
            calibration.firstPoint.y;


        const distancia =
            Math.hypot(
                dx,
                dy
            );


        if (distancia < 0.05) {

            setCalibrationStatus(
                (
                    "El segundo clic debe indicar "
                    +
                    "una dirección."
                ),
                "error"
            );

            return;
        }


        const yaw =
            Math.atan2(
                dy,
                dx
            );


        sendInitialPose(
            calibration.firstPoint.x,
            calibration.firstPoint.y,
            yaw
        );
    }


    function installCalibrationUI() {

        const loadButton =
            document.getElementById(
                "loadMapButton"
            );

        const scene =
            getScene();


        if (
            !loadButton
            ||
            !scene
        ) {
            return;
        }


        if (
            !document.getElementById(
                "mapCalibrationButton"
            )
        ) {

            const button =
                document.createElement(
                    "button"
                );

            button.id =
                "mapCalibrationButton";

            button.type =
                "button";

            button.textContent =
                "Calibrar pose";

            button.className =
                loadButton.className;


            loadButton.insertAdjacentElement(
                "afterend",
                button
            );


            const status =
                document.createElement(
                    "span"
                );

            status.id =
                "mapCalibrationStatus";


            button.insertAdjacentElement(
                "afterend",
                status
            );


            button.addEventListener(
                "click",
                () => {

                    if (
                        calibration.active
                    ) {
                        cancelCalibration();

                    } else {
                        startCalibration();
                    }
                }
            );
        }


        if (
            !document.getElementById(
                "mapCalibrationPoint"
            )
        ) {

            const point =
                document.createElement(
                    "div"
                );

            point.id =
                "mapCalibrationPoint";

            point.hidden =
                true;

            scene.appendChild(
                point
            );
        }


        scene.addEventListener(
            "mousedown",
            handleCalibrationClick,
            true
        );


        document.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Escape"
                    &&
                    calibration.active
                ) {
                    cancelCalibration();
                }
            }
        );
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            installCalibrationUI
        );

    } else {

        installCalibrationUI();
    }

})();


// =========================================================
// SAFEVISION NIVEL 3C - PUNTOS DE NAVEGACION
// =========================================================

(() => {

    if (
        window.safeVisionNavPlannerInstalled
    ) {
        return;
    }

    window.safeVisionNavPlannerInstalled =
        true;


    const navPlanner = {
        points: [],
        map: null,
        placing: false,
        lastStatus: null,
        executionSeen: false,
        orientationPointId: null,
        timer: null
    };


    function navPointId(index) {

        let value =
            index + 1;

        let text =
            "";

        while (value > 0) {

            value -= 1;

            text =
                String.fromCharCode(
                    65
                    +
                    (
                        value
                        %
                        26
                    )
                )
                +
                text;

            value =
                Math.floor(
                    value / 26
                );
        }

        return text;
    }


    function getSelectedNavMap() {

        const select =
            document.getElementById(
                "mapSelect"
            );

        return select
            ? select.value
            : "";
    }


    function navScreenToMap(
        clientX,
        clientY
    ) {

        const image =
            document.getElementById(
                "mapImage"
            );

        const meta =
            safeVisionMapPose
            &&
            safeVisionMapPose.meta;

        if (
            !image
            ||
            !meta
        ) {
            return null;
        }


        const rect =
            image.getBoundingClientRect();


        if (
            clientX < rect.left
            ||
            clientX > rect.right
            ||
            clientY < rect.top
            ||
            clientY > rect.bottom
        ) {
            return null;
        }


        const width =
            Number(
                meta.width
            );

        const height =
            Number(
                meta.height
            );

        const resolution =
            Number(
                meta.resolution
            );

        const originX =
            Number(
                meta.origin.x
            );

        const originY =
            Number(
                meta.origin.y
            );

        const originYaw =
            Number(
                meta.origin.yaw
                ||
                0
            );


        if (
            !width
            ||
            !height
            ||
            !resolution
        ) {
            return null;
        }


        const u =
            (
                clientX
                -
                rect.left
            )
            /
            rect.width;

        const v =
            (
                clientY
                -
                rect.top
            )
            /
            rect.height;


        const localX =
            (
                u
                *
                width
            )
            *
            resolution;

        const localY =
            (
                height
                -
                (
                    v
                    *
                    height
                )
            )
            *
            resolution;


        const cosO =
            Math.cos(
                originYaw
            );

        const sinO =
            Math.sin(
                originYaw
            );


        return {
            x:
                originX
                +
                cosO * localX
                -
                sinO * localY,

            y:
                originY
                +
                sinO * localX
                +
                cosO * localY,

            u,
            v
        };
    }


    function ensureNavOverlay() {

        const viewport =
            document.getElementById(
                "mapViewport"
            );

        if (!viewport) {
            return null;
        }


        let overlay =
            document.getElementById(
                "mapNavOverlay"
            );


        if (!overlay) {

            overlay =
                document.createElement(
                    "div"
                );

            overlay.id =
                "mapNavOverlay";

            viewport.appendChild(
                overlay
            );
        }


        return overlay;
    }



    // =====================================================
    // SAFEVISION NIVEL 3C.2 - TABLA DE NAVEGACION
    // =====================================================

    function ensureNavQueueTable() {

        const viewport =
            document.getElementById(
                "mapViewport"
            );


        if (!viewport) {
            return null;
        }


        let panel =
            document.getElementById(
                "mapNavQueuePanel"
            );


        if (panel) {
            return panel;
        }


        panel =
            document.createElement(
                "div"
            );

        panel.id =
            "mapNavQueuePanel";

        panel.innerHTML =
            `
            <div class="map-nav-table-header">
                <strong>Cola de navegación</strong>

                <span id="mapNavQueueCount">
                    0 puntos
                </span>
            </div>

            <div
                id="mapNavQueueEmpty"
                class="map-nav-table-empty"
            >
                Aún no hay puntos.
            </div>

            <div class="map-nav-table-scroll">
                <table
                    id="mapNavQueueTable"
                    class="map-nav-table"
                    hidden
                >
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Punto</th>
                            <th>X</th>
                            <th>Y</th>
                            <th>Orientación</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>

                    <tbody
                        id="mapNavQueueBody"
                    ></tbody>
                </table>
            </div>
            `;


        viewport.insertAdjacentElement(
            "afterend",
            panel
        );


        return panel;
    }



    // =====================================================
    // SAFEVISION NIVEL 3C.3 - EDICION DE COLA
    // =====================================================

    function navQueueIsRunning() {

        return Boolean(
            navPlanner.lastStatus
            &&
            navPlanner.lastStatus.running
        );
    }


    function navYawMatches(
        localYaw,
        remoteYaw
    ) {

        const localAuto =
            localYaw === null
            ||
            localYaw === undefined;

        const remoteAuto =
            remoteYaw === null
            ||
            remoteYaw === undefined;


        if (
            localAuto
            ||
            remoteAuto
        ) {
            return (
                localAuto
                &&
                remoteAuto
            );
        }


        const local =
            Number(localYaw);

        const remote =
            Number(remoteYaw);


        if (
            !Number.isFinite(local)
            ||
            !Number.isFinite(remote)
        ) {
            return false;
        }


        const difference =
            Math.atan2(
                Math.sin(
                    remote - local
                ),
                Math.cos(
                    remote - local
                )
            );


        return (
            Math.abs(difference)
            <
            0.001
        );
    }


    function navStatusMatchesCurrentQueue(
        status
    ) {

        if (
            !status
            ||
            !navPlanner.map
            ||
            status.map !== navPlanner.map
        ) {
            return false;
        }


        const completed =
            Array.isArray(
                status.completed
            )
                ?
                status.completed
                :
                [];

        const remaining =
            Array.isArray(
                status.remaining
            )
                ?
                status.remaining
                :
                [];


        const queue =
            completed.concat(
                remaining
            );


        if (
            queue.length
            !==
            navPlanner.points.length
        ) {
            return false;
        }


        return navPlanner.points.every(
            (point, index) => {

                const remote =
                    queue[index];


                if (!remote) {
                    return false;
                }


                return (
                    remote.id === point.id
                    &&
                    Math.abs(
                        Number(remote.x)
                        -
                        Number(point.x)
                    )
                    <
                    0.000001
                    &&
                    Math.abs(
                        Number(remote.y)
                        -
                        Number(point.y)
                    )
                    <
                    0.000001
                    &&
                    navYawMatches(
                        point.yaw,
                        remote.yaw
                    )
                );
            }
        );
    }


    function navVisibleExecutionStatus() {

        const status =
            navPlanner.lastStatus
            ||
            {};


        if (
            !navStatusMatchesCurrentQueue(
                status
            )
        ) {
            return {};
        }


        if (
            !navPlanner.executionSeen
            &&
            (
                status.state === "ready"
                ||
                status.state === "running"
                ||
                status.state === "relocalizing"
            )
        ) {

            navPlanner.executionSeen =
                true;
        }


        return navPlanner.executionSeen
            ?
            status
            :
            {};
    }


    function beginNavOrientation(
        pointId
    ) {

        if (navQueueIsRunning()) {

            setNavStatus(
                "No se puede orientar mientras navega.",
                "warning"
            );

            return;
        }


        const point =
            navPlanner.points.find(
                item =>
                    item.id === pointId
            );


        if (!point) {
            return;
        }


        navPlanner.orientationPointId =
            pointId;


        renderNavMarkers();

        renderNavQueue();


        setNavStatus(
            (
                pointId
                +
                " · haz clic en el mapa hacia donde debe mirar"
            ),
            "active"
        );
    }


    function setNavPointAuto(
        pointId
    ) {

        if (navQueueIsRunning()) {
            return;
        }


        const point =
            navPlanner.points.find(
                item =>
                    item.id === pointId
            );


        if (!point) {
            return;
        }


        point.yaw =
            null;

        navPlanner.orientationPointId =
            null;

        navPlanner.executionSeen =
            false;


        renderNavMarkers();

        renderNavQueue();

        updateNavButtons();


        setNavStatus(
            (
                pointId
                +
                " · orientación Auto"
            ),
            "ready"
        );
    }


    function renumberNavPoints() {

        navPlanner.points.forEach(
            (point, index) => {

                point.id =
                    navPointId(
                        index
                    );
            }
        );
    }


    function refreshNavQueueAfterEdit(
        message
    ) {

        navPlanner.executionSeen =
            false;

        navPlanner.orientationPointId =
            null;

        renumberNavPoints();


        if (
            navPlanner.points.length
            ===
            0
        ) {

            navPlanner.map =
                null;
        }


        renderNavMarkers();

        updateNavButtons();

        setNavStatus(
            message,
            navPlanner.points.length
                ?
                "ready"
                :
                ""
        );
    }


    function moveNavPoint(
        index,
        direction
    ) {

        if (navQueueIsRunning()) {

            setNavStatus(
                "No se puede reordenar mientras navega.",
                "warning"
            );

            return;
        }


        const target =
            index
            +
            direction;


        if (
            target < 0
            ||
            target >= navPlanner.points.length
        ) {
            return;
        }


        const point =
            navPlanner.points[index];


        navPlanner.points[index] =
            navPlanner.points[target];

        navPlanner.points[target] =
            point;


        refreshNavQueueAfterEdit(
            "Orden de puntos actualizado"
        );
    }


    function deleteNavPoint(
        index
    ) {

        if (navQueueIsRunning()) {

            setNavStatus(
                "No se puede eliminar mientras navega.",
                "warning"
            );

            return;
        }


        if (
            index < 0
            ||
            index >= navPlanner.points.length
        ) {
            return;
        }


        navPlanner.points.splice(
            index,
            1
        );


        refreshNavQueueAfterEdit(
            navPlanner.points.length
                ?
                "Punto eliminado"
                :
                "Cola vacía"
        );
    }


    function renderNavQueue() {

        const panel =
            ensureNavQueueTable();


        if (!panel) {
            return;
        }


        const table =
            document.getElementById(
                "mapNavQueueTable"
            );

        const body =
            document.getElementById(
                "mapNavQueueBody"
            );

        const empty =
            document.getElementById(
                "mapNavQueueEmpty"
            );

        const count =
            document.getElementById(
                "mapNavQueueCount"
            );


        if (
            !table
            ||
            !body
            ||
            !empty
            ||
            !count
        ) {
            return;
        }


        const total =
            navPlanner.points.length;


        count.textContent =
            (
                total
                +
                (
                    total === 1
                        ?
                        " punto"
                        :
                        " puntos"
                )
            );


        body.replaceChildren();


        if (total === 0) {

            table.hidden =
                true;

            empty.hidden =
                false;

            return;
        }


        table.hidden =
            false;

        empty.hidden =
            true;


        const executionStatus =
            navVisibleExecutionStatus();


        const completed =
            new Set(
                Array.isArray(
                    executionStatus.completed
                )
                    ?
                    executionStatus.completed.map(
                        point => point.id
                    )
                    :
                    []
            );


        const currentId =
            executionStatus.current
                ?
                executionStatus.current.id
                :
                null;


        navPlanner.points.forEach(
            (point, index) => {

                const row =
                    document.createElement(
                        "tr"
                    );


                let state =
                    "Pendiente";


                if (
                    completed.has(
                        point.id
                    )
                ) {

                    state =
                        "Completado";

                    row.classList.add(
                        "completed"
                    );

                } else if (
                    currentId ===
                    point.id
                ) {

                    state =
                        "En curso";

                    row.classList.add(
                        "current"
                    );
                }


                const yawText =
                    (
                        point.yaw === null
                        ||
                        point.yaw === undefined
                    )
                        ?
                        "Auto"
                        :
                        (
                            Math.round(
                                Number(point.yaw)
                                *
                                180
                                /
                                Math.PI
                            )
                            +
                            "°"
                        );


                const cells = [
                    String(index + 1),
                    String(point.id),
                    Number(point.x).toFixed(2),
                    Number(point.y).toFixed(2),
                    yawText,
                    state
                ];


                for (
                    const value
                    of cells
                ) {

                    const cell =
                        document.createElement(
                            "td"
                        );

                    cell.textContent =
                        value;

                    row.appendChild(
                        cell
                    );
                }


                const actions =
                    document.createElement(
                        "td"
                    );

                actions.className =
                    "map-nav-row-actions";


                const running =
                    navQueueIsRunning();


                const upButton =
                    document.createElement(
                        "button"
                    );

                upButton.type =
                    "button";

                upButton.className =
                    "map-nav-row-button";

                upButton.textContent =
                    "↑";

                upButton.title =
                    "Subir punto";

                upButton.disabled =
                    running
                    ||
                    index === 0;

                upButton.addEventListener(
                    "click",
                    () => {

                        moveNavPoint(
                            index,
                            -1
                        );
                    }
                );


                const downButton =
                    document.createElement(
                        "button"
                    );

                downButton.type =
                    "button";

                downButton.className =
                    "map-nav-row-button";

                downButton.textContent =
                    "↓";

                downButton.title =
                    "Bajar punto";

                downButton.disabled =
                    running
                    ||
                    index
                    ===
                    navPlanner.points.length - 1;

                downButton.addEventListener(
                    "click",
                    () => {

                        moveNavPoint(
                            index,
                            1
                        );
                    }
                );


                const orientButton =
                    document.createElement(
                        "button"
                    );

                orientButton.type =
                    "button";

                orientButton.className =
                    "map-nav-row-button";

                orientButton.textContent =
                    (
                        navPlanner.orientationPointId
                        ===
                        point.id
                    )
                        ?
                        "Elige mapa"
                        :
                        "Orientar";

                orientButton.title =
                    "Elegir orientación en el mapa";

                orientButton.disabled =
                    running;

                orientButton.addEventListener(
                    "click",
                    () => {

                        beginNavOrientation(
                            point.id
                        );
                    }
                );


                const autoButton =
                    document.createElement(
                        "button"
                    );

                autoButton.type =
                    "button";

                autoButton.className =
                    "map-nav-row-button";

                autoButton.textContent =
                    "Auto";

                autoButton.title =
                    "Volver a orientación automática";

                autoButton.disabled =
                    (
                        running
                        ||
                        point.yaw === null
                        ||
                        point.yaw === undefined
                    );

                autoButton.addEventListener(
                    "click",
                    () => {

                        setNavPointAuto(
                            point.id
                        );
                    }
                );


                const deleteButton =
                    document.createElement(
                        "button"
                    );

                deleteButton.type =
                    "button";

                deleteButton.className =
                    "map-nav-row-button danger";

                deleteButton.textContent =
                    "Eliminar";

                deleteButton.title =
                    "Eliminar este punto";

                deleteButton.disabled =
                    running;

                deleteButton.addEventListener(
                    "click",
                    () => {

                        deleteNavPoint(
                            index
                        );
                    }
                );


                actions.appendChild(
                    upButton
                );

                actions.appendChild(
                    downButton
                );

                actions.appendChild(
                    orientButton
                );

                actions.appendChild(
                    autoButton
                );

                actions.appendChild(
                    deleteButton
                );


                row.appendChild(
                    actions
                );


                body.appendChild(
                    row
                );
            }
        );
    }


    // =====================================================
    // SAFEVISION - WAYPOINTS CANVAS
    // Misma estrategia de escala que robotAlignmentGuide.
    // =====================================================

    function getNavWaypointCanvas(
        width,
        height,
        renderScale
    ) {

        const scene =
            document.getElementById(
                "mapScene"
            );


        if (!scene) {
            return null;
        }


        let canvas =
            document.getElementById(
                "safeVisionNavWaypointCanvas"
            );


        if (!canvas) {

            canvas =
                document.createElement(
                    "canvas"
                );

            canvas.id =
                "safeVisionNavWaypointCanvas";

            canvas.style.position =
                "absolute";

            canvas.style.inset =
                "0";

            canvas.style.zIndex =
                "45";

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


        const targetWidth =
            Math.max(
                1,
                Math.round(
                    width
                    *
                    renderScale
                )
            );

        const targetHeight =
            Math.max(
                1,
                Math.round(
                    height
                    *
                    renderScale
                )
            );


        if (
            canvas.width
            !==
            targetWidth
        ) {

            canvas.width =
                targetWidth;
        }


        if (
            canvas.height
            !==
            targetHeight
        ) {

            canvas.height =
                targetHeight;
        }


        return canvas;
    }


    function renderNavMarkers() {

        if (
            typeof renderNavQueue
            ===
            "function"
        ) {

            renderNavQueue();
        }


        const image =
            document.getElementById(
                "mapImage"
            );


        if (
            !image
            ||
            image.offsetParent === null
        ) {
            return;
        }


        document.querySelectorAll(
            ".map-nav-marker, "
            +
            ".safevision-nav-visible-marker, "
            +
            ".safevision-nav-screen-marker"
        ).forEach(
            marker => marker.remove()
        );


        const oldOverlay =
            document.getElementById(
                "mapNavOverlay"
            );


        if (oldOverlay) {

            oldOverlay.replaceChildren();

            oldOverlay.style.display =
                "none";
        }


        const width =
            Number(
                image.naturalWidth
                ||
                image.width
            );

        const height =
            Number(
                image.naturalHeight
                ||
                image.height
            );


        if (
            !width
            ||
            !height
        ) {
            return;
        }


        const zoomScale =
            Math.max(
                1,
                Number(
                    mapView.scale
                )
                ||
                1
            );


        const deviceScale =
            Math.max(
                1,
                Number(
                    window.devicePixelRatio
                )
                ||
                1
            );


        const renderScale =
            Math.min(
                5,
                zoomScale
                *
                deviceScale
            );


        const canvas =
            getNavWaypointCanvas(
                width,
                height,
                renderScale
            );


        if (!canvas) {
            return;
        }


        const rect =
            canvas.getBoundingClientRect();


        const scaleX =
            rect.width
            /
            width;

        const scaleY =
            rect.height
            /
            height;


        const displayScale =
            Math.max(
                0.05,
                (
                    scaleX
                    +
                    scaleY
                )
                /
                2
            );


        const screenCompensation =
            1.0
            /
            displayScale;


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


        const status =
            (
                typeof navVisibleExecutionStatus
                ===
                "function"
            )
                ?
                navVisibleExecutionStatus()
                :
                (
                    navPlanner.lastStatus
                    ||
                    {}
                );


        const completed =
            new Set(
                Array.isArray(
                    status.completed
                )
                    ?
                    status.completed.map(
                        point => point.id
                    )
                    :
                    []
            );


        const currentId =
            status.current
                ?
                status.current.id
                :
                null;


        const radius =
            2.8
            *
            screenCompensation;

        const outline =
            0.8
            *
            screenCompensation;

        const labelFont =
            9
            *
            screenCompensation;

        const labelGap =
            6
            *
            screenCompensation;


        for (
            const point
            of navPlanner.points
        ) {

            const u =
                Number(
                    point.u
                );

            const v =
                Number(
                    point.v
                );


            if (
                !Number.isFinite(u)
                ||
                !Number.isFinite(v)
            ) {
                continue;
            }


            const pixelX =
                u
                *
                width;

            const pixelY =
                v
                *
                height;


            let color =
                "#22c55e";


            if (
                completed.has(
                    point.id
                )
            ) {

                color =
                    "#2563eb";
            }


            if (
                currentId
                ===
                point.id
            ) {

                color =
                    "#f59e0b";
            }


            ctx.beginPath();

            ctx.arc(
                pixelX,
                pixelY,
                radius,
                0,
                Math.PI * 2
            );

            ctx.fillStyle =
                color;

            ctx.fill();


            ctx.lineWidth =
                outline;

            ctx.strokeStyle =
                "#ffffff";

            ctx.stroke();


            const orientationSelected =
                navPlanner.orientationPointId
                ===
                point.id;


            if (orientationSelected) {

                ctx.beginPath();

                ctx.arc(
                    pixelX,
                    pixelY,
                    radius
                    +
                    3.5
                    *
                    screenCompensation,
                    0,
                    Math.PI * 2
                );

                ctx.lineWidth =
                    1.2
                    *
                    screenCompensation;

                ctx.strokeStyle =
                    "#ef4444";

                ctx.stroke();
            }


            const hasYaw =
                (
                    point.yaw !== null
                    &&
                    point.yaw !== undefined
                    &&
                    Number.isFinite(
                        Number(
                            point.yaw
                        )
                    )
                );


            if (hasYaw) {

                const yaw =
                    Number(
                        point.yaw
                    );


                const dx =
                    Math.cos(
                        yaw
                    );

                const dy =
                    -Math.sin(
                        yaw
                    );


                const startDistance =
                    4.5
                    *
                    screenCompensation;

                const arrowDistance =
                    14
                    *
                    screenCompensation;


                const startX =
                    pixelX
                    +
                    dx
                    *
                    startDistance;

                const startY =
                    pixelY
                    +
                    dy
                    *
                    startDistance;


                const tipX =
                    pixelX
                    +
                    dx
                    *
                    arrowDistance;

                const tipY =
                    pixelY
                    +
                    dy
                    *
                    arrowDistance;


                ctx.beginPath();

                ctx.moveTo(
                    startX,
                    startY
                );

                ctx.lineTo(
                    tipX,
                    tipY
                );

                ctx.lineWidth =
                    1.4
                    *
                    screenCompensation;

                ctx.strokeStyle =
                    "#ef4444";

                ctx.lineCap =
                    "round";

                ctx.stroke();


                const triangleLength =
                    4.5
                    *
                    screenCompensation;

                const triangleHalf =
                    3.2
                    *
                    screenCompensation;


                const baseX =
                    tipX
                    -
                    dx
                    *
                    triangleLength;

                const baseY =
                    tipY
                    -
                    dy
                    *
                    triangleLength;


                const perpendicularX =
                    -dy;

                const perpendicularY =
                    dx;


                ctx.beginPath();

                ctx.moveTo(
                    tipX,
                    tipY
                );

                ctx.lineTo(
                    baseX
                    +
                    perpendicularX
                    *
                    triangleHalf,
                    baseY
                    +
                    perpendicularY
                    *
                    triangleHalf
                );

                ctx.lineTo(
                    baseX
                    -
                    perpendicularX
                    *
                    triangleHalf,
                    baseY
                    -
                    perpendicularY
                    *
                    triangleHalf
                );

                ctx.closePath();

                ctx.fillStyle =
                    "#ef4444";

                ctx.fill();
            }


            ctx.font =
                (
                    "700 "
                    +
                    labelFont
                    +
                    "px sans-serif"
                );

            ctx.textAlign =
                "left";

            ctx.textBaseline =
                "middle";

            ctx.lineJoin =
                "round";


            ctx.lineWidth =
                2
                *
                screenCompensation;

            ctx.strokeStyle =
                "rgba(255,255,255,0.95)";

            ctx.strokeText(
                String(
                    point.id
                ),
                pixelX
                +
                labelGap,
                pixelY
            );


            ctx.fillStyle =
                "#111827";

            ctx.fillText(
                String(
                    point.id
                ),
                pixelX
                +
                labelGap,
                pixelY
            );
        }
    }


    window.safeVisionNavRenderMarkers =
        renderNavMarkers;


    function setNavStatus(
        text,
        state = ""
    ) {

        const element =
            document.getElementById(
                "mapNavStatus"
            );

        if (!element) {
            return;
        }

        element.textContent =
            text;

        element.dataset.state =
            state;
    }


    function updateNavButtons() {

        const status =
            navPlanner.lastStatus
            ||
            {};

        const running =
            status.running
            ===
            true;


        const pointButton =
            document.getElementById(
                "mapNavPointsButton"
            );

        const startButton =
            document.getElementById(
                "mapNavStartButton"
            );

        const cancelButton =
            document.getElementById(
                "mapNavCancelButton"
            );

        const clearButton =
            document.getElementById(
                "mapNavClearButton"
            );


        if (pointButton) {
            pointButton.disabled =
                running;
        }

        if (startButton) {
            startButton.disabled =
                (
                    running
                    ||
                    navPlanner.points.length
                    ===
                    0
                );
        }

        if (cancelButton) {
            cancelButton.disabled =
                !running;
        }

        if (clearButton) {
            clearButton.disabled =
                running;
        }
    }


    function setNavPlacementMode(
        active
    ) {

        const status =
            navPlanner.lastStatus
            ||
            {};

        if (
            active
            &&
            status.running
        ) {
            return;
        }


        if (
            active
            &&
            typeof setAreaZoomMode
            ===
            "function"
        ) {
            setAreaZoomMode(
                false
            );
        }


        navPlanner.placing =
            Boolean(
                active
            );


        const button =
            document.getElementById(
                "mapNavPointsButton"
            );

        const viewport =
            document.getElementById(
                "mapViewport"
            );


        if (button) {

            button.textContent =
                navPlanner.placing
                    ?
                    "Finalizar puntos"
                    :
                    "Agregar puntos";

            button.classList.toggle(
                "active",
                navPlanner.placing
            );
        }


        if (viewport) {
            viewport.classList.toggle(
                "map-nav-placing",
                navPlanner.placing
            );
        }


        if (navPlanner.placing) {

            setNavStatus(
                (
                    "Modo puntos activo · "
                    +
                    "clic en el mapa para A, B, C..."
                ),
                "active"
            );

        } else if (
            navPlanner.points.length
            >
            0
        ) {

            setNavStatus(
                (
                    navPlanner.points.length
                    +
                    " punto(s) marcados"
                ),
                "ready"
            );
        }
    }


    async function navRequest(
        url,
        options = {}
    ) {

        const response =
            await fetch(
                url,
                {
                    cache:
                        "no-store",
                    ...options
                }
            );


        let data =
            {};

        try {
            data =
                await response.json();

        } catch (_) {
            throw new Error(
                "Respuesta inválida del servidor."
            );
        }


        if (
            !response.ok
            ||
            data.ok
            ===
            false
        ) {

            throw new Error(
                data.error
                ||
                data.message
                ||
                "Error de navegación."
            );
        }


        return data;
    }


    function applyNavStatus(
        status
    ) {

        navPlanner.lastStatus =
            status;


        const state =
            status.state
            ||
            "unknown";


        if (
            status.running
            ===
            true
        ) {

            const current =
                status.current
                &&
                status.current.id
                    ?
                    status.current.id
                    :
                    "...";

            setNavStatus(
                (
                    `Navegando a ${current}`
                    +
                    ` · ${status.remaining_count || 0} pendiente(s)`
                ),
                "running"
            );

        } else if (
            state ===
            "completed"
        ) {

            setNavStatus(
                (
                    `Cola completada`
                    +
                    ` · ${status.completed_count || 0} punto(s)`
                ),
                "success"
            );

        } else if (
            state ===
            "error"
        ) {

            setNavStatus(
                (
                    "Error: "
                    +
                    (
                        status.message
                        ||
                        "navegación"
                    )
                ),
                "error"
            );

        } else if (
            state ===
            "cancelled"
        ) {

            setNavStatus(
                (
                    "Cancelada"
                    +
                    ` · ${status.remaining_count || 0} pendiente(s)`
                ),
                "warning"
            );

        } else if (
            state ===
            "ready"
        ) {

            setNavStatus(
                (
                    "Cola lista"
                    +
                    ` · ${status.remaining_count || 0} punto(s)`
                ),
                "ready"
            );

        } else if (
            navPlanner.points.length
            >
            0
        ) {

            setNavStatus(
                (
                    navPlanner.points.length
                    +
                    " punto(s) marcados"
                ),
                "ready"
            );

        } else {

            setNavStatus(
                "Cola vacía"
            );
        }


        if (
            status.running
            ===
            true
        ) {
            setNavPlacementMode(
                false
            );
        }


        updateNavButtons();
        renderNavMarkers();
    }


    async function refreshNavStatus() {

        try {

            const status =
                await navRequest(
                    "/nav/status"
                );

            applyNavStatus(
                status
            );

            return status;

        } catch (error) {

            setNavStatus(
                (
                    "Navegación no disponible: "
                    +
                    error.message
                ),
                "error"
            );

            updateNavButtons();

            return null;
        }
    }


    async function waitNavReady(
        expectedCount
    ) {

        const end =
            Date.now()
            +
            4000;


        while (
            Date.now()
            <
            end
        ) {

            const status =
                await refreshNavStatus();


            if (
                status
                &&
                status.state
                ===
                "ready"
                &&
                status.remaining_count
                ===
                expectedCount
                &&
                navStatusMatchesCurrentQueue(
                    status
                )
            ) {
                return;
            }


            if (
                status
                &&
                status.state
                ===
                "error"
            ) {
                throw new Error(
                    status.message
                    ||
                    "La cola rechazó los puntos."
                );
            }


            await new Promise(
                resolve =>
                    setTimeout(
                        resolve,
                        120
                    )
            );
        }


        throw new Error(
            "La cola no confirmó la carga."
        );
    }


    async function startNavQueue() {

        navPlanner.orientationPointId =
            null;

        try {

            if (
                navPlanner.points.length
                ===
                0
            ) {
                throw new Error(
                    "Marca al menos un punto."
                );
            }


            const mapName =
                navPlanner.map
                ||
                getSelectedNavMap();


            if (!mapName) {
                throw new Error(
                    "Selecciona un mapa."
                );
            }


            const status =
                await refreshNavStatus();


            if (
                !status
                ||
                status.available
                !==
                true
            ) {
                throw new Error(
                    "La navegación no está disponible."
                );
            }


            if (
                status.active_map
                !==
                mapName
            ) {
                throw new Error(
                    (
                        `El mapa activo es ${status.active_map || "ninguno"}`
                        +
                        ` y los puntos pertenecen a ${mapName}.`
                    )
                );
            }


            setNavPlacementMode(
                false
            );

            setNavStatus(
                "Cargando cola...",
                "active"
            );


            await navRequest(
                "/nav/queue",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            map:
                                mapName,

                            points:
                                navPlanner.points.map(
                                    point => ({
                                        id:
                                            point.id,
                                        x:
                                            point.x,
                                        y:
                                            point.y,
                                        yaw:
                                            point.yaw
                                    })
                                )
                        })
                }
            );


            await waitNavReady(
                navPlanner.points.length
            );


            await navRequest(
                "/nav/start",
                {
                    method:
                        "POST"
                }
            );


            setNavStatus(
                "Iniciando navegación...",
                "running"
            );


            await new Promise(
                resolve =>
                    setTimeout(
                        resolve,
                        300
                    )
            );


            await refreshNavStatus();

        } catch (error) {

            setNavStatus(
                (
                    "Error: "
                    +
                    error.message
                ),
                "error"
            );

            log(
                (
                    "Navegación A/B/C: "
                    +
                    error.message
                ),
                "error"
            );
        }
    }


    async function cancelNavQueue() {

        try {

            await navRequest(
                "/nav/cancel",
                {
                    method:
                        "POST"
                }
            );


            setNavStatus(
                "Cancelando...",
                "warning"
            );


            await new Promise(
                resolve =>
                    setTimeout(
                        resolve,
                        300
                    )
            );


            await refreshNavStatus();

        } catch (error) {

            setNavStatus(
                (
                    "Error: "
                    +
                    error.message
                ),
                "error"
            );
        }
    }


    async function clearNavQueue() {

        navPlanner.orientationPointId =
            null;

        try {

            const status =
                navPlanner.lastStatus
                ||
                {};


            if (
                status.running
                ===
                true
            ) {
                throw new Error(
                    "Cancela la navegación antes de limpiar."
                );
            }


            await navRequest(
                "/nav/clear",
                {
                    method:
                        "POST"
                }
            );


            navPlanner.points =
                [];

            navPlanner.map =
                null;

            setNavPlacementMode(
                false
            );

            renderNavMarkers();

            await refreshNavStatus();

        } catch (error) {

            setNavStatus(
                (
                    "Error: "
                    +
                    error.message
                ),
                "error"
            );
        }
    }


    function handleNavPointClick(
        event
    ) {

        if (
            event.button
            !==
            0
        ) {
            return;
        }


        const scene =
            document.getElementById(
                "mapScene"
            );


        if (
            scene
            &&
            scene.classList.contains(
                "map-calibrating"
            )
        ) {
            return;
        }


        if (
            mapView.areaSelecting
        ) {
            return;
        }


        if (
            navPlanner.orientationPointId
        ) {

            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();


            const source =
                navPlanner.points.find(
                    item =>
                        item.id
                        ===
                        navPlanner.orientationPointId
                );


            const target =
                navScreenToMap(
                    event.clientX,
                    event.clientY
                );


            if (
                !source
                ||
                !target
            ) {

                setNavStatus(
                    "Haz clic dentro de la imagen del mapa.",
                    "error"
                );

                return;
            }


            const dx =
                Number(target.x)
                -
                Number(source.x);

            const dy =
                Number(target.y)
                -
                Number(source.y);


            if (
                Math.hypot(
                    dx,
                    dy
                )
                <
                0.03
            ) {

                setNavStatus(
                    (
                        source.id
                        +
                        " · elige una dirección un poco más alejada"
                    ),
                    "warning"
                );

                return;
            }


            source.yaw =
                Math.atan2(
                    dy,
                    dx
                );


            const degrees =
                Math.round(
                    source.yaw
                    *
                    180
                    /
                    Math.PI
                );


            navPlanner.orientationPointId =
                null;

            navPlanner.executionSeen =
                false;


            renderNavMarkers();

            renderNavQueue();

            updateNavButtons();


            setNavStatus(
                (
                    source.id
                    +
                    " · orientación "
                    +
                    degrees
                    +
                    "°"
                ),
                "ready"
            );

            return;
        }


        if (!navPlanner.placing) {
            return;
        }


        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();


        if (
            navPlanner.points.length
            >=
            50
        ) {

            setNavStatus(
                "Máximo 50 puntos.",
                "error"
            );

            return;
        }


        const mapName =
            getSelectedNavMap();


        if (!mapName) {

            setNavStatus(
                "Selecciona y muestra un mapa.",
                "error"
            );

            return;
        }


        const point =
            navScreenToMap(
                event.clientX,
                event.clientY
            );


        if (!point) {

            setNavStatus(
                "Haz clic dentro de la imagen del mapa.",
                "error"
            );

            return;
        }


        if (
            navPlanner.map
            &&
            navPlanner.map
            !==
            mapName
        ) {

            setNavStatus(
                "Limpia los puntos antes de cambiar de mapa.",
                "error"
            );

            return;
        }


        navPlanner.executionSeen =
            false;

        navPlanner.map =
            mapName;


        navPlanner.points.push({
            id:
                navPointId(
                    navPlanner.points.length
                ),

            x:
                point.x,

            y:
                point.y,

            yaw:
                null,

            u:
                point.u,

            v:
                point.v
        });


        renderNavMarkers();

        updateNavButtons();

        setNavStatus(
            (
                `${navPlanner.points.length} punto(s) marcados`
                +
                " · clic para continuar"
            ),
            "active"
        );
    }


    function installNavPlannerUI() {

        const toolbar =
            document.querySelector(
                ".map-toolbar"
            );

        const scene =
            document.getElementById(
                "mapScene"
            );

        const viewport =
            document.getElementById(
                "mapViewport"
            );


        if (
            !toolbar
            ||
            !scene
            ||
            !viewport
        ) {
            return;
        }


        if (
            document.getElementById(
                "mapNavPointsButton"
            )
        ) {
            return;
        }


        const pointsButton =
            document.createElement(
                "button"
            );

        pointsButton.id =
            "mapNavPointsButton";

        pointsButton.type =
            "button";

        pointsButton.textContent =
            "Agregar puntos";


        const startButton =
            document.createElement(
                "button"
            );

        startButton.id =
            "mapNavStartButton";

        startButton.type =
            "button";

        startButton.textContent =
            "Iniciar";

        startButton.disabled =
            true;


        const cancelButton =
            document.createElement(
                "button"
            );

        cancelButton.id =
            "mapNavCancelButton";

        cancelButton.type =
            "button";

        cancelButton.textContent =
            "Cancelar";

        cancelButton.disabled =
            true;


        const clearButton =
            document.createElement(
                "button"
            );

        clearButton.id =
            "mapNavClearButton";

        clearButton.type =
            "button";

        clearButton.textContent =
            "Borrar cola";

        clearButton.title =
            "Eliminar todos los puntos de navegación";


        const status =
            document.createElement(
                "span"
            );

        status.id =
            "mapNavStatus";

        status.textContent =
            "Cola vacía";


        toolbar.appendChild(
            pointsButton
        );

        toolbar.appendChild(
            startButton
        );

        toolbar.appendChild(
            cancelButton
        );

        toolbar.appendChild(
            clearButton
        );

        toolbar.appendChild(
            status
        );


        ensureNavOverlay();

        ensureNavQueueTable();

        renderNavQueue();


        pointsButton.addEventListener(
            "click",
            () => {

                setNavPlacementMode(
                    !navPlanner.placing
                );
            }
        );


        startButton.addEventListener(
            "click",
            startNavQueue
        );


        cancelButton.addEventListener(
            "click",
            cancelNavQueue
        );


        clearButton.addEventListener(
            "click",
            clearNavQueue
        );


        scene.addEventListener(
            "mousedown",
            handleNavPointClick,
            true
        );


        const calibrationButton =
            document.getElementById(
                "mapCalibrationButton"
            );


        if (calibrationButton) {

            calibrationButton.addEventListener(
                "click",
                () => {

                    if (
                        navPlanner.placing
                    ) {
                        setNavPlacementMode(
                            false
                        );
                    }
                },
                true
            );
        }


        const mapSelect =
            document.getElementById(
                "mapSelect"
            );


        if (mapSelect) {

            mapSelect.addEventListener(
                "change",
                () => {

                    if (
                        navPlanner.points.length
                        ===
                        0
                    ) {
                        navPlanner.map =
                            null;
                    }

                    renderNavMarkers();
                }
            );
        }


        window.addEventListener(
            "resize",
            renderNavMarkers
        );


        navPlanner.timer =
            window.setInterval(
                refreshNavStatus,
                500
            );


        refreshNavStatus();
    }


    if (
        document.readyState
        ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            installNavPlannerUI
        );

    } else {

        installNavPlannerUI();
    }

})();


// =========================================================
// SAFEVISION MISION AUTOMATICA - SELECTOR
// =========================================================

(() => {

    const autoMissionState = {
        loaded:
            null,

        simulation:
            null,

        prepared:
            false,

        running:
            false,

        busy:
            false,

        pollTimer:
            null,

        listLoaded:
            false
    };


    const pilotButton =
        document.getElementById(
            "pilotTabButton"
        );

    const autoButton =
        document.getElementById(
            "autoTabButton"
        );

    const pilotView =
        document.getElementById(
            "pilotModeView"
        );

    const autoView =
        document.getElementById(
            "autoModeView"
        );

    const subtitle =
        document.getElementById(
            "dashboardSubtitle"
        );

    const missionSelect =
        document.getElementById(
            "autoMissionSelect"
        );

    const refreshButton =
        document.getElementById(
            "autoMissionRefresh"
        );

    const startButton =
        document.getElementById(
            "autoMissionStart"
        );

    const cancelButton =
        document.getElementById(
            "autoMissionCancel"
        );

    const missionMap =
        document.getElementById(
            "autoMissionMap"
        );

    const missionInitial =
        document.getElementById(
            "autoMissionInitial"
        );

    const missionPoints =
        document.getElementById(
            "autoMissionPoints"
        );

    const missionActions =
        document.getElementById(
            "autoMissionActions"
        );

    const missionProgress =
        document.getElementById(
            "autoMissionProgress"
        );

    const missionCurrentAction =
        document.getElementById(
            "autoMissionCurrentAction"
        );

    const missionCode =
        document.getElementById(
            "autoMissionCode"
        );

    const missionStatus =
        document.getElementById(
            "autoMissionStatus"
        );


    if (
        !pilotButton
        ||
        !autoButton
        ||
        !pilotView
        ||
        !autoView
        ||
        !missionSelect
        ||
        !startButton
        ||
        !cancelButton
        ||
        !missionProgress
        ||
        !missionCurrentAction
    ) {
        return;
    }


    function setMissionStatus(
        message,
        state=""
    ) {

        missionStatus.textContent =
            message;

        missionStatus.className =
            "auto-mission-status";

        if (state) {
            missionStatus.classList.add(
                state
            );
        }
    }


    function stopMissionPolling() {

        if (
            autoMissionState.pollTimer
            !==
            null
        ) {

            clearTimeout(
                autoMissionState.pollTimer
            );

            autoMissionState.pollTimer =
                null;
        }
    }


    function currentActionLabel(
        action
    ) {

        if (!action) {
            return "—";
        }


        if (
            typeof action
            ===
            "string"
        ) {
            return action;
        }


        if (
            typeof action
            !==
            "object"
        ) {
            return "—";
        }


        const name =
            action.name
            ||
            "acción";


        if (
            action.point
            &&
            typeof action.point
            ===
            "object"
            &&
            action.point.id
        ) {

            return (
                name
                +
                " "
                +
                action.point.id
            );
        }


        if (action.reference_id) {

            return (
                name
                +
                " "
                +
                action.reference_id
            );
        }


        return name;
    }


    function updateMissionControls() {

        const running =
            autoMissionState.running;

        const busy =
            autoMissionState.busy;

        const controlsLocked =
            (
                running
                ||
                busy
            );


        missionSelect.disabled =
            controlsLocked;

        refreshButton.disabled =
            controlsLocked;


        startButton.disabled =
            (
                controlsLocked
                ||
                !autoMissionState.prepared
            );


        cancelButton.disabled =
            (
                !running
                ||
                busy
            );


        pilotButton.disabled =
            running;


        pilotButton.title =
            running
                ?
                "La misión automática está en ejecución."
                :
                "";


        startButton.title =
            running
                ?
                "La misión está en ejecución."
                :
                (
                    autoMissionState.prepared
                        ?
                        "Iniciar misión preparada."
                        :
                        "La misión debe estar preparada antes de iniciar."
                );


        cancelButton.title =
            running
                ?
                "Cancelar la misión en ejecución."
                :
                "No hay una misión en ejecución.";
    }


    function applyMissionRuntimeStatus(
        status
    ) {

        const count =
            Number(
                status.action_count
            );

        const index =
            Number(
                status.action_index
            );


        const safeCount =
            Number.isFinite(
                count
            )
                ?
                count
                :
                0;

        const safeIndex =
            Number.isFinite(
                index
            )
                ?
                index
                :
                0;


        missionProgress.textContent =
            (
                String(safeIndex)
                +
                " / "
                +
                String(safeCount)
            );


        missionCurrentAction.textContent =
            currentActionLabel(
                status.current_action
            );


        autoMissionState.running =
            Boolean(
                status.running
            );


        const state =
            status.state
            ||
            "";


        const message =
            status.message
            ||
            state
            ||
            "Estado desconocido.";


        if (state === "completed") {

            autoMissionState.prepared =
                false;

            setMissionStatus(
                message,
                "ready"
            );

        } else if (
            state === "error"
        ) {

            autoMissionState.prepared =
                false;

            setMissionStatus(
                message,
                "error"
            );

        } else if (
            state === "cancelled"
        ) {

            autoMissionState.prepared =
                false;

            setMissionStatus(
                message
            );

        } else if (
            autoMissionState.running
        ) {

            setMissionStatus(
                message,
                "loading"
            );

        } else if (
            state === "ready"
        ) {

            autoMissionState.prepared =
                true;

            setMissionStatus(
                message,
                "ready"
            );

        } else {

            setMissionStatus(
                message
            );
        }


        updateMissionControls();
    }


    async function pollMissionStatus() {

        stopMissionPolling();


        try {

            const status =
                await requestJson(
                    "/mission/status"
                );


            applyMissionRuntimeStatus(
                status
            );


            if (
                autoMissionState.running
            ) {

                autoMissionState.pollTimer =
                    setTimeout(
                        pollMissionStatus,
                        250
                    );
            }


        } catch (error) {

            setMissionStatus(
                error.message
                ||
                "No se pudo consultar el estado de la misión.",
                "error"
            );


            if (
                autoMissionState.running
            ) {

                autoMissionState.pollTimer =
                    setTimeout(
                        pollMissionStatus,
                        1000
                    );
            }
        }
    }


    function clearMissionDetails() {

        stopMissionPolling();

        autoMissionState.loaded =
            null;

        autoMissionState.simulation =
            null;

        autoMissionState.prepared =
            false;

        autoMissionState.running =
            false;

        missionMap.textContent =
            "—";

        missionInitial.textContent =
            "—";

        missionPoints.textContent =
            "—";

        missionActions.textContent =
            "—";

        missionProgress.textContent =
            "0 / 0";

        missionCurrentAction.textContent =
            "—";

        missionCode.textContent =
            "Selecciona una misión.";

        updateMissionControls();
    }


    async function requestJson(
        url,
        options={}
    ) {

        const response =
            await fetch(
                url,
                options
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (error) {

            data = {};
        }


        if (!response.ok) {

            throw new Error(
                data.message
                ||
                data.error
                ||
                `HTTP ${response.status}`
            );
        }


        return data;
    }


    async function simulateMission(
        mission
    ) {

        const result =
            await requestJson(
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
                                mission.code
                                ||
                                "",

                            points:
                                Array.isArray(
                                    mission.points
                                )
                                    ?
                                    mission.points
                                    :
                                    []
                        })
                }
            );


        if (!result.ok) {

            const errors =
                Array.isArray(
                    result.errors
                )
                    ?
                    result.errors
                    :
                    [];


            throw new Error(
                errors.length
                    ?
                    (
                        errors[0].message
                        ||
                        "La simulación rechazó la misión."
                    )
                    :
                    "La simulación rechazó la misión."
            );
        }


        return result;
    }


    async function loadMissionDetails(
        name
    ) {

        autoMissionState.busy =
            true;

        clearMissionDetails();


        if (!name) {

            autoMissionState.busy =
                false;

            updateMissionControls();

            setMissionStatus(
                "Esperando selección."
            );

            return;
        }


        setMissionStatus(
            "Cargando misión...",
            "loading"
        );


        missionSelect.disabled =
            true;


        try {

            const data =
                await requestJson(
                    "/missions/load?name="
                    +
                    encodeURIComponent(
                        name
                    )
                );


            const mission =
                data.mission;


            if (
                !mission
                ||
                typeof mission
                !==
                "object"
            ) {

                throw new Error(
                    "El servidor no devolvió una misión válida."
                );
            }


            const simulation =
                await simulateMission(
                    mission
                );


            if (
                !Array.isArray(
                    simulation.trace
                )
            ) {

                throw new Error(
                    "La simulación no devolvió una traza válida."
                );
            }


            autoMissionState.loaded =
                mission;

            autoMissionState.simulation =
                simulation;

            autoMissionState.prepared =
                false;


            missionMap.textContent =
                mission.map
                ||
                "—";


            missionInitial.textContent =
                mission.initial_point_id
                ||
                "—";


            missionPoints.textContent =
                Array.isArray(
                    mission.points
                )
                    ?
                    String(
                        mission.points.length
                    )
                    :
                    "0";


            missionActions.textContent =
                String(
                    simulation.action_count == null
                        ?
                        0
                        :
                        simulation.action_count
                );


            missionProgress.textContent =
                (
                    "0 / "
                    +
                    String(
                        simulation.action_count == null
                            ?
                            0
                            :
                            simulation.action_count
                    )
                );


            missionCurrentAction.textContent =
                "—";


            missionCode.textContent =
                (
                    typeof mission.code
                    ===
                    "string"
                    &&
                    mission.code.trim()
                )
                    ?
                    mission.code
                    :
                    "Sin programa.";


            autoMissionState.prepared =
                false;

            autoMissionState.running =
                false;

            updateMissionControls();


            setMissionStatus(
                "Preparando misión en el robot...",
                "loading"
            );


            try {

                const prepared =
                    await requestJson(
                        "/mission/prepare",
                        {
                            method:
                                "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    mission:
                                        mission,

                                    trace:
                                        simulation.trace
                                })
                        }
                    );


                if (
                    prepared.state
                    !==
                    "ready"
                ) {

                    throw new Error(
                        prepared.message
                        ||
                        "El robot no dejó la misión en estado ready."
                    );
                }


                autoMissionState.prepared =
                    true;

                autoMissionState.running =
                    false;

                applyMissionRuntimeStatus(
                    prepared
                );


                setMissionStatus(
                    "Misión preparada en el robot.",
                    "ready"
                );


                if (
                    typeof log
                    ===
                    "function"
                ) {

                    log(
                        `Misión automática preparada: ${mission.name}`
                    );
                }


            } catch (prepareError) {

                autoMissionState.prepared =
                    false;

                autoMissionState.running =
                    false;

                updateMissionControls();


                setMissionStatus(
                    prepareError.message
                    ||
                    "No se pudo preparar la misión en el robot.",
                    "error"
                );


                if (
                    typeof log
                    ===
                    "function"
                ) {

                    log(
                        `Misión automática no preparada: ${mission.name}`
                    );
                }


                return;
            }


        } catch (error) {

            clearMissionDetails();

            setMissionStatus(
                error.message
                ||
                "No se pudo cargar la misión.",
                "error"
            );

        } finally {

            autoMissionState.busy =
                false;

            updateMissionControls();
        }
    }


    async function loadMissionList() {

        const previous =
            missionSelect.value;


        autoMissionState.busy =
            true;


        missionSelect.disabled =
            true;

        refreshButton.disabled =
            true;


        missionSelect.innerHTML =
            "";


        const loadingOption =
            document.createElement(
                "option"
            );

        loadingOption.value =
            "";

        loadingOption.textContent =
            "Cargando misiones...";

        missionSelect.appendChild(
            loadingOption
        );


        clearMissionDetails();

        setMissionStatus(
            "Consultando biblioteca...",
            "loading"
        );


        try {

            const data =
                await requestJson(
                    "/missions"
                );


            const missions =
                Array.isArray(
                    data.missions
                )
                    ?
                    data.missions
                    :
                    [];


            missionSelect.innerHTML =
                "";


            if (!missions.length) {

                const emptyOption =
                    document.createElement(
                        "option"
                    );

                emptyOption.value =
                    "";

                emptyOption.textContent =
                    "No hay misiones guardadas";

                missionSelect.appendChild(
                    emptyOption
                );


                setMissionStatus(
                    "Biblioteca de misiones vacía."
                );

                autoMissionState.listLoaded =
                    true;

                return;
            }


            const placeholder =
                document.createElement(
                    "option"
                );

            placeholder.value =
                "";

            placeholder.textContent =
                "Seleccionar misión...";

            missionSelect.appendChild(
                placeholder
            );


            missions.forEach(
                item => {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        item.name;

                    option.textContent =
                        item.name;


                    missionSelect.appendChild(
                        option
                    );
                }
            );


            autoMissionState.listLoaded =
                true;


            const names =
                missions.map(
                    item =>
                        item.name
                );


            if (
                previous
                &&
                names.includes(
                    previous
                )
            ) {

                missionSelect.value =
                    previous;

                await loadMissionDetails(
                    previous
                );

            } else {

                missionSelect.value =
                    "";

                setMissionStatus(
                    `${missions.length} misión(es) disponible(s).`
                );
            }


        } catch (error) {

            missionSelect.innerHTML =
                "";


            const errorOption =
                document.createElement(
                    "option"
                );

            errorOption.value =
                "";

            errorOption.textContent =
                "Error al consultar misiones";

            missionSelect.appendChild(
                errorOption
            );


            setMissionStatus(
                error.message
                ||
                "No se pudieron consultar las misiones.",
                "error"
            );

        } finally {

            autoMissionState.busy =
                false;

            updateMissionControls();
        }
    }


    function setDashboardMode(
        mode
    ) {

        if (
            mode === "pilot"
            &&
            autoMissionState.running
        ) {

            setMissionStatus(
                "La misión automática sigue en ejecución. Cancélala o espera a que termine.",
                "loading"
            );

            return;
        }


        const automatic =
            mode ===
            "automatic";


        pilotView.hidden =
            automatic;

        autoView.hidden =
            !automatic;


        pilotButton.classList.toggle(
            "is-active",
            !automatic
        );

        autoButton.classList.toggle(
            "is-active",
            automatic
        );


        if (subtitle) {

            subtitle.textContent =
                automatic
                    ?
                    "Misión Automática · SafeVision"
                    :
                    "Misión Pilotada · Nivel 2";
        }


        if (
            automatic
            &&
            !autoMissionState.listLoaded
            &&
            !autoMissionState.busy
        ) {

            loadMissionList();
        }
    }


    pilotButton.addEventListener(
        "click",
        () => {

            setDashboardMode(
                "pilot"
            );
        }
    );


    autoButton.addEventListener(
        "click",
        () => {

            setDashboardMode(
                "automatic"
            );
        }
    );


    missionSelect.addEventListener(
        "change",
        () => {

            loadMissionDetails(
                missionSelect.value
            );
        }
    );


    startButton.addEventListener(
        "click",
        async () => {

            if (
                !autoMissionState.prepared
                ||
                autoMissionState.running
            ) {
                return;
            }


            autoMissionState.busy =
                true;

            updateMissionControls();

            setMissionStatus(
                "Iniciando misión...",
                "loading"
            );


            try {

                const started =
                    await requestJson(
                        "/mission/start",
                        {
                            method:
                                "POST"
                        }
                    );


                applyMissionRuntimeStatus(
                    started
                );


                autoMissionState.busy =
                    false;

                updateMissionControls();


                if (
                    autoMissionState.running
                ) {

                    pollMissionStatus();
                }


                if (
                    typeof log
                    ===
                    "function"
                ) {

                    log(
                        "Misión automática iniciada."
                    );
                }


            } catch (error) {

                autoMissionState.running =
                    false;

                autoMissionState.busy =
                    false;

                setMissionStatus(
                    error.message
                    ||
                    "No se pudo iniciar la misión.",
                    "error"
                );

                updateMissionControls();
            }
        }
    );


    cancelButton.addEventListener(
        "click",
        async () => {

            if (
                !autoMissionState.running
            ) {
                return;
            }


            autoMissionState.busy =
                true;

            updateMissionControls();

            setMissionStatus(
                "Cancelando misión...",
                "loading"
            );


            try {

                const cancelled =
                    await requestJson(
                        "/mission/cancel",
                        {
                            method:
                                "POST"
                        }
                    );


                applyMissionRuntimeStatus(
                    cancelled
                );


                autoMissionState.busy =
                    false;

                updateMissionControls();


                if (
                    autoMissionState.running
                ) {

                    pollMissionStatus();
                }


            } catch (error) {

                autoMissionState.busy =
                    false;

                setMissionStatus(
                    error.message
                    ||
                    "No se pudo cancelar la misión.",
                    "error"
                );

                updateMissionControls();
            }
        }
    );


    refreshButton.addEventListener(
        "click",
        loadMissionList
    );


    setDashboardMode(
        "pilot"
    );

})();
