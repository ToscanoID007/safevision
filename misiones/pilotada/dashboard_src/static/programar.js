const $p = (id) =>
    document.getElementById(id);


// =========================================================
// ESTADO GENERAL
// =========================================================

const progMapView = {
    scale: 1,
    x: 0,
    y: 0,
    rotation: 0,
    locked: false,

    dragging: false,
    dragStartX: 0,
    dragStartY: 0,

    areaSelecting: false,
    selectionDragging: false,
    selectionStartX: 0,
    selectionStartY: 0
};


const progPlanner = {
    points: [],
    map: null,
    meta: null,

    placing: false,

    selectedId: null,
    orientationPointId: null,
    initialPointId: null,

    nextPointId: 0
};



const progMissionState = {
    savedName: null
};


// =========================================================
// LOG
// =========================================================

function progLog(
    message
) {

    const box =
        $p("progConsole");


    if (!box) {
        return;
    }


    const time =
        new Date()
        .toLocaleTimeString();


    box.textContent =
        (
            "["
            +
            time
            +
            "] "
            +
            message
            +
            "\n"
            +
            box.textContent
        );
}


// =========================================================
// MAPA - TRANSFORM VISUAL
// =========================================================

function updateProgRotationUI() {

    const slider =
        $p("progRotationSlider");

    const output =
        $p("progRotationValue");


    const value =
        Math.round(
            Number(
                progMapView.rotation
                ||
                0
            )
        );


    if (slider) {

        slider.value =
            String(
                value
            );
    }


    if (output) {

        output.textContent =
            (
                value
                +
                "°"
            );
    }
}


function applyProgMapView() {

    const scene =
        $p("progMapScene");


    if (!scene) {
        return;
    }


    scene.style.transform =
        (
            "translate("
            +
            progMapView.x
            +
            "px, "
            +
            progMapView.y
            +
            "px) "
            +
            "scale("
            +
            progMapView.scale
            +
            ") "
            +
            "rotate("
            +
            progMapView.rotation
            +
            "deg)"
        );


    window.requestAnimationFrame(
        renderProgMarkers
    );
}


function resetProgMapView() {

    if (progMapView.locked) {
        return;
    }


    progMapView.scale =
        1;

    progMapView.x =
        0;

    progMapView.y =
        0;

    progMapView.rotation =
        0;


    cancelProgAreaZoom();

    updateProgRotationUI();

    applyProgMapView();
}


function zoomProgMap(
    factor
) {

    if (progMapView.locked) {

        progLog(
            "Mapa bloqueado."
        );

        return;
    }


    progMapView.scale *=
        factor;


    progMapView.scale =
        Math.max(
            0.5,
            Math.min(
                10,
                progMapView.scale
            )
        );


    applyProgMapView();
}


function setProgRotation(
    value
) {

    if (progMapView.locked) {

        updateProgRotationUI();

        progLog(
            "Mapa bloqueado."
        );

        return;
    }


    const degrees =
        Number(
            value
        );


    if (
        !Number.isFinite(
            degrees
        )
    ) {
        return;
    }


    progMapView.rotation =
        Math.max(
            -180,
            Math.min(
                180,
                degrees
            )
        );


    updateProgRotationUI();

    applyProgMapView();
}


// =========================================================
// BLOQUEO
// =========================================================

function updateProgLockUI() {

    const button =
        $p("progMapLock");

    const badge =
        $p("progMapLockedBadge");


    if (button) {

        button.textContent =
            progMapView.locked
                ?
                "Desbloquear"
                :
                "Bloquear";


        button.classList.toggle(
            "prog-locked",
            progMapView.locked
        );
    }


    if (badge) {

        badge.hidden =
            !progMapView.locked;
    }


    updateProgPlannerButtons();
}


function toggleProgMapLock() {

    progMapView.locked =
        !progMapView.locked;


    if (progMapView.locked) {

        progPlanner.placing =
            false;

        progPlanner.orientationPointId =
            null;

        cancelProgAreaZoom();
    }


    updateProgLockUI();

    renderProgPlanner();


    progLog(
        progMapView.locked
            ?
            "Mapa bloqueado."
            :
            "Mapa desbloqueado."
    );
}


// =========================================================
// ZOOM DE AREA
// =========================================================

function cancelProgAreaZoom() {

    progMapView.areaSelecting =
        false;

    progMapView.selectionDragging =
        false;


    const box =
        $p("progAreaSelection");

    const button =
        $p("progAreaZoom");


    if (box) {

        box.hidden =
            true;
    }


    if (button) {

        button.classList.remove(
            "prog-active-tool"
        );

        button.textContent =
            "Zoom área";
    }
}


function toggleProgAreaZoom() {

    if (progMapView.locked) {

        progLog(
            "Desbloquea el mapa para usar Zoom área."
        );

        return;
    }


    progMapView.areaSelecting =
        !progMapView.areaSelecting;


    progPlanner.placing =
        false;

    progPlanner.orientationPointId =
        null;


    const button =
        $p("progAreaZoom");


    if (button) {

        button.classList.toggle(
            "prog-active-tool",
            progMapView.areaSelecting
        );

        button.textContent =
            progMapView.areaSelecting
                ?
                "Cancelar zoom"
                :
                "Zoom área";
    }


    if (!progMapView.areaSelecting) {

        cancelProgAreaZoom();

    } else {

        progLog(
            "Zoom área: arrastra un rectángulo."
        );
    }


    updateProgPlannerButtons();
}


function startProgAreaSelection(
    event
) {

    if (
        !progMapView.areaSelecting
        ||
        progMapView.locked
        ||
        event.button !== 0
    ) {
        return false;
    }


    const viewport =
        $p("progMapViewport");

    const box =
        $p("progAreaSelection");


    if (
        !viewport
        ||
        !box
    ) {
        return false;
    }


    const rect =
        viewport.getBoundingClientRect();


    progMapView.selectionDragging =
        true;

    progMapView.selectionStartX =
        event.clientX
        -
        rect.left;

    progMapView.selectionStartY =
        event.clientY
        -
        rect.top;


    box.style.left =
        (
            progMapView.selectionStartX
            +
            "px"
        );

    box.style.top =
        (
            progMapView.selectionStartY
            +
            "px"
        );

    box.style.width =
        "0px";

    box.style.height =
        "0px";

    box.hidden =
        false;


    event.preventDefault();

    event.stopPropagation();

    return true;
}


function moveProgAreaSelection(
    event
) {

    if (
        !progMapView.selectionDragging
    ) {
        return;
    }


    const viewport =
        $p("progMapViewport");

    const box =
        $p("progAreaSelection");


    if (
        !viewport
        ||
        !box
    ) {
        return;
    }


    const rect =
        viewport.getBoundingClientRect();


    const currentX =
        Math.max(
            0,
            Math.min(
                rect.width,
                event.clientX
                -
                rect.left
            )
        );

    const currentY =
        Math.max(
            0,
            Math.min(
                rect.height,
                event.clientY
                -
                rect.top
            )
        );


    const left =
        Math.min(
            progMapView.selectionStartX,
            currentX
        );

    const top =
        Math.min(
            progMapView.selectionStartY,
            currentY
        );

    const width =
        Math.abs(
            currentX
            -
            progMapView.selectionStartX
        );

    const height =
        Math.abs(
            currentY
            -
            progMapView.selectionStartY
        );


    box.style.left =
        left
        +
        "px";

    box.style.top =
        top
        +
        "px";

    box.style.width =
        width
        +
        "px";

    box.style.height =
        height
        +
        "px";
}


