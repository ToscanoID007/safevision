// Lógica de conexión SSH
function conectarRobot() {
    const ip = document.getElementById('robot-ip').value;
    const statusText = document.getElementById('status-conexion');
    
    if (!ip) {
        alert("Por favor, ingresa la IP de la Raspberry Pi.");
        return;
    }

    statusText.innerText = "Estado: Conectando...";
    statusText.style.color = "orange";

    fetch('/conectar_robot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ip })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            statusText.innerText = "Estado: 🟢 Conectado";
            statusText.style.color = "#00ff00";
        } else {
            statusText.innerText = "Estado: 🔴 Error de conexión";
            statusText.style.color = "red";
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("Error:", error);
        statusText.innerText = "Estado: 🔴 Fallo crítico";
    });
}

// Lógica de Teleoperación y Comandos
function enviarComando(modo) {
    fetch('/set_control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: modo })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Comando enviado:", data);
        // Si el usuario encendió la cámara, actualizamos el src de la imagen
        // para que empiece a solicitar el stream de video a Flask
        if (modo === 'camara') {
            setTimeout(() => {
                document.getElementById('video-stream').src = "/video_feed?" + new Date().getTime();
            }, 2000); // Damos 2 segundos a la Pi para levantar el stream
        }
        if (modo === 'apagar') {
            document.getElementById('video-stream').src = "";
        }
    })
    .catch(error => console.error("Error al enviar comando:", error));
}

// Lógica para subir los modelos de IA
function subirModelos() {
    const filePt = document.getElementById('archivo-pt').files[0];
    const fileJson = document.getElementById('archivo-json').files[0];

    if (!filePt) {
        alert("¡Debes seleccionar al menos un archivo .pt!");
        return;
    }

    const formData = new FormData();
    formData.append("model_pt", filePt);
    if (fileJson) {
        formData.append("model_json", fileJson);
    }

    fetch('/upload_models', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert("✅ Modelo cargado en el motor de visión con éxito.");
        } else {
            alert("❌ Error: " + data.message);
        }
    })
    .catch(error => console.error("Error al subir modelo:", error));
}

// Actualizar el texto del slider de confianza en tiempo real
function actualizarConfianza(valor) {
    const porcentaje = Math.round(valor * 100);
    document.getElementById('valor-confianza').innerText = porcentaje + "%";

    // Enviar el nuevo valor al backend
    fetch('/update_confidence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confidence: valor })
    })
    .then(response => response.json())
    .then(data => console.log("Confianza actualizada:", data))
    .catch(error => console.error("Error al actualizar confianza:", error));
}
