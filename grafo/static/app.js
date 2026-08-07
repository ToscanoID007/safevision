let cy = null;
let graphData = null;

let hiddenNodeIds = new Set();
let selectedNodeId = null;


// =========================================================
// COLORES
// =========================================================

const COLORS = {
    ".py": "#4F81BD",
    ".sh": "#6AA84F",
    ".bat": "#8E7CC3",
    ".ps1": "#674EA7",
    ".js": "#F1C232",
    ".html": "#E69138",
    ".css": "#C27BA0",
    ".json": "#CC4125",
    ".yaml": "#3D85C6",
    ".yml": "#3D85C6",
    ".txt": "#999999",
    ".cfg": "#999999",
    ".ini": "#999999",

    ".pt": "#111111",
    ".torchscript": "#222222",
    ".onnx": "#444444"
};


// =========================================================
// UTILIDADES
// =========================================================

function escaparHTML(valor) {

    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatearBytes(bytes) {

    if (bytes === 0) {
        return "0 bytes";
    }

    if (!bytes) {
        return "N/A";
    }

    const unidades = [
        "bytes",
        "KB",
        "MB",
        "GB"
    ];

    const indice = Math.min(
        unidades.length - 1,

        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        )
    );

    const valor =
        bytes /
        Math.pow(
            1024,
            indice
        );

    return (
        valor.toFixed(
            indice === 0
                ? 0
                : 2
        ) +
        " " +
        unidades[indice]
    );
}


function limitar(
    valor,
    minimo,
    maximo
) {

    return Math.max(
        minimo,
        Math.min(
            maximo,
            valor
        )
    );
}


// =========================================================
// ESTADÍSTICAS
// =========================================================

function actualizarEstadisticas() {

    if (!graphData) {
        return;
    }

    const total =
        graphData.nodes.length;

    const ocultos =
        hiddenNodeIds.size;

    const visibles =
        total - ocultos;

    document
        .getElementById(
            "graph-stats"
        )
        .textContent =
            `${total} archivos · ` +
            `${graphData.edges.length} relaciones · ` +
            `${visibles} visibles`;

    document
        .getElementById(
            "nodes-counter"
        )
        .textContent =
            `${visibles}/${total}`;
}


// =========================================================
// VISIBILIDAD DE NODOS
// =========================================================

function aplicarVisibilidad() {

    if (!cy) {
        return;
    }


    cy.nodes().forEach(
        nodo => {

            if (
                hiddenNodeIds.has(
                    nodo.id()
                )
            ) {

                nodo.addClass(
                    "node-hidden"
                );

            } else {

                nodo.removeClass(
                    "node-hidden"
                );
            }

        }
    );


    cy.edges().forEach(
        edge => {

            const sourceId =
                edge.source().id();

            const targetId =
                edge.target().id();

            if (
                hiddenNodeIds.has(sourceId) ||
                hiddenNodeIds.has(targetId)
            ) {

                edge.addClass(
                    "edge-hidden"
                );

            } else {

                edge.removeClass(
                    "edge-hidden"
                );
            }

        }
    );


    actualizarEstadisticas();

    reconstruirListaNodos(
        document
            .getElementById(
                "search"
            )
            .value
    );
}


function ocultarNodo(id) {

    hiddenNodeIds.add(
        id
    );

    aplicarVisibilidad();


    if (
        selectedNodeId === id
    ) {

        selectedNodeId = null;

        cy.elements()
            .unselect();

        cy.elements()
            .removeClass(
                "related-node related-edge"
            );

        document
            .getElementById(
                "info"
            )
            .innerHTML = `
                <div class="info-section">
                    El nodo fue ocultado.
                    Puedes volver a mostrarlo desde
                    la lista de archivos de la izquierda.
                </div>
            `;
    }
}


function mostrarNodoOculto(id) {

    hiddenNodeIds.delete(
        id
    );

    aplicarVisibilidad();
}


function alternarVisibilidadNodo(id) {

    if (
        hiddenNodeIds.has(id)
    ) {

        mostrarNodoOculto(
            id
        );

    } else {

        ocultarNodo(
            id
        );
    }
}