function finishProgAreaSelection(
    event
) {

    if (
        !progMapView.selectionDragging
    ) {
        return;
    }


    const viewport =
        $p("progMapViewport");

    const box =
        $p("progAreaSelection");


    if (
        !viewport
        ||
        !box
    ) {

        cancelProgAreaZoom();

        return;
    }


    const rect =
        viewport.getBoundingClientRect();


    const left =
        parseFloat(
            box.style.left
        )
        ||
        0;

    const top =
        parseFloat(
            box.style.top
        )
        ||
        0;

    const width =
        parseFloat(
            box.style.width
        )
        ||
        0;

    const height =
        parseFloat(
            box.style.height
        )
        ||
        0;


    if (
        width < 20
        ||
        height < 20
    ) {

        cancelProgAreaZoom();

        return;
    }


    const factor =
        Math.min(
            rect.width
            /
            width,
            rect.height
            /
            height
        )
        *
        0.90;


    const oldScale =
        progMapView.scale;


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


    const selectionCenterX =
        left
        +
        width
        /
        2;

    const selectionCenterY =
        top
        +
        height
        /
        2;


    const viewportCenterX =
        rect.width
        /
        2;

    const viewportCenterY =
        rect.height
        /
        2;


    progMapView.x =
        (
            viewportCenterX
            +
            progMapView.x
            -
            selectionCenterX
        )
        *
        realFactor;

    progMapView.y =
        (
            viewportCenterY
            +
            progMapView.y
            -
            selectionCenterY
        )
        *
        realFactor;


    progMapView.scale =
        newScale;


    cancelProgAreaZoom();

    applyProgMapView();


    progLog(
        "Zoom de área aplicado."
    );


    event.preventDefault();
}


// =========================================================
// MAPAS
// =========================================================

async function loadProgMaps() {

    const select =
        $p("progMapSelect");


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
                "No se pudieron cargar mapas."
            );
        }


        for (
            const map
            of data.maps || []
        ) {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                map.name;

            option.textContent =
                map.name;

            select.appendChild(
                option
            );
        }


        progLog(
            (
                (data.maps || []).length
                +
                " mapa(s) disponibles."
            )
        );


    } catch (error) {

        progLog(
            (
                "Mapas: "
                +
                error.message
            )
        );
    }
}


async function loadProgMapMeta(
    name
) {

    const response =
        await fetch(
            (
                "/map_meta/"
                +
                encodeURIComponent(
                    name
                )
            ),
            {
                cache:
                    "no-store"
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
            "Metadatos no disponibles."
        );
    }


    progPlanner.map =
        name;

    progPlanner.meta =
        data;
}


function showProgMap() {

    const select =
        $p("progMapSelect");

    const image =
        $p("progMapImage");

    const scene =
        $p("progMapScene");

    const placeholder =
        $p("progMapPlaceholder");

    const status =
        $p("progMapStatus");


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


    const name =
        select.value;


    if (!name) {

        progLog(
            "Selecciona un mapa."
        );

        return;
    }


    if (
        progPlanner.points.length
        &&
        progPlanner.map
        &&
        progPlanner.map
        !==
        name
    ) {

        progLog(
            "Borra los puntos antes de cambiar de mapa."
        );

        return;
    }


    image.onload =
        async () => {

            try {

                await loadProgMapMeta(
                    name
                );


                scene.hidden =
                    false;

                placeholder.hidden =
                    true;


                resetProgMapView();


                if (status) {

                    status.textContent =
                        (
                            "Mapa: "
                            +
                            name
                        );
                }


                renderProgPlanner();


                progLog(
                    (
                        "Mapa preparado para puntos: "
                        +
                        name
                    )
                );


            } catch (error) {

                progPlanner.meta =
                    null;


                progLog(
                    (
                        "Metadatos: "
                        +
                        error.message
                    )
                );


                renderProgPlanner();
            }
        };


    image.src =
        (
            "/map_image/"
            +
            encodeURIComponent(
                name
            )
            +
            "?t="
            +
            Date.now()
        );
}


// =========================================================
// CONVERSION DE COORDENADAS
// MISMA BASE QUE PILOTADA + INVERSA DE ROTACION VISUAL
// =========================================================

function getProgImageLayout() {

    const viewport =
        $p("progMapViewport");

    const image =
        $p("progMapImage");


    if (
        !viewport
        ||
        !image
        ||
        !image.naturalWidth
        ||
        !image.naturalHeight
    ) {
        return null;
    }


    const width =
        viewport.clientWidth;

    const height =
        viewport.clientHeight;


    if (
        width <= 0
        ||
        height <= 0
    ) {
        return null;
    }


    const imageRatio =
        image.naturalWidth
        /
        image.naturalHeight;

    const viewportRatio =
        width
        /
        height;


    let imageWidth;
    let imageHeight;
    let left;
    let top;


    if (
        viewportRatio
        >
        imageRatio
    ) {

        imageHeight =
            height;

        imageWidth =
            imageHeight
            *
            imageRatio;

        left =
            (
                width
                -
                imageWidth
            )
            /
            2;

        top =
            0;

    } else {

        imageWidth =
            width;

        imageHeight =
            imageWidth
            /
            imageRatio;

        left =
            0;

        top =
            (
                height
                -
                imageHeight
            )
            /
            2;
    }


    return {
        viewportWidth:
            width,

        viewportHeight:
            height,

        left:
            left,

        top:
            top,

        width:
            imageWidth,

        height:
            imageHeight
    };
}


function progScreenToScene(
    clientX,
    clientY
) {

    const viewport =
        $p("progMapViewport");

    const layout =
        getProgImageLayout();


    if (
        !viewport
        ||
        !layout
    ) {
        return null;
    }


    const rect =
        viewport.getBoundingClientRect();


    const screenX =
        clientX
        -
        rect.left;

    const screenY =
        clientY
        -
        rect.top;


    const centerX =
        layout.viewportWidth
        /
        2;

    const centerY =
        layout.viewportHeight
        /
        2;


    const scale =
        Number(
            progMapView.scale
        );


    if (
        !Number.isFinite(
            scale
        )
        ||
        scale <= 0
    ) {
        return null;
    }


    const scaledX =
        (
            screenX
            -
            centerX
            -
            progMapView.x
        )
        /
        scale;

    const scaledY =
        (
            screenY
            -
            centerY
            -
            progMapView.y
        )
        /
        scale;


    const angle =
        -
        Number(
            progMapView.rotation
            ||
            0
        )
        *
        Math.PI
        /
        180;


    const cosA =
        Math.cos(
            angle
        );

    const sinA =
        Math.sin(
            angle
        );


    return {
        x:
            centerX
            +
            cosA
            *
            scaledX
            -
            sinA
            *
            scaledY,

        y:
            centerY
            +
            sinA
            *
            scaledX
            +
            cosA
            *
            scaledY
    };
}


