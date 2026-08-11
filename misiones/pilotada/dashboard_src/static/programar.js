const $p = (id) =>
    document.getElementById(id);


const progMapView = {
    scale: 1,
    x: 0,
    y: 0,
    rotation: 0,
    locked: false,
    areaSelecting: false,
    areaStartX: 0,
    areaStartY: 0
};


function progLog(message) {

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
}


function resetProgMapView() {

    progMapView.scale =
        1;

    progMapView.x =
        0;

    progMapView.y =
        0;

    progMapView.rotation =
        0;

    cancelProgAreaZoom();

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
                8,
                progMapView.scale
            )
        );


    applyProgMapView();
}


function rotateProgMap(
    degrees
) {

    if (progMapView.locked) {

        progLog(
            "Mapa bloqueado."
        );

        return;
    }


    progMapView.rotation +=
        degrees;


    while (
        progMapView.rotation
        >=
        360
    ) {

        progMapView.rotation -=
            360;
    }


    while (
        progMapView.rotation
        <
        0
    ) {

        progMapView.rotation +=
            360;
    }


    applyProgMapView();


    progLog(
        (
            "Rotación del mapa: "
            +
            progMapView.rotation
            +
            "°"
        )
    );
}


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


        if (progMapView.locked) {

            button.classList.add(
                "prog-locked"
            );

        } else {

            button.classList.remove(
                "prog-locked"
            );
        }
    }


    if (badge) {

        badge.hidden =
            !progMapView.locked;
    }
}


function toggleProgMapLock() {

    progMapView.locked =
        !progMapView.locked;


    if (progMapView.locked) {

        cancelProgAreaZoom();
    }


    updateProgLockUI();


    progLog(
        (
            "Mapa "
            +
            (
                progMapView.locked
                    ?
                    "bloqueado."
                    :
                    "desbloqueado."
            )
        )
    );
}


function cancelProgAreaZoom() {

    const overlay =
        $p("progAreaSelection");

    const button =
        $p("progAreaZoom");


    progMapView.areaSelecting =
        false;


    if (overlay) {

        overlay.hidden =
            true;

        overlay.style.width =
            "0px";

        overlay.style.height =
            "0px";
    }


    if (button) {

        button.classList.remove(
            "prog-active-tool"
        );

        button.textContent =
            "Zoom área";
    }
}


function beginProgAreaZoomMode() {

    if (progMapView.locked) {

        progLog(
            "Desbloquea el mapa para usar Zoom área."
        );

        return;
    }


    progMapView.areaSelecting =
        !progMapView.areaSelecting;


    const button =
        $p("progAreaZoom");


    if (button) {

        if (progMapView.areaSelecting) {

            button.classList.add(
                "prog-active-tool"
            );

            button.textContent =
                "Cancelar zoom";

        } else {

            button.classList.remove(
                "prog-active-tool"
            );

            button.textContent =
                "Zoom área";
        }
    }


    if (progMapView.areaSelecting) {

        progLog(
            "Zoom área: arrastra un rectángulo sobre el mapa."
        );

    } else {

        cancelProgAreaZoom();
    }
}


function progAreaPointerDown(
    event
) {

    if (
        !progMapView.areaSelecting
        ||
        progMapView.locked
        ||
        event.button !== 0
    ) {
        return;
    }


    const viewport =
        $p("progMapViewport");

    const overlay =
        $p("progAreaSelection");


    if (
        !viewport
        ||
        !overlay
    ) {
        return;
    }


    const rect =
        viewport.getBoundingClientRect();


    progMapView.areaStartX =
        event.clientX
        -
        rect.left;

    progMapView.areaStartY =
        event.clientY
        -
        rect.top;


    overlay.style.left =
        progMapView.areaStartX
        +
        "px";

    overlay.style.top =
        progMapView.areaStartY
        +
        "px";

    overlay.style.width =
        "0px";

    overlay.style.height =
        "0px";

    overlay.hidden =
        false;


    event.preventDefault();
}


function progAreaPointerMove(
    event
) {

    const overlay =
        $p("progAreaSelection");

    const viewport =
        $p("progMapViewport");


    if (
        !progMapView.areaSelecting
        ||
        !overlay
        ||
        overlay.hidden
        ||
        !viewport
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
            progMapView.areaStartX,
            currentX
        );

    const top =
        Math.min(
            progMapView.areaStartY,
            currentY
        );

    const width =
        Math.abs(
            currentX
            -
            progMapView.areaStartX
        );

    const height =
        Math.abs(
            currentY
            -
            progMapView.areaStartY
        );


    overlay.style.left =
        left
        +
        "px";

    overlay.style.top =
        top
        +
        "px";

    overlay.style.width =
        width
        +
        "px";

    overlay.style.height =
        height
        +
        "px";
}


