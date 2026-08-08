const state = {
    connected: false,
    confidenceTimer: null
};


const $ = (id) => document.getElementById(id);


function log(message) {
    const box = $("log");

    const time = new Date()
        .toLocaleTimeString();

    box.textContent =
        `[${time}] ${message}\n`
        +
        box.textContent;
}


function yesNo(value) {
    if (value === true) {
        return "OK";
    }

    if (value === false) {
        return "FAIL";
    }

    return "—";
}


function renderRobot(robot) {
    $("rosStatus").textContent =
        yesNo(robot.ros_master);

    $("driverStatus").textContent =
        yesNo(robot.driver);

    $("cameraStatus").textContent =
        yesNo(robot.camera);


    const mode =
        robot.control_mode
        ||
        "desconocido";


    if (robot.control === true) {
        $("controlStatus").textContent =
            `${mode.toUpperCase()} · OK`;
    } else {
        $("controlStatus").textContent =
            mode.toUpperCase();
    }
}


function startVideo() {
    const img =
        $("videoFeed");

    const placeholder =
        $("videoPlaceholder");


    img.src =
        "/video_feed?t="
        +
        Date.now();


    img.hidden = false;
    placeholder.hidden = true;
}


async function connectRobot() {
    const ip =
        $("robotIp")
        .value
        .trim();


    if (!ip) {
        log(
            "Escribe la IP del robot."
        );

        return;
    }


    $("connectButton").disabled = true;

    log(
        `Conectando a ${ip}...`
    );


    try {
        const response = await fetch(
            "/connect",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    ip: ip
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                data.message
                ||
                "No se pudo conectar."
            );
        }


        state.connected = true;


        $("connectionBadge")
            .textContent =
            "CONECTADO";


        $("connectionBadge")
            .className =
            "badge badge-on";


        renderRobot(
            data.robot
        );


        startVideo();


        log(
            `Robot conectado: ${ip}`
        );


    } catch (error) {
        state.connected = false;


        $("connectionBadge")
            .textContent =
            "DESCONECTADO";


        $("connectionBadge")
            .className =
            "badge badge-off";


        log(
            `Error: ${error.message}`
        );


    } finally {
        $("connectButton").disabled = false;
    }
}


async function uploadModel(event) {
    event.preventDefault();


    const pt =
        $("modelPt").files[0];


    const json =
        $("modelJson").files[0];


    if (!pt) {
        log(
            "Selecciona un archivo .pt."
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


    log(
        `Cargando modelo ${pt.name}...`
    );


    try {
        const response = await fetch(
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


        renderModel(
            data.model
        );


        log(
            `Modelo listo: ${data.model.model}`
        );


    } catch (error) {
        log(
            `Error IA: ${error.message}`
        );
    }
}


function renderModel(info) {
    $("modelName").textContent =
        info.model
        ||
        "Ninguno";


    const metadata =
        info.metadata
        ||
        {};


    const parts = [];


    if (metadata.nombre_modelo) {
        parts.push(
            `Nombre: ${metadata.nombre_modelo}`
        );
    }


    if (metadata.version) {
        parts.push(
            `Versión: ${metadata.version}`
        );
    }


    if (info.json) {
        parts.push(
            `JSON: ${info.json}`
        );
    }


    if (parts.length === 0) {
        parts.push(
            `Archivo: ${info.model}`
        );
    }


    $("modelMetadata")
        .textContent =
        parts.join(" · ");


    const classes =
        $("classes");


    classes.innerHTML = "";


    if (
        !info.classes
        ||
        info.classes.length === 0
    ) {
        classes.innerHTML =
            '<span class="muted">'
            +
            'Sin clases disponibles.'
            +
            '</span>';

        return;
    }


    for (
        const className
        of info.classes
    ) {
        const tag =
            document.createElement(
                "span"
            );


        tag.className =
            "class-tag";


        tag.textContent =
            className;


        classes.appendChild(
            tag
        );
    }
}


async function sendConfidence(value) {
    try {
        await fetch(
            "/confidence",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    confidence:
                        value / 100
                })
            }
        );

    } catch (_) {
        // No saturar el log con el slider.
    }
}


async function pollRobot() {
    if (!state.connected) {
        return;
    }


    try {
        const response = await fetch(
            "/robot_status"
        );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error();
        }


        renderRobot(
            data.robot
        );


    } catch (_) {
        $("connectionBadge")
            .textContent =
            "SIN RESPUESTA";


        $("connectionBadge")
            .className =
            "badge badge-warn";
    }
}


$("connectButton")
    .addEventListener(
        "click",
        connectRobot
    );


$("modelForm")
    .addEventListener(
        "submit",
        uploadModel
    );


$("confidence")
    .addEventListener(
        "input",
        (event) => {
            const value =
                Number(
                    event.target.value
                );


            $("confidenceValue")
                .textContent =
                `${value}%`;


            clearTimeout(
                state.confidenceTimer
            );


            state.confidenceTimer =
                setTimeout(
                    () => {
                        sendConfidence(
                            value
                        );
                    },
                    150
                );
        }
    );


setInterval(
    pollRobot,
    3000
);