function progScreenToMap(
    clientX,
    clientY
) {

    const meta =
        progPlanner.meta;

    const layout =
        getProgImageLayout();

    const scenePoint =
        progScreenToScene(
            clientX,
            clientY
        );


    if (
        !meta
        ||
        !layout
        ||
        !scenePoint
    ) {
        return null;
    }


    const u =
        (
            scenePoint.x
            -
            layout.left
        )
        /
        layout.width;

    const v =
        (
            scenePoint.y
            -
            layout.top
        )
        /
        layout.height;


    if (
        u < 0
        ||
        u > 1
        ||
        v < 0
        ||
        v > 1
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


    const pixelX =
        u
        *
        width;

    const pixelY =
        v
        *
        height;


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


    return {
        x:
            originX
            +
            cosO
            *
            localX
            -
            sinO
            *
            localY,

        y:
            originY
            +
            sinO
            *
            localX
            +
            cosO
            *
            localY,

        u:
            u,

        v:
            v
    };
}


// =========================================================
// IDs A / B / C ...
// =========================================================

function progPointId(
    value
) {

    const number =
        Number(
            value
        );


    if (
        !Number.isInteger(
            number
        )
        ||
        number < 0
        ||
        number > 0xFFF
    ) {
        return null;
    }


    return (
        "0x"
        +
        number
            .toString(16)
            .toUpperCase()
            .padStart(
                3,
                "0"
            )
    );
}


function normalizeProgPointId(
    value
) {

    const text =
        String(
            value
            ||
            ""
        ).trim();


    const match =
        text.match(
            /^0[xX]([0-9a-fA-F]{1,3})$/
        );


    if (!match) {
        return null;
    }


    const number =
        parseInt(
            match[1],
            16
        );


    return progPointId(
        number
    );
}


function progPointIdExists(
    id,
    ignoredPoint = null
) {

    return progPlanner.points.some(
        point => {

            if (
                ignoredPoint
                &&
                point === ignoredPoint
            ) {
                return false;
            }


            return (
                point.id
                ===
                id
            );
        }
    );
}


function nextProgPointId() {

    while (
        progPlanner.nextPointId
        <=
        0xFFF
    ) {

        const id =
            progPointId(
                progPlanner.nextPointId
            );


        progPlanner.nextPointId +=
            1;


        if (
            !progPointIdExists(
                id
            )
        ) {

            return id;
        }
    }


    return null;
}


function renumberProgPoints() {

    /*
     * Los IDs son estables.
     * El orden se obtiene directamente
     * de la posición en progPlanner.points.
     */

}


// =========================================================
// CANVAS - MISMA ESTRATEGIA DE PILOTADA
// =========================================================

function ensureProgWaypointCanvas() {

    const scene =
        $p("progMapScene");


    if (!scene) {
        return null;
    }


    let canvas =
        $p("progWaypointCanvas");


    if (!canvas) {

        canvas =
            document.createElement(
                "canvas"
            );

        canvas.id =
            "progWaypointCanvas";

        canvas.style.position =
            "absolute";

        canvas.style.inset =
            "0";

        canvas.style.zIndex =
            "25";

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


function renderProgMarkers() {

    const scene =
        $p("progMapScene");

    const image =
        $p("progMapImage");

    const canvas =
        ensureProgWaypointCanvas();

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
        image.offsetParent
        ===
        null
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
                progMapView.scale
                ||
                1
            )
        );

    const deviceScale =
        Math.max(
            1,
            window.devicePixelRatio
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


    const screenCompensation =
        1
        /
        Math.max(
            0.01,
            Number(
                progMapView.scale
                ||
                1
            )
        );


    for (
        let pointIndex = 0;
        pointIndex < progPlanner.points.length;
        pointIndex += 1
    ) {

        const point =
            progPlanner.points[
                pointIndex
            ];

        const u =
            Number(
                point.u
            );

        const v =
            Number(
                point.v
            );


        if (
            !Number.isFinite(
                u
            )
            ||
            !Number.isFinite(
                v
            )
        ) {
            continue;
        }


        const pixelX =
            layout.left
            +
            u
            *
            layout.width;

        const pixelY =
            layout.top
            +
            v
            *
            layout.height;


        const selected =
            progPlanner.selectedId
            ===
            point.id;

        const initial =
            progPlanner.initialPointId
            ===
            point.id;

        const orienting =
            progPlanner.orientationPointId
            ===
            point.id;


        if (
            selected
            ||
            orienting
        ) {

            ctx.beginPath();

            ctx.arc(
                pixelX,
                pixelY,
                6
                *
                screenCompensation,
                0,
                Math.PI
                *
                2
            );

            ctx.lineWidth =
                1.2
                *
                screenCompensation;

            ctx.strokeStyle =
                orienting
                    ?
                    "#ef4444"
                    :
                    "#60a5fa";

            ctx.stroke();
        }


        if (initial) {

            ctx.beginPath();

            ctx.arc(
                pixelX,
                pixelY,
                8
                *
                screenCompensation,
                0,
                Math.PI
                *
                2
            );

            ctx.lineWidth =
                1.2
                *
                screenCompensation;

            ctx.strokeStyle =
                "#fbbf24";

            ctx.stroke();
        }


        ctx.beginPath();

        ctx.arc(
            pixelX,
            pixelY,
            2.8
            *
            screenCompensation,
            0,
            Math.PI
            *
            2
        );

        ctx.fillStyle =
            "#22c55e";

        ctx.fill();


        ctx.lineWidth =
            1
            *
            screenCompensation;

        ctx.strokeStyle =
            "#ffffff";

        ctx.stroke();


        const hasYaw =
            (
                point.yaw
                !==
                null
                &&
                point.yaw
                !==
                undefined
                &&
                Number.isFinite(
                    Number(
                        point.yaw
                    )
                )
            );


        if (hasYaw) {

            const originYaw =
                Number(
                    progPlanner.meta.origin.yaw
                    ||
                    0
                );


            const visualYaw =
                Number(
                    point.yaw
                )
                -
                originYaw;


            const dx =
                Math.cos(
                    visualYaw
                );

            const dy =
                -Math.sin(
                    visualYaw
                );


            const startDistance =
                5
                *
                screenCompensation;

            const arrowDistance =
                15
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


            ctx.beginPath();

            ctx.moveTo(
                tipX,
                tipY
            );

            ctx.lineTo(
                baseX
                -
                dy
                *
                triangleHalf,
                baseY
                +
                dx
                *
                triangleHalf
            );

            ctx.lineTo(
                baseX
                +
                dy
                *
                triangleHalf,
                baseY
                -
                dx
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
                9
                *
                screenCompensation
                +
                "px sans-serif"
            );

        ctx.fillStyle =
            "#ffffff";

        ctx.textBaseline =
            "middle";

        const displayLabel =
            (
                String(
                    pointIndex + 1
                )
                +
                " · "
                +
                point.id
            );


        ctx.fillText(
            displayLabel,
            pixelX
            +
            6
            *
            screenCompensation,
            pixelY
            -
            6
            *
            screenCompensation
        );


        const pointAlias =
            normalizeProgAlias(
                point.alias
            );


        if (pointAlias) {

            ctx.font =
                (
                    8
                    *
                    screenCompensation
                    +
                    "px sans-serif"
                );

            ctx.fillStyle =
                "#bfdbfe";


            ctx.fillText(
                (
                    initial
                        ?
                        "★ "
                        :
                        ""
                )
                +
                pointAlias,
                pixelX
                +
                6
                *
                screenCompensation,
                pixelY
                +
                5
                *
                screenCompensation
            );
        }


        if (initial) {

            ctx.font =
                (
                    9
                    *
                    screenCompensation
                    +
                    "px sans-serif"
                );

            ctx.fillStyle =
                "#fbbf24";

            ctx.fillText(
                "★",
                pixelX
                -
                14
                *
                screenCompensation,
                pixelY
                -
                7
                *
                screenCompensation
            );
        }
    }
}


// =========================================================
// TABLA
// =========================================================

function normalizeProgAlias(
    value
) {

    return String(
        value
        ||
        ""
    ).trim();
}


function validProgAlias(
    value
) {

    if (!value) {
        return true;
    }


    return /^[A-Za-z_][A-Za-z0-9_]*$/.test(
        value
    );
}


function progAliasExists(
    alias,
    ignoredPoint = null
) {

    const normalized =
        normalizeProgAlias(
            alias
        ).toLowerCase();


    if (!normalized) {
        return false;
    }


    return progPlanner.points.some(
        point => {

            if (
                ignoredPoint
                &&
                point === ignoredPoint
            ) {
                return false;
            }


            return (
                normalizeProgAlias(
                    point.alias
                ).toLowerCase()
                ===
                normalized
            );
        }
    );
}


function selectedProgPoint() {

    return (
        progPlanner.points.find(
            point =>
                point.id
                ===
                progPlanner.selectedId
        )
        ||
        null
    );
}


function updateProgInitialSelect() {

    const select =
        $p("progInitialPoint");


    if (!select) {
        return;
    }


    select.replaceChildren();


    const empty =
        document.createElement(
            "option"
        );

    empty.value =
        "";

    empty.textContent =
        progPlanner.points.length
            ?
            "Sin definir"
            :
            "Sin puntos";


    select.appendChild(
        empty
    );


    for (
        const point
        of progPlanner.points
    ) {

        const option =
            document.createElement(
                "option"
            );


        const alias =
            normalizeProgAlias(
                point.alias
            );


        option.value =
            point.id;


        option.textContent =
            (
                point.id
                +
                (
                    alias
                        ?
                        " · "
                        +
                        alias
                        :
                        ""
                )
            );


        select.appendChild(
            option
        );
    }


    select.value =
        progPlanner.initialPointId
        ||
        "";


    select.disabled =
        (
            progPlanner.points.length
            ===
            0
            ||
            progMapView.locked
        );
}


function makeProgRowButton(
    text,
    disabled,
    callback
) {

    const button =
        document.createElement(
            "button"
        );

    button.type =
        "button";

    button.className =
        "prog-route-row-button";

    button.textContent =
        text;

    button.disabled =
        Boolean(
            disabled
        );


    button.addEventListener(
        "click",
        event => {

            event.stopPropagation();

            callback();
        }
    );


    return button;
}


function renderProgTable() {

    const body =
        $p("progRouteTableBody");

    const count =
        $p("progPointCount");


    if (count) {

        count.textContent =
            String(
                progPlanner.points.length
            );
    }


    if (!body) {
        return;
    }


    body.replaceChildren();


    if (
        progPlanner.points.length
        ===
        0
    ) {

        const row =
            document.createElement(
                "tr"
            );

        row.className =
            "prog-empty-row";


        const cell =
            document.createElement(
                "td"
            );

        cell.colSpan =
            7;

        cell.textContent =
            progPlanner.meta
                ?
                "Pulsa Agregar puntos y haz clic en el mapa."
                :
                "Carga un mapa y agrega puntos.";


        row.appendChild(
            cell
        );

        body.appendChild(
            row
        );


        updateProgInitialSelect();

        return;
    }


    progPlanner.points.forEach(
        (point, index) => {

            const row =
                document.createElement(
                    "tr"
                );


            if (
                point.id
                ===
                progPlanner.selectedId
            ) {

                row.classList.add(
                    "prog-selected"
                );
            }


            row.addEventListener(
                "click",
                () => {

                    progPlanner.selectedId =
                        point.id;

                    progPlanner.orientationPointId =
                        null;

                    renderProgPlanner();
                }
            );


            // ---------------------------------------------
            // ORDEN
            // ---------------------------------------------

            const orderCell =
                document.createElement(
                    "td"
                );

            orderCell.textContent =
                String(
                    index + 1
                );

            row.appendChild(
                orderCell
            );


            // ---------------------------------------------
            // ID HEX EDITABLE
            // ---------------------------------------------

            const idCell =
                document.createElement(
                    "td"
                );

            const idInput =
                document.createElement(
                    "input"
                );

            idInput.type =
                "text";

            idInput.className =
                "prog-point-id-input";

            idInput.value =
                point.id;

            idInput.maxLength =
                5;

            idInput.disabled =
                progMapView.locked;


            idInput.addEventListener(
                "click",
                event => {

                    event.stopPropagation();
                }
            );


            idInput.addEventListener(
                "change",
                event => {

                    event.stopPropagation();


                    const oldId =
                        point.id;

                    const proposed =
                        normalizeProgPointId(
                            idInput.value
                        );


                    if (!proposed) {

                        idInput.value =
                            oldId;

                        progLog(
                            "ID inválido. Usa 0x000 hasta 0xFFF."
                        );

                        return;
                    }


                    if (
                        progPointIdExists(
                            proposed,
                            point
                        )
                    ) {

                        idInput.value =
                            oldId;

                        progLog(
                            (
                                proposed
                                +
                                " ya pertenece a otro punto."
                            )
                        );

                        return;
                    }


                    point.id =
                        proposed;


                    if (
                        progPlanner.selectedId
                        ===
                        oldId
                    ) {

                        progPlanner.selectedId =
                            proposed;
                    }


                    if (
                        progPlanner.orientationPointId
                        ===
                        oldId
                    ) {

                        progPlanner.orientationPointId =
                            proposed;
                    }


                    if (
                        progPlanner.initialPointId
                        ===
                        oldId
                    ) {

                        progPlanner.initialPointId =
                            proposed;
                    }


                    progLog(
                        (
                            oldId
                            +
                            " → "
                            +
                            proposed
                        )
                    );


                    renderProgPlanner();
                }
            );


            idCell.appendChild(
                idInput
            );

            row.appendChild(
                idCell
            );


            // ---------------------------------------------
            // ★ + ALIAS
            // ---------------------------------------------

            const aliasCell =
                document.createElement(
                    "td"
                );

            aliasCell.className =
                "prog-alias-cell";


            const initialButton =
                document.createElement(
                    "button"
                );

            initialButton.type =
                "button";

            initialButton.className =
                "prog-inline-initial";

            initialButton.textContent =
                point.id
                ===
                progPlanner.initialPointId
                    ?
                    "★"
                    :
                    "☆";

            initialButton.title =
                point.id
                ===
                progPlanner.initialPointId
                    ?
                    "Punto inicial"
                    :
                    "Marcar como punto inicial";

            initialButton.disabled =
                (
                    progMapView.locked
                    ||
                    point.id
                    ===
                    progPlanner.initialPointId
                );


            initialButton.addEventListener(
                "click",
                event => {

                    event.stopPropagation();


                    progPlanner.selectedId =
                        point.id;

                    progPlanner.initialPointId =
                        point.id;


                    progLog(
                        (
                            point.id
                            +
                            ": punto inicial."
                        )
                    );


                    renderProgPlanner();
                }
            );


            const aliasInput =
                document.createElement(
                    "input"
                );

            aliasInput.type =
                "text";

            aliasInput.className =
                "prog-alias-input";

            aliasInput.value =
                point.alias
                ||
                "";

            aliasInput.placeholder =
                "entrada_lab1";

            aliasInput.disabled =
                progMapView.locked;


            aliasInput.addEventListener(
                "click",
                event => {

                    event.stopPropagation();
                }
            );


            aliasInput.addEventListener(
                "change",
                event => {

                    event.stopPropagation();


                    const previous =
                        point.alias
                        ||
                        "";

                    const proposed =
                        normalizeProgAlias(
                            aliasInput.value
                        );


                    if (
                        !validProgAlias(
                            proposed
                        )
                    ) {

                        aliasInput.value =
                            previous;

                        progLog(
                            "Alias inválido: usa letras, números y _."
                        );

                        return;
                    }


                    if (
                        progAliasExists(
                            proposed,
                            point
                        )
                    ) {

                        aliasInput.value =
                            previous;

                        progLog(
                            "Ese alias ya pertenece a otro punto."
                        );

                        return;
                    }


                    point.alias =
                        proposed;

                    aliasInput.value =
                        proposed;


                    progLog(
                        proposed
                            ?
                            (
                                point.id
                                +
                                " = "
                                +
                                proposed
                            )
                            :
                            (
                                point.id
                                +
                                ": alias eliminado."
                            )
                    );


                    renderProgPlanner();
                }
            );


            aliasCell.appendChild(
                initialButton
            );

            aliasCell.appendChild(
                aliasInput
            );

            row.appendChild(
                aliasCell
            );


            // ---------------------------------------------
            // X / Y / ORIENTACION
            // ---------------------------------------------

            const yawText =
                (
                    point.yaw
                    ===
                    null
                    ||
                    point.yaw
                    ===
                    undefined
                )
                    ?
                    "Auto"
                    :
                    (
                        Math.round(
                            Number(
                                point.yaw
                            )
                            *
                            180
                            /
                            Math.PI
                        )
                        +
                        "°"
                    );


            const values = [
                Number(
                    point.x
                ).toFixed(
                    2
                ),

                Number(
                    point.y
                ).toFixed(
                    2
                ),

                yawText
            ];


            for (
                const value
                of values
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


            // ---------------------------------------------
            // ACCIONES
            // ---------------------------------------------

            const actions =
                document.createElement(
                    "td"
                );

            actions.className =
                "prog-route-actions";


            actions.appendChild(
                makeProgRowButton(
                    "↑",
                    (
                        progMapView.locked
                        ||
                        index === 0
                    ),
                    () => {

                        const previous =
                            progPlanner.points[
                                index - 1
                            ];


                        progPlanner.points[
                            index - 1
                        ] =
                            point;

                        progPlanner.points[
                            index
                        ] =
                            previous;


                        renderProgPlanner();
                    }
                )
            );


            actions.appendChild(
                makeProgRowButton(
                    "↓",
                    (
                        progMapView.locked
                        ||
                        index
                        ===
                        progPlanner.points.length
                        -
                        1
                    ),
                    () => {

                        const next =
                            progPlanner.points[
                                index + 1
                            ];


                        progPlanner.points[
                            index + 1
                        ] =
                            point;

                        progPlanner.points[
                            index
                        ] =
                            next;


                        renderProgPlanner();
                    }
                )
            );


            actions.appendChild(
                makeProgRowButton(
                    "Eliminar",
                    progMapView.locked,
                    () => {

                        progPlanner.points.splice(
                            index,
                            1
                        );


                        if (
                            progPlanner.selectedId
                            ===
                            point.id
                        ) {

                            progPlanner.selectedId =
                                null;
                        }


                        if (
                            progPlanner.orientationPointId
                            ===
                            point.id
                        ) {

                            progPlanner.orientationPointId =
                                null;
                        }


                        if (
                            progPlanner.initialPointId
                            ===
                            point.id
                        ) {

                            progPlanner.initialPointId =
                                null;
                        }


                        renderProgPlanner();
                    }
                )
            );


            row.appendChild(
                actions
            );

            body.appendChild(
                row
            );
        }
    );


    updateProgInitialSelect();
}


// =========================================================
// BOTONES DE PUNTOS
// =========================================================

function updateProgPlannerButtons() {

    const add =
        $p("progAddPoints");

    const clear =
        $p("progClearPoints");

    const orient =
        $p("progOrientPoint");

    const auto =
        $p("progAutoPoint");

    const initial =
        $p("progInitialPointButton");


    const selected =
        selectedProgPoint();


    if (add) {

        add.disabled =
            (
                !progPlanner.meta
                ||
                progMapView.locked
            );

        add.textContent =
            progPlanner.placing
                ?
                "Finalizar puntos"
                :
                "Agregar puntos";

        add.classList.toggle(
            "prog-active-tool",
            progPlanner.placing
        );
    }


    if (clear) {

        clear.disabled =
            (
                progPlanner.points.length
                ===
                0
                ||
                progMapView.locked
            );
    }


    if (orient) {

        orient.disabled =
            (
                !selected
                ||
                progMapView.locked
            );

        orient.textContent =
            (
                selected
                &&
                progPlanner.orientationPointId
                ===
                selected.id
            )
                ?
                "Elige mapa"
                :
                "Orientar";
    }


    if (auto) {

        auto.disabled =
            (
                !selected
                ||
                selected.yaw
                ===
                null
                ||
                selected.yaw
                ===
                undefined
                ||
                progMapView.locked
            );
    }


    if (initial) {

        initial.disabled =
            (
                !selected
                ||
                progMapView.locked
            );
    }
}


function renderProgPlanner() {

    renderProgTable();

    updateProgPlannerButtons();

    renderProgMarkers();
}


function setProgPlacementMode(
    active
) {

    if (
        active
        &&
        (
            progMapView.locked
            ||
            !progPlanner.meta
        )
    ) {
        return;
    }


    progPlanner.placing =
        Boolean(
            active
        );

    progPlanner.orientationPointId =
        null;


    if (active) {

        cancelProgAreaZoom();

        progLog(
            "Agregar puntos activo: clic en el mapa."
        );

    } else {

        progLog(
            (
                progPlanner.points.length
                +
                " punto(s) marcados."
            )
        );
    }


    renderProgPlanner();
}


function beginProgOrientation() {

    const point =
        selectedProgPoint();


    if (
        !point
        ||
        progMapView.locked
    ) {
        return;
    }


    progPlanner.placing =
        false;

    progPlanner.orientationPointId =
        point.id;


    cancelProgAreaZoom();


    progLog(
        (
            point.id
            +
            ": haz clic hacia donde debe mirar."
        )
    );


    renderProgPlanner();
}


function setProgAuto() {

    const point =
        selectedProgPoint();


    if (
        !point
        ||
        progMapView.locked
    ) {
        return;
    }


    point.yaw =
        null;

    progPlanner.orientationPointId =
        null;


    progLog(
        (
            point.id
            +
            ": orientación Auto."
        )
    );


    renderProgPlanner();
}


function setProgInitial() {

    const point =
        selectedProgPoint();


    if (
        !point
        ||
        progMapView.locked
    ) {
        return;
    }


    progPlanner.initialPointId =
        point.id;


    progLog(
        (
            point.id
            +
            ": punto inicial."
        )
    );


    renderProgPlanner();
}


function clearProgPoints() {

    if (
        progMapView.locked
        ||
        progPlanner.points.length
        ===
        0
    ) {
        return;
    }


    if (
        !window.confirm(
            "¿Borrar todos los puntos?"
        )
    ) {
        return;
    }


    progPlanner.points =
        [];

    progPlanner.placing =
        false;

    progPlanner.selectedId =
        null;

    progPlanner.orientationPointId =
        null;

    progPlanner.initialPointId =
        null;


    renderProgPlanner();


    progLog(
        "Puntos borrados."
    );
}


// =========================================================
// CLICK DE MAPA - PORTADO DE PILOTADA
// =========================================================

function handleProgPointClick(
    event
) {

    if (
        event.button
        !==
        0
        ||
        progMapView.locked
        ||
        progMapView.areaSelecting
    ) {
        return;
    }


    const target =
        progScreenToMap(
            event.clientX,
            event.clientY
        );


    if (
        progPlanner.orientationPointId
    ) {

        event.preventDefault();

        event.stopPropagation();

        event.stopImmediatePropagation();


        const point =
            progPlanner.points.find(
                item =>
                    item.id
                    ===
                    progPlanner.orientationPointId
            );


        if (
            !point
            ||
            !target
        ) {

            progLog(
                "Haz clic dentro de la imagen del mapa."
            );

            return;
        }


        const dx =
            Number(
                target.x
            )
            -
            Number(
                point.x
            );

        const dy =
            Number(
                target.y
            )
            -
            Number(
                point.y
            );


        if (
            Math.hypot(
                dx,
                dy
            )
            <
            0.03
        ) {

            progLog(
                "Elige una dirección un poco más alejada."
            );

            return;
        }


        point.yaw =
            Math.atan2(
                dy,
                dx
            );


        const degrees =
            Math.round(
                Number(
                    point.yaw
                )
                *
                180
                /
                Math.PI
            );


        progPlanner.orientationPointId =
            null;


        progLog(
            (
                point.id
                +
                ": referencia guardada "
                +
                degrees
                +
                "°."
            )
        );


        renderProgPlanner();

        return;
    }


    if (!progPlanner.placing) {
        return;
    }


    event.preventDefault();

    event.stopPropagation();

    event.stopImmediatePropagation();


    if (!target) {

        progLog(
            "Haz clic dentro de la imagen del mapa."
        );

        return;
    }


    const newId =
        nextProgPointId();


    if (!newId) {

        progLog(
            "No quedan IDs automáticos entre 0x000 y 0xFFF."
        );

        return;
    }


    const point = {
        id:
            newId,

        alias:
            "",

        x:
            target.x,

        y:
            target.y,

        yaw:
            null,

        u:
            target.u,

        v:
            target.v
    };


    progPlanner.points.push(
        point
    );


    progPlanner.selectedId =
        point.id;


    progLog(
        (
            point.id
            +
            ": punto agregado."
        )
    );


    renderProgPlanner();
}



// =========================================================
// PERSISTENCIA DE MISIONES
// =========================================================

function missionNameError(
    value
) {
    const name =
        String(
            value
            ||
            ""
        ).trim();

    if (!name) {
        return "El nombre no puede estar vacío.";
    }

    if (name.length > 64) {
        return "El nombre no puede superar 64 caracteres.";
    }

    if (
        name === "."
        ||
        name === ".."
        ||
        name.endsWith(".")
    ) {
        return "Nombre de misión inválido.";
    }

    if (
        name.toLowerCase().endsWith(
            ".sfmision"
        )
    ) {
        return "Escribe el nombre sin la extensión .sfmision.";
    }

    if (
        /[<>:"/\\|?*\u0000-\u001F]/.test(
            name
        )
    ) {
        return "El nombre contiene caracteres no permitidos.";
    }

    return null;
}


function buildMissionPayload() {

    const nameInput =
        $p("progMissionName");

    const codeInput =
        $p("progCode");

    const mapSelect =
        $p("progMapSelect");


    const name =
        nameInput
            ?
            nameInput.value.trim()
            :
            "";


    const nameError =
        missionNameError(
            name
        );


    if (nameError) {
        throw new Error(
            nameError
        );
    }


    return {
        format:
            "safevision-mission",

        version:
            1,

        name:
            name,

        map:
            (
                progPlanner.map
                ||
                (
                    mapSelect
                        ?
                        mapSelect.value
                        :
                        ""
                )
                ||
                ""
            ),

        initial_point_id:
            progPlanner.initialPointId,

        next_point_id:
            progPlanner.nextPointId,

        points:
            progPlanner.points.map(
                (point, index) => ({
                    order:
                        index + 1,

                    id:
                        point.id,

                    alias:
                        point.alias
                        ||
                        "",

                    x:
                        Number(
                            point.x
                        ),

                    y:
                        Number(
                            point.y
                        ),

                    yaw:
                        (
                            point.yaw
                            ===
                            undefined
                                ?
                                null
                                :
                                point.yaw
                        ),

                    u:
                        point.u,

                    v:
                        point.v
                })
            ),

        code:
            codeInput
                ?
                codeInput.value
                :
                ""
    };
}


async function missionFetchJson(
    url,
    options = {}
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
            (
                "Error HTTP "
                +
                response.status
            )
        );
    }


    return data;
}


function updateMissionSaveStatus(
    data
) {

    const element =
        $p(
            "progMissionSaveStatus"
        );


    if (!element) {
        return;
    }


    const pcOk =
        Boolean(
            data
            &&
            data.pc
            &&
            data.pc.ok
        );


    const piOk =
        Boolean(
            data
            &&
            data.pi
            &&
            data.pi.ok
        );


    const piState =
        (
            data
            &&
            data.pi
            &&
            data.pi.state
        )
        ||
        "";


    let text =
        pcOk
            ?
            "✓ PC"
            :
            "⚠ PC";


    if (piOk) {

        text +=
            " · ✓ Pi";

    } else if (
        piState
        ===
        "disconnected"
    ) {

        text +=
            " · ⚠ Pi desconectada";

    } else {

        text +=
            " · ⚠ Pi";
    }


    element.textContent =
        text;
}


function setMissionUnsaved() {

    const element =
        $p(
            "progMissionSaveStatus"
        );


    if (element) {
        element.textContent =
            "Sin guardar";
    }
}


async function refreshMissionStorageConfig() {

    const folder =
        $p(
            "progMissionFolder"
        );


    try {

        const data =
            await missionFetchJson(
                "/missions/config"
            );


        if (folder) {
            folder.textContent =
                data.folder;
        }

    } catch (error) {

        if (folder) {
            folder.textContent =
                "No disponible";
        }


        progLog(
            (
                "Biblioteca: "
                +
                error.message
            )
        );
    }
}


async function changeMissionFolder() {

    try {

        const data =
            await missionFetchJson(
                "/missions/select-folder",
                {
                    method:
                        "POST"
                }
            );


        if (
            data.cancelled
            ||
            !data.ok
        ) {
            return;
        }


        const folder =
            $p(
                "progMissionFolder"
            );


        if (folder) {
            folder.textContent =
                data.folder;
        }


        progLog(
            (
                "Carpeta de misiones: "
                +
                data.folder
            )
        );

    } catch (error) {

        progLog(
            (
                "No se pudo cambiar carpeta: "
                +
                error.message
            )
        );
    }
}


async function saveCurrentMission(
    overwrite = true
) {

    let mission;

    try {

        mission =
            buildMissionPayload();

    } catch (error) {

        progLog(
            error.message
        );

        return null;
    }


    try {

        const data =
            await missionFetchJson(
                (
                    "/missions/save?overwrite="
                    +
                    (
                        overwrite
                            ?
                            "1"
                            :
                            "0"
                    )
                ),
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            mission
                        )
                }
            );


        progMissionState.savedName =
            mission.name;


        updateMissionSaveStatus(
            data
        );


        progLog(
            (
                "Misión guardada: "
                +
                mission.name
            )
        );


        return data;

    } catch (error) {

        progLog(
            (
                "No se pudo guardar: "
                +
                error.message
            )
        );

        return null;
    }
}


