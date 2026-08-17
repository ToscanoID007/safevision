const $m = (id) =>
    document.getElementById(id);


const mapsConnection = {
    connected: false,
    checked: false
};


const mapsState = {
    maps: [],
    selected: null,

    view: {
        scale: 1,
        x: 0,
        y: 0,
        rotation: 0,

        dragging: false,
        startX: 0,
        startY: 0,

        areaSelecting: false,
        areaStartX: 0,
        areaStartY: 0
    }
};


// =========================================================
// CONEXION GLOBAL DEL DASHBOARD
// =========================================================

function renderMapsConnection() {

    const badge =
        $m("mapsConnectionBadge");


    if (!badge) {
        return;
    }


    if (mapsConnection.connected) {

        badge.textContent =
            "● CONECTADO";

        badge.classList.add(
            "maps-connection-on"
        );

        badge.classList.remove(
            "maps-connection-off"
        );

    } else {

        badge.textContent =
            "● DESCONECTADO";

        badge.classList.remove(
            "maps-connection-on"
        );

        badge.classList.add(
            "maps-connection-off"
        );
    }
}


async function checkMapsConnection() {

    const previous =
        mapsConnection.connected;


    try {

        const response =
            await fetch(
                "/connection_status",
                {
                    cache:
                        "no-store"
                }
            );


        const data =
            await response.json();


        mapsConnection.connected =
            Boolean(
                response.ok
                &&
                data.connected
            );


    } catch (error) {

        mapsConnection.connected =
            false;
    }


    renderMapsConnection();

    setActionState();


    if (
        mapsConnection.connected
        &&
        !previous
    ) {

        mapsStatus(
            "Robot conectado. Cargando mapas..."
        );

        await loadMaps();
    }


    if (
        !mapsConnection.connected
        &&
        previous
    ) {

        mapsState.maps = [];
        mapsState.selected = null;

        clearSelectedMap();
        renderMapsList();

        mapsStatus(
            "Robot desconectado."
        );
    }


    mapsConnection.checked =
        true;
}


// =========================================================
// ESTADO UI
// =========================================================

function mapsStatus(message) {

    const viewerStatus =
        $m("mapsViewerStatus");

    if (viewerStatus) {
        viewerStatus.textContent =
            message;
    }
}


function setActionState() {

    const selected =
        Boolean(
            mapsState.selected
        );


    const managementIds = [
        "mapsRename",
        "mapsDuplicate",
        "mapsDelete"
    ];


    for (const id of managementIds) {

        const button =
            $m(id);

        if (button) {
            button.disabled =
                !selected;
        }
    }


    const editButton =
        $m("mapsEdit");


    if (editButton) {

        editButton.disabled =
            !selected;
    }


    const importButton =
        $m("mapsImport");

    const createButton =
        $m("mapsCreate");


    const exportButton =
        $m("mapsExport");


    if (exportButton) {
        exportButton.disabled =
            !selected;
    }


    if (importButton) {
        importButton.disabled =
            !mapsConnection.connected;
    }

    if (createButton) {
        createButton.disabled = true;
    }


    const zoomIds = [
        "mapsZoomOut",
        "mapsZoomIn",
        "mapsAreaZoom",
        "mapsResetView"
    ];


    for (const id of zoomIds) {

        const button =
            $m(id);

        if (button) {
            button.disabled =
                !selected;
        }
    }


    const rotationSlider =
        $m("mapsRotationSlider");


    if (rotationSlider) {

        rotationSlider.disabled =
            !selected;
    }
}


// =========================================================
// LISTA
// =========================================================