function ocultarTodos() {

    if (!graphData) {
        return;
    }

    hiddenNodeIds =
        new Set(
            graphData.nodes.map(
                n => n.id
            )
        );

    selectedNodeId =
        null;

    cy.elements()
        .unselect();

    cy.elements()
        .removeClass(
            "related-node related-edge search-match"
        );

    document
        .getElementById(
            "info"
        )
        .innerHTML = `
            <div class="info-section">
                Todos los nodos están ocultos.
                Usa <strong>Mostrar todo</strong>
                o los botones 👁 de la lista izquierda.
            </div>
        `;

    aplicarVisibilidad();
}


function mostrarTodos() {

    hiddenNodeIds.clear();

    aplicarVisibilidad();

    setTimeout(
        () => {

            if (!cy) {
                return;
            }

            cy.resize();

            cy.fit(
                cy.elements(),
                80
            );

        },
        50
    );
}


// =========================================================
// LISTA IZQUIERDA
// =========================================================

function reconstruirListaNodos(
    filtro = ""
) {

    if (!graphData) {
        return;
    }

    const texto =
        String(filtro || "")
            .trim()
            .toLowerCase();


    const nodos =
        [...graphData.nodes]
            .sort(
                (a, b) =>
                    a.name.localeCompare(
                        b.name
                    )
            )
            .filter(
                nodo => {

                    if (!texto) {
                        return true;
                    }

                    return (
                        nodo.name
                            .toLowerCase()
                            .includes(texto) ||

                        nodo.id
                            .toLowerCase()
                            .includes(texto)
                    );
                }
            );


    const contenedor =
        document.getElementById(
            "nodes-list"
        );


    if (
        nodos.length === 0
    ) {

        contenedor.innerHTML = `
            <div
                style="
                    padding:15px;
                    color:#888;
                    font-size:12px;
                "
            >
                No hay archivos que coincidan.
            </div>
        `;

        return;
    }


    contenedor.innerHTML =
        nodos.map(
            nodo => {

                const oculto =
                    hiddenNodeIds.has(
                        nodo.id
                    );

                const seleccionado =
                    selectedNodeId ===
                    nodo.id;

                return `

                    <div
                        class="
                            node-list-item
                            ${oculto ? "hidden-node-item" : ""}
                            ${seleccionado ? "selected-list-node" : ""}
                        "
                    >

                        <div
                            class="node-list-main"
                            data-node-open="${escaparHTML(nodo.id)}"
                            title="${escaparHTML(nodo.id)}"
                        >

                            <span class="node-list-name">
                                ${escaparHTML(nodo.name)}
                            </span>

                            <span class="node-list-path">
                                ${escaparHTML(nodo.id)}
                            </span>

                        </div>


                        <button
                            class="node-list-toggle"
                            data-node-toggle="${escaparHTML(nodo.id)}"
                            title="${
                                oculto
                                    ? "Mostrar nodo"
                                    : "Ocultar nodo"
                            }"
                        >
                            ${
                                oculto
                                    ? "🚫"
                                    : "👁"
                            }
                        </button>

                    </div>
                `;
            }
        )
        .join("");


    // -----------------------------------------------------
    // ABRIR NODO DESDE LA LISTA
    // -----------------------------------------------------

    document
        .querySelectorAll(
            "[data-node-open]"
        )
        .forEach(
            elemento => {

                elemento.addEventListener(
                    "click",
                    () => {

                        const id =
                            elemento.dataset.nodeOpen;

                        abrirNodoDesdeLista(
                            id
                        );
                    }
                );
            }
        );


    // -----------------------------------------------------
    // BOTÓN OCULTAR / MOSTRAR
    // -----------------------------------------------------

    document
        .querySelectorAll(
            "[data-node-toggle]"
        )
        .forEach(
            boton => {

                boton.addEventListener(
                    "click",
                    evento => {

                        evento.stopPropagation();

                        const id =
                            boton.dataset.nodeToggle;

                        alternarVisibilidadNodo(
                            id
                        );
                    }
                );
            }
        );
}


