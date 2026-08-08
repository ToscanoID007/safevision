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
    busy: false
};


// Huella aproximada ROSMASTER X3 vista desde arriba.
// Yahboom: aproximadamente 24 cm x 20 cm.
const ROSMASTER_X3_LENGTH_M = 0.24;
const ROSMASTER_X3_WIDTH_M = 0.20;


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
            return;
        }


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

        marker.hidden = false;


    } catch (_) {

        const marker =
            $("robotMarker");

        if (marker) {
            marker.hidden = true;
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