async function saveMissionAs() {

    const input =
        $p(
            "progMissionName"
        );


    if (!input) {
        return;
    }


    const previous =
        input.value;


    const proposed =
        window.prompt(
            "Nuevo nombre de la misión:",
            previous
        );


    if (proposed === null) {
        return;
    }


    const error =
        missionNameError(
            proposed
        );


    if (error) {

        progLog(
            error
        );

        return;
    }


    input.value =
        proposed.trim();


    const result =
        await saveCurrentMission(
            false
        );


    if (!result) {
        input.value =
            previous;
    }
}


async function duplicateCurrentMission() {

    let mission;

    try {

        mission =
            buildMissionPayload();

    } catch (error) {

        progLog(
            error.message
        );

        return;
    }


    try {

        const data =
            await missionFetchJson(
                "/missions/duplicate",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            mission
                        )
                }
            );


        const input =
            $p(
                "progMissionName"
            );


        if (input) {
            input.value =
                data.mission.name;
        }


        progMissionState.savedName =
            data.mission.name;


        updateMissionSaveStatus(
            data
        );


        progLog(
            (
                "Copia creada: "
                +
                data.mission.name
            )
        );

    } catch (error) {

        progLog(
            (
                "No se pudo duplicar: "
                +
                error.message
            )
        );
    }
}


