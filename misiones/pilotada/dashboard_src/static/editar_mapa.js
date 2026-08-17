const $e = id =>
    document.getElementById(id);


const E = {
    name: window.SAFEVISION_EDITOR_MAP,

    canvas: null,
    ctx: null,

    width: 0,
    height: 0,

    tool: "draw",
    color: 254,
    brush: 5,

    drawing: false,
    panning: false,

    lastX: 0,
    lastY: 0,

    panStartX: 0,
    panStartY: 0,

    scale: 1,
    panX: 0,
    panY: 0,

    history: [],
    maxHistory: 20,

    loaded: false,
    dirty: false,
    saving: false
};


// =========================================================
// UI
// =========================================================

function status(text) {

    $e("editorStatus").textContent =
        text;
}


function dirty(value) {

    E.dirty =
        Boolean(value);


    const label =
        $e("editorDirty");


    label.textContent =
        E.dirty
            ?
            "Cambios sin guardar"
            :
            "Sin cambios";


    label.classList.toggle(
        "dirty",
        E.dirty
    );


    $e("saveButton").disabled =
        !E.loaded
        ||
        !E.dirty
        ||
        E.saving;
}


async function checkConnection() {

    const badge =
        $e("editorConnection");


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


        const ok =
            Boolean(
                response.ok
                &&
                data.connected
            );


        badge.textContent =
            ok
                ?
                "● CONECTADO"
                :
                "● DESCONECTADO";


        badge.classList.toggle(
            "editor-on",
            ok
        );

        badge.classList.toggle(
            "editor-off",
            !ok
        );


    } catch (_) {

        badge.textContent =
            "● DESCONECTADO";

        badge.classList.remove(
            "editor-on"
        );

        badge.classList.add(
            "editor-off"
        );
    }
}


// =========================================================
// VISTA
// =========================================================

function applyView() {

    $e("editorScene").style.transform =
        (
            "translate(-50%, -50%) "
            +
            "translate("
            +
            E.panX
            +
            "px, "
            +
            E.panY
            +
            "px) "
            +
            "scale("
            +
            E.scale
            +
            ")"
        );
}


function fitView() {

    const viewport =
        $e("editorViewport");


    if (
        !E.loaded
        ||
        !viewport
    ) {
        return;
    }


    const availableW =
        Math.max(
            100,
            viewport.clientWidth - 50
        );

    const availableH =
        Math.max(
            100,
            viewport.clientHeight - 50
        );


    E.scale =
        Math.min(
            availableW / E.width,
            availableH / E.height,
            4
        );


    E.panX = 0;
    E.panY = 0;


    applyView();
}


function zoom(factor) {

    E.scale *= factor;

    E.scale =
        Math.max(
            0.2,
            Math.min(
                20,
                E.scale
            )
        );

    applyView();
}


// =========================================================
// HERRAMIENTAS
// =========================================================

function setTool(tool) {

    E.tool = tool;


    $e("toolDraw")
    .classList.toggle(
        "active",
        tool === "draw"
    );


    $e("toolPan")
    .classList.toggle(
        "active",
        tool === "pan"
    );


    $e("editorViewport")
    .classList.toggle(
        "pan-mode",
        tool === "pan"
    );
}


function setColor(
    value,
    activeId
) {

    E.color = value;

    setTool("draw");


    for (const id of [
        "colorFree",
        "colorWall",
        "colorUnknown"
    ]) {

        $e(id)
        .classList.toggle(
            "active",
            id === activeId
        );
    }
}


// =========================================================
// PIXELES / HISTORIAL
// =========================================================

function captureGray() {

    const image =
        E.ctx.getImageData(
            0,
            0,
            E.width,
            E.height
        );


    const gray =
        new Uint8Array(
            E.width * E.height
        );


    for (
        let p = 0, i = 0;
        p < gray.length;
        p += 1, i += 4
    ) {

        gray[p] =
            image.data[i];
    }


    return gray;
}


function restoreGray(gray) {

    const image =
        E.ctx.createImageData(
            E.width,
            E.height
        );


    for (
        let p = 0, i = 0;
        p < gray.length;
        p += 1, i += 4
    ) {

        const v = gray[p];

        image.data[i] = v;
        image.data[i + 1] = v;
        image.data[i + 2] = v;
        image.data[i + 3] = 255;
    }


    E.ctx.putImageData(
        image,
        0,
        0
    );
}


function pushHistory() {

    E.history.push(
        captureGray()
    );


    if (
        E.history.length
        >
        E.maxHistory
    ) {

        E.history.shift();
    }


    $e("undoButton").disabled =
        E.history.length <= 1;
}


function undo() {

    if (
        E.history.length
        <=
        1
    ) {
        return;
    }


    E.history.pop();


    restoreGray(
        E.history[
            E.history.length - 1
        ]
    );


    dirty(
        E.history.length > 1
    );


    $e("undoButton").disabled =
        E.history.length <= 1;


    status(
        "Cambio deshecho."
    );
}


