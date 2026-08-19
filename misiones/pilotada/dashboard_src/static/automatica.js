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
    // MODELO IA LOCAL · REUTILIZA PILOTADA
    // =====================================================

    const autoModelForm =
        document.getElementById(
            "autoModelForm"
        );

    const autoModelPt =
        document.getElementById(
            "autoModelPt"
        );

    const autoModelJson =
        document.getElementById(
            "autoModelJson"
        );

    const autoModelStatus =
        document.getElementById(
            "autoModelStatus"
        );

    const autoConfidence =
        document.getElementById(
            "autoConfidence"
        );

    const autoConfidenceValue =
        document.getElementById(
            "autoConfidenceValue"
        );

    let autoConfidenceTimer =
        null;


    function setAutoModelStatus(
        message,
        state=""
    ) {
        if (!autoModelStatus) {
            return;
        }

        autoModelStatus.textContent =
            message;

        autoModelStatus.className =
            "auto-model-status";

        if (state) {
            autoModelStatus.classList.add(
                state
            );
        }
    }


    async function uploadAutomaticModel(
        event
    ) {
        event.preventDefault();

        const pt =
            autoModelPt
            &&
            autoModelPt.files[0];

        const json =
            autoModelJson
            &&
            autoModelJson.files[0];

        if (!pt) {
            setAutoModelStatus(
                "Selecciona un archivo .pt.",
                "error"
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

        setAutoModelStatus(
            `Cargando ${pt.name}...`,
            "loading"
        );

        try {
            const response =
                await fetch(
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

            const info =
                data.model
                ||
                {};

            setAutoModelStatus(
                (
                    "Modelo listo: "
                    +
                    (
                        info.model
                        ||
                        pt.name
                    )
                ),
                "ready"
            );

            const confidence =
                Number(
                    info.confidence
                );

            if (
                autoConfidence
                &&
                autoConfidenceValue
                &&
                Number.isFinite(
                    confidence
                )
            ) {
                const percent =
                    Math.round(
                        confidence * 100
                    );

                autoConfidence.value =
                    String(percent);

                autoConfidenceValue.textContent =
                    `${percent}%`;
            }

        } catch (error) {
            setAutoModelStatus(
                (
                    "Error IA: "
                    +
                    error.message
                ),
                "error"
            );
        }
    }


    async function loadAutomaticModelInfo() {
        if (
            !autoConfidence
            ||
            !autoConfidenceValue
        ) {
            return;
        }

        try {
            const response =
                await fetch(
                    "/model_info",
                    {
                        cache: "no-store"
                    }
                );

            if (!response.ok) {
                return;
            }

            const info =
                await response.json();

            const confidence =
                Number(
                    info.confidence
                );

            if (Number.isFinite(confidence)) {
                const percent =
                    Math.round(
                        confidence * 100
                    );

                autoConfidence.value =
                    String(percent);

                autoConfidenceValue.textContent =
                    `${percent}%`;
            }

            if (
                info.loaded
                &&
                info.model
            ) {
                setAutoModelStatus(
                    (
                        "Motor IA listo: "
                        +
                        info.model
                    ),
                    "ready"
                );
            }

        } catch (_) {
            // La misión sigue funcionando aunque IA no esté cargada.
        }
    }


    function scheduleAutomaticConfidence() {
        if (
            !autoConfidence
            ||
            !autoConfidenceValue
        ) {
            return;
        }

        const value =
            Number(
                autoConfidence.value
            );

        autoConfidenceValue.textContent =
            `${value}%`;

        if (autoConfidenceTimer) {
            clearTimeout(
                autoConfidenceTimer
            );
        }

        autoConfidenceTimer =
            window.setTimeout(
                async () => {
                    try {
                        const response =
                            await fetch(
                                "/confidence",
                                {
                                    method: "POST",

                                    headers: {
                                        "Content-Type":
                                            "application/json"
                                    },

                                    body:
                                        JSON.stringify({
                                            confidence:
                                                value / 100
                                        })
                                }
                            );

                        const data =
                            await response.json();

                        if (!response.ok) {
                            throw new Error(
                                data.message
                                ||
                                "Confianza inválida."
                            );
                        }

                    } catch (error) {
                        setAutoModelStatus(
                            (
                                "Error confianza: "
                                +
                                error.message
                            ),
                            "error"
                        );
                    }
                },
                180
            );
    }


    if (autoModelForm) {
        autoModelForm.addEventListener(
            "submit",
            uploadAutomaticModel
        );
    }

    if (autoConfidence) {
        autoConfidence.addEventListener(
            "input",
            scheduleAutomaticConfidence
        );
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

        renderAutomaticExecution();
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


    // =====================================================
    // CAPA DE EJECUCION REAL
    // Misma representacion visual del simulador.
    // =====================================================

    const autoExecution = {

        pose:
            null,

        timer:
            null,

        busy:
            false,

        token:
            0,

        /*
         * Recorrido REAL de la misión.
         *
         * No se llena mientras el robot está simplemente
         * localizado: solamente durante mission.running.
         */
        path:
            [],

        recording:
            false,

        /*
         * Ignora ruido pequeño de AMCL y evita guardar
         * cinco muestras iguales por segundo.
         */
        sampleDistanceM:
            0.06,

        /*
         * Flechas direccionales aproximadamente
         * cada 25 cm de recorrido.
         */
        arrowSpacingM:
            0.25,

        /*
         * 5000 muestras x 6 cm ~= 300 m.
         */
        maxPathPoints:
            5000
    };


    function ensureAutomaticExecutionCanvas() {

        if (!mapScene) {
            return null;
        }


        let canvas =
            document.getElementById(
                "autoExecutionCanvas"
            );


        if (!canvas) {

            canvas =
                document.createElement(
                    "canvas"
                );

            canvas.id =
                "autoExecutionCanvas";

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


            mapScene.appendChild(
                canvas
            );
        }


        return canvas;
    }


    // =====================================================
    // TRAYECTORIA REAL
    // =====================================================

    function clearAutomaticExecutionPath() {

        autoExecution.path =
            [];


        renderAutomaticExecution();
    }


    function appendAutomaticExecutionPose(
        pose
    ) {

        if (
            !autoExecution.recording
            ||
            !pose
        ) {
            return;
        }


        const x =
            Number(
                pose.x
            );

        const y =
            Number(
                pose.y
            );

        const u =
            Number(
                pose.u
            );

        const v =
            Number(
                pose.v
            );


        if (
            !Number.isFinite(x)
            ||
            !Number.isFinite(y)
            ||
            !Number.isFinite(u)
            ||
            !Number.isFinite(v)
        ) {
            return;
        }


        const last =
            autoExecution.path.length
                ?
                autoExecution.path[
                    autoExecution.path.length
                    -
                    1
                ]
                :
                null;


        /*
         * Solo guardar una nueva muestra si realmente
         * avanzó aproximadamente 6 cm.
         */
        if (last) {

            const distance =
                Math.hypot(
                    x
                    -
                    last.x,

                    y
                    -
                    last.y
                );


            if (
                distance
                <
                autoExecution.sampleDistanceM
            ) {
                return;
            }
        }


        autoExecution.path.push({

            x:
                x,

            y:
                y,

            u:
                u,

            v:
                v
        });


        const overflow =
            autoExecution.path.length
            -
            autoExecution.maxPathPoints;


        if (overflow > 0) {

            autoExecution.path.splice(
                0,
                overflow
            );
        }
    }


    function setAutomaticExecutionRunning(
        running
    ) {

        const next =
            Boolean(
                running
            );


        if (
            next
            ===
            autoExecution.recording
        ) {
            return;
        }


        if (next) {

            /*
             * Cada ejecución comienza con una trayectoria
             * limpia. Una misión anterior no se mezcla.
             */
            autoExecution.path =
                [];

            autoExecution.recording =
                true;


            /*
             * La pose actual será el primer punto.
             */
            if (autoExecution.pose) {

                appendAutomaticExecutionPose(
                    autoExecution.pose
                );
            }

        } else {

            /*
             * Al finalizar/cancelar dejamos la trayectoria
             * dibujada para poder revisarla.
             */
            autoExecution.recording =
                false;
        }


        renderAutomaticExecution();
    }


    // =====================================================
    // ROSMASTER X3 · HUELLA REAL
    //
    // Recurso reciclado directamente de Misión Pilotada.
    // =====================================================

    const ROSMASTER_X3_LENGTH_M =
        0.24;

    const ROSMASTER_X3_WIDTH_M =
        0.20;


    function hideAutomaticRobotMarker() {

        const marker =
            document.getElementById(
                "robotMarker"
            );


        if (marker) {

            marker.hidden =
                true;
        }
    }


    function renderAutomaticRobotMarker() {

        const marker =
            document.getElementById(
                "robotMarker"
            );

        const pose =
            autoExecution.pose;

        const meta =
            autoMapData.meta;


        if (
            !marker
            ||
            !pose
            ||
            !meta
        ) {

            hideAutomaticRobotMarker();

            return;
        }


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


        const u =
            Number(
                pose.u
            );

        const v =
            Number(
                pose.v
            );

        const yawRel =
            Number(
                pose.visualYaw
            );


        if (
            !Number.isFinite(
                resolution
            )
            ||
            resolution <= 0
            ||
            !Number.isFinite(
                width
            )
            ||
            width <= 0
            ||
            !Number.isFinite(
                height
            )
            ||
            height <= 0
            ||
            !Number.isFinite(
                u
            )
            ||
            !Number.isFinite(
                v
            )
            ||
            !Number.isFinite(
                yawRel
            )
        ) {

            hideAutomaticRobotMarker();

            return;
        }


        if (
            u < 0
            ||
            u > 1
            ||
            v < 0
            ||
            v > 1
        ) {

            hideAutomaticRobotMarker();

            return;
        }


        /*
         * Igual que Pilotada:
         * posición normalizada dentro del mapa.
         */
        const leftPct =
            u
            *
            100;

        const topPct =
            v
            *
            100;


        /*
         * Dimensiones físicas completas del mapa.
         */
        const mapWidthMeters =
            width
            *
            resolution;

        const mapHeightMeters =
            height
            *
            resolution;


        /*
         * Huella física ROSMASTER X3:
         *
         * longitud = 0.24 m
         * ancho    = 0.20 m
         */
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


        /*
         * MISMA ORIENTACIÓN DE PILOTADA.
         *
         * Frente físico = +X.
         * Y de imagen crece hacia abajo.
         */
        const yawDeg =
            yawRel
            *
            180
            /
            Math.PI;


        marker.style.transform =
            (
                "translate(-50%, -50%) "
                +
                `rotate(${-yawDeg}deg)`
            );


        const x =
            Number(
                pose.x
            );

        const y =
            Number(
                pose.y
            );

        const rawYaw =
            Number(
                pose.yaw
            );


        marker.title =
            (
                "Robot"
                +
                (
                    Number.isFinite(x)
                        ?
                        ` | X ${x.toFixed(2)} m`
                        :
                        ""
                )
                +
                (
                    Number.isFinite(y)
                        ?
                        ` | Y ${y.toFixed(2)} m`
                        :
                        ""
                )
                +
                (
                    Number.isFinite(rawYaw)
                        ?
                        (
                            " | "
                            +
                            (
                                rawYaw
                                *
                                180
                                /
                                Math.PI
                            ).toFixed(1)
                            +
                            "°"
                        )
                        :
                        ""
                )
            );


        marker.hidden =
            false;
    }


    function renderAutomaticExecution() {

        const canvas =
            ensureAutomaticExecutionCanvas();

        const layout =
            getAutomaticImageLayout();


        if (
            !canvas
            ||
            !mapScene
        ) {

            renderAutomaticRobotMarker();

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

            renderAutomaticRobotMarker();

            return;
        }


        /*
         * Misma estrategia de compensación visual que
         * usamos en las demás capas del mapa.
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

            renderAutomaticRobotMarker();

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


        const path =
            autoExecution.path;


        if (
            layout
            &&
            path.length >= 2
        ) {

            const compensation =
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


            function toScreen(
                point
            ) {

                return {

                    x:
                        layout.left
                        +
                        Number(
                            point.u
                        )
                        *
                        layout.width,

                    y:
                        layout.top
                        +
                        Number(
                            point.v
                        )
                        *
                        layout.height
                };
            }


            // =============================================
            // LÍNEA AZUL PUNTEADA
            // Recurso visual reciclado de Simulación.
            // =============================================

            ctx.save();

            ctx.beginPath();


            const first =
                toScreen(
                    path[0]
                );


            ctx.moveTo(
                first.x,
                first.y
            );


            for (
                let index = 1;
                index < path.length;
                index += 1
            ) {

                const current =
                    toScreen(
                        path[index]
                    );


                ctx.lineTo(
                    current.x,
                    current.y
                );
            }


            ctx.strokeStyle =
                "#60a5fa";

            ctx.lineWidth =
                2
                *
                compensation;

            ctx.lineCap =
                "round";

            ctx.lineJoin =
                "round";

            ctx.setLineDash([
                6
                *
                compensation,

                4
                *
                compensation
            ]);


            ctx.stroke();

            ctx.setLineDash([]);

            ctx.restore();


            // =============================================
            // FLECHAS DE SENTIDO
            //
            // No usamos cientos de DOM nodes.
            // Son triángulos pequeños en el mismo canvas.
            // =============================================

            let traveled =
                0;

            let nextArrow =
                autoExecution.arrowSpacingM;


            for (
                let index = 1;
                index < path.length;
                index += 1
            ) {

                const previousPose =
                    path[
                        index
                        -
                        1
                    ];

                const currentPose =
                    path[index];


                const segmentMeters =
                    Math.hypot(
                        currentPose.x
                        -
                        previousPose.x,

                        currentPose.y
                        -
                        previousPose.y
                    );


                traveled +=
                    segmentMeters;


                if (
                    traveled
                    <
                    nextArrow
                ) {
                    continue;
                }


                const previous =
                    toScreen(
                        previousPose
                    );

                const current =
                    toScreen(
                        currentPose
                    );


                const angle =
                    Math.atan2(
                        current.y
                        -
                        previous.y,

                        current.x
                        -
                        previous.x
                    );


                const size =
                    4.5
                    *
                    compensation;


                ctx.save();

                ctx.translate(
                    current.x,
                    current.y
                );

                ctx.rotate(
                    angle
                );


                ctx.beginPath();

                ctx.moveTo(
                    size,
                    0
                );

                ctx.lineTo(
                    -size
                    *
                    0.8,
                    -size
                    *
                    0.65
                );

                ctx.lineTo(
                    -size
                    *
                    0.8,
                    size
                    *
                    0.65
                );

                ctx.closePath();


                ctx.fillStyle =
                    "#60a5fa";

                ctx.fill();


                ctx.lineWidth =
                    0.8
                    *
                    compensation;

                ctx.strokeStyle =
                    "#ffffff";

                ctx.stroke();


                ctx.restore();


                nextArrow +=
                    autoExecution.arrowSpacingM;
            }
        }


        /*
         * El footprint no pertenece al canvas.
         * Sigue usando #robotMarker z=30.
         */
        renderAutomaticRobotMarker();
    }


    function stopAutomaticPoseTracking() {

        autoExecution.token +=
            1;


        if (
            autoExecution.timer
            !==
            null
        ) {

            clearInterval(
                autoExecution.timer
            );

            autoExecution.timer =
                null;
        }


        autoExecution.busy =
            false;

        autoExecution.pose =
            null;


        renderAutomaticExecution();
    }


    async function updateAutomaticRealPose(
        token
    ) {

        if (
            token
            !==
            autoExecution.token
            ||
            autoExecution.busy
            ||
            !autoMapData.meta
        ) {
            return;
        }


        autoExecution.busy =
            true;


        try {

            const response =
                await fetch(
                    "/map_pose",
                    {
                        cache:
                            "no-store"
                    }
                );


            let pose = {};


            try {

                pose =
                    await response.json();

            } catch (error) {

                pose = {};
            }


            /*
             * Evita que una respuesta antigua de un
             * mapa anterior vuelva a pintar el robot.
             */
            if (
                token
                !==
                autoExecution.token
            ) {
                return;
            }


            if (
                !response.ok
                ||
                !pose.ok
                ||
                !pose.localized
            ) {

                autoExecution.pose =
                    null;

                renderAutomaticExecution();

                return;
            }


            const x =
                Number(
                    pose.x
                );

            const y =
                Number(
                    pose.y
                );

            const yaw =
                Number(
                    pose.yaw
                );


            if (
                !Number.isFinite(x)
                ||
                !Number.isFinite(y)
                ||
                !Number.isFinite(yaw)
            ) {

                autoExecution.pose =
                    null;

                renderAutomaticExecution();

                return;
            }


            /*
             * Reutilizamos exactamente la conversion
             * x/y -> u/v que ya usa Automatica para
             * colocar los waypoints.
             */
            const uv =
                automaticPointUV({
                    x:
                        x,

                    y:
                        y
                });


            if (
                !uv
                ||
                !Number.isFinite(
                    Number(
                        uv.u
                    )
                )
                ||
                !Number.isFinite(
                    Number(
                        uv.v
                    )
                )
            ) {

                autoExecution.pose =
                    null;

                renderAutomaticExecution();

                return;
            }


            const u =
                Number(
                    uv.u
                );

            const v =
                Number(
                    uv.v
                );


            /*
             * Pose fuera de los limites del mapa:
             * no dibujar marcador.
             */
            if (
                u < 0
                ||
                u > 1
                ||
                v < 0
                ||
                v > 1
            ) {

                autoExecution.pose =
                    null;

                renderAutomaticExecution();

                return;
            }


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


            autoExecution.pose = {

                x:
                    x,

                y:
                    y,

                yaw:
                    yaw,

                u:
                    u,

                v:
                    v,

                /*
                 * Igual que los yaw de los waypoints:
                 * orientación relativa al mapa.
                 *
                 * NO hay offsets +pi, 90 o 180 grados.
                 */
                visualYaw:
                    yaw
                    -
                    originYaw
            };


            appendAutomaticExecutionPose(
                autoExecution.pose
            );


            renderAutomaticExecution();


        } catch (error) {

            if (
                token
                ===
                autoExecution.token
            ) {

                autoExecution.pose =
                    null;

                renderAutomaticExecution();
            }


        } finally {

            if (
                token
                ===
                autoExecution.token
            ) {

                autoExecution.busy =
                    false;
            }
        }
    }


    function startAutomaticPoseTracking() {

        stopAutomaticPoseTracking();


        /*
         * stopAutomaticPoseTracking incrementa el token.
         * Generamos uno nuevo para esta sesion.
         */
        autoExecution.token +=
            1;


        const token =
            autoExecution.token;


        updateAutomaticRealPose(
            token
        );


        /*
         * 5 Hz:
         * suficientemente fluido para visualización y
         * muy inferior al ritmo del sistema ROS.
         */
        autoExecution.timer =
            setInterval(
                () => {

                    updateAutomaticRealPose(
                        token
                    );
                },
                200
            );
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


                startAutomaticPoseTracking();
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


        stopAutomaticPoseTracking();


        autoExecution.recording =
            false;

        clearAutomaticExecutionPath();


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


                ensureAutomaticExecutionCanvas();

                focusAutomaticMap();

                renderAutomaticMissionMarkers();


                renderAutomaticExecution();
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


    const mapClearPathButton =
        document.getElementById(
            "mapClearPath"
        );


    if (mapClearPathButton) {

        mapClearPathButton.addEventListener(
            "click",
            () => {

                clearAutomaticExecutionPath();
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


    window.addEventListener(
        "resize",
        renderAutomaticExecution
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


        /*
         * running=true también incluye el traslado previo
         * hasta la estrella.
         *
         * Ese traslado NO pertenece al código programado.
         */
        setAutomaticExecutionRunning(
            (
                autoMissionState.running
                &&
                state
                !==
                "positioning_initial"
            )
        );


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




    // =====================================================
    // SAFEVISION AUTOMATICA · CALIBRACIONES PILOTADA
    // =====================================================

    const AUTO_CALIBRATION_ROBOT_LENGTH_M = 0.24;
    const AUTO_CALIBRATION_ROBOT_WIDTH_M = 0.20;

    const automaticCalibration = {
        active: false,
        firstPoint: null,
        applying: false
    };

    const automaticCalibrationRaster = {
        rasterMapName: null,
        rasterWidth: 0,
        rasterHeight: 0,
        raster: null
    };

    const calibrationPoseButton =
        document.getElementById("autoCalibrationPose");

    const calibrationMeasuresButton =
        document.getElementById("autoCalibrationMeasures");

    const calibrationStatus =
        document.getElementById("autoCalibrationStatus");

    const calibrationPoint =
        document.getElementById("autoCalibrationPoint");

    function automaticCalibrationMapName() {
        return (
            (autoMapData.mission && autoMapData.mission.map)
            ||
            ""
        );
    }

    function setAutomaticCalibrationStatus(message, state = "") {
        if (!calibrationStatus) {
            return;
        }

        calibrationStatus.textContent = message || "";
        calibrationStatus.dataset.state = state || "";
    }

    function automaticCalibrationReady() {
        return Boolean(
            connectionState.connected
            &&
            autoMissionState.loaded
            &&
            autoMapData.mission
            &&
            autoMapData.meta
            &&
            mapImage
            &&
            mapImage.complete
            &&
            mapImage.naturalWidth
            &&
            mapImage.naturalHeight
            &&
            !autoMissionState.busy
            &&
            !autoMissionState.running
            &&
            !automaticCalibration.applying
        );
    }

    function updateAutomaticCalibrationControls() {
        const ready = automaticCalibrationReady();

        if (calibrationPoseButton) {
            calibrationPoseButton.disabled = !ready;
        }

        if (calibrationMeasuresButton) {
            calibrationMeasuresButton.disabled = !ready;
        }
    }

    function cancelAutomaticCalibration(keepStatus = false) {
        automaticCalibration.active = false;
        automaticCalibration.firstPoint = null;

        if (calibrationPoseButton) {
            calibrationPoseButton.textContent = "Calibrar pose";
        }

        if (mapScene) {
            mapScene.classList.remove("auto-map-calibrating");
        }

        if (calibrationPoint) {
            calibrationPoint.hidden = true;
        }

        if (!keepStatus) {
            setAutomaticCalibrationStatus("");
        }

        updateAutomaticCalibrationControls();
    }

    function automaticViewportToScene(clientX, clientY) {
        if (!mapViewport || !mapScene) {
            return null;
        }

        const viewportRect = mapViewport.getBoundingClientRect();
        const parentX = clientX - viewportRect.left;
        const parentY = clientY - viewportRect.top;
        const style = window.getComputedStyle(mapScene);

        let matrix;
        try {
            matrix = (
                style.transform && style.transform !== "none"
            )
                ? new DOMMatrix(style.transform)
                : new DOMMatrix();
        } catch (error) {
            matrix = new DOMMatrix();
        }

        let originX = mapScene.clientWidth / 2;
        let originY = mapScene.clientHeight / 2;
        const originParts = String(style.transformOrigin || "").split(/\s+/);

        if (originParts.length >= 2) {
            const ox = Number.parseFloat(originParts[0]);
            const oy = Number.parseFloat(originParts[1]);
            if (Number.isFinite(ox)) originX = ox;
            if (Number.isFinite(oy)) originY = oy;
        }

        const offsetX = Number(mapScene.offsetLeft || 0);
        const offsetY = Number(mapScene.offsetTop || 0);

        try {
            const inverse = matrix.inverse();
            const point = new DOMPoint(
                parentX - offsetX - originX,
                parentY - offsetY - originY
            ).matrixTransform(inverse);

            return {
                x: point.x + originX,
                y: point.y + originY
            };
        } catch (error) {
            return null;
        }
    }

    function automaticScreenToMap(clientX, clientY) {
        if (!autoMapData.meta || !mapImage) {
            return null;
        }

        const scenePoint = automaticViewportToScene(clientX, clientY);
        const layout = getAutomaticImageLayout();

        if (!scenePoint || !layout || !layout.width || !layout.height) {
            return null;
        }

        const u = (scenePoint.x - layout.left) / layout.width;
        const v = (scenePoint.y - layout.top) / layout.height;

        if (u < 0 || u > 1 || v < 0 || v > 1) {
            return null;
        }

        const meta = autoMapData.meta;
        const width = Number(meta.width);
        const height = Number(meta.height);
        const resolution = Number(meta.resolution);
        const originX = Number(meta.origin.x);
        const originY = Number(meta.origin.y);
        const originYaw = Number(meta.origin.yaw || 0);

        if (
            !Number.isFinite(width)
            || !Number.isFinite(height)
            || !Number.isFinite(resolution)
            || !Number.isFinite(originX)
            || !Number.isFinite(originY)
        ) {
            return null;
        }

        const pixelX = u * width;
        const pixelY = v * height;
        const localX = pixelX * resolution;
        const localY = (height - pixelY) * resolution;
        const cosO = Math.cos(originYaw);
        const sinO = Math.sin(originYaw);

        return {
            x: originX + cosO * localX - sinO * localY,
            y: originY + sinO * localX + cosO * localY,
            u,
            v,
            sceneX: scenePoint.x,
            sceneY: scenePoint.y
        };
    }

    function showAutomaticCalibrationPoint(point) {
        if (!calibrationPoint || !point) {
            return;
        }

        calibrationPoint.style.left = point.sceneX + "px";
        calibrationPoint.style.top = point.sceneY + "px";
        calibrationPoint.hidden = false;
    }

    async function applyAutomaticInitialPose(x, y, yaw, successMessage) {
        automaticCalibration.applying = true;
        updateAutomaticCalibrationControls();
        setAutomaticCalibrationStatus("Aplicando pose a AMCL...", "active");

        try {
            const response = await fetch(
                "/initialpose",
                {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({x, y, yaw})
                }
            );

            let data = {};
            try {
                data = await response.json();
            } catch (error) {
                data = {};
            }

            if (!response.ok || !data.ok) {
                throw new Error(
                    data.message || data.error || "No se pudo aplicar la pose."
                );
            }

            setAutomaticCalibrationStatus(successMessage, "success");
            cancelAutomaticCalibration(true);

            window.setTimeout(
                () => updateAutomaticRealPose(autoExecution.token),
                700
            );

            return true;
        } catch (error) {
            setAutomaticCalibrationStatus(
                "Error: " + error.message,
                "error"
            );
            return false;
        } finally {
            automaticCalibration.applying = false;
            updateAutomaticCalibrationControls();
        }
    }

    function startAutomaticPoseCalibration() {
        if (!automaticCalibrationReady()) {
            setAutomaticCalibrationStatus(
                "Selecciona una misión y espera a que cargue su mapa.",
                "error"
            );
            return;
        }

        if (automaticCalibration.active) {
            cancelAutomaticCalibration();
            return;
        }

        automaticCalibration.active = true;
        automaticCalibration.firstPoint = null;

        if (calibrationPoseButton) {
            calibrationPoseButton.textContent = "Cancelar calibración";
        }

        if (mapScene) {
            mapScene.classList.add("auto-map-calibrating");
        }

        if (calibrationPoint) {
            calibrationPoint.hidden = true;
        }

        setAutomaticCalibrationStatus(
            "1/2: clic donde está el CENTRO del robot.",
            "active"
        );
    }

    async function handleAutomaticCalibrationClick(event) {
        if (!automaticCalibration.active || event.button !== 0) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        const point = automaticScreenToMap(event.clientX, event.clientY);

        if (!point) {
            setAutomaticCalibrationStatus(
                "Haz clic dentro de la imagen del mapa.",
                "error"
            );
            return;
        }

        if (!automaticCalibration.firstPoint) {
            automaticCalibration.firstPoint = point;
            showAutomaticCalibrationPoint(point);
            setAutomaticCalibrationStatus(
                "2/2: clic hacia donde apunta el FRENTE del robot.",
                "active"
            );
            return;
        }

        const dx = point.x - automaticCalibration.firstPoint.x;
        const dy = point.y - automaticCalibration.firstPoint.y;
        const distance = Math.hypot(dx, dy);

        if (distance < 0.05) {
            setAutomaticCalibrationStatus(
                "El segundo clic debe indicar una dirección.",
                "error"
            );
            return;
        }

        const x = automaticCalibration.firstPoint.x;
        const y = automaticCalibration.firstPoint.y;
        const yaw = Math.atan2(dy, dx);
        const deg = yaw * 180 / Math.PI;

        await applyAutomaticInitialPose(
            x,
            y,
            yaw,
            `Pose aplicada: ${x.toFixed(2)}, ${y.toFixed(2)}, ${deg.toFixed(1)}°`
        );
    }

function automaticPhysicalMeasurePrompt(
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

function automaticWorldPoseToAlignment(
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

function evaluateAutomaticPhysicalPose(
    x,
    y,
    yaw,
    measurements,
    raster,
    meta
) {

    const p =
        automaticWorldPoseToAlignment(
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
                AUTO_CALIBRATION_ROBOT_LENGTH_M / 2
        },

        I: {
            angle:
                p.yawRel
                +
                Math.PI / 2,
            offset:
                AUTO_CALIBRATION_ROBOT_WIDTH_M / 2
        },

        D: {
            angle:
                p.yawRel
                -
                Math.PI / 2,
            offset:
                AUTO_CALIBRATION_ROBOT_WIDTH_M / 2
        },

        A: {
            angle:
                p.yawRel
                +
                Math.PI,
            offset:
                AUTO_CALIBRATION_ROBOT_LENGTH_M / 2
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
            measureAutomaticAlignmentClearance(
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

function searchAutomaticPhysicalPose(
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
            evaluateAutomaticPhysicalPose(
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

function getAutomaticCalibrationRaster(
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
        automaticCalibrationRaster.raster
        &&
        automaticCalibrationRaster.rasterMapName
            === automaticCalibrationMapName()
        &&
        automaticCalibrationRaster.rasterWidth
            === width
        &&
        automaticCalibrationRaster.rasterHeight
            === height
    ) {
        return automaticCalibrationRaster.raster;
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


        automaticCalibrationRaster.rasterMapName =
            automaticCalibrationMapName();

        automaticCalibrationRaster.rasterWidth =
            width;

        automaticCalibrationRaster.rasterHeight =
            height;

        automaticCalibrationRaster.raster =
            raster;


        return raster;


    } catch (_) {

        return null;
    }
}

function classifyAutomaticAlignmentPixel(
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

function measureAutomaticAlignmentClearance(
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
            classifyAutomaticAlignmentPixel(
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

    async function runAutomaticPhysicalCalibration() {
        try {
            if (!automaticCalibrationReady()) {
                throw new Error(
                    "Selecciona una misión y espera a que cargue su mapa."
                );
            }

            if (!autoExecution.pose) {
                throw new Error(
                    "Espera a que aparezca la pose actual del robot en el mapa."
                );
            }

            window.alert(
                "Calibración aproximada por medidas físicas.\n\n"
                + "Mide desde el borde del robot hasta las paredes.\n"
                + "Puedes dejar campos vacíos.\n\n"
                + "Se requieren al menos 3 medidas."
            );

            const measurements = {};

            for (const item of [
                ["F", "Frente"],
                ["I", "Izquierda"],
                ["D", "Derecha"],
                ["A", "Atrás"]
            ]) {
                const result = automaticPhysicalMeasurePrompt(item[1]);
                if (result.cancelled) {
                    return;
                }
                measurements[item[0]] = result.value;
            }

            const available = Object.values(measurements)
                .filter(value => value !== null)
                .length;

            if (available < 3) {
                throw new Error("Se requieren al menos 3 medidas físicas.");
            }

            const meta = autoMapData.meta;
            const raster = getAutomaticCalibrationRaster(
                Number(meta.width),
                Number(meta.height)
            );

            if (!raster) {
                throw new Error("No pude leer el mapa para calcular el ajuste.");
            }

            setAutomaticCalibrationStatus(
                "Calculando pose por medidas...",
                "active"
            );

            const best = searchAutomaticPhysicalPose(
                autoExecution.pose,
                measurements,
                raster,
                meta
            );

            if (!best) {
                throw new Error(
                    "No encontré una pose compatible con esas medidas."
                );
            }

            const yawDeg = best.yaw * 180 / Math.PI;
            const labels = {
                F: "Frente",
                I: "Izquierda",
                D: "Derecha",
                A: "Atrás"
            };
            const lines = [];

            for (const key of ["F", "I", "D", "A"]) {
                if (measurements[key] === null) {
                    continue;
                }
                lines.push(
                    `${labels[key]}: físico ${measurements[key].toFixed(2)} m`
                    + ` | mapa ${best.predicted[key].toFixed(2)} m`
                );
            }

            const accepted = window.confirm(
                "Pose sugerida\n\n"
                + `X: ${best.x.toFixed(3)} m\n`
                + `Y: ${best.y.toFixed(3)} m\n`
                + `Yaw: ${yawDeg.toFixed(1)}°\n\n`
                + `Desajuste medio estimado: ${best.meanError.toFixed(3)} m\n\n`
                + lines.join("\n")
                + "\n\nAceptar para aplicar esta pose."
            );

            if (!accepted) {
                setAutomaticCalibrationStatus(
                    "Calibración por medidas cancelada."
                );
                return;
            }

            const applied = await applyAutomaticInitialPose(
                best.x,
                best.y,
                best.yaw,
                `Medidas aplicadas · error aprox. ${best.meanError.toFixed(2)} m`
            );

            if (applied) {
                window.alert(
                    "Pose aplicada.\n\n"
                    + `Desajuste estimado: ${best.meanError.toFixed(3)} m\n\n`
                    + "Mueve un poco el robot para que AMCL/IMU terminen de estabilizar la estimación."
                );
            }
        } catch (error) {
            setAutomaticCalibrationStatus(
                "Error: " + error.message,
                "error"
            );
            window.alert(error.message);
        }
    }

    if (calibrationPoseButton) {
        calibrationPoseButton.addEventListener(
            "click",
            startAutomaticPoseCalibration
        );
    }

    if (calibrationMeasuresButton) {
        calibrationMeasuresButton.addEventListener(
            "click",
            runAutomaticPhysicalCalibration
        );
    }

    if (mapViewport) {
        mapViewport.addEventListener(
            "mousedown",
            handleAutomaticCalibrationClick,
            true
        );
    }

    missionSelect.addEventListener(
        "change",
        () => {
            cancelAutomaticCalibration();
            automaticCalibrationRaster.rasterMapName = null;
            automaticCalibrationRaster.rasterWidth = 0;
            automaticCalibrationRaster.rasterHeight = 0;
            automaticCalibrationRaster.raster = null;
            updateAutomaticCalibrationControls();
        }
    );

    window.setInterval(
        updateAutomaticCalibrationControls,
        250
    );

    updateAutomaticCalibrationControls();



    // =====================================================
    // SAFEVISION AUTOMATICA · GUIA EXACTA DE PILOTADA
    // =====================================================

    const automaticAlignmentGuide = {
        rasterMapName:
            null,

        rasterWidth:
            0,

        rasterHeight:
            0,

        raster:
            null,

        visible:
            true
    };


    function automaticAlignmentMapName() {

        return (
            (
                autoMapData.mission
                &&
                autoMapData.mission.map
            )
            ||
            ""
        );
    }


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
        automaticAlignmentGuide.raster
        &&
        automaticAlignmentGuide.rasterMapName
            === automaticAlignmentMapName()
        &&
        automaticAlignmentGuide.rasterWidth
            === width
        &&
        automaticAlignmentGuide.rasterHeight
            === height
    ) {
        return automaticAlignmentGuide.raster;
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


        automaticAlignmentGuide.rasterMapName =
            automaticAlignmentMapName();

        automaticAlignmentGuide.rasterWidth =
            width;

        automaticAlignmentGuide.rasterHeight =
            height;

        automaticAlignmentGuide.raster =
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
        !automaticAlignmentGuide.visible
    ) {

        hideRobotAlignmentGuide();
        return;
    }


    const zoomScale =
        Math.max(
            1,
            Number(
                autoMapView.scale
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


    function updateAutomaticAlignmentGuideToggleUI() {

        const button =
            document.getElementById(
                "autoAlignmentGuideToggle"
            );


        if (!button) {
            return;
        }


        button.textContent =
            automaticAlignmentGuide.visible
                ?
                "Ocultar guía"
                :
                "Mostrar guía";


        button.classList.toggle(
            "active",
            automaticAlignmentGuide.visible
        );


        button.disabled =
            !(
                autoMapData.meta
                &&
                autoExecution.pose
            );
    }


    function renderAutomaticAlignmentGuide() {

        const pose =
            autoExecution.pose;

        const meta =
            autoMapData.meta;


        if (
            !automaticAlignmentGuide.visible
            ||
            !pose
            ||
            !meta
        ) {

            hideRobotAlignmentGuide();

            updateAutomaticAlignmentGuideToggleUI();

            return;
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


        const u =
            Number(
                pose.u
            );

        const v =
            Number(
                pose.v
            );


        if (
            !Number.isFinite(width)
            ||
            !Number.isFinite(height)
            ||
            !Number.isFinite(resolution)
            ||
            !Number.isFinite(u)
            ||
            !Number.isFinite(v)
            ||
            resolution <= 0
        ) {

            hideRobotAlignmentGuide();

            updateAutomaticAlignmentGuideToggleUI();

            return;
        }


        const pixelX =
            u
            *
            width;

        const pixelY =
            v
            *
            height;


        const originYaw =
            Number(
                (
                    meta.origin
                    &&
                    meta.origin.yaw
                )
                ||
                0
            );


        const yawRel =
            Number.isFinite(
                Number(
                    pose.visualYaw
                )
            )
                ?
                Number(
                    pose.visualYaw
                )
                :
                (
                    Number(
                        pose.yaw
                    )
                    -
                    originYaw
                );


        updateRobotAlignmentGuide(
            pixelX,
            pixelY,
            yawRel,
            resolution,
            width,
            height
        );


        updateAutomaticAlignmentGuideToggleUI();
    }


    const automaticAlignmentToggle =
        document.getElementById(
            "autoAlignmentGuideToggle"
        );


    if (automaticAlignmentToggle) {

        automaticAlignmentToggle.addEventListener(
            "click",
            () => {

                automaticAlignmentGuide.visible =
                    !automaticAlignmentGuide.visible;


                updateAutomaticAlignmentGuideToggleUI();


                if (
                    !automaticAlignmentGuide.visible
                ) {

                    hideRobotAlignmentGuide();

                    return;
                }


                renderAutomaticAlignmentGuide();
            }
        );
    }


    missionSelect.addEventListener(
        "change",
        () => {

            automaticAlignmentGuide.rasterMapName =
                null;

            automaticAlignmentGuide.rasterWidth =
                0;

            automaticAlignmentGuide.rasterHeight =
                0;

            automaticAlignmentGuide.raster =
                null;


            hideRobotAlignmentGuide();

            updateAutomaticAlignmentGuideToggleUI();
        }
    );


    window.setInterval(
        renderAutomaticAlignmentGuide,
        200
    );


    updateAutomaticAlignmentGuideToggleUI();


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
    loadAutomaticModelInfo();

})();