async function deleteCurrentMission() {

    const input =
        $p(
            "progMissionName"
        );


    if (!input) {
        return;
    }


    const name =
        input.value.trim();


    const error =
        missionNameError(
            name
        );


    if (error) {

        progLog(
            error
        );

        return;
    }


    const target =
        window.prompt(
            "Eliminar de: pc, pi o ambos",
            "ambos"
        );


    if (target === null) {
        return;
    }


    const normalized =
        target
            .trim()
            .toLowerCase();


    if (
        ![
            "pc",
            "pi",
            "ambos"
        ].includes(
            normalized
        )
    ) {

        progLog(
            "Usa pc, pi o ambos."
        );

        return;
    }


    if (
        !window.confirm(
            (
                "¿Eliminar '"
                +
                name
                +
                "' de "
                +
                normalized
                +
                "?"
            )
        )
    ) {
        return;
    }


    try {

        const data =
            await missionFetchJson(
                "/missions/delete",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            name:
                                name,

                            target:
                                normalized
                        })
                }
            );


        const messages = [];


        if (data.pc) {
            messages.push(
                data.pc.message
            );
        }


        if (data.pi) {
            messages.push(
                data.pi.message
            );
        }


        progLog(
            messages.join(
                " "
            )
        );


        if (
            normalized
            ===
            "pc"
            ||
            normalized
            ===
            "ambos"
        ) {

            progMissionState.savedName =
                null;

            setMissionUnsaved();
        }

    } catch (error) {

        progLog(
            (
                "No se pudo eliminar: "
                +
                error.message
            )
        );
    }
}