// =========================================================
// DIBUJO
// =========================================================

function eventToPixel(event) {

    const rect =
        E.canvas
        .getBoundingClientRect();


    return {
        x:
            Math.max(
                0,
                Math.min(
                    E.width - 1,
                    Math.floor(
                        (
                            event.clientX
                            -
                            rect.left
                        )
                        *
                        E.width
                        /
                        rect.width
                    )
                )
            ),

        y:
            Math.max(
                0,
                Math.min(
                    E.height - 1,
                    Math.floor(
                        (
                            event.clientY
                            -
                            rect.top
                        )
                        *
                        E.height
                        /
                        rect.height
                    )
                )
            )
    };
}


function paintPixel(x, y) {

    const radius =
        Math.floor(
            E.brush / 2
        );


    const x0 =
        Math.max(
            0,
            x - radius
        );

    const y0 =
        Math.max(
            0,
            y - radius
        );

    const x1 =
        Math.min(
            E.width - 1,
            x + radius
        );

    const y1 =
        Math.min(
            E.height - 1,
            y + radius
        );


    const v =
        E.color;


    E.ctx.fillStyle =
        "rgb("
        +
        v
        +
        ","
        +
        v
        +
        ","
        +
        v
        +
        ")";


    E.ctx.fillRect(
        x0,
        y0,
        x1 - x0 + 1,
        y1 - y0 + 1
    );
}


function paintLine(
    x0,
    y0,
    x1,
    y1
) {

    const dx =
        Math.abs(
            x1 - x0
        );

    const dy =
        Math.abs(
            y1 - y0
        );


    const sx =
        x0 < x1
            ?
            1
            :
            -1;

    const sy =
        y0 < y1
            ?
            1
            :
            -1;


    let err =
        dx - dy;


    while (true) {

        paintPixel(
            x0,
            y0
        );


        if (
            x0 === x1
            &&
            y0 === y1
        ) {
            break;
        }


        const e2 =
            2 * err;


        if (e2 > -dy) {

            err -= dy;
            x0 += sx;
        }


        if (e2 < dx) {

            err += dx;
            y0 += sy;
        }
    }
}


// =========================================================
// MOUSE
// =========================================================

function beginPan(event) {

    E.panning = true;

    E.panStartX =
        event.clientX - E.panX;

    E.panStartY =
        event.clientY - E.panY;


    $e("editorViewport")
    .classList.add(
        "dragging"
    );


    event.preventDefault();
}


function mouseDown(event) {

    if (!E.loaded) {
        return;
    }


    if (
        event.button === 2
        ||
        E.tool === "pan"
    ) {

        beginPan(event);

        return;
    }


    if (event.button !== 0) {
        return;
    }


    const point =
        eventToPixel(event);


    E.drawing = true;

    E.lastX = point.x;
    E.lastY = point.y;


    paintPixel(
        point.x,
        point.y
    );


    dirty(true);

    event.preventDefault();
}


function mouseMove(event) {

    if (E.panning) {

        E.panX =
            event.clientX
            -
            E.panStartX;

        E.panY =
            event.clientY
            -
            E.panStartY;


        applyView();

        return;
    }


    if (!E.drawing) {
        return;
    }


    const point =
        eventToPixel(event);


    paintLine(
        E.lastX,
        E.lastY,
        point.x,
        point.y
    );


    E.lastX = point.x;
    E.lastY = point.y;
}


function mouseUp() {

    if (E.drawing) {

        E.drawing = false;

        pushHistory();

        status(
            "Cambio aplicado."
        );
    }


    if (E.panning) {

        E.panning = false;

        $e("editorViewport")
        .classList.remove(
            "dragging"
        );
    }
}


// =========================================================
// PGM
// =========================================================

function buildPGM() {

    const gray =
        captureGray();


    const header =
        (
            "P5\n"
            +
            E.width
            +
            " "
            +
            E.height
            +
            "\n255\n"
        );


    const headerBytes =
        new TextEncoder()
        .encode(
            header
        );


    const result =
        new Uint8Array(
            headerBytes.length
            +
            gray.length
        );


    result.set(
        headerBytes,
        0
    );


    result.set(
        gray,
        headerBytes.length
    );


    return result;
}


// =========================================================
// GUARDAR
// =========================================================

