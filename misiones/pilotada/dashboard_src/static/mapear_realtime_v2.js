"use strict";

/*
 * ========================================================
 * SAFEVISION MAPEAR REALTIME V2
 * FOOTPRINT VECTORIAL FISICO + MAPA RASTER NITIDO
 * ========================================================
 *
 * ROSMASTER X3 (stack Yahboom):
 *
 *   largo X = 0.234 m
 *   ancho Y = 0.200 m
 *
 * El footprint usa unidades DEL MAPA:
 *
 *   largo_px = 0.234 / resolution
 *   ancho_px = 0.200 / resolution
 *
 * Por tanto:
 * - conserva escala fisica respecto al OccupancyGrid;
 * - crece y disminuye junto con el mapa al hacer zoom;
 * - no usa un tamaño visual fijo;
 * - SVG mantiene bordes/nariz definidos al ampliar.
 *
 * El mapa sigue siendo un raster OccupancyGrid. No se inventa
 * detalle nuevo al ampliar; se desactiva el suavizado para
 * mantener cada celda del mapa visualmente definida.
 */

(() => {

    if (window.safeVisionMapearRealtimeV2) {
        return;
    }

    window.safeVisionMapearRealtimeV2 = true;


    const ROBOT_LENGTH_M = 0.234;
    const ROBOT_WIDTH_M = 0.200;

    const META_MS = 500;
    const POSE_MS = 100;

    const SVG_NS =
        "http://www.w3.org/2000/svg";


    const state = {
        meta: null,
        metaBusy: false,
        poseBusy: false,
        metaTimer: null,
        poseTimer: null
    };


    function byId(id) {
        return document.getElementById(id);
    }


    function svgElement(name) {
        return document.createElementNS(
            SVG_NS,
            name
        );
    }


    /*
     * =====================================================
     * ESTILO
     * =====================================================
     */

    function installStyle() {

        if (byId("sfMapearRealtimeV2Style")) {
            return;
        }


        const style =
            document.createElement("style");


        style.id =
            "sfMapearRealtimeV2Style";


        style.textContent = `
            /*
             * El OccupancyGrid es raster.
             * Al ampliar no hay informacion nueva que crear:
             * nearest-neighbour conserva los pixeles/celdas
             * definidos en lugar de emborronarlos.
             */
            #mapImage {
                image-rendering: -moz-crisp-edges;
                image-rendering: crisp-edges;
                image-rendering: pixelated;
            }


            /*
             * Footprint vectorial.
             * Es hijo de mapScene, por lo que recibe exactamente
             * el mismo pan / zoom / rotacion que el mapa.
             */
            #sfRobotFootprintSvg {
                position: absolute;

                z-index: 59;

                overflow: visible;

                pointer-events: none;
                user-select: none;

                shape-rendering: geometricPrecision;
            }


            #sfRobotFootprintSvg[hidden] {
                display: none !important;
            }


            #sfRobotFootprintBody {
                fill: #ff2d2d;
                fill-opacity: 0.84;

                /*
                 * Sin sombra: evita borrosidad al ampliar.
                 */
                shape-rendering: geometricPrecision;
            }


            /*
             * Nariz / frente +X.
             * Está DENTRO de la huella física.
             */
            #sfRobotFootprintNose {
                fill: #ffffff;
                fill-opacity: 0.98;

                shape-rendering: geometricPrecision;
            }
        `;


        document.head.appendChild(
            style
        );
    }


    /*
     * =====================================================
     * GEOMETRIA DE LA IMAGEN object-fit: contain
     * =====================================================
     */

    function renderedMapGeometry(meta) {

        const scene =
            byId("mapScene");


        if (
            !scene
            ||
            !meta
        ) {
            return null;
        }


        const sceneWidth =
            Number(scene.clientWidth);

        const sceneHeight =
            Number(scene.clientHeight);

        const mapWidth =
            Number(meta.width);

        const mapHeight =
            Number(meta.height);


        if (
            !Number.isFinite(sceneWidth)
            ||
            !Number.isFinite(sceneHeight)
            ||
            sceneWidth <= 0
            ||
            sceneHeight <= 0
            ||
            !Number.isFinite(mapWidth)
            ||
            !Number.isFinite(mapHeight)
            ||
            mapWidth <= 0
            ||
            mapHeight <= 0
        ) {
            return null;
        }


        const displayScale =
            Math.min(
                sceneWidth / mapWidth,
                sceneHeight / mapHeight
            );


        const renderedWidth =
            mapWidth * displayScale;

        const renderedHeight =
            mapHeight * displayScale;


        return {
            offsetX:
                (
                    sceneWidth
                    -
                    renderedWidth
                ) / 2,

            offsetY:
                (
                    sceneHeight
                    -
                    renderedHeight
                ) / 2,

            renderedWidth,
            renderedHeight
        };
    }


    /*
     * =====================================================
     * POSE ROS -> COORDENADAS DEL OccupancyGrid/PNG
     * =====================================================
     */

    function projectPose(
        pose,
        meta
    ) {

        if (
            !pose
            ||
            !meta
            ||
            !meta.origin
        ) {
            return null;
        }


        const resolution =
            Number(meta.resolution);

        const width =
            Number(meta.width);

        const height =
            Number(meta.height);


        const originX =
            Number(meta.origin.x);

        const originY =
            Number(meta.origin.y);

        const originYaw =
            Number(
                meta.origin.yaw
                ||
                0
            );


        const x =
            Number(pose.x);

        const y =
            Number(pose.y);

        const yaw =
            Number(pose.yaw);


        if (
            !Number.isFinite(resolution)
            ||
            resolution <= 0
            ||
            !Number.isFinite(width)
            ||
            !Number.isFinite(height)
            ||
            !Number.isFinite(originX)
            ||
            !Number.isFinite(originY)
            ||
            !Number.isFinite(originYaw)
            ||
            !Number.isFinite(x)
            ||
            !Number.isFinite(y)
            ||
            !Number.isFinite(yaw)
        ) {
            return null;
        }


        const dx =
            x - originX;

        const dy =
            y - originY;


        const cosO =
            Math.cos(originYaw);

        const sinO =
            Math.sin(originYaw);


        /*
         * Mundo -> marco local del mapa.
         */
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


        /*
         * OccupancyGrid:
         * Y crece hacia arriba.
         *
         * PNG:
         * Y crece hacia abajo.
         */
        const pixelY =
            height
            -
            (
                localY / resolution
            );


        if (
            pixelX < 0
            ||
            pixelX > width
            ||
            pixelY < 0
            ||
            pixelY > height
        ) {
            return null;
        }


        return {
            pixelX,
            pixelY,

            yawRel:
                yaw - originYaw,

            resolution,
            width,
            height
        };
    }


    /*
     * =====================================================
     * SVG VECTORIAL
     * =====================================================
     */

    function ensureFootprintSvg(
        meta,
        geometry
    ) {

        const scene =
            byId("mapScene");


        if (!scene) {
            return null;
        }


        let svg =
            byId("sfRobotFootprintSvg");


        if (!svg) {

            svg =
                svgElement("svg");

            svg.id =
                "sfRobotFootprintSvg";

            svg.hidden =
                true;


            const group =
                svgElement("g");

            group.id =
                "sfRobotFootprintGroup";


            const body =
                svgElement("rect");

            body.id =
                "sfRobotFootprintBody";


            const nose =
                svgElement("rect");

            nose.id =
                "sfRobotFootprintNose";


            group.appendChild(body);
            group.appendChild(nose);
            svg.appendChild(group);

            scene.appendChild(svg);
        }


        const width =
            Number(meta.width);

        const height =
            Number(meta.height);


        svg.setAttribute(
            "viewBox",
            `0 0 ${width} ${height}`
        );

        svg.setAttribute(
            "preserveAspectRatio",
            "none"
        );


        /*
         * SVG y PNG ocupan exactamente el mismo rectangulo.
         * Luego mapScene transforma ambos juntos.
         */
        svg.style.left =
            `${geometry.offsetX}px`;

        svg.style.top =
            `${geometry.offsetY}px`;

        svg.style.width =
            `${geometry.renderedWidth}px`;

        svg.style.height =
            `${geometry.renderedHeight}px`;


        return {
            svg,
            group:
                byId(
                    "sfRobotFootprintGroup"
                ),

            body:
                byId(
                    "sfRobotFootprintBody"
                ),

            nose:
                byId(
                    "sfRobotFootprintNose"
                )
        };
    }


    function hideFootprint() {

        const svg =
            byId("sfRobotFootprintSvg");


        if (svg) {
            svg.hidden = true;
        }
    }


    function renderFootprint(
        projected,
        meta,
        geometry
    ) {

        const parts =
            ensureFootprintSvg(
                meta,
                geometry
            );


        if (
            !parts
            ||
            !parts.group
            ||
            !parts.body
            ||
            !parts.nose
        ) {
            return;
        }


        /*
         * =================================================
         * DIMENSION FISICA REAL
         * =================================================
         *
         * HAB2 @ 0.05 m/pixel:
         *
         *   largo = 0.234 / 0.05 = 4.68 px de mapa
         *   ancho = 0.200 / 0.05 = 4.00 px de mapa
         *
         * NO son pixeles fijos de pantalla.
         */
        const robotLengthPx =
            ROBOT_LENGTH_M
            /
            projected.resolution;

        const robotWidthPx =
            ROBOT_WIDTH_M
            /
            projected.resolution;


        /*
         * Bordes redondeados, sin cambiar el bounding-box
         * físico exterior del robot.
         */
        const radius =
            Math.min(
                robotLengthPx,
                robotWidthPx
            )
            *
            0.24;


        parts.body.setAttribute(
            "x",
            String(
                -robotLengthPx / 2
            )
        );

        parts.body.setAttribute(
            "y",
            String(
                -robotWidthPx / 2
            )
        );

        parts.body.setAttribute(
            "width",
            String(robotLengthPx)
        );

        parts.body.setAttribute(
            "height",
            String(robotWidthPx)
        );

        parts.body.setAttribute(
            "rx",
            String(radius)
        );

        parts.body.setAttribute(
            "ry",
            String(radius)
        );


        /*
         * =================================================
         * NARIZ BLANCA
         * =================================================
         *
         * Frente ROS = +X.
         *
         * El indicador está dentro del footprint.
         * Es un pequeño rectángulo/cápsula blanca pegado
         * al borde frontal.
         */
        const noseDepth =
            robotLengthPx
            *
            0.22;

        const noseHeight =
            robotWidthPx
            *
            0.52;


        parts.nose.setAttribute(
            "x",
            String(
                robotLengthPx / 2
                -
                noseDepth
            )
        );

        parts.nose.setAttribute(
            "y",
            String(
                -noseHeight / 2
            )
        );

        parts.nose.setAttribute(
            "width",
            String(noseDepth)
        );

        parts.nose.setAttribute(
            "height",
            String(noseHeight)
        );

        parts.nose.setAttribute(
            "rx",
            String(
                Math.min(
                    noseDepth,
                    noseHeight
                )
                *
                0.45
            )
        );

        parts.nose.setAttribute(
            "ry",
            String(
                Math.min(
                    noseDepth,
                    noseHeight
                )
                *
                0.45
            )
        );


        /*
         * En imagen Y crece hacia abajo:
         * giro visual = -yawRel.
         */
        const yawDeg =
            -projected.yawRel
            *
            180
            /
            Math.PI;


        parts.group.setAttribute(
            "transform",
            (
                `translate(`
                +
                `${projected.pixelX} `
                +
                `${projected.pixelY}`
                +
                `) rotate(${yawDeg})`
            )
        );


        parts.svg.dataset.robotLengthM =
            String(ROBOT_LENGTH_M);

        parts.svg.dataset.robotWidthM =
            String(ROBOT_WIDTH_M);

        parts.svg.dataset.robotLengthMapPx =
            robotLengthPx.toFixed(3);

        parts.svg.dataset.robotWidthMapPx =
            robotWidthPx.toFixed(3);


        parts.svg.hidden =
            false;
    }


    /*
     * =====================================================
     * HTTP
     * =====================================================
     */

    async function refreshMeta() {

        if (state.metaBusy) {
            return;
        }


        state.metaBusy =
            true;


        try {

            const response =
                await fetch(
                    "/mapping/meta",
                    {
                        cache:
                            "no-store"
                    }
                );


            if (!response.ok) {
                return;
            }


            const meta =
                await response.json();


            if (
                meta
                &&
                meta.ok === true
                &&
                meta.available === true
            ) {
                state.meta =
                    meta;
            }


        } catch (_) {

            /*
             * Mantener ultimo meta valido.
             */


        } finally {

            state.metaBusy =
                false;
        }
    }


    async function refreshPose() {

        if (
            state.poseBusy
            ||
            !state.meta
        ) {
            return;
        }


        state.poseBusy =
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


            if (!response.ok) {
                hideFootprint();
                return;
            }


            const pose =
                await response.json();


            if (
                !pose
                ||
                pose.ok !== true
                ||
                pose.localized !== true
            ) {
                hideFootprint();
                return;
            }


            const age =
                Number(
                    pose.age_seconds
                );


            if (
                Number.isFinite(age)
                &&
                age > 1.5
            ) {
                hideFootprint();
                return;
            }


            const projected =
                projectPose(
                    pose,
                    state.meta
                );


            const geometry =
                renderedMapGeometry(
                    state.meta
                );


            if (
                !projected
                ||
                !geometry
            ) {
                hideFootprint();
                return;
            }


            renderFootprint(
                projected,
                state.meta,
                geometry
            );


        } catch (_) {

            hideFootprint();


        } finally {

            state.poseBusy =
                false;
        }
    }


    /*
     * =====================================================
     * ARRANQUE
     * =====================================================
     */

    function start() {

        installStyle();


        /*
         * El marcador DOM viejo queda desactivado.
         */
        const oldMarker =
            byId("robotMarker");


        if (oldMarker) {
            oldMarker.hidden = true;
        }


        refreshMeta();


        window.setTimeout(
            refreshPose,
            150
        );


        state.metaTimer =
            window.setInterval(
                refreshMeta,
                META_MS
            );


        state.poseTimer =
            window.setInterval(
                refreshPose,
                POSE_MS
            );


        console.info(
            "[SafeVision] Mapear V2: footprint vectorial fisico activo"
        );
    }


    if (
        document.readyState
        ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            start,
            {
                once: true
            }
        );


    } else {

        start();
    }


    /*
     * Recalcular geometria si cambia tamaño de ventana.
     * Zoom/pan/rotacion no requieren rerasterizar el SVG:
     * es vectorial e hijo de mapScene.
     */
    window.addEventListener(
        "resize",
        refreshPose
    );


    window.addEventListener(
        "beforeunload",
        () => {

            if (state.metaTimer) {
                clearInterval(
                    state.metaTimer
                );
            }


            if (state.poseTimer) {
                clearInterval(
                    state.poseTimer
                );
            }
        }
    );

})();
