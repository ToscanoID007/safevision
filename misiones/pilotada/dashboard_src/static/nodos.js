(function () {
    "use strict";

    var filas = document.getElementById("ndRows");
    var log = document.getElementById("ndLog");
    var aviso = document.getElementById("ndMappingNotice");
    var badgePerfil = document.getElementById("ndProfile");
    var badgeConn = document.getElementById("ndConnection");
    var ocupado = null;          // recurso con una accion en curso
    var INTERVALO_MS = 3000;

    var ETIQUETAS = {
        ros_master: "ROS Master", robot_server: "Robot Server", camera: "Cámara",
        driver: "Driver del chasis", core: "Odometría + IMU + EKF", selector: "Selector de velocidad",
        mando: "Mando", lidar: "LiDAR", localization: "Localización (AMCL + mapa)",
        pose_exporter: "Exportador de pose", navigation: "Navegación (move_base)",
        nav_queue: "Cola de navegación", teclado: "Teclado web", mapping: "Mapeo (Gmapping)"
    };

    function ahora() { return new Date().toLocaleTimeString(); }

    function escribir(texto) {
        log.textContent += "[" + ahora() + "] " + texto + "\n";
        log.scrollTop = log.scrollHeight;
    }

    function esc(t) { return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

    function pintar(datos) {
        var activos = {};
        datos.resources.forEach(function (r) { activos[r.name] = r.active; });
        badgePerfil.textContent = "perfil: " + (datos.profile.requested || "ninguno") +
            " · inferido: " + datos.profile.inferred + (datos.profile.map ? " · mapa " + datos.profile.map : "");
        aviso.hidden = !datos.mapping_active;

        var html = "";
        datos.resources.forEach(function (r) {
            var nombre = ETIQUETAS[r.name] || r.name;
            var deps = r.deps.map(function (d) {
                return '<span class="' + (activos[d] ? "" : "missing") + '">' + esc(d) + "</span>";
            }).join(", ") || "—";
            var dependientes = r.dependents.length ? r.dependents.map(esc).join(", ") : "—";
            var accion;
            if (ocupado === r.name) {
                accion = '<span class="nd-busy">en curso…</span>';
            } else if (r.read_only) {
                accion = '<span class="nd-deps">' + esc(r.reason) + "</span>";
            } else if (r.can_start) {
                accion = '<button class="nd-btn start" data-accion="start" data-recurso="' + esc(r.name) + '"' +
                    (ocupado ? " disabled" : "") + ">Arrancar</button>";
            } else if (r.can_stop) {
                accion = '<button class="nd-btn stop" data-accion="stop" data-recurso="' + esc(r.name) + '"' +
                    (ocupado ? " disabled" : "") + ">Detener</button>";
            } else {
                accion = '<span class="nd-deps">' + esc(r.reason || "—") + "</span>";
            }
            html += "<tr" + (r.read_only ? ' class="nd-ro"' : "") + ">" +
                '<td><span class="nd-dot ' + (r.active ? "on" : "off") + '"></span><span class="nd-name">' + esc(nombre) + "</span>" +
                '<div class="nd-deps">' + esc(r.name) + "</div></td>" +
                "<td>" + (r.active ? "activo" : "inactivo") + "</td>" +
                "<td>" + (r.pid ? esc(r.pid) : "—") + "</td>" +
                '<td class="nd-deps">' + deps + "</td>" +
                '<td class="nd-deps">' + dependientes + "</td>" +
                "<td>" + accion + "</td></tr>";
        });
        filas.innerHTML = html;
    }

    async function refrescar() {
        try {
            var resp = await fetch("/runtime/resources", { cache: "no-store" });
            var datos = await resp.json();
            if (!resp.ok || !datos.ok) {
                badgeConn.textContent = datos.message || ("error " + resp.status);
                return;
            }
            badgeConn.textContent = "conectado";
            pintar(datos);
        } catch (e) {
            badgeConn.textContent = "sin conexión";
        }
    }

    async function actuar(recurso, accion) {
        if (ocupado) { return; }
        ocupado = recurso;
        escribir((accion === "start" ? "Arrancando " : "Deteniendo ") + recurso + " (puede tardar hasta un minuto)…");
        await refrescar();
        try {
            var resp = await fetch("/runtime/resource/" + encodeURIComponent(recurso), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: accion })
            });
            var datos = await resp.json();
            var pasos = (datos.steps || []).map(function (s) { return (s.ok ? "✓ " : "✗ ") + s.resource; }).join("  ");
            escribir((datos.ok ? "OK: " : "FALLO: ") + (datos.message || "") + (pasos ? "   [" + pasos + "]" : ""));
        } catch (e) {
            escribir("FALLO: no se pudo contactar con el dashboard (" + e + ")");
        } finally {
            ocupado = null;
            await refrescar();
        }
    }

    filas.addEventListener("click", function (ev) {
        var boton = ev.target.closest("button[data-recurso]");
        if (!boton || boton.disabled) { return; }
        actuar(boton.getAttribute("data-recurso"), boton.getAttribute("data-accion"));
    });

    escribir("Gestor de nodos listo.");
    refrescar();
    window.setInterval(refrescar, INTERVALO_MS);
})();