async function saveMap() {

    if (
        !E.loaded
        ||
        !E.dirty
        ||
        E.saving
    ) {
        return;
    }


    E.saving = true;

    $e("saveButton").disabled =
        true;


    status(
        "Guardando mapa..."
    );


    try {

        const response =
            await fetch(
                "/maps/edit/"
                +
                encodeURIComponent(
                    E.name
                ),
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/x-portable-graymap"
                    },

                    body:
                        buildPGM()
                }
            );


        let data = {};


        const responseText =
            await response.text();


        try {

            data =
                responseText
                    ?
                    JSON.parse(
                        responseText
                    )
                    :
                    {};

        } catch (parseError) {

            throw new Error(
                (
                    "Respuesta inválida del servidor "
                    +
                    "(HTTP "
                    +
                    response.status
                    +
                    ")."
                )
            );
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
                (
                    "Error al guardar "
                    +
                    "(HTTP "
                    +
                    response.status
                    +
                    ")."
                )
            );
        }


        E.history = [];

        pushHistory();

        dirty(false);


        status(
            "Mapa guardado correctamente. Volviendo..."
        );


        window.setTimeout(
            () => {

                window.location.href =
                    (
                        "/mapas?map="
                        +
                        encodeURIComponent(
                            E.name
                        )
                    );

            },
            650
        );


    } catch (error) {

        status(
            "Error: "
            +
            error.message
        );


    } finally {

        E.saving = false;

        dirty(E.dirty);
    }
}


// =========================================================
// CARGA
// =========================================================

function loadMap() {

    const image =
        new Image();


    image.onload =
        () => {

            E.width =
                image.naturalWidth;

            E.height =
                image.naturalHeight;


            E.canvas.width =
                E.width;

            E.canvas.height =
                E.height;


            E.ctx.imageSmoothingEnabled =
                false;


            E.ctx.drawImage(
                image,
                0,
                0
            );


            E.loaded = true;

            E.history = [];

            pushHistory();

            dirty(false);


            $e("editorLoading").hidden =
                true;

            $e("editorScene").hidden =
                false;


            window.requestAnimationFrame(
                fitView
            );


            status(
                "Editor listo · "
                +
                E.width
                +
                " × "
                +
                E.height
                +
                " px"
            );
        };


    image.onerror =
        () => {

            $e("editorLoading")
            .textContent =
                "No se pudo cargar el mapa.";

            status(
                "Error cargando mapa."
            );
        };


    image.src =
        "/map_image/"
        +
        encodeURIComponent(
            E.name
        )
        +
        "?t="
        +
        Date.now();
}


// =========================================================
// INICIO
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        E.canvas =
            $e("editorCanvas");

        E.ctx =
            E.canvas.getContext(
                "2d",
                {
                    willReadFrequently:
                        true
                }
            );


        $e("toolDraw").onclick =
            () => setTool("draw");

        $e("toolPan").onclick =
            () => setTool("pan");

        $e("colorFree").onclick =
            () => setColor(
                254,
                "colorFree"
            );

        $e("colorWall").onclick =
            () => setColor(
                0,
                "colorWall"
            );

        $e("colorUnknown").onclick =
            () => setColor(
                205,
                "colorUnknown"
            );


        $e("brushSize").oninput =
            event => {

                E.brush =
                    Number(
                        event.target.value
                    );

                $e("brushValue")
                .textContent =
                    String(E.brush);
            };


        $e("undoButton").onclick =
            undo;


        $e("zoomOut").onclick =
            () => zoom(0.8);

        $e("zoomIn").onclick =
            () => zoom(1.2);

        $e("resetView").onclick =
            fitView;


        $e("saveButton").onclick =
            saveMap;


        $e("cancelButton").onclick =
            () => {

                if (
                    E.dirty
                    &&
                    !window.confirm(
                        "Hay cambios sin guardar. ¿Salir?"
                    )
                ) {
                    return;
                }


                window.location.href =
                    "/mapas";
            };


        E.canvas.addEventListener(
            "mousedown",
            mouseDown
        );


        window.addEventListener(
            "mousemove",
            mouseMove
        );


        window.addEventListener(
            "mouseup",
            mouseUp
        );


        E.canvas.addEventListener(
            "contextmenu",
            event => {
                event.preventDefault();
            }
        );


        $e("editorViewport")
        .addEventListener(
            "wheel",
            event => {

                event.preventDefault();

                zoom(
                    event.deltaY < 0
                        ?
                        1.1
                        :
                        0.9
                );
            },
            {
                passive: false
            }
        );


        document.addEventListener(
            "keydown",
            event => {

                const key =
                    event.key.toLowerCase();


                if (
                    event.ctrlKey
                    &&
                    key === "z"
                ) {

                    event.preventDefault();
                    undo();

                } else if (
                    event.ctrlKey
                    &&
                    key === "s"
                ) {

                    event.preventDefault();
                    saveMap();

                } else if (
                    key === "1"
                ) {

                    setColor(
                        254,
                        "colorFree"
                    );

                } else if (
                    key === "2"
                ) {

                    setColor(
                        0,
                        "colorWall"
                    );

                } else if (
                    key === "e"
                ) {

                    setColor(
                        205,
                        "colorUnknown"
                    );

                } else if (
                    key === "m"
                ) {

                    setTool(
                        E.tool === "draw"
                            ?
                            "pan"
                            :
                            "draw"
                    );
                }
            }
        );


        checkConnection();

        window.setInterval(
            checkConnection,
            3000
        );


        loadMap();
    }
);