function abrirNodoDesdeLista(id) {

    if (!cy) {
        return;
    }


    // Si estaba oculto, lo mostramos
    // automáticamente.

    if (
        hiddenNodeIds.has(id)
    ) {

        hiddenNodeIds.delete(
            id
        );

        aplicarVisibilidad();
    }


    const nodo =
        cy.getElementById(
            id
        );


    if (
        !nodo ||
        nodo.length === 0
    ) {
        return;
    }


    cy.elements()
        .unselect();

    nodo.select();


    cy.animate(
        {

            center: {
                eles:
                    nodo
            },

            zoom:
                Math.max(
                    cy.zoom(),
                    1.15
                )

        },
        {
            duration:
                300
        }
    );


    mostrarNodo(
        nodo
    );
}


// =========================================================
// LAYOUT
// =========================================================

function crearLayout(
    animar = true,
    randomizar = true
) {

    return {

        name:
            "cose",

        animate:
            animar,

        animationDuration:
            700,

        randomize:
            randomizar,

        fit:
            true,

        padding:
            90,

        nodeRepulsion:
            function () {
                return 180000;
            },

        nodeOverlap:
            55,

        idealEdgeLength:
            function () {
                return 145;
            },

        edgeElasticity:
            function () {
                return 90;
            },

        nestingFactor:
            1.2,

        gravity:
            0.14,

        numIter:
            1800,

        initialTemp:
            1000,

        coolingFactor:
            0.95,

        minTemp:
            1.0,

        componentSpacing:
            140
    };
}


function reordenarGrafo() {

    if (!cy) {
        return;
    }

    cy.elements()
        .removeClass(
            "related-node related-edge search-match"
        );

    cy.layout(
        crearLayout(
            true,
            true
        )
    ).run();
}


// =========================================================
// RELACIONES
// =========================================================

function obtenerRelaciones(nodo) {

    const relaciones = [];


    nodo.connectedEdges().forEach(
        edge => {

            const source =
                edge.source();

            const target =
                edge.target();

            const tipo =
                edge.data("type") ||
                "reference";


            if (
                source.id() ===
                nodo.id()
            ) {

                relaciones.push({

                    direccion:
                        "saliente",

                    simbolo:
                        "→",

                    tipo:
                        tipo,

                    nodo:
                        target
                });

            } else {

                relaciones.push({

                    direccion:
                        "entrante",

                    simbolo:
                        "←",

                    tipo:
                        tipo,

                    nodo:
                        source
                });
            }

        }
    );


    relaciones.sort(
        (a, b) =>
            a.nodo
                .data("label")
                .localeCompare(
                    b.nodo.data(
                        "label"
                    )
                )
    );


    return relaciones;
}


function resaltarNodo(nodo) {

    cy.elements()
        .removeClass(
            "related-node related-edge"
        );


    nodo
        .connectedEdges()
        .filter(
            edge =>
                !hiddenNodeIds.has(
                    edge.source().id()
                ) &&
                !hiddenNodeIds.has(
                    edge.target().id()
                )
        )
        .addClass(
            "related-edge"
        );


    nodo
        .neighborhood("node")
        .filter(
            n =>
                !hiddenNodeIds.has(
                    n.id()
                )
        )
        .addClass(
            "related-node"
        );
}


// =========================================================
// MOSTRAR INFORMACIÓN
// =========================================================