function renderMapsList() {

    const list =
        $m("mapsList");

    const search =
        $m("mapsSearch");

    const count =
        $m("mapsCount");


    if (!list) {
        return;
    }


    const query =
        (
            search
                ?
                search.value
                :
                ""
        )
        .trim()
        .toLowerCase();


    const filtered =
        mapsState.maps.filter(
            item =>
                String(
                    item.name
                )
                .toLowerCase()
                .includes(
                    query
                )
        );


    list.innerHTML = "";


    if (!filtered.length) {

        const message =
            document.createElement(
                "div"
            );

        message.className =
            "maps-list-message";

        message.textContent =
            mapsState.maps.length
                ?
                "No hay coincidencias."
                :
                "No hay mapas disponibles.";

        list.appendChild(
            message
        );

    } else {

        for (const map of filtered) {

            const button =
                document.createElement(
                    "button"
                );

            button.type =
                "button";

            button.className =
                "maps-list-item";

            button.textContent =
                map.name;


            if (
                mapsState.selected
                ===
                map.name
            ) {

                button.classList.add(
                    "active"
                );
            }


            button.addEventListener(
                "click",
                () => {
                    selectMap(
                        map.name
                    );
                }
            );


            list.appendChild(
                button
            );
        }
    }


    if (count) {

        count.textContent =
            (
                mapsState.maps.length
                +
                (
                    mapsState.maps.length === 1
                        ?
                        " mapa"
                        :
                        " mapas"
                )
            );
    }
}


async function loadMaps() {

    const list =
        $m("mapsList");


    if (list) {
        list.innerHTML =
            '<div class="maps-list-message">Cargando mapas...</div>';
    }


    try {

        const response =
            await fetch(
                "/maps",
                {
                    cache:
                        "no-store"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message
                ||
                data.error
                ||
                "No se pudieron obtener los mapas."
            );
        }


        mapsState.maps =
            Array.isArray(
                data.maps
            )
                ?
                data.maps
                :
                [];


        const stillExists =
            mapsState.maps.some(
                item =>
                    item.name
                    ===
                    mapsState.selected
            );


        if (!stillExists) {

            mapsState.selected =
                null;

            clearSelectedMap();
        }


        renderMapsList();


        mapsStatus(
            mapsState.maps.length
                ?
                "Selecciona un mapa de la lista."
                :
                "No hay mapas disponibles."
        );


    } catch (error) {

        mapsState.maps = [];

        renderMapsList();

        mapsStatus(
            "Error: "
            +
            error.message
        );
    }
}


// =========================================================
// VISOR
// =========================================================

function updateMapsRotationUI() {

    const slider =
        $m("mapsRotationSlider");

    const output =
        $m("mapsRotationValue");


    const value =
        Math.round(
            Number(
                mapsState.view.rotation
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
            value
            +
            "°";
    }
}


function setMapsRotation(
    value
) {

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


    mapsState.view.rotation =
        degrees;


    updateMapsRotationUI();

    applyMapView();
}


function cancelMapsAreaZoom() {

    const overlay =
        $m("mapsAreaSelection");

    const button =
        $m("mapsAreaZoom");

    const viewport =
        $m("mapsViewport");


    mapsState.view.areaSelecting =
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
            "maps-active-tool"
        );

        button.textContent =
            "Zoom área";
    }


    if (viewport) {

        viewport.classList.remove(
            "maps-area-mode"
        );
    }
}


function beginMapsAreaZoom() {

    if (!mapsState.selected) {
        return;
    }


    mapsState.view.areaSelecting =
        !mapsState.view.areaSelecting;


    const button =
        $m("mapsAreaZoom");

    const viewport =
        $m("mapsViewport");


    if (
        mapsState.view.areaSelecting
    ) {

        if (button) {

            button.classList.add(
                "maps-active-tool"
            );

            button.textContent =
                "Cancelar zoom";
        }


        if (viewport) {

            viewport.classList.add(
                "maps-area-mode"
            );
        }


        mapsStatus(
            "Zoom área: arrastra un rectángulo sobre el mapa."
        );


    } else {

        cancelMapsAreaZoom();

        mapsStatus(
            "Zoom de área cancelado."
        );
    }
}