function progAreaPointerUp(
    event
) {

    const overlay =
        $p("progAreaSelection");

    const viewport =
        $p("progMapViewport");


    if (
        !progMapView.areaSelecting
        ||
        !overlay
        ||
        overlay.hidden
        ||
        !viewport
    ) {
        return;
    }


    const width =
        parseFloat(
            overlay.style.width
        )
        ||
        0;

    const height =
        parseFloat(
            overlay.style.height
        )
        ||
        0;

    const left =
        parseFloat(
            overlay.style.left
        )
        ||
        0;

    const top =
        parseFloat(
            overlay.style.top
        )
        ||
        0;


    if (
        width < 20
        ||
        height < 20
    ) {

        cancelProgAreaZoom();

        progLog(
            "Zoom área cancelado: selección demasiado pequeña."
        );

        return;
    }


    const rect =
        viewport.getBoundingClientRect();


    const oldScale =
        progMapView.scale;


    const requestedFactor =
        Math.min(
            rect.width
            /
            width,
            rect.height
            /
            height
        );


    const newScale =
        Math.max(
            0.5,
            Math.min(
                8,
                oldScale
                *
                requestedFactor
            )
        );


    const factor =
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


    const offsetX =
        selectedCenterX
        -
        rect.width
        /
        2;

    const offsetY =
        selectedCenterY
        -
        rect.height
        /
        2;


    progMapView.x =
        factor
        *
        (
            progMapView.x
            -
            offsetX
        );

    progMapView.y =
        factor
        *
        (
            progMapView.y
            -
            offsetY
        );

    progMapView.scale =
        newScale;


    cancelProgAreaZoom();

    applyProgMapView();


    progLog(
        "Zoom de área aplicado."
    );


    event.preventDefault();
}


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


    image.onload =
        () => {

            scene.hidden =
                false;

            placeholder.hidden =
                true;

            resetProgMapView();


            const addPointsButton =
                $p("progAddPoints");


            if (addPointsButton) {

                addPointsButton.disabled =
                    false;
            }


            if (status) {

                status.textContent =
                    (
                        "Mapa: "
                        +
                        name
                    );
            }


            progLog(
                (
                    "Mapa mostrado: "
                    +
                    name
                )
            );
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


function validateProgramDraft() {

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
            "Programa vacío."
        );

        return;
    }


    progLog(
        "Validación sintáctica se implementará en la siguiente fase."
    );
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

ir("A")
esperar(2)
orientar(0)
`;
    }


    progLog(
        "Nuevo programa preparado."
    );
}


window.addEventListener(
    "DOMContentLoaded",
    () => {

        const loadMapButton =
            $p("progLoadMap");

        const zoomInButton =
            $p("progZoomIn");

        const zoomOutButton =
            $p("progZoomOut");

        const resetMapButton =
            $p("progResetMap");

        const validateButton =
            $p("progValidateButton");

        const newButton =
            $p("progNewButton");

        const rotateLeftButton =
            $p("progRotateLeft");

        const rotateRightButton =
            $p("progRotateRight");

        const areaZoomButton =
            $p("progAreaZoom");

        const mapLockButton =
            $p("progMapLock");

        const viewport =
            $p("progMapViewport");



        if (loadMapButton) {

            loadMapButton.addEventListener(
                "click",
                showProgMap
            );
        }


        if (zoomInButton) {

            zoomInButton.addEventListener(
                "click",
                () => {

                    zoomProgMap(
                        1.25
                    );
                }
            );
        }


        if (zoomOutButton) {

            zoomOutButton.addEventListener(
                "click",
                () => {

                    zoomProgMap(
                        0.8
                    );
                }
            );
        }


        if (resetMapButton) {

            resetMapButton.addEventListener(
                "click",
                resetProgMapView
            );
        }


        if (rotateLeftButton) {

            rotateLeftButton.addEventListener(
                "click",
                () => {

                    rotateProgMap(
                        -90
                    );
                }
            );
        }


        if (rotateRightButton) {

            rotateRightButton.addEventListener(
                "click",
                () => {

                    rotateProgMap(
                        90
                    );
                }
            );
        }


        if (areaZoomButton) {

            areaZoomButton.addEventListener(
                "click",
                beginProgAreaZoomMode
            );
        }


        if (mapLockButton) {

            mapLockButton.addEventListener(
                "click",
                toggleProgMapLock
            );
        }


        if (viewport) {

            viewport.addEventListener(
                "mousedown",
                progAreaPointerDown
            );

            viewport.addEventListener(
                "mousemove",
                progAreaPointerMove
            );

            viewport.addEventListener(
                "mouseup",
                progAreaPointerUp
            );

            viewport.addEventListener(
                "mouseleave",
                progAreaPointerMove
            );
        }


        updateProgLockUI();


        if (validateButton) {

            validateButton.addEventListener(
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


        loadProgMaps();
    }
);
