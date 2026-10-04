(function () {
    "use strict";

    var $ = function (id) { return document.getElementById(id); };
    var log = $("wfLog");
    var estado = null;        // ultimo /api/wifi
    var redes = [];           // ultimo escaneo
    var esperandoCambio = null;
    var INTERVALO_MS = 4000;

    function ahora() { return new Date().toLocaleTimeString(); }
    function escribir(t) { log.textContent += "[" + ahora() + "] " + t + "\n"; log.scrollTop = log.scrollHeight; }
    function esc(t) {
        return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    async function pedir(metodo, url, cuerpo) {
        var opciones = { method: metodo, headers: {} };
        if (cuerpo) { opciones.headers["Content-Type"] = "application/json"; opciones.body = JSON.stringify(cuerpo); }
        var r = await fetch(url, opciones);
        var datos = {};
        try { datos = await r.json(); } catch (e) { datos = { ok: false, message: "Respuesta inválida." }; }
        datos._http = r.status;
        return datos;
    }

    function barras(senal) {
        var n = senal >= 75 ? 4 : senal >= 50 ? 3 : senal >= 30 ? 2 : 1;
        return "▮▮▮▮".slice(0, n) + "▯▯▯▯".slice(n);
    }

    function guardada(ssid) {
        if (!estado) return null;
        return (estado.guardadas || []).filter(function (p) { return p.ssid === ssid || p.nombre === ssid; })[0] || null;
    }

    function aviso(texto) {
        $("wfAviso").hidden = !texto;
        $("wfAviso").innerHTML = texto || "";
    }

    // ---------------- estado ----------------
    function pintarEstado(d) {
        var badge = $("wfConexion");
        if (!d || d.ok === false) {
            badge.textContent = "robot sin conexión";
            $("wfRedActual").textContent = "—";
            $("wfDetalle").textContent = d && d.message ? d.message : "";
            $("wfVolverAp").hidden = true;
            return;
        }
        estado = d;
        badge.textContent = "robot en " + (d.robot_ip || d.ip || "—");
        if (d.modo === "ap") {
            $("wfRedActual").textContent = "Red propia: " + d.ap.ssid;
            $("wfDetalle").textContent = "Dirección fija " + d.ap.ip + ". Sin internet mientras estés en esta red.";
        } else if (d.modo === "cliente") {
            $("wfRedActual").textContent = d.ssid;
            $("wfDetalle").textContent = "Dirección " + (d.ip || "—") + " (la asigna esta red).";
        } else {
            $("wfRedActual").textContent = "Sin red";
            $("wfDetalle").textContent = "El robot está buscando una red o creando la suya.";
        }
        $("wfVolverAp").hidden = d.modo === "ap";
        pintarGuardadas();
        if (redes.length) pintarRedes();
        if (esperandoCambio) {
            var destino = esperandoCambio.destino;
            var llego = (d.modo === "ap" && destino === d.ap.ssid) || d.ssid === destino;
            var vencido = Date.now() - esperandoCambio.desde > 90000;
            if (llego) {
                escribir("✓ El robot está en " + destino + " (" + (d.robot_ip || d.ip) + ").");
                aviso("");
                esperandoCambio = null;
            } else if (vencido && !d.ocupado) {
                escribir("✗ El robot no entró en " + destino + "; está en " + (d.ssid || "—") + ".");
                aviso("El robot no pudo conectarse a <strong>" + esc(destino) +
                      "</strong>. Revisa la contraseña y que la red sea de 2.4 GHz.");
                esperandoCambio = null;
            }
        }
    }

    var refrescando = false;
    async function refrescar() {
        if (refrescando) return;          // no acumular consultas si el robot tarda
        refrescando = true;
        try { pintarEstado(await pedir("GET", "/api/wifi")); }
        catch (e) { pintarEstado({ ok: false, message: "El dashboard no responde." }); }
        finally { refrescando = false; }
    }

    function pintarGuardadas() {
        var lista = (estado && estado.guardadas) || [];
        if (!lista.length) { $("wfGuardadas").innerHTML = '<div class="wf-vacio">Ninguna.</div>'; return; }
        $("wfGuardadas").innerHTML = lista.map(function (p) {
            var acciones = p.activa ? '<span class="wf-activa">● en uso</span>' :
                '<button class="sv-btn ok" data-conectar="' + esc(p.nombre) + '">Conectar</button>' +
                '<button class="sv-btn peligro" data-olvidar="' + esc(p.nombre) + '">Olvidar</button>';
            return '<div class="wf-fila' + (p.activa ? " en-uso" : "") + '"><div><div class="wf-ssid">' + esc(p.ssid) + '</div>' +
                '<div class="wf-meta">banda: ' + (p.banda === "bg" ? "2.4 GHz" : p.banda === "a" ? "5 GHz" : "automática") +
                '</div></div><div></div><div class="wf-acciones">' + acciones + "</div></div>";
        }).join("");
    }

    // ---------------- escaneo ----------------
    function pintarRedes() {
        if (!redes.length) { $("wfLista").innerHTML = '<div class="wf-vacio">No se vio ninguna red.</div>'; return; }
        $("wfLista").innerHTML = redes.map(function (r) {
            var bandas = r.bandas.map(function (b) {
                return '<span class="wf-banda ' + (b === "2.4" ? "ok" : "no") + '">' + b + " GHz</span>";
            }).join("");
            var seguridad = r.abierta ? "abierta" : r.empresarial ? "empresarial (no compatible)" : "con contraseña";
            var g = guardada(r.ssid);
            var accion;
            if (!r.compatible) accion = '<span class="wf-nota-fila">sólo 5 GHz</span>';
            else if (r.empresarial) accion = '<span class="wf-nota-fila">no compatible</span>';
            else if (g && g.activa) accion = '<span class="wf-activa">● en uso</span>';
            else if (g) accion = '<button class="sv-btn ok" data-conectar="' + esc(g.nombre) + '">Conectar</button>' +
                                 '<button class="sv-btn" data-elegir="' + esc(r.ssid) + '">Cambiar clave</button>';
            else accion = '<button class="sv-btn ok" data-elegir="' + esc(r.ssid) + '">Elegir</button>';
            var gris = !r.compatible || r.empresarial;
            return '<div class="wf-fila' + (gris ? " gris" : "") + (g && g.activa ? " en-uso" : "") + '"><div><div class="wf-ssid">' + esc(r.ssid) +
                '</div><div class="wf-meta">' + bandas + seguridad + (g ? " · guardada" : "") + '</div></div>' +
                '<div class="wf-senal" title="' + (r.senal_24 || r.senal) + '%">' + barras(r.senal_24 || r.senal) +
                '</div><div class="wf-acciones">' + accion + "</div></div>";
        }).join("");
    }

    async function buscar() {
        $("wfBuscar").disabled = true;
        $("wfEscaneoInfo").textContent = "Buscando redes… (unos segundos)";
        try {
            var d = await pedir("GET", "/api/wifi/scan");
            if (!d.ok) { $("wfEscaneoInfo").textContent = d.message || "No se pudo buscar."; return; }
            redes = d.redes || [];
            if (d.en_vivo) {
                $("wfEscaneoInfo").textContent = "Búsqueda hecha ahora.";
            } else {
                var edad = d.edad_s == null ? "" : " (hace " + Math.max(1, Math.round(d.edad_s / 60)) + " min)";
                $("wfEscaneoInfo").textContent = (d.aviso || "") + edad;
            }
            pintarRedes();
        } catch (e) {
            $("wfEscaneoInfo").textContent = "El robot no respondió.";
        } finally {
            $("wfBuscar").disabled = false;
        }
    }

    // ---------------- dialogo ----------------
    var dlgSsid = null;
    var dlgOculta = false;

    function abrirDialogo(ssid, oculta) {
        dlgOculta = !!oculta;
        var r = redes.filter(function (x) { return x.ssid === ssid; })[0];
        var abierta = !!(r && r.abierta);
        dlgSsid = ssid;
        $("wfDlgSsid").textContent = ssid;
        $("wfDlgClave").value = "";
        $("wfDlgClave").type = "password";
        $("wfDlgClaveFila").hidden = abierta;
        $("wfDlgAbierta").hidden = !abierta;
        $("wfDlgError").hidden = true;
        $("wfDlgAhora").checked = true;
        $("wfDialogo").showModal();
        if (!abierta) $("wfDlgClave").focus();
    }

    async function guardar() {
        var clave = $("wfDlgClaveFila").hidden ? "" : $("wfDlgClave").value;
        if (!$("wfDlgClaveFila").hidden && (clave.length < 8 || clave.length > 64)) {
            $("wfDlgError").textContent = "La contraseña debe tener entre 8 y 63 caracteres.";
            $("wfDlgError").hidden = false;
            return;
        }
        var ahoraSi = $("wfDlgAhora").checked;
        $("wfDlgGuardar").disabled = true;
        try {
            var d = await pedir("POST", "/api/wifi/add", { ssid: dlgSsid, password: clave, connect: ahoraSi, hidden: dlgOculta });
            if (!d.ok) { $("wfDlgError").textContent = d.message; $("wfDlgError").hidden = false; return; }
            $("wfDialogo").close();
            escribir("✓ " + d.message);
            if (ahoraSi && d.cambio && d.cambio.cambio) iniciarEspera(d.cambio.destino);
            refrescar();
        } catch (e) {
            $("wfDlgError").textContent = "El robot no respondió.";
            $("wfDlgError").hidden = false;
        } finally {
            $("wfDlgGuardar").disabled = false;
        }
    }

    function iniciarEspera(destino) {
        esperandoCambio = { destino: destino, desde: Date.now() };
        aviso("El robot se está cambiando a <strong>" + esc(destino) + "</strong>. " +
              "Si tu laptop pierde la conexión, conéctala a <strong>" + esc(destino) +
              "</strong>. Esta página volverá a encontrar al robot sola (puede tardar hasta un minuto).");
        escribir("… cambiando a " + destino);
    }

    async function conectar(nombre) {
        var d = await pedir("POST", "/api/wifi/connect", { name: nombre });
        escribir((d.ok ? "✓ " : "✗ ") + d.message);
        if (d.ok && d.cambio) iniciarEspera(d.destino);
    }

    async function olvidar(nombre) {
        if (!confirm("¿Olvidar la red «" + nombre + "»? El robot ya no se conectará a ella al encender.")) return;
        var d = await pedir("POST", "/api/wifi/forget", { name: nombre });
        escribir((d.ok ? "✓ " : "✗ ") + d.message);
        refrescar();
    }

    // ---------------- eventos ----------------
    document.addEventListener("click", function (ev) {
        var b = ev.target.closest("button");
        if (!b) return;
        if (b.dataset.elegir) abrirDialogo(b.dataset.elegir);
        else if (b.dataset.conectar) conectar(b.dataset.conectar);
        else if (b.dataset.olvidar) olvidar(b.dataset.olvidar);
    });
    $("wfBuscar").addEventListener("click", buscar);
    $("wfDlgGuardar").addEventListener("click", guardar);
    $("wfDlgClave").addEventListener("keydown", function (ev) { if (ev.key === "Enter") { ev.preventDefault(); guardar(); } });
    $("wfDlgVer").addEventListener("click", function () {
        $("wfDlgClave").type = $("wfDlgClave").type === "password" ? "text" : "password";
    });
    $("wfOcultaBtn").addEventListener("click", function () {
        var ssid = $("wfOcultaSsid").value.trim();
        if (ssid) abrirDialogo(ssid, !redes.some(function (r) { return r.ssid === ssid; }));
    });
    $("wfVolverAp").addEventListener("click", function () {
        if (confirm("El robot dejará la red actual y creará SafeVision-Robot (10.42.0.1). " +
                    "Tendrás que conectar tu laptop a esa red. ¿Continuar?")) conectar("SafeVision-AP");
    });

    refrescar();
    buscar();
    setInterval(refrescar, INTERVALO_MS);
})();