function mapsAreaPointerDown(
    event
) {

    if (
        !mapsState.view.areaSelecting
        ||
        event.button !== 0
    ) {
        return;
    }


    const viewport =
        $m("mapsViewport");

    const overlay =
        $m("mapsAreaSelection");


    if (
        !viewport
        ||
        !overlay
    ) {
        return;
    }


    const rect =
        viewport.getBoundingClientRect();


    mapsState.view.areaStartX =
        event.clientX
        -
        rect.left;

    mapsState.view.areaStartY =
        event.clientY
        -
        rect.top;


    overlay.style.left =
        mapsState.view.areaStartX
        +
        "px";

    overlay.style.top =
        mapsState.view.areaStartY
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


function mapsAreaPointerMove(
    event
) {

    const overlay =
        $m("mapsAreaSelection");

    const viewport =
        $m("mapsViewport");


    if (
        !mapsState.view.areaSelecting
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
            mapsState.view.areaStartX,
            currentX
        );

    const top =
        Math.min(
            mapsState.view.areaStartY,
            currentY
        );

    const width =
        Math.abs(
            currentX
            -
            mapsState.view.areaStartX
        );

    const height =
        Math.abs(
            currentY
            -
            mapsState.view.areaStartY
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


function mapsAreaPointerUp(
    event
) {

    const overlay =
        $m("mapsAreaSelection");

    const viewport =
        $m("mapsViewport");


    if (
        !mapsState.view.areaSelecting
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

        cancelMapsAreaZoom();

        mapsStatus(
            "Zoom área cancelado: selección demasiado pequeña."
        );

        return;
    }


    const rect =
        viewport.getBoundingClientRect();


    const oldScale =
        mapsState.view.scale;


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


    mapsState.view.x =
        factor
        *
        (
            mapsState.view.x
            -
            offsetX
        );

    mapsState.view.y =
        factor
        *
        (
            mapsState.view.y
            -
            offsetY
        );

    mapsState.view.scale =
        newScale;


    cancelMapsAreaZoom();

    applyMapView();


    mapsStatus(
        "Zoom de área aplicado."
    );


    event.preventDefault();
}


function applyMapView() {

    const scene =
        $m("mapsScene");


    if (!scene) {
        return;
    }


    scene.style.transform =
        (
            "translate("
            +
            mapsState.view.x
            +
            "px, "
            +
            mapsState.view.y
            +
            "px) "
            +
            "scale("
            +
            mapsState.view.scale
            +
            ") "
            +
            "rotate("
            +
            mapsState.view.rotation
            +
            "deg)"
        );
}


function resetMapView() {

    mapsState.view.scale =
        1;

    mapsState.view.x =
        0;

    mapsState.view.y =
        0;

    mapsState.view.rotation =
        0;


    cancelMapsAreaZoom();

    updateMapsRotationUI();

    applyMapView();
}


function zoomMap(
    factor
) {

    if (!mapsState.selected) {
        return;
    }


    mapsState.view.scale *=
        factor;


    mapsState.view.scale =
        Math.max(
            0.5,
            Math.min(
                10,
                mapsState.view.scale
            )
        );


    applyMapView();
}


function clearSelectedMap() {

    const scene =
        $m("mapsScene");

    const image =
        $m("mapsImage");

    const placeholder =
        $m("mapsPlaceholder");

    const title =
        $m("mapsSelectedName");

    const actionName =
        $m("mapsActionName");


    if (scene) {
        scene.hidden = true;
    }

    if (image) {
        image.removeAttribute(
            "src"
        );
    }

    if (placeholder) {
        placeholder.hidden = false;
        placeholder.textContent =
            "Selecciona un mapa de la lista.";
    }

    if (title) {
        title.textContent =
            "Sin mapa seleccionado";
    }

    if (actionName) {
        actionName.textContent =
            "Sin selección";
    }


    resetMapView();
    setActionState();
}


function selectMap(
    name
) {

    const image =
        $m("mapsImage");

    const scene =
        $m("mapsScene");

    const placeholder =
        $m("mapsPlaceholder");

    const title =
        $m("mapsSelectedName");

    const actionName =
        $m("mapsActionName");

    const actionStatus =
        $m("mapsActionStatus");


    if (
        !image
        ||
        !scene
        ||
        !placeholder
    ) {
        return;
    }


    mapsState.selected =
        name;


    renderMapsList();


    if (title) {
        title.textContent =
            name;
    }

    if (actionName) {
        actionName.textContent =
            name;
    }

    if (actionStatus) {
        actionStatus.textContent =
            "Mapa seleccionado: "
            +
            name;
    }


    placeholder.hidden =
        false;

    placeholder.textContent =
        "Cargando mapa...";

    scene.hidden =
        true;


    image.onload =
        () => {

            resetMapView();

            scene.hidden =
                false;

            placeholder.hidden =
                true;

            setActionState();

            mapsStatus(
                "Mapa cargado: "
                +
                name
            );
        };


    image.onerror =
        () => {

            scene.hidden =
                true;

            placeholder.hidden =
                false;

            placeholder.textContent =
                "No se pudo cargar el mapa.";

            mapsStatus(
                "Error cargando: "
                +
                name
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


// =========================================================
// MODAL
// =========================================================

let mapsModalResolve = null;


function closeMapsModal(
    result
) {

    const modal =
        $m("mapsModal");


    if (modal) {
        modal.hidden = true;
    }


    if (mapsModalResolve) {

        mapsModalResolve(
            result
        );

        mapsModalResolve =
            null;
    }
}


function openMapsModal({
    title,
    text,
    value = "",
    input = true,
    confirmText = "Confirmar",
    danger = false
}) {

    const modal =
        $m("mapsModal");

    const titleBox =
        $m("mapsModalTitle");

    const textBox =
        $m("mapsModalText");

    const inputWrap =
        $m("mapsModalInputWrap");

    const inputBox =
        $m("mapsModalInput");

    const errorBox =
        $m("mapsModalError");

    const confirm =
        $m("mapsModalConfirm");


    if (
        !modal
        ||
        !confirm
    ) {

        return Promise.resolve(
            null
        );
    }


    if (titleBox) {
        titleBox.textContent =
            title;
    }


    if (textBox) {
        textBox.textContent =
            text;
    }


    if (inputWrap) {
        inputWrap.hidden =
            !input;
    }


    if (inputBox) {

        inputBox.value =
            value;
    }


    if (errorBox) {

        errorBox.hidden =
            true;

        errorBox.textContent =
            "";
    }


    confirm.textContent =
        confirmText;


    confirm.classList.toggle(
        "maps-modal-danger",
        danger
    );


    modal.hidden =
        false;


    if (
        input
        &&
        inputBox
    ) {

        window.setTimeout(
            () => {

                inputBox.focus();
                inputBox.select();

            },
            20
        );
    }


    return new Promise(
        resolve => {

            mapsModalResolve =
                resolve;
        }
    );
}


function mapsOperationError(
    message
) {

    const actionStatus =
        $m("mapsActionStatus");


    if (actionStatus) {

        actionStatus.textContent =
            "Error: "
            +
            message;
    }


    mapsStatus(
        "Error: "
        +
        message
    );
}


function modalError(
    message
) {

    const box =
        $m("mapsModalError");


    if (!box) {
        return;
    }


    box.textContent =
        message;

    box.hidden =
        false;
}


// =========================================================
// NOMBRES
// =========================================================

function validateMapName(
    value
) {

    const name =
        String(
            value
            ||
            ""
        ).trim();


    if (!name) {
        return {
            ok: false,
            error: "El nombre no puede estar vacío."
        };
    }


    if (name.length > 80) {
        return {
            ok: false,
            error: "El nombre es demasiado largo."
        };
    }


    if (
        name.includes("/")
        ||
        name.includes("\\")
        ||
        name === "."
        ||
        name === ".."
    ) {

        return {
            ok: false,
            error: "El nombre contiene caracteres no permitidos."
        };
    }


    const lower =
        name.toLowerCase();


    if (
        lower.endsWith(".yaml")
        ||
        lower.endsWith(".pgm")
        ||
        lower.endsWith(".zip")
    ) {

        return {
            ok: false,
            error: "Escribe solo el nombre, sin extensión."
        };
    }


    return {
        ok: true,
        name
    };
}


// =========================================================
// API
// =========================================================

async function postMapAction(
    action,
    payload
) {

    const response =
        await fetch(
            "/maps/"
            +
            action,
            {
                method:
                    "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(
                        payload
                    )
            }
        );


    let data = {};


    try {

        data =
            await response.json();

    } catch (error) {

        data = {};
    }


    if (
        !response.ok
        ||
        !data.ok
    ) {

        throw new Error(
            data.error
            ||
            data.message
            ||
            "La operación no pudo completarse."
        );
    }


    return data;
}


// =========================================================
// RENOMBRAR
// =========================================================

async function renameSelectedMap() {

    const current =
        mapsState.selected;


    if (!current) {
        return;
    }


    const result =
        await openMapsModal({
            title:
                "Renombrar mapa",

            text:
                "Cambiar nombre de "
                +
                current
                +
                ".",

            value:
                current,

            input:
                true,

            confirmText:
                "Renombrar"
        });


    if (result === null) {
        return;
    }


    const checked =
        validateMapName(
            result
        );


    if (!checked.ok) {

        mapsOperationError(
            checked.error
        );

        return;
    }


    if (
        checked.name
        ===
        current
    ) {

        mapsOperationError(
            "El nuevo nombre es igual al actual."
        );

        return;
    }


    try {

        const data =
            await postMapAction(
                "rename",
                {
                    name:
                        current,

                    new_name:
                        checked.name
                }
            );


        closeMapsModal(
            null
        );


        mapsState.selected =
            data.name;


        await loadMaps();


        if (
            mapsState.maps.some(
                item =>
                    item.name
                    ===
                    data.name
            )
        ) {

            selectMap(
                data.name
            );
        }


        mapsStatus(
            "Mapa renombrado a "
            +
            data.name
            +
            "."
        );


    } catch (error) {

        mapsOperationError(
            error.message
        );
    }
}


// =========================================================
// DUPLICAR
// =========================================================

async function duplicateSelectedMap() {

    const current =
        mapsState.selected;


    if (!current) {
        return;
    }


    const result =
        await openMapsModal({
            title:
                "Duplicar mapa",

            text:
                "Crear una copia independiente de "
                +
                current
                +
                ".",

            value:
                current
                +
                "_copia",

            input:
                true,

            confirmText:
                "Duplicar"
        });


    if (result === null) {
        return;
    }


    const checked =
        validateMapName(
            result
        );


    if (!checked.ok) {

        mapsOperationError(
            checked.error
        );

        return;
    }


    try {

        const data =
            await postMapAction(
                "duplicate",
                {
                    name:
                        current,

                    new_name:
                        checked.name
                }
            );


        closeMapsModal(
            null
        );


        await loadMaps();


        if (
            mapsState.maps.some(
                item =>
                    item.name
                    ===
                    data.name
            )
        ) {

            selectMap(
                data.name
            );
        }


        mapsStatus(
            "Copia creada: "
            +
            data.name
            +
            "."
        );


    } catch (error) {

        mapsOperationError(
            error.message
        );
    }
}


// =========================================================
// ELIMINAR
// =========================================================

async function deleteSelectedMap() {

    const current =
        mapsState.selected;


    if (!current) {
        return;
    }


    const result =
        await openMapsModal({
            title:
                "Eliminar mapa",

            text:
                (
                    "Se eliminará permanentemente "
                    +
                    current
                    +
                    ". Esta operación no se puede deshacer."
                ),

            input:
                false,

            confirmText:
                "Eliminar mapa",

            danger:
                true
        });


    if (result === null) {
        return;
    }


    try {

        await postMapAction(
            "delete",
            {
                name:
                    current
            }
        );


        closeMapsModal(
            null
        );


        mapsState.selected =
            null;


        clearSelectedMap();

        await loadMaps();


        mapsStatus(
            "Mapa eliminado: "
            +
            current
            +
            "."
        );


    } catch (error) {

        mapsOperationError(
            error.message
        );
    }
}


// =========================================================
// EXPORTAR / IMPORTAR
// =========================================================

async function exportSelectedMap() {

    const name =
        mapsState.selected;


    if (!name) {
        return;
    }


    try {

        mapsStatus(
            "Preparando exportación de "
            +
            name
            +
            "..."
        );


        const response =
            await fetch(
                "/maps/export/"
                +
                encodeURIComponent(
                    name
                ),
                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {

            let message =
                "No se pudo exportar el mapa.";


            try {

                const data =
                    await response.json();

                message =
                    data.error
                    ||
                    data.message
                    ||
                    message;

            } catch (error) {
            }


            throw new Error(
                message
            );
        }


        const blob =
            await response.blob();


        const url =
            URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            url;

        link.download =
            name
            +
            ".zip";


        document.body.appendChild(
            link
        );

        link.click();

        link.remove();


        URL.revokeObjectURL(
            url
        );


        mapsStatus(
            "Mapa exportado: "
            +
            name
            +
            ".zip"
        );


    } catch (error) {

        mapsOperationError(
            error.message
        );
    }
}


async function importMapFile(
    file
) {

    if (!file) {
        return;
    }


    if (
        !file.name
        .toLowerCase()
        .endsWith(
            ".zip"
        )
    ) {

        mapsOperationError(
            "Selecciona un archivo .zip."
        );

        return;
    }


    const suggested =
        file.name.replace(
            /\.zip$/i,
            ""
        );


    const result =
        await openMapsModal({
            title:
                "Importar mapa",

            text:
                (
                    "El ZIP debe contener "
                    +
                    "un archivo YAML y un PGM."
                ),

            value:
                suggested,

            input:
                true,

            confirmText:
                "Importar"
        });


    if (result === null) {
        return;
    }


    const checked =
        validateMapName(
            result
        );


    if (!checked.ok) {

        mapsOperationError(
            checked.error
        );

        return;
    }


    const form =
        new FormData();


    form.append(
        "file",
        file
    );

    form.append(
        "name",
        checked.name
    );


    try {

        mapsStatus(
            "Importando mapa..."
        );


        const response =
            await fetch(
                "/maps/import",
                {
                    method:
                        "POST",

                    body:
                        form
                }
            );


        let data = {};


        try {

            data =
                await response.json();

        } catch (error) {
        }


        if (
            !response.ok
            ||
            !data.ok
        ) {

            throw new Error(
                data.error
                ||
                data.message
                ||
                "No se pudo importar el mapa."
            );
        }


        await loadMaps();


        if (
            mapsState.maps.some(
                item =>
                    item.name
                    ===
                    data.name
            )
        ) {

            selectMap(
                data.name
            );
        }


        mapsStatus(
            "Mapa importado: "
            +
            data.name
            +
            "."
        );


    } catch (error) {

        mapsOperationError(
            error.message
        );
    }
}


// =========================================================
// EVENTOS
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const search =
            $m("mapsSearch");

        const refresh =
            $m("mapsRefresh");

        const zoomOut =
            $m("mapsZoomOut");

        const zoomIn =
            $m("mapsZoomIn");

        const reset =
            $m("mapsResetView");

        const rotationSlider =
            $m("mapsRotationSlider");

        const areaZoom =
            $m("mapsAreaZoom");

        const exportButton =
            $m("mapsExport");

        const importButton =
            $m("mapsImport");

        const importFile =
            $m("mapsImportFile");

        const editButton =
            $m("mapsEdit");

        const viewport =
            $m("mapsViewport");

        const renameButton =
            $m("mapsRename");

        const duplicateButton =
            $m("mapsDuplicate");

        const deleteButton =
            $m("mapsDelete");

        const modal =
            $m("mapsModal");

        const modalInput =
            $m("mapsModalInput");

        const modalCancel =
            $m("mapsModalCancel");

        const modalConfirm =
            $m("mapsModalConfirm");


        if (search) {

            search.addEventListener(
                "input",
                renderMapsList
            );
        }


        if (renameButton) {

            renameButton.addEventListener(
                "click",
                renameSelectedMap
            );
        }


        if (duplicateButton) {

            duplicateButton.addEventListener(
                "click",
                duplicateSelectedMap
            );
        }


        if (deleteButton) {

            deleteButton.addEventListener(
                "click",
                deleteSelectedMap
            );
        }


        if (modalCancel) {

            modalCancel.addEventListener(
                "click",
                () => {
                    closeMapsModal(
                        null
                    );
                }
            );
        }


        if (modalConfirm) {

            modalConfirm.addEventListener(
                "click",
                () => {

                    const inputWrap =
                        $m(
                            "mapsModalInputWrap"
                        );


                    if (
                        inputWrap
                        &&
                        !inputWrap.hidden
                    ) {

                        closeMapsModal(
                            modalInput
                                ?
                                modalInput.value
                                :
                                ""
                        );

                    } else {

                        closeMapsModal(
                            true
                        );
                    }
                }
            );
        }


        if (modalInput) {

            modalInput.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key
                        ===
                        "Enter"
                    ) {

                        event.preventDefault();

                        closeMapsModal(
                            modalInput.value
                        );
                    }
                }
            );
        }


        if (modal) {

            modal.addEventListener(
                "mousedown",
                event => {

                    if (
                        event.target
                        ===
                        modal
                    ) {

                        closeMapsModal(
                            null
                        );
                    }
                }
            );
        }


        document.addEventListener(
            "keydown",
            event => {

                if (
                    event.key
                    ===
                    "Escape"
                    &&
                    modal
                    &&
                    !modal.hidden
                ) {

                    closeMapsModal(
                        null
                    );
                }
            }
        );


        if (refresh) {

            refresh.addEventListener(
                "click",
                loadMaps
            );
        }


        if (zoomOut) {

            zoomOut.addEventListener(
                "click",
                () => {
                    zoomMap(
                        0.85
                    );
                }
            );
        }


        if (zoomIn) {

            zoomIn.addEventListener(
                "click",
                () => {
                    zoomMap(
                        1.18
                    );
                }
            );
        }


        if (reset) {

            reset.addEventListener(
                "click",
                resetMapView
            );
        }


        if (rotationSlider) {

            rotationSlider.addEventListener(
                "input",
                event => {

                    setMapsRotation(
                        event.target.value
                    );
                }
            );
        }


        if (areaZoom) {

            areaZoom.addEventListener(
                "click",
                beginMapsAreaZoom
            );
        }


        if (exportButton) {

            exportButton.addEventListener(
                "click",
                exportSelectedMap
            );
        }



        if (editButton) {

            editButton.addEventListener(
                "click",
                () => {

                    if (!mapsState.selected) {
                        return;
                    }


                    window.location.href =
                        (
                            "/mapas/editar/"
                            +
                            encodeURIComponent(
                                mapsState.selected
                            )
                        );
                }
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

                    const file =
                        (
                            importFile.files
                            &&
                            importFile.files[0]
                        )
                            ?
                            importFile.files[0]
                            :
                            null;


                    importMapFile(
                        file
                    );
                }
            );
        }


        if (viewport) {

            viewport.addEventListener(
                "mousedown",
                mapsAreaPointerDown
            );

            viewport.addEventListener(
                "mousemove",
                mapsAreaPointerMove
            );

            viewport.addEventListener(
                "mouseup",
                mapsAreaPointerUp
            );

            viewport.addEventListener(
                "mouseleave",
                mapsAreaPointerMove
            );

            viewport.addEventListener(
                "mousedown",
                event => {

                    if (
                        !mapsState.selected
                        ||
                        mapsState.view.areaSelecting
                        ||
                        event.button !== 0
                    ) {
                        return;
                    }


                    mapsState.view.dragging =
                        true;

                    mapsState.view.startX =
                        event.clientX
                        -
                        mapsState.view.x;

                    mapsState.view.startY =
                        event.clientY
                        -
                        mapsState.view.y;


                    viewport.classList.add(
                        "dragging"
                    );
                }
            );


            viewport.addEventListener(
                "wheel",
                event => {

                    if (!mapsState.selected) {
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
        }


        window.addEventListener(
            "mousemove",
            event => {

                if (
                    !mapsState.view.dragging
                ) {
                    return;
                }


                mapsState.view.x =
                    event.clientX
                    -
                    mapsState.view.startX;

                mapsState.view.y =
                    event.clientY
                    -
                    mapsState.view.startY;


                applyMapView();
            }
        );


        window.addEventListener(
            "mouseup",
            () => {

                mapsState.view.dragging =
                    false;


                if (viewport) {

                    viewport.classList.remove(
                        "dragging"
                    );
                }
            }
        );


        setActionState();

        checkMapsConnection();

        window.setInterval(
            checkMapsConnection,
            3000
        );
    }
);