function missionNextIdFromPoints(
    points
) {

    let maximum =
        -1;


    for (
        const point
        of points
    ) {

        const value =
            parseInt(
                String(
                    point.id
                ).slice(
                    2
                ),
                16
            );


        if (
            Number.isInteger(
                value
            )
            &&
            value > maximum
        ) {

            maximum =
                value;
        }
    }


    return Math.min(
        0x1000,
        maximum + 1
    );
}


function applyMissionData(
    mission
) {

    const name =
        $p(
            "progMissionName"
        );

    const code =
        $p(
            "progCode"
        );

    const mapSelect =
        $p(
            "progMapSelect"
        );


    if (name) {
        name.value =
            mission.name;
    }


    if (code) {
        code.value =
            mission.code
            ||
            "";
    }


    const mapName =
        mission.map
        ||
        "";


    if (
        mapSelect
        &&
        mapName
    ) {

        let found =
            Array.from(
                mapSelect.options
            ).some(
                option =>
                    option.value
                    ===
                    mapName
            );


        if (!found) {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                mapName;

            option.textContent =
                mapName;

            mapSelect.appendChild(
                option
            );
        }


        mapSelect.value =
            mapName;
    }


    progPlanner.points =
        [];

    progPlanner.selectedId =
        null;

    progPlanner.orientationPointId =
        null;

    progPlanner.initialPointId =
        null;


    renderProgPlanner();


    let applied =
        false;


    const applyPlanner =
        () => {

            if (applied) {
                return;
            }


            applied =
                true;


            progPlanner.map =
                mapName
                ||
                null;


            progPlanner.points =
                (
                    mission.points
                    ||
                    []
                )
                .slice()
                .sort(
                    (a, b) =>
                        Number(
                            a.order
                            ||
                            0
                        )
                        -
                        Number(
                            b.order
                            ||
                            0
                        )
                )
                .map(
                    point => ({
                        id:
                            point.id,

                        alias:
                            point.alias
                            ||
                            "",

                        x:
                            Number(
                                point.x
                            ),

                        y:
                            Number(
                                point.y
                            ),

                        yaw:
                            (
                                point.yaw
                                ===
                                undefined
                                    ?
                                    null
                                    :
                                    point.yaw
                            ),

                        u:
                            point.u,

                        v:
                            point.v
                    })
                );


            progPlanner.initialPointId =
                mission.initial_point_id
                ||
                null;


            const storedNext =
                Number(
                    mission.next_point_id
                );


            progPlanner.nextPointId =
                (
                    Number.isInteger(
                        storedNext
                    )
                    &&
                    storedNext >= 0
                    &&
                    storedNext <= 0x1000
                )
                    ?
                    storedNext
                    :
                    missionNextIdFromPoints(
                        progPlanner.points
                    );


            renderProgPlanner();


            progMissionState.savedName =
                mission.name;


            const status =
                $p(
                    "progMissionSaveStatus"
                );


            if (status) {
                status.textContent =
                    "Misión abierta";
            }


            progLog(
                (
                    "Misión abierta: "
                    +
                    mission.name
                )
            );
        };


    if (
        mapName
        &&
        mapSelect
    ) {

        const image =
            $p(
                "progMapImage"
            );


        if (image) {

            image.addEventListener(
                "load",
                () => {

                    window.setTimeout(
                        applyPlanner,
                        0
                    );
                },
                {
                    once:
                        true
                }
            );
        }


        showProgMap();


        window.setTimeout(
            applyPlanner,
            1000
        );

    } else {

        applyPlanner();
    }
}