async function mostrarNodo(nodo) {

    selectedNodeId =
        nodo.id();

    reconstruirListaNodos(
        document
            .getElementById(
                "search"
            )
            .value
    );


    const n =
        nodo.data();


    resaltarNodo(
        nodo
    );


    const relaciones =
        obtenerRelaciones(
            nodo
        );


    let htmlRelaciones = "";


    if (
        relaciones.length === 0
    ) {

        htmlRelaciones = `
            <div class="empty-message">
                No se detectaron relaciones para este archivo.
            </div>
        `;

    } else {

        htmlRelaciones =
            relaciones
                .map(
                    rel => {

                        const oculto =
                            hiddenNodeIds.has(
                                rel.nodo.id()
                            );

                        return `

                            <div
                                class="relation-item"
                                data-node-id="${escaparHTML(rel.nodo.id())}"
                            >

                                <span class="relation-arrow">
                                    ${rel.simbolo}
                                </span>

                                <span class="relation-name">
                                    ${escaparHTML(rel.nodo.data("label"))}
                                    ${
                                        oculto
                                            ? " 🚫"
                                            : ""
                                    }
                                </span>

                                <span class="relation-type">
                                    ${escaparHTML(rel.tipo)}
                                </span>

                            </div>
                        `;
                    }
                )
                .join("");
    }


    const info =
        document.getElementById(
            "info"
        );


    info.innerHTML = `

        <div class="info-section">

            <div class="section-title">
                Archivo
            </div>


            <div class="info-item">

                <div class="info-title">
                    Nombre
                </div>

                <div class="info-value">
                    ${escaparHTML(n.label)}
                </div>

            </div>


            <div class="info-item">

                <div class="info-title">
                    ID
                </div>

                <div class="info-value path-value">
                    ${escaparHTML(n.id)}
                </div>

            </div>


            <div class="info-item">

                <div class="info-title">
                    Ruta
                </div>

                <div class="info-value path-value">
                    ${escaparHTML(n.path)}
                </div>

            </div>


            <div class="info-grid">

                <div class="info-item">

                    <div class="info-title">
                        Extensión
                    </div>

                    <div class="info-value">
                        ${escaparHTML(n.ext || "sin extensión")}
                    </div>

                </div>


                <div class="info-item">

                    <div class="info-title">
                        Tamaño
                    </div>

                    <div class="info-value">
                        ${escaparHTML(formatearBytes(n.size))}
                    </div>

                </div>

            </div>


            <div class="info-item">

                <div class="info-title">
                    Modificado
                </div>

                <div class="info-value">
                    ${escaparHTML(n.modified)}
                </div>

            </div>


            <div class="node-actions">

                <button
                    id="hide-selected-node"
                    class="node-action-button danger"
                    type="button"
                >
                    🚫 Ocultar nodo
                </button>

            </div>

        </div>


        <div class="info-section">

            <div class="section-title">

                Relaciones

                <span class="section-counter">
                    ${relaciones.length}
                </span>

            </div>

            <div id="relations-list">
                ${htmlRelaciones}
            </div>

        </div>


        <div class="info-section">

            <div class="section-title">
                Contenido
            </div>

            <div id="code-status">
                Cargando archivo...
            </div>

            <pre id="code-view"></pre>

        </div>
    `;


    // -----------------------------------------------------
    // OCULTAR NODO SELECCIONADO
    // -----------------------------------------------------

    document
        .getElementById(
            "hide-selected-node"
        )
        .addEventListener(
            "click",
            function () {

                ocultarNodo(
                    n.id
                );
            }
        );


    // -----------------------------------------------------
    // RELACIONES CLICABLES
    // -----------------------------------------------------

    document
        .querySelectorAll(
            ".relation-item"
        )
        .forEach(
            elemento => {

                elemento.addEventListener(
                    "click",
                    () => {

                        const id =
                            elemento.dataset.nodeId;

                        abrirNodoDesdeLista(
                            id
                        );
                    }
                );
            }
        );


    // -----------------------------------------------------
    // SOLICITAR CÓDIGO
    // -----------------------------------------------------

    const codeStatus =
        document.getElementById(
            "code-status"
        );

    const codeView =
        document.getElementById(
            "code-view"
        );


    try {

        const respuesta =
            await fetch(
                `/code?id=${encodeURIComponent(n.id)}`
            );


        const resultado =
            await respuesta.json();


        if (
            !respuesta.ok ||
            !resultado.ok
        ) {

            codeStatus.textContent =
                resultado.error ||
                "No se pudo leer el archivo.";

            codeView.textContent =
                "";

            return;
        }


        if (
            !resultado.readable
        ) {

            codeStatus.textContent =
                resultado.message ||
                "Archivo no disponible como texto.";

            codeView.textContent =
                "";

            return;
        }


        const lineas =
            resultado.code === ""
                ? 0
                : resultado.code
                    .split("\n")
                    .length;


        codeStatus.textContent =
            `${lineas} líneas`;


        codeView.textContent =
            resultado.code;

    } catch (error) {

        codeStatus.textContent =
            "Error de comunicación con el servidor.";

        codeView.textContent =
            String(error);
    }
}


