const $mp = id =>
    document.getElementById(id);


function setConnection(connected) {

    const badge =
        $mp("mapearConnection");

    badge.textContent =
        connected
            ?
            "● CONECTADO"
            :
            "● DESCONECTADO";

    badge.classList.toggle(
        "connected",
        connected
    );

    badge.classList.toggle(
        "disconnected",
        !connected
    );
}


async function checkConnection() {

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

        setConnection(
            Boolean(
                response.ok
                &&
                data.connected
            )
        );

    } catch (_) {

        setConnection(false);
    }
}


function startCamera() {

    const img =
        $mp("mapearVideo");

    const placeholder =
        $mp("cameraPlaceholder");


    img.src =
        "/video_feed?t="
        +
        Date.now();


    img.hidden = false;
    placeholder.hidden = true;


    $mp("cameraStatus")
    .textContent =
        "● ACTIVA";


    $mp("cameraControlStatus")
    .textContent =
        "● ACTIVA";
}



document.addEventListener(
    "DOMContentLoaded",
    () => {

        checkConnection();

        window.setInterval(
            checkConnection,
            3000
        );

        startCamera();
    }
);