async function openMissionFromLibrary() {

    try {

        const data =
            await missionFetchJson(
                "/missions"
            );


        const missions =
            data.missions
            ||
            [];


        if (!missions.length) {

            progLog(
                "No hay misiones guardadas en la PC."
            );

            return;
        }


        const menu =
            missions
                .map(
                    (item, index) =>
                        (
                            String(
                                index + 1
                            )
                            +
                            ") "
                            +
                            item.name
                        )
                )
                .join(
                    "\n"
                );


        const selected =
            window.prompt(
                (
                    "Misiones guardadas:\n\n"
                    +
                    menu
                    +
                    "\n\nEscribe el número:"
                )
            );


        if (selected === null) {
            return;
        }


        const index =
            Number(
                selected
            )
            -
            1;


        if (
            !Number.isInteger(
                index
            )
            ||
            index < 0
            ||
            index >= missions.length
        ) {

            progLog(
                "Selección inválida."
            );

            return;
        }


        const loaded =
            await missionFetchJson(
                (
                    "/missions/load?name="
                    +
                    encodeURIComponent(
                        missions[index].name
                    )
                )
            );


        applyMissionData(
            loaded.mission
        );

    } catch (error) {

        progLog(
            (
                "No se pudo abrir: "
                +
                error.message
            )
        );
    }
}


async function importMissionFile(
    file
) {

    if (!file) {
        return;
    }


    const form =
        new FormData();


    form.append(
        "file",
        file
    );


    try {

        const data =
            await missionFetchJson(
                "/missions/import",
                {
                    method:
                        "POST",

                    body:
                        form
                }
            );


        updateMissionSaveStatus(
            data
        );


        applyMissionData(
            data.mission
        );


        progLog(
            (
                "Misión importada: "
                +
                data.mission.name
            )
        );

    } catch (error) {

        progLog(
            (
                "No se pudo importar: "
                +
                error.message
            )
        );
    }
}


async function loadMissionFromQuery() {

    const params =
        new URLSearchParams(
            window.location.search
        );


    const name =
        params.get(
            "mission"
        );


    if (!name) {
        return;
    }


    try {

        const data =
            await missionFetchJson(
                (
                    "/missions/load?name="
                    +
                    encodeURIComponent(
                        name
                    )
                )
            );


        applyMissionData(
            data.mission
        );

    } catch (error) {

        progLog(
            (
                "No se pudo abrir la misión solicitada: "
                +
                error.message
            )
        );
    }
}


// =========================================================
// EDITOR DE CODIGO - PLACEHOLDER
// =========================================================

async function validateProgramDraft() {

    const element =
        $p(
            "progCode"
        );


    const code =
        element
            ?
            element.value
            :
            "";


    if (!code.trim()) {

        progLog(
            "Programa vacío."
        );

        return;
    }


    try {

        const data =
            await missionFetchJson(
                "/programar/validate",
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
                                progPlanner.points.map(
                                    point => ({
                                        id:
                                            point.id,

                                        alias:
                                            point.alias
                                            ||
                                            ""
                                    })
                                )
                        })
                }
            );


        if (!data.ok) {

            const messages =
                (
                    data.errors
                    ||
                    []
                )
                .map(
                    item => {

                        const location =
                            item.line
                                ?
                                (
                                    "Línea "
                                    +
                                    item.line
                                    +
                                    ": "
                                )
                                :
                                "";


                        return (
                            "✗ "
                            +
                            location
                            +
                            item.message
                        );
                    }
                );


            progLog(
                (
                    "Programa inválido.\n"
                    +
                    messages.join(
                        "\n"
                    )
                )
            );

            return;
        }


        const resolved =
            (
                data.commands
                ||
                []
            )
            .filter(
                item =>
                    item.name
                    ===
                    "ir"
            )
            .map(
                item =>
                    (
                        item.target
                        +
                        " → "
                        +
                        item.target_id
                    )
            );


        let message =
            (
                "✓ Programa válido · "
                +
                data.command_count
                +
                (
                    data.command_count
                    ===
                    1
                        ?
                        " instrucción."
                        :
                        " instrucciones."
                )
            );


        if (resolved.length) {

            message +=
                (
                    "\nReferencias: "
                    +
                    resolved.join(
                        ", "
                    )
                );
        }


        progLog(
            message
        );

    } catch (error) {

        progLog(
            (
                "No se pudo validar: "
                +
                error.message
            )
        );
    }
}