// =========================================================
// ZOOM
// =========================================================

function zoomCentro(factor) {

    if (!cy) {
        return;
    }

    const contenedor =
        document.getElementById(
            "graph"
        );


    const nivel =
        limitar(
            cy.zoom() * factor,
            cy.minZoom(),
            cy.maxZoom()
        );


    cy.zoom({

        level:
            nivel,

        renderedPosition: {

            x:
                contenedor.clientWidth / 2,

            y:
                contenedor.clientHeight / 2
        }

    });
}


// =========================================================
// TOUCHPAD
// =========================================================

function configurarTouchpad() {

    const graph =
        document.getElementById(
            "graph"
        );


    graph.addEventListener(
        "wheel",
        function (evento) {

            if (!cy) {
                return;
            }


            evento.preventDefault();


            let dx =
                evento.deltaX;

            let dy =
                evento.deltaY;


            if (
                evento.deltaMode === 1
            ) {

                dx *= 16;
                dy *= 16;
            }


            if (
                evento.deltaMode === 2
            ) {

                dx *=
                    graph.clientWidth;

                dy *=
                    graph.clientHeight;
            }


            // PELLIZCO / CTRL + RUEDA

            if (
                evento.ctrlKey
            ) {

                const rect =
                    graph
                        .getBoundingClientRect();


                const intensidad =
                    Math.exp(
                        -dy * 0.006
                    );


                const nivel =
                    limitar(
                        cy.zoom() *
                        intensidad,
                        cy.minZoom(),
                        cy.maxZoom()
                    );


                cy.zoom({

                    level:
                        nivel,

                    renderedPosition: {

                        x:
                            evento.clientX -
                            rect.left,

                        y:
                            evento.clientY -
                            rect.top
                    }

                });


                return;
            }


            // DOS DEDOS = PAN

            const pan =
                cy.pan();


            cy.pan({

                x:
                    pan.x - dx,

                y:
                    pan.y - dy
            });

        },
        {
            passive: false
        }
    );
}


// =========================================================
// PANEL DERECHO REDIMENSIONABLE
// =========================================================

function configurarSidebarRedimensionable() {

    const resizer =
        document.getElementById(
            "sidebar-resizer"
        );


    let inicioX = 0;
    let anchoInicial = 0;
    let activo = false;


    resizer.addEventListener(
        "pointerdown",
        function (evento) {

            activo = true;

            inicioX =
                evento.clientX;


            anchoInicial =
                document
                    .getElementById(
                        "sidebar"
                    )
                    .getBoundingClientRect()
                    .width;


            document.body
                .classList
                .add(
                    "resizing-sidebar"
                );


            resizer.setPointerCapture(
                evento.pointerId
            );
        }
    );


    resizer.addEventListener(
        "pointermove",
        function (evento) {

            if (!activo) {
                return;
            }


            const diferencia =
                inicioX -
                evento.clientX;


            const maximo =
                Math.min(
                    900,
                    window.innerWidth * 0.72
                );


            const nuevoAncho =
                limitar(
                    anchoInicial +
                    diferencia,
                    300,
                    maximo
                );


            document
                .documentElement
                .style
                .setProperty(
                    "--sidebar-width",
                    `${nuevoAncho}px`
                );


            if (cy) {
                cy.resize();
            }
        }
    );


    function terminarResize(evento) {

        if (!activo) {
            return;
        }


        activo = false;


        document.body
            .classList
            .remove(
                "resizing-sidebar"
            );


        try {

            resizer.releasePointerCapture(
                evento.pointerId
            );

        } catch (_) {
        }


        if (cy) {
            cy.resize();
        }
    }


    resizer.addEventListener(
        "pointerup",
        terminarResize
    );


    resizer.addEventListener(
        "pointercancel",
        terminarResize
    );
}


