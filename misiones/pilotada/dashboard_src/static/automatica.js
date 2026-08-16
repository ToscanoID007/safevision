// =========================================================
// SAFEVISION MISION AUTOMATICA - PAGINA INDEPENDIENTE
// =========================================================

(() => {

    const connectionState = {
        connected:
            false
    };


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


    const connectionBadge =
        document.getElementById(
            "autoConnectionBadge"
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
        !connectionBadge
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


    function renderConnectionState(
        connected
    ) {

        connectionState.connected =
            connected;


        if (connected) {

            connectionBadge.textContent =
                "CONECTADO";

            connectionBadge.className =
                "badge badge-on";

        } else {

            connectionBadge.textContent =
                "DESCONECTADO";

            connectionBadge.className =
                "badge badge-off";
        }
    }


    // =====================================================
    // CAMARA + MAPA + RUTA DE MISION
    // =====================================================

    function startAutomaticVideo() {

        const image =
            document.getElementById(
                "videoFeed"
            );

        const placeholder =
            document.getElementById(
                "videoPlaceholder"
            );


        if (
            !image
            ||
            !placeholder
        ) {
            return;
        }


        image.src =
            "/video_feed?t="
            +
            Date.now();

        image.hidden =
            false;

        placeholder.hidden =
            true;
    }


    const autoMapView = {

        scale:
            1,

        x:
            0,

        y:
            0,

        rotation:
            0,

        dragging:
            false,

        startX:
            0,

        startY:
            0,

        locked:
            false,

        areaSelecting:
            false,

        selectionDragging:
            false,

        selectionStartX:
            0,

        selectionStartY:
            0,

        labelsVisible:
            true
    };


    const autoMapData = {

        mission:
            null,

        meta:
            null
    };


    const mapViewport =
        document.getElementById(
            "mapViewport"
        );

    const mapScene =
        document.getElementById(
            "mapScene"
        );

    const mapImage =
        document.getElementById(
            "mapImage"
        );

    const mapPlaceholder =
        document.getElementById(
            "mapPlaceholder"
        );

    const mapName =
        document.getElementById(
            "autoMapName"
        );

    const mapZoomIn =
        document.getElementById(
            "mapZoomIn"
        );

    const mapZoomOut =
        document.getElementById(
            "mapZoomOut"
        );

    const mapReset =
        document.getElementById(
            "mapReset"
        );

    const mapAreaZoom =
        document.getElementById(
            "mapAreaZoom"
        );

    const mapLock =
        document.getElementById(
            "mapLock"
        );

    const mapToggleLabels =
        document.getElementById(
            "mapToggleLabels"
        );

    const mapRotationSlider =
        document.getElementById(
            "mapRotationSlider"
        );

    const mapRotationValue =
        document.getElementById(
            "mapRotationValue"
        );


    let mapSelectionBox =
        null;


    function updateAutomaticLabelsUI() {

        if (!mapToggleLabels) {
            return;
        }


        mapToggleLabels.textContent =
            autoMapView.labelsVisible
                ?
                "Ocultar etiquetas"
                :
                "Mostrar etiquetas";


        mapToggleLabels.classList.toggle(
            "active",
            !autoMapView.labelsVisible
        );
    }


    function updateAutomaticRotationUI() {

        const value =
            Math.round(
                Number(
                    autoMapView.rotation
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
                autoMapView.locked;
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


    function applyAutomaticMapView() {

        if (!mapScene) {
            return;
        }


        mapScene.style.transform =
            (
                "translate("
                +
                autoMapView.x
                +
                "px, "
                +
                autoMapView.y
                +
                "px) "
                +
                "scale("
                +
                autoMapView.scale
                +
                ") "
                +
                "rotate("
                +
                autoMapView.rotation
                +
                "deg)"
            );


        renderAutomaticMissionMarkers();
    }


    function setAutomaticRotation(
        value
    ) {

        if (autoMapView.locked) {
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


        autoMapView.rotation =
            rotation;


        updateAutomaticRotationUI();

        applyAutomaticMapView();
    }


    function focusAutomaticMap() {

        autoMapView.scale =
            2.5;

        autoMapView.x =
            0;

        autoMapView.y =
            0;


        applyAutomaticMapView();
    }


    function resetAutomaticMap() {

        if (autoMapView.locked) {
            return;
        }


        autoMapView.scale =
            1;

        autoMapView.x =
            0;

        autoMapView.y =
            0;

        autoMapView.rotation =
            0;


        updateAutomaticRotationUI();

        applyAutomaticMapView();
    }


    function zoomAutomaticMap(
        factor
    ) {

        if (autoMapView.locked) {
            return;
        }


        autoMapView.scale *=
            factor;


        autoMapView.scale =
            Math.max(
                0.5,
                Math.min(
                    10,
                    autoMapView.scale
                )
            );


        applyAutomaticMapView();
    }


    function getAutomaticImageLayout() {

        if (
            !mapScene
            ||
            !mapImage
            ||
            !mapImage.naturalWidth
            ||
            !mapImage.naturalHeight
        ) {
            return null;
        }


        const sceneWidth =
            mapScene.clientWidth;

        const sceneHeight =
            mapScene.clientHeight;


        if (
            sceneWidth <= 0
            ||
            sceneHeight <= 0
        ) {
            return null;
        }


        const imageRatio =
            mapImage.naturalWidth
            /
            mapImage.naturalHeight;

        const sceneRatio =
            sceneWidth
            /
            sceneHeight;


        let width;
        let height;


        if (
            imageRatio
            >
            sceneRatio
        ) {

            width =
                sceneWidth;

            height =
                width
                /
                imageRatio;

        } else {

            height =
                sceneHeight;

            width =
                height
                *
                imageRatio;
        }


        return {

            left:
                (
                    sceneWidth
                    -
                    width
                )
                /
                2,

            top:
                (
                    sceneHeight
                    -
                    height
                )
                /
                2,

            width:
                width,

            height:
                height
        };
    }


    function automaticPointUV(
        point
    ) {

        const directU =
            Number(
                point.u
            );

        const directV =
            Number(
                point.v
            );


        if (
            Number.isFinite(
                directU
            )
            &&
            Number.isFinite(
                directV
            )
        ) {

            return {
                u:
                    directU,

                v:
                    directV
            };
        }


        const meta =
            autoMapData.meta;


        if (
            !meta
            ||
            !meta.origin
        ) {
            return null;
        }


        const x =
            Number(
                point.x
            );

        const y =
            Number(
                point.y
            );

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


        if (
            !Number.isFinite(x)
            ||
            !Number.isFinite(y)
            ||
            !Number.isFinite(resolution)
            ||
            resolution <= 0
            ||
            !Number.isFinite(width)
            ||
            width <= 0
            ||
            !Number.isFinite(height)
            ||
            height <= 0
            ||
            !Number.isFinite(originX)
            ||
            !Number.isFinite(originY)
        ) {
            return null;
        }


        const dx =
            x
            -
            originX;

        const dy =
            y
            -
            originY;


        const cosYaw =
            Math.cos(
                originYaw
            );

        const sinYaw =
            Math.sin(
                originYaw
            );


        const localX =
            cosYaw
            *
            dx
            +
            sinYaw
            *
            dy;

        const localY =
            -sinYaw
            *
            dx
            +
            cosYaw
            *
            dy;


        const pixelX =
            localX
            /
            resolution;

        const pixelY =
            localY
            /
            resolution;


        return {

            u:
                pixelX
                /
                width,

            v:
                1
                -
                pixelY
                /
                height
        };
    }


    function ensureAutomaticWaypointCanvas() {

        if (!mapScene) {
            return null;
        }


        let canvas =
            document.getElementById(
                "autoWaypointCanvas"
            );


        if (!canvas) {

            canvas =
                document.createElement(
                    "canvas"
                );

            canvas.id =
                "autoWaypointCanvas";


            mapScene.appendChild(
                canvas
            );
        }


        return canvas;
    }


    function renderAutomaticMissionMarkers() {

        const mission =
            autoMapData.mission;

        const canvas =
            ensureAutomaticWaypointCanvas();

        const layout =
            getAutomaticImageLayout();


        if (
            !mission
            ||
            !mapScene
            ||
            !mapImage
            ||
            !canvas
            ||
            !layout
            ||
            mapImage.offsetParent
            ===
            null
        ) {
            return;
        }


        const width =
            mapScene.clientWidth;

        const height =
            mapScene.clientHeight;


        if (
            width <= 0
            ||
            height <= 0
        ) {
            return;
        }


        /*
         * MISMA ESTRATEGIA DE PROGRAMAR:
         * aumentar resolución interna del canvas
         * según zoom + devicePixelRatio.
         */
        const zoomScale =
            Math.max(
                1,
                Number(
                    autoMapView.scale
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


        /*
         * MISMA COMPENSACION VISUAL DE PROGRAMAR.
         * Al hacer zoom, punto/texto/flecha mantienen
         * aproximadamente el mismo tamaño en pantalla.
         */
        const screenCompensation =
            1
            /
            Math.max(
                0.01,
                Number(
                    autoMapView.scale
                    ||
                    1
                )
            );


        const points =
            Array.isArray(
                mission.points
            )
                ?
                mission.points
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
                :
                [];


        const originYaw =
            Number(
                (
                    autoMapData.meta
                    &&
                    autoMapData.meta.origin
                    &&
                    autoMapData.meta.origin.yaw
                )
                ||
                0
            );


        for (
            let pointIndex = 0;
            pointIndex < points.length;
            pointIndex += 1
        ) {

            const point =
                points[
                    pointIndex
                ];


            /*
             * Automática admite misiones antiguas
             * con x/y aunque no tengan u/v.
             *
             * Después de esta conversión,
             * el renderer trabaja exactamente
             * en coordenadas normalizadas como Programar.
             */
            const uv =
                automaticPointUV(
                    point
                );


            if (!uv) {
                continue;
            }


            const u =
                Number(
                    uv.u
                );

            const v =
                Number(
                    uv.v
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


            const initial =
                mission.initial_point_id
                ===
                point.id;


            /*
             * PUNTO INICIAL:
             * mismo aro amarillo de Programar.
             */
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


            /*
             * WAYPOINT:
             * mismo centro verde + borde blanco.
             */
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


            /*
             * ORIENTACION:
             * misma flecha roja de Programar.
             */
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


            /*
             * ETIQUETA MINIMALISTA
             *
             *   • 0x000
             *
             * El punto conserva toda su geometría.
             * Solo mostramos su ID real en negro.
             */
            const label =
                String(
                    point.id
                    ||
                    ""
                );


            if (
                label
                &&
                autoMapView.labelsVisible
            ) {

                ctx.save();


                /*
                 * El canvas completo rota junto al mapa.
                 *
                 * Trasladamos al punto y aplicamos la
                 * rotación inversa únicamente al texto.
                 *
                 * Resultado:
                 *
                 * - la etiqueta sigue físicamente al punto;
                 * - pero 0x000 permanece horizontal.
                 */
                ctx.translate(
                    pixelX,
                    pixelY
                );

                ctx.rotate(
                    (
                        -Number(
                            autoMapView.rotation
                            ||
                            0
                        )
                        *
                        Math.PI
                    )
                    /
                    180
                );


                ctx.font =
                    (
                        "600 "
                        +
                        (
                            10
                            *
                            screenCompensation
                        )
                        +
                        "px sans-serif"
                    );

                ctx.textAlign =
                    "left";

                ctx.textBaseline =
                    "middle";

                ctx.fillStyle =
                    "#111111";


                ctx.fillText(
                    label,
                    7
                    *
                    screenCompensation,
                    0
                );


                ctx.restore();
            }


        }
    }


    async function loadAutomaticMapMeta(
        name
    ) {

        autoMapData.meta =
            null;


        if (!name) {
            return;
        }


        try {

            const meta =
                await requestJson(
                    "/map_meta/"
                    +
                    encodeURIComponent(
                        name
                    )
                );


            if (
                meta
                &&
                typeof meta
                ===
                "object"
            ) {

                autoMapData.meta =
                    meta;
            }

        } catch (error) {

            autoMapData.meta =
                null;
        }


        renderAutomaticMissionMarkers();
    }


    function clearAutomaticMissionMap() {

        autoMapData.mission =
            null;

        autoMapData.meta =
            null;


        if (mapScene) {

            mapScene.hidden =
                true;
        }


        if (mapImage) {

            mapImage.removeAttribute(
                "src"
            );
        }


        if (mapName) {

            mapName.textContent =
                "Sin mapa";
        }


        const canvas =
            document.getElementById(
                "autoWaypointCanvas"
            );


        if (canvas) {

            const ctx =
                canvas.getContext(
                    "2d"
                );

            if (ctx) {

                ctx.clearRect(
                    0,
                    0,
                    canvas.width,
                    canvas.height
                );
            }
        }


        if (mapPlaceholder) {

            mapPlaceholder.textContent =
                "Selecciona una misión para mostrar su mapa.";

            mapPlaceholder.hidden =
                false;
        }
    }


    function showAutomaticMissionMap(
        mission
    ) {

        const name =
            (
                mission
                &&
                mission.map
            )
            ||
            "";


        if (
            !name
            ||
            !mapImage
            ||
            !mapScene
            ||
            !mapPlaceholder
        ) {

            clearAutomaticMissionMap();
            return;
        }


        autoMapData.mission =
            mission;

        autoMapData.meta =
            null;


        if (mapName) {

            mapName.textContent =
                name;
        }


        loadAutomaticMapMeta(
            name
        );


        mapImage.onload =
            () => {

                mapScene.hidden =
                    false;

                mapPlaceholder.hidden =
                    true;


                ensureAutomaticWaypointCanvas();

                focusAutomaticMap();

                renderAutomaticMissionMarkers();
            };


        mapImage.onerror =
            () => {

                mapScene.hidden =
                    true;

                mapPlaceholder.hidden =
                    false;

                mapPlaceholder.textContent =
                    "No se pudo cargar el mapa de la misión.";
            };


        mapImage.src =
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


    function ensureAutomaticSelectionBox() {

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


    function setAutomaticAreaMode(
        active
    ) {

        if (
            autoMapView.locked
            &&
            active
        ) {
            return;
        }


        autoMapView.areaSelecting =
            Boolean(
                active
            );


        if (mapAreaZoom) {

            mapAreaZoom.classList.toggle(
                "active",
                autoMapView.areaSelecting
            );
        }


        if (mapViewport) {

            mapViewport.classList.toggle(
                "map-area-selecting",
                autoMapView.areaSelecting
            );
        }


        if (
            !autoMapView.areaSelecting
            &&
            mapSelectionBox
        ) {

            mapSelectionBox.hidden =
                true;
        }
    }


    function updateAutomaticLockUI() {

        if (mapLock) {

            mapLock.textContent =
                autoMapView.locked
                    ?
                    "Desbloquear"
                    :
                    "Bloquear";

            mapLock.classList.toggle(
                "active",
                autoMapView.locked
            );
        }


        if (mapViewport) {

            mapViewport.classList.toggle(
                "map-locked",
                autoMapView.locked
            );
        }


        updateAutomaticRotationUI();
    }


    function clampAutomaticMap(
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


    function finishAutomaticAreaZoom(
        event
    ) {

        if (
            !autoMapView.selectionDragging
            ||
            !mapViewport
            ||
            !mapSelectionBox
        ) {
            return;
        }


        autoMapView.selectionDragging =
            false;


        const bounds =
            mapViewport.getBoundingClientRect();


        const endX =
            clampAutomaticMap(
                event.clientX
                -
                bounds.left,
                0,
                bounds.width
            );

        const endY =
            clampAutomaticMap(
                event.clientY
                -
                bounds.top,
                0,
                bounds.height
            );


        const left =
            Math.min(
                autoMapView.selectionStartX,
                endX
            );

        const top =
            Math.min(
                autoMapView.selectionStartY,
                endY
            );

        const width =
            Math.abs(
                endX
                -
                autoMapView.selectionStartX
            );

        const height =
            Math.abs(
                endY
                -
                autoMapView.selectionStartY
            );


        mapSelectionBox.hidden =
            true;


        if (
            width < 20
            ||
            height < 20
        ) {

            setAutomaticAreaMode(
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
            autoMapView.scale;

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
            width
            /
            2;

        const selectedCenterY =
            top
            +
            height
            /
            2;

        const viewportCenterX =
            bounds.width
            /
            2;

        const viewportCenterY =
            bounds.height
            /
            2;


        autoMapView.x =
            (
                viewportCenterX
                +
                autoMapView.x
                -
                selectedCenterX
            )
            *
            realFactor;

        autoMapView.y =
            (
                viewportCenterY
                +
                autoMapView.y
                -
                selectedCenterY
            )
            *
            realFactor;

        autoMapView.scale =
            newScale;


        applyAutomaticMapView();

        setAutomaticAreaMode(
            false
        );
    }


    ensureAutomaticSelectionBox();

    ensureAutomaticWaypointCanvas();

    updateAutomaticRotationUI();

    updateAutomaticLabelsUI();

    updateAutomaticLockUI();


    if (mapRotationSlider) {

        mapRotationSlider.addEventListener(
            "input",
            () => {

                setAutomaticRotation(
                    mapRotationSlider.value
                );
            }
        );
    }


    if (mapZoomIn) {

        mapZoomIn.addEventListener(
            "click",
            () =>
                zoomAutomaticMap(
                    1.25
                )
        );
    }


    if (mapZoomOut) {

        mapZoomOut.addEventListener(
            "click",
            () =>
                zoomAutomaticMap(
                    0.8
                )
        );
    }


    if (mapReset) {

        mapReset.addEventListener(
            "click",
            resetAutomaticMap
        );
    }


    if (mapAreaZoom) {

        mapAreaZoom.addEventListener(
            "click",
            () => {

                if (autoMapView.locked) {
                    return;
                }


                setAutomaticAreaMode(
                    !autoMapView.areaSelecting
                );
            }
        );
    }


    if (mapToggleLabels) {

        mapToggleLabels.addEventListener(
            "click",
            () => {

                autoMapView.labelsVisible =
                    !autoMapView.labelsVisible;


                updateAutomaticLabelsUI();

                renderAutomaticMissionMarkers();
            }
        );
    }


    if (mapLock) {

        mapLock.addEventListener(
            "click",
            () => {

                autoMapView.locked =
                    !autoMapView.locked;

                autoMapView.dragging =
                    false;

                autoMapView.selectionDragging =
                    false;


                setAutomaticAreaMode(
                    false
                );

                updateAutomaticLockUI();
            }
        );
    }


    if (mapViewport) {

        mapViewport.addEventListener(
            "wheel",
            event => {

                if (
                    !mapScene
                    ||
                    mapScene.hidden
                ) {
                    return;
                }


                event.preventDefault();


                zoomAutomaticMap(
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
                    !mapScene
                    ||
                    mapScene.hidden
                    ||
                    autoMapView.locked
                ) {
                    return;
                }


                if (
                    autoMapView.areaSelecting
                ) {

                    event.preventDefault();

                    event.stopImmediatePropagation();


                    ensureAutomaticSelectionBox();


                    const bounds =
                        mapViewport.getBoundingClientRect();


                    autoMapView.selectionStartX =
                        clampAutomaticMap(
                            event.clientX
                            -
                            bounds.left,
                            0,
                            bounds.width
                        );

                    autoMapView.selectionStartY =
                        clampAutomaticMap(
                            event.clientY
                            -
                            bounds.top,
                            0,
                            bounds.height
                        );


                    autoMapView.selectionDragging =
                        true;


                    mapSelectionBox.style.left =
                        autoMapView.selectionStartX
                        +
                        "px";

                    mapSelectionBox.style.top =
                        autoMapView.selectionStartY
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


                autoMapView.dragging =
                    true;

                autoMapView.startX =
                    event.clientX
                    -
                    autoMapView.x;

                autoMapView.startY =
                    event.clientY
                    -
                    autoMapView.y;


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
                autoMapView.selectionDragging
                &&
                mapViewport
                &&
                mapSelectionBox
            ) {

                const bounds =
                    mapViewport.getBoundingClientRect();


                const currentX =
                    clampAutomaticMap(
                        event.clientX
                        -
                        bounds.left,
                        0,
                        bounds.width
                    );

                const currentY =
                    clampAutomaticMap(
                        event.clientY
                        -
                        bounds.top,
                        0,
                        bounds.height
                    );


                const left =
                    Math.min(
                        autoMapView.selectionStartX,
                        currentX
                    );

                const top =
                    Math.min(
                        autoMapView.selectionStartY,
                        currentY
                    );

                const width =
                    Math.abs(
                        currentX
                        -
                        autoMapView.selectionStartX
                    );

                const height =
                    Math.abs(
                        currentY
                        -
                        autoMapView.selectionStartY
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


            if (
                !autoMapView.dragging
            ) {
                return;
            }


            autoMapView.x =
                event.clientX
                -
                autoMapView.startX;

            autoMapView.y =
                event.clientY
                -
                autoMapView.startY;


            applyAutomaticMapView();
        }
    );


    window.addEventListener(
        "mouseup",
        event => {

            if (
                autoMapView.selectionDragging
            ) {

                finishAutomaticAreaZoom(
                    event
                );
            }


            autoMapView.dragging =
                false;


            if (mapViewport) {

                mapViewport.classList.remove(
                    "dragging"
                );
            }
        }
    );


    window.addEventListener(
        "resize",
        renderAutomaticMissionMarkers
    );


    async function initializeAutomaticPage() {

        missionSelect.innerHTML =
            "";


        const option =
            document.createElement(
                "option"
            );

        option.value =
            "";

        option.textContent =
            "Conecta el robot para continuar";

        missionSelect.appendChild(
            option
        );


        renderConnectionState(
            false
        );

        updateMissionControls();


        try {

            await requestJson(
                "/robot_status"
            );


            renderConnectionState(
                true
            );


            startAutomaticVideo();


            await loadMissionList();


        } catch (error) {

            renderConnectionState(
                false
            );

            setMissionStatus(
                "Conecta el robot para preparar una misión."
            );

            updateMissionControls();
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

        const connected =
            connectionState.connected;


        const controlsLocked =
            (
                running
                ||
                busy
                ||
                !connected
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
                !connected
                ||
                !running
                ||
                busy
            );


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


        clearAutomaticMissionMap();

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

        if (
            !connectionState.connected
        ) {

            setMissionStatus(
                "Conecta el robot antes de preparar una misión.",
                "error"
            );

            updateMissionControls();

            return;
        }


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


            showAutomaticMissionMap(
                mission
            );


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

        if (
            !connectionState.connected
        ) {

            setMissionStatus(
                "Conecta el robot para consultar las misiones."
            );

            updateMissionControls();

            return;
        }


        const previous =
            missionSelect.value;


        let storedMission =
            "";

        try {

            storedMission =
                sessionStorage.getItem(
                    "safevision.autoMission.selected"
                )
                ||
                "";

        } catch (error) {

            storedMission =
                "";
        }



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


            const preferredMission =
            previous
            ||
            storedMission;


        if (
            preferredMission
            &&
            names.includes(
                preferredMission
            )
        ) {

            missionSelect.value =
                preferredMission;

            await loadMissionDetails(
                preferredMission
            );

        } else {

            missionSelect.value =
                "";


            if (
                storedMission
                &&
                !names.includes(
                    storedMission
                )
            ) {

                try {

                    sessionStorage.removeItem(
                        "safevision.autoMission.selected"
                    );

                } catch (error) {

                    // sessionStorage no disponible.
                }
            }


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


    missionSelect.addEventListener(
        "change",
        () => {

            const selectedMission =
                missionSelect.value;


            try {

                if (selectedMission) {

                    sessionStorage.setItem(
                        "safevision.autoMission.selected",
                        selectedMission
                    );

                } else {

                    sessionStorage.removeItem(
                        "safevision.autoMission.selected"
                    );
                }

            } catch (error) {

                // sessionStorage no disponible.
            }


            loadMissionDetails(
                selectedMission
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


    initializeAutomaticPage();

})();
