const $mp = id =>
    document.getElementById(id);


function setConnection(connected) {

    const badge =
        $mp("mapearConnection");

    badge.textContent =
        connected
            ?
            "● CONECTADO"
            :
            "● DESCONECTADO";

    badge.classList.toggle(
        "connected",
        connected
    );

    badge.classList.toggle(
        "disconnected",
        !connected
    );
}


async function checkConnection() {

    try {

        const response =
            await fetch(
                "/connection_status",
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        setConnection(
            Boolean(
                response.ok
                &&
                data.connected
            )
        );

    } catch (_) {

        setConnection(false);
    }
}


function startCamera() {

    const img =
        $mp("mapearVideo");

    const placeholder =
        $mp("cameraPlaceholder");


    img.src =
        "/video_feed?t="
        +
        Date.now();


    img.hidden = false;
    placeholder.hidden = true;


    $mp("cameraStatus")
    .textContent =
        "● ACTIVA";


    $mp("cameraControlStatus")
    .textContent =
        "● ACTIVA";
}



// =========================================================
// VISOR DE MAPA
// Adaptación directa del visor probado de Automática.
// =========================================================

const mapView = {
    scale: 1,
    x: 0,
    y: 0,
    rotation: 0,

    dragging: false,
    startX: 0,
    startY: 0,

    areaSelecting: false,
    selectionDragging: false,
    selectionStartX: 0,
    selectionStartY: 0,

    ready: false
};


const mapViewport =
    $mp("mapViewport");

const mapScene =
    $mp("mapScene");

const mapZoomIn =
    $mp("zoomIn");

const mapZoomOut =
    $mp("zoomOut");

const mapReset =
    $mp("resetMap");

const mapAreaZoom =
    $mp("areaZoom");

const mapRotationSlider =
    $mp("rotationSlider");

const mapRotationValue =
    $mp("rotationValue");


let mapSelectionBox =
    null;


function updateMapRotationUI() {

    const value =
        Math.round(
            Number(
                mapView.rotation
                ||
                0
            )
        );


    if (mapRotationSlider) {

        mapRotationSlider.value =
            String(
                value
            );

        mapRotationSlider.disabled =
            !mapView.ready;
    }


    if (mapRotationValue) {

        mapRotationValue.textContent =
            String(
                value
            )
            +
            "°";
    }
}


function applyMapView() {

    if (!mapScene) {
        return;
    }


    mapScene.style.transform =
        (
            "translate("
            +
            mapView.x
            +
            "px, "
            +
            mapView.y
            +
            "px) "
            +
            "scale("
            +
            mapView.scale
            +
            ") "
            +
            "rotate("
            +
            mapView.rotation
            +
            "deg)"
        );
}


function setMapRotation(
    value
) {

    if (!mapView.ready) {
        return;
    }


    let rotation =
        Number(
            value
        );


    if (!Number.isFinite(rotation)) {
        rotation = 0;
    }


    rotation =
        Math.max(
            -180,
            Math.min(
                180,
                rotation
            )
        );


    mapView.rotation =
        rotation;


    updateMapRotationUI();

    applyMapView();
}


function resetMapView() {

    mapView.scale =
        1;

    mapView.x =
        0;

    mapView.y =
        0;

    mapView.rotation =
        0;


    updateMapRotationUI();

    applyMapView();
}


function zoomMap(
    factor
) {

    if (!mapView.ready) {
        return;
    }


    mapView.scale *=
        factor;


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


function setAreaZoomMode(
    active
) {

    mapView.areaSelecting =
        Boolean(
            active
            &&
            mapView.ready
        );


    if (mapAreaZoom) {

        mapAreaZoom.classList.toggle(
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
            event.clientX
            -
            bounds.left,
            0,
            bounds.width
        );

    const endY =
        clampMapCoordinate(
            event.clientY
            -
            bounds.top,
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
            bounds.width
            /
            width,
            bounds.height
            /
            height
        )
        *
        0.90;


    const oldScale =
        mapView.scale;


    const newScale =
        Math.max(
            0.5,
            Math.min(
                10,
                oldScale
                *
                factor
            )
        );


    const realFactor =
        newScale
        /
        oldScale;


    const selectedCenterX =
        left
        +
        width / 2;

    const selectedCenterY =
        top
        +
        height / 2;


    const viewportCenterX =
        bounds.width / 2;

    const viewportCenterY =
        bounds.height / 2;


    mapView.x =
        (
            viewportCenterX
            +
            mapView.x
            -
            selectedCenterX
        )
        *
        realFactor;


    mapView.y =
        (
            viewportCenterY
            +
            mapView.y
            -
            selectedCenterY
        )
        *
        realFactor;


    mapView.scale =
        newScale;


    applyMapView();

    setAreaZoomMode(
        false
    );
}


function setMapViewerEnabled(
    enabled
) {

    mapView.ready =
        Boolean(
            enabled
        );


    [
        mapZoomIn,
        mapZoomOut,
        mapReset,
        mapAreaZoom

    ].forEach(
        element => {

            if (element) {

                element.disabled =
                    !mapView.ready;
            }
        }
    );


    updateMapRotationUI();


    if (!mapView.ready) {

        mapView.dragging =
            false;

        mapView.selectionDragging =
            false;

        setAreaZoomMode(
            false
        );
    }
}


function installMapViewer() {

    ensureMapSelectionBox();

    setMapViewerEnabled(
        false
    );


    if (mapRotationSlider) {

        mapRotationSlider.addEventListener(
            "input",
            () => {

                setMapRotation(
                    mapRotationSlider.value
                );
            }
        );
    }


    if (mapZoomIn) {

        mapZoomIn.addEventListener(
            "click",
            () =>
                zoomMap(
                    1.25
                )
        );
    }


    if (mapZoomOut) {

        mapZoomOut.addEventListener(
            "click",
            () =>
                zoomMap(
                    0.8
                )
        );
    }


    if (mapReset) {

        mapReset.addEventListener(
            "click",
            resetMapView
        );
    }


    if (mapAreaZoom) {

        mapAreaZoom.addEventListener(
            "click",
            () => {

                setAreaZoomMode(
                    !mapView.areaSelecting
                );
            }
        );
    }


    if (mapViewport) {

        mapViewport.addEventListener(
            "wheel",
            event => {

                if (
                    !mapView.ready
                    ||
                    !mapScene
                    ||
                    mapScene.hidden
                ) {
                    return;
                }


                event.preventDefault();


                zoomMap(
                    event.deltaY < 0
                        ?
                        1.15
                        :
                        0.87
                );
            },
            {
                passive:
                    false
            }
        );


        mapViewport.addEventListener(
            "mousedown",
            event => {

                if (
                    !mapView.ready
                    ||
                    !mapScene
                    ||
                    mapScene.hidden
                ) {
                    return;
                }


                if (
                    mapView.areaSelecting
                ) {

                    event.preventDefault();

                    event.stopImmediatePropagation();


                    ensureMapSelectionBox();


                    const bounds =
                        mapViewport.getBoundingClientRect();


                    mapView.selectionStartX =
                        clampMapCoordinate(
                            event.clientX
                            -
                            bounds.left,
                            0,
                            bounds.width
                        );

                    mapView.selectionStartY =
                        clampMapCoordinate(
                            event.clientY
                            -
                            bounds.top,
                            0,
                            bounds.height
                        );


                    mapView.selectionDragging =
                        true;


                    mapSelectionBox.style.left =
                        mapView.selectionStartX
                        +
                        "px";

                    mapSelectionBox.style.top =
                        mapView.selectionStartY
                        +
                        "px";

                    mapSelectionBox.style.width =
                        "0px";

                    mapSelectionBox.style.height =
                        "0px";

                    mapSelectionBox.hidden =
                        false;


                    return;
                }


                mapView.dragging =
                    true;

                mapView.startX =
                    event.clientX
                    -
                    mapView.x;

                mapView.startY =
                    event.clientY
                    -
                    mapView.y;


                mapViewport.classList.add(
                    "dragging"
                );
            }
        );
    }


    window.addEventListener(
        "mousemove",
        event => {

            if (
                mapView.selectionDragging
                &&
                mapViewport
                &&
                mapSelectionBox
            ) {

                const bounds =
                    mapViewport.getBoundingClientRect();


                const currentX =
                    clampMapCoordinate(
                        event.clientX
                        -
                        bounds.left,
                        0,
                        bounds.width
                    );

                const currentY =
                    clampMapCoordinate(
                        event.clientY
                        -
                        bounds.top,
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
                    left
                    +
                    "px";

                mapSelectionBox.style.top =
                    top
                    +
                    "px";

                mapSelectionBox.style.width =
                    width
                    +
                    "px";

                mapSelectionBox.style.height =
                    height
                    +
                    "px";


                return;
            }


            if (!mapView.dragging) {
                return;
            }


            mapView.x =
                event.clientX
                -
                mapView.startX;

            mapView.y =
                event.clientY
                -
                mapView.startY;


            applyMapView();
        }
    );


    window.addEventListener(
        "mouseup",
        event => {

            if (
                mapView.selectionDragging
            ) {

                finishAreaZoom(
                    event
                );
            }


            mapView.dragging =
                false;


            if (mapViewport) {

                mapViewport.classList.remove(
                    "dragging"
                );
            }
        }
    );
}


// =========================================================
// MAPA ROS EN VIVO
// =========================================================

const liveMapState = {
    version: null,
    pendingVersion: null,
    meta: null,
    busy: false
};


function setLiveMapUnavailable(
    message
) {

    const scene =
        $mp("mapScene");

    const placeholder =
        $mp("mapPlaceholder");


    if (
        liveMapState.version === null
    ) {

        scene.hidden = true;

        placeholder.hidden = false;

        placeholder.textContent =
            message;
    }


    $mp("toolbarStatus")
    .textContent =
        message;
}


function loadLiveMapImage(
    meta
) {

    const image =
        $mp("mapImage");

    const scene =
        $mp("mapScene");

    const placeholder =
        $mp("mapPlaceholder");


    const version =
        Number(
            meta.version
        );


    if (
        !Number.isFinite(version)
        ||
        version === liveMapState.version
        ||
        version === liveMapState.pendingVersion
    ) {
        return;
    }


    liveMapState.pendingVersion =
        version;


    image.onload =
        () => {

            const firstMap =
                liveMapState.version === null;

            liveMapState.version =
                version;

            liveMapState.pendingVersion =
                null;


            scene.hidden = false;

            placeholder.hidden = true;


            setMapViewerEnabled(
                true
            );


            if (firstMap) {

                resetMapView();
            }


            $mp("mapSubtitle")
            .textContent =
                (
                    "Mapa ROS · "
                    +
                    meta.width
                    +
                    "×"
                    +
                    meta.height
                    +
                    " · "
                    +
                    Number(
                        meta.resolution
                    ).toFixed(3)
                    +
                    " m/píxel"
                );


            $mp("toolbarStatus")
            .textContent =
                (
                    "Mapa recibido · versión "
                    +
                    version
                );
        };


    image.onerror =
        () => {

            liveMapState.pendingVersion =
                null;

            setLiveMapUnavailable(
                "No se pudo cargar el mapa ROS."
            );
        };


    image.src =
        (
            "/mapping/map?v="
            +
            encodeURIComponent(
                version
            )
            +
            "&t="
            +
            Date.now()
        );
}


async function refreshLiveMap() {

    if (liveMapState.busy) {
        return;
    }


    liveMapState.busy = true;


    try {

        const response =
            await fetch(
                "/mapping/meta",
                {
                    cache: "no-store"
                }
            );


        const meta =
            await response.json();


        if (
            !response.ok
            ||
            !meta
            ||
            !meta.ok
            ||
            !meta.available
        ) {

            throw new Error(
                (
                    meta
                    &&
                    (
                        meta.error
                        ||
                        meta.message
                    )
                )
                ||
                "Mapa ROS no disponible."
            );
        }


        liveMapState.meta =
            meta;


        loadLiveMapImage(
            meta
        );


    } catch (error) {

        setLiveMapUnavailable(
            (
                error
                &&
                error.message
            )
            ||
            "Mapa ROS no disponible."
        );


    } finally {

        liveMapState.busy =
            false;
    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        checkConnection();

        window.setInterval(
            checkConnection,
            3000
        );

        installMapViewer();

        startCamera();

        refreshLiveMap();

        window.setInterval(
            refreshLiveMap,
            500
        );
    }
);