function resetProgramDraft() {

    const name =
        $p("progMissionName");

    const code =
        $p("progCode");


    if (name) {
        name.value =
            "Nueva misión";
    }


    if (code) {

        code.value =
`# SafeVision

ir("0x000")
esperar(2)
orientar(0)
`;
    }


    progPlanner.points =
        [];

    progPlanner.selectedId =
        null;

    progPlanner.orientationPointId =
        null;

    progPlanner.initialPointId =
        null;

    progPlanner.nextPointId =
        0;


    progMissionState.savedName =
        null;


    setMissionUnsaved();

    renderProgPlanner();


    progLog(
        "Nueva misión preparada."
    );
}


// =========================================================
// INSTALACION
// =========================================================

window.addEventListener(
    "DOMContentLoaded",
    () => {

        const viewport =
            $p("progMapViewport");

        const scene =
            $p("progMapScene");

        const loadMap =
            $p("progLoadMap");

        const zoomIn =
            $p("progZoomIn");

        const zoomOut =
            $p("progZoomOut");

        const resetMap =
            $p("progResetMap");

        const rotation =
            $p("progRotationSlider");

        const areaZoom =
            $p("progAreaZoom");

        const lock =
            $p("progMapLock");

        const add =
            $p("progAddPoints");

        const clear =
            $p("progClearPoints");

        const orient =
            $p("progOrientPoint");

        const auto =
            $p("progAutoPoint");

        const initial =
            $p("progInitialPointButton");

        const initialSelect =
            $p("progInitialPoint");

        const validate =
            $p("progValidateButton");

        const newButton =
            $p("progNewButton");

        const openButton =
            $p("progOpenButton");

        const saveButton =
            $p("progSaveButton");

        const saveAsButton =
            $p("progSaveAsButton");

        const duplicateButton =
            $p("progDuplicateButton");

        const deleteButton =
            $p("progDeleteButton");

        const importButton =
            $p("progImportButton");

        const importFile =
            $p("progImportFile");

        const exportButton =
            $p("progExportButton");

        const folderButton =
            $p("progFolderButton");


        ensureProgWaypointCanvas();


        if (loadMap) {

            loadMap.addEventListener(
                "click",
                showProgMap
            );
        }


        if (zoomIn) {

            zoomIn.addEventListener(
                "click",
                () => {

                    zoomProgMap(
                        1.25
                    );
                }
            );
        }


        if (zoomOut) {

            zoomOut.addEventListener(
                "click",
                () => {

                    zoomProgMap(
                        0.8
                    );
                }
            );
        }


        if (resetMap) {

            resetMap.addEventListener(
                "click",
                resetProgMapView
            );
        }


        if (rotation) {

            rotation.addEventListener(
                "input",
                () => {

                    setProgRotation(
                        rotation.value
                    );
                }
            );
        }


        if (areaZoom) {

            areaZoom.addEventListener(
                "click",
                toggleProgAreaZoom
            );
        }


        if (lock) {

            lock.addEventListener(
                "click",
                toggleProgMapLock
            );
        }


        if (add) {

            add.addEventListener(
                "click",
                () => {

                    setProgPlacementMode(
                        !progPlanner.placing
                    );
                }
            );
        }


        if (clear) {

            clear.addEventListener(
                "click",
                clearProgPoints
            );
        }


        if (orient) {

            orient.addEventListener(
                "click",
                beginProgOrientation
            );
        }


        if (auto) {

            auto.addEventListener(
                "click",
                setProgAuto
            );
        }


        if (initial) {

            initial.addEventListener(
                "click",
                setProgInitial
            );
        }


        if (initialSelect) {

            initialSelect.addEventListener(
                "change",
                () => {

                    if (progMapView.locked) {
                        return;
                    }


                    progPlanner.initialPointId =
                        initialSelect.value
                        ||
                        null;


                    renderProgPlanner();
                }
            );
        }


        if (validate) {

            validate.addEventListener(
                "click",
                validateProgramDraft
            );
        }


        if (newButton) {

            newButton.addEventListener(
                "click",
                resetProgramDraft
            );
        }


        if (openButton) {

            openButton.addEventListener(
                "click",
                openMissionFromLibrary
            );
        }


        if (saveButton) {

            saveButton.addEventListener(
                "click",
                () => {

                    saveCurrentMission(
                        true
                    );
                }
            );
        }


        if (saveAsButton) {

            saveAsButton.addEventListener(
                "click",
                saveMissionAs
            );
        }


        if (duplicateButton) {

            duplicateButton.addEventListener(
                "click",
                duplicateCurrentMission
            );
        }


        if (deleteButton) {

            deleteButton.addEventListener(
                "click",
                deleteCurrentMission
            );
        }


        if (
            importButton
            &&
            importFile
        ) {

            importButton.addEventListener(
                "click",
                () => {

                    importFile.value =
                        "";

                    importFile.click();
                }
            );


            importFile.addEventListener(
                "change",
                () => {

                    importMissionFile(
                        importFile.files[
                            0
                        ]
                    );
                }
            );
        }


        if (exportButton) {

            exportButton.addEventListener(
                "click",
                () => {

                    window.open(
                        "/misiones/archivos",
                        "_blank"
                    );
                }
            );
        }


        if (folderButton) {

            folderButton.addEventListener(
                "click",
                changeMissionFolder
            );
        }


        refreshMissionStorageConfig();


        window.setTimeout(
            loadMissionFromQuery,
            500
        );


        if (scene) {

            scene.addEventListener(
                "mousedown",
                handleProgPointClick,
                true
            );
        }


        if (viewport) {

            viewport.addEventListener(
                "mousedown",
                event => {

                    if (
                        startProgAreaSelection(
                            event
                        )
                    ) {
                        return;
                    }


                    if (
                        progMapView.locked
                        ||
                        progPlanner.placing
                        ||
                        progPlanner.orientationPointId
                        ||
                        event.button !== 0
                    ) {
                        return;
                    }


                    progMapView.dragging =
                        true;

                    progMapView.dragStartX =
                        event.clientX
                        -
                        progMapView.x;

                    progMapView.dragStartY =
                        event.clientY
                        -
                        progMapView.y;
                }
            );


            viewport.addEventListener(
                "wheel",
                event => {

                    if (
                        progMapView.locked
                        ||
                        progMapView.areaSelecting
                    ) {

                        event.preventDefault();

                        return;
                    }


                    event.preventDefault();


                    zoomProgMap(
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
        }


        window.addEventListener(
            "mousemove",
            event => {

                if (
                    progMapView.selectionDragging
                ) {

                    moveProgAreaSelection(
                        event
                    );

                    return;
                }


                if (
                    !progMapView.dragging
                ) {
                    return;
                }


                progMapView.x =
                    event.clientX
                    -
                    progMapView.dragStartX;

                progMapView.y =
                    event.clientY
                    -
                    progMapView.dragStartY;


                applyProgMapView();
            }
        );


        window.addEventListener(
            "mouseup",
            event => {

                if (
                    progMapView.selectionDragging
                ) {

                    finishProgAreaSelection(
                        event
                    );
                }


                progMapView.dragging =
                    false;
            }
        );


        window.addEventListener(
            "resize",
            renderProgMarkers
        );


        updateProgRotationUI();

        updateProgLockUI();

        renderProgPlanner();

        loadProgMaps();
    }
);