// =========================================================
// CARGAR GRAFO
// =========================================================

async function cargarGrafo() {

    const respuesta =
        await fetch(
            "/files"
        );


    graphData =
        await respuesta.json();


    const elementos = [];


    // -----------------------------------------------------
    // NODOS
    // -----------------------------------------------------

    graphData.nodes.forEach(
        n => {

            elementos.push({

                data: {

                    id:
                        n.id,

                    label:
                        n.name,

                    path:
                        n.path,

                    ext:
                        n.ext,

                    size:
                        n.size,

                    modified:
                        n.modified,

                    color:
                        COLORS[n.ext] ||
                        "#888888"
                }

            });
        }
    );


    // -----------------------------------------------------
    // ARISTAS
    // -----------------------------------------------------

    graphData.edges.forEach(
        (e, index) => {

            elementos.push({

                data: {

                    id:
                        `edge-${index}`,

                    source:
                        e.source,

                    target:
                        e.target,

                    type:
                        e.type
                }

            });
        }
    );


    // -----------------------------------------------------
    // CYTOSCAPE
    // -----------------------------------------------------

    cy = cytoscape({

        container:
            document.getElementById(
                "graph"
            ),

        elements:
            elementos,

        minZoom:
            0.12,

        maxZoom:
            4.5,

        userZoomingEnabled:
            false,

        userPanningEnabled:
            true,

        boxSelectionEnabled:
            false,

        autoungrabify:
            false,


        style: [

            {
                selector:
                    "node",

                style: {

                    "label":
                        "data(label)",

                    "width":
                        30,

                    "height":
                        30,

                    "font-size":
                        "10px",

                    "font-weight":
                        500,

                    "text-valign":
                        "bottom",

                    "text-halign":
                        "center",

                    "text-margin-y":
                        8,

                    "text-wrap":
                        "wrap",

                    "text-max-width":
                        "130px",

                    "text-background-color":
                        "#ffffff",

                    "text-background-opacity":
                        0.82,

                    "text-background-padding":
                        "2px",

                    "background-color":
                        "data(color)",

                    "color":
                        "#222222",

                    "border-width":
                        1.5,

                    "border-color":
                        "#666666",

                    "overlay-opacity":
                        0
                }
            },


            {
                selector:
                    "edge",

                style: {

                    "width":
                        1.3,

                    "curve-style":
                        "bezier",

                    "target-arrow-shape":
                        "triangle",

                    "arrow-scale":
                        0.72,

                    "line-color":
                        "#c4c4c4",

                    "target-arrow-color":
                        "#c4c4c4",

                    "opacity":
                        0.68
                }
            },


            {
                selector:
                    ".node-hidden",

                style: {
                    "display":
                        "none"
                }
            },


            {
                selector:
                    ".edge-hidden",

                style: {
                    "display":
                        "none"
                }
            },


            {
                selector:
                    "node:selected",

                style: {

                    "border-width":
                        5,

                    "border-color":
                        "#D32F2F",

                    "z-index":
                        9999
                }
            },


            {
                selector:
                    ".related-node",

                style: {

                    "border-width":
                        4,

                    "border-color":
                        "#FF9800",

                    "z-index":
                        9000
                }
            },


            {
                selector:
                    ".related-edge",

                style: {

                    "width":
                        3.5,

                    "line-color":
                        "#FF9800",

                    "target-arrow-color":
                        "#FF9800",

                    "opacity":
                        1,

                    "z-index":
                        8000
                }
            },


            {
                selector:
                    ".search-match",

                style: {

                    "border-width":
                        5,

                    "border-color":
                        "#FFD600",

                    "background-color":
                        "#FFF176",

                    "z-index":
                        9500
                }
            }

        ],


        layout:
            crearLayout(
                true,
                true
            )

    });


    actualizarEstadisticas();

    reconstruirListaNodos();


    // -----------------------------------------------------
    // CLICK EN NODO
    // -----------------------------------------------------

    cy.on(
        "tap",
        "node",
        function (evt) {

            mostrarNodo(
                evt.target
            );
        }
    );


    // -----------------------------------------------------
    // CLICK EN FONDO
    // -----------------------------------------------------

    cy.on(
        "tap",
        function (evt) {

            if (
                evt.target === cy
            ) {

                selectedNodeId =
                    null;


                cy.elements()
                    .unselect();


                cy.elements()
                    .removeClass(
                        "related-node related-edge"
                    );


                reconstruirListaNodos(
                    document
                        .getElementById(
                            "search"
                        )
                        .value
                );
            }
        }
    );


    window.addEventListener(
        "resize",
        function () {

            if (cy) {
                cy.resize();
            }
        }
    );
}


