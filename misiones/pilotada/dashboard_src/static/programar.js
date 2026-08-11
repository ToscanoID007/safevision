const $p = (id) =>
    document.getElementById(id);


const progMapView = {
    scale: 1,
    x: 0,
    y: 0
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
            ")"
        );
}


function resetProgMapView() {

    progMapView.scale =
        1;

    progMapView.x =
        0;

    progMapView.y =
        0;

    applyProgMapView();
}


function zoomProgMap(
    factor
) {

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
