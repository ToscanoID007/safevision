/* =========================================================
   SafeVision - control de velocidad del mando (Pilotada y Mapear)
   El robot aplica el factor en su selector de cmd_vel; aqui solo se
   elige y se envia. Solo reduce: 100 % es la velocidad de fabrica.
   ========================================================= */
(function () {
    "use strict";

    var bloques = Array.prototype.slice.call(document.querySelectorAll("[data-sv-velocidad]"));
    if (!bloques.length) return;

    var envio = null;

    function pintar(d) {
        bloques.forEach(function (b) {
            var rango = b.querySelector("[data-sv-velocidad-rango]");
            var valor = b.querySelector("[data-sv-velocidad-valor]");
            var detalle = b.querySelector("[data-sv-velocidad-detalle]");
            if (!d || d.ok === false) {
                rango.disabled = true;
                valor.textContent = "—";
                detalle.textContent = (d && d.message) || "Robot no conectado.";
                return;
            }
            rango.disabled = false;
            if (document.activeElement !== rango) rango.value = d.porcentaje;
            valor.textContent = d.porcentaje + " %";
            detalle.textContent = "Máximo " + d.lineal_max.toFixed(2) + " m/s y " +
                d.angular_max.toFixed(1) + " rad/s al girar. Más bajo = más preciso.";
        });
    }

    async function consultar() {
        try {
            var r = await fetch("/runtime/speed", { cache: "no-store" });
            pintar(await r.json());
        } catch (e) {
            pintar({ ok: false, message: "No se pudo consultar la velocidad." });
        }
    }

    function enviar(porcentaje) {
        clearTimeout(envio);
        bloques.forEach(function (b) {
            b.querySelector("[data-sv-velocidad-valor]").textContent = porcentaje + " %";
        });
        envio = setTimeout(async function () {
            try {
                var r = await fetch("/runtime/speed", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ factor: porcentaje / 100 })
                });
                pintar(await r.json());
            } catch (e) {
                pintar({ ok: false, message: "No se pudo cambiar la velocidad." });
            }
        }, 250);
    }

    bloques.forEach(function (b) {
        var rango = b.querySelector("[data-sv-velocidad-rango]");
        rango.addEventListener("input", function () { enviar(parseInt(rango.value, 10)); });
    });

    consultar();
    setInterval(consultar, 15000);
})();