// =========================================================
// BUSCADOR
// =========================================================

document
    .getElementById(
        "search"
    )
    .addEventListener(
        "input",
        function () {

            if (!cy) {
                return;
            }


            const texto =
                this.value
                    .trim()
                    .toLowerCase();


            reconstruirListaNodos(
                texto
            );


            cy.nodes()
                .removeClass(
                    "search-match"
                );


            if (
                texto === ""
            ) {

                return;
            }


            const encontrados =
                cy.nodes()
                    .filter(
                        n => {

                            if (
                                hiddenNodeIds.has(
                                    n.id()
                                )
                            ) {
                                return false;
                            }


                            const nombre =
                                String(
                                    n.data(
                                        "label"
                                    ) || ""
                                )
                                    .toLowerCase();


                            const ruta =
                                n.id()
                                    .toLowerCase();


                            return (
                                nombre.includes(
                                    texto
                                ) ||
                                ruta.includes(
                                    texto
                                )
                            );
                        }
                    );


            encontrados.addClass(
                "search-match"
            );


            if (
                encontrados.length > 0
            ) {

                cy.animate(
                    {

                        fit: {

                            eles:
                                encontrados,

                            padding:
                                120
                        }

                    },
                    {
                        duration:
                            300
                    }
                );
            }
        }
    );


// =========================================================
// BOTONES OCULTAR / MOSTRAR
// =========================================================

document
    .getElementById(
        "hide-all"
    )
    .addEventListener(
        "click",
        ocultarTodos
    );


document
    .getElementById(
        "show-all"
    )
    .addEventListener(
        "click",
        mostrarTodos
    );


// =========================================================
// BOTONES DEL GRAFO
// =========================================================

document
    .getElementById(
        "zoom-in"
    )
    .addEventListener(
        "click",
        function () {

            zoomCentro(
                1.25
            );
        }
    );


document
    .getElementById(
        "zoom-out"
    )
    .addEventListener(
        "click",
        function () {

            zoomCentro(
                0.80
            );
        }
    );


document
    .getElementById(
        "fit-graph"
    )
    .addEventListener(
        "click",
        function () {

            if (!cy) {
                return;
            }


            const visibles =
                cy.nodes()
                    .filter(
                        nodo =>
                            !hiddenNodeIds.has(
                                nodo.id()
                            )
                    );


            if (
                visibles.length === 0
            ) {
                return;
            }


            cy.animate(
                {

                    fit: {

                        eles:
                            visibles,

                        padding:
                            90
                    }

                },
                {
                    duration:
                        350
                }
            );
        }
    );


document
    .getElementById(
        "relayout-graph"
    )
    .addEventListener(
        "click",
        reordenarGrafo
    );


// =========================================================
// ARRANQUE
// =========================================================

configurarTouchpad();

configurarSidebarRedimensionable();


cargarGrafo()
    .catch(
        error => {

            console.error(
                "Error cargando el grafo:",
                error
            );


            document
                .getElementById(
                    "info"
                )
                .textContent =
                    "No fue posible cargar el grafo.";
        }
    );
