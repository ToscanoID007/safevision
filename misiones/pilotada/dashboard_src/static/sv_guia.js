/* =========================================================
   SafeVision - panel "Guia": practicas y manuales al lado del dashboard
   - Boton flotante "Guia" en todas las paginas.
   - Panel a la derecha. En pantallas anchas se acopla y la pagina se
     estrecha para seguir siendo usable; en pantallas estrechas la cubre.
   - Recuerda documento, posicion de lectura, ancho y tamano de letra
     entre paginas (localStorage).
   - Markdown con marked (static/vendor), sin internet.
   ========================================================= */
(function () {
    "use strict";

    var REPO_WEB = "https://github.com/ToscanoID007/safevision/blob/wip-handoff/";
    var ANCHO_MIN = 340, ANCHO_ACOPLE = 1100, ANCHO_MOVIL = 760;
    var catalogo = [];
    var actual = null;            // {id, ruta, titulo, ...}
    var panel, cuerpo, selDoc, selSeccion, boton, asa;
    var guardarScroll = null;

    // ---------- almacenamiento tolerante a fallos ----------
    function leer(clave, defecto) {
        try { var v = localStorage.getItem("sv_guia_" + clave); return v === null ? defecto : v; }
        catch (e) { return defecto; }
    }
    function escribir(clave, valor) {
        try { localStorage.setItem("sv_guia_" + clave, String(valor)); } catch (e) { /* sin almacenamiento */ }
    }

    function esc(t) {
        return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    function slug(texto) {
        return "g-" + String(texto).toLowerCase()
            .normalize("NFD").replace(/[̀-ͯ]/g, "")
            .replace(/<[^>]*>/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    }

    // ---------- rutas entre documentos ----------
    function resolver(base, rel) {
        var partes = base.split("/"); partes.pop();
        rel.split("/").forEach(function (p) {
            if (p === "..") partes.pop();
            else if (p && p !== ".") partes.push(p);
        });
        return partes.join("/");
    }

    function guiaPorRuta(ruta) {
        return catalogo.filter(function (g) { return g.ruta === ruta; })[0] || null;
    }

    // ---------- conversion Markdown ----------
    function configurarMarked() {
        var r = new marked.Renderer();
        // HTML crudo: solo se respeta <br>. Marcadores como <MAPA> o <IP-DEL-ROBOT>
        // se muestran tal cual (el navegador los borraria como etiquetas).
        r.html = function (html) {
            return /^\s*<br\s*\/?>\s*$/i.test(html) ? "<br>" : esc(html);
        };
        r.heading = function (texto, nivel, crudo) {
            return "<h" + nivel + ' id="' + slug(crudo) + '">' + texto + "</h" + nivel + ">";
        };
        r.code = function (codigo, lenguaje) {
            if ((lenguaje || "").trim() === "mermaid") {
                return '<div class="sv-guia-diagrama"><div class="sv-guia-diagrama-cab">Diagrama ' +
                    "(dibujado completo en GitHub)</div><pre>" + esc(codigo) + "</pre></div>";
            }
            return '<div class="sv-guia-codigo"><button type="button" class="sv-guia-copiar">Copiar</button>' +
                "<pre><code>" + esc(codigo) + "</code></pre></div>";
        };
        r.table = function (cabecera, filas) {
            return '<div class="sv-guia-tabla"><table><thead>' + cabecera + "</thead><tbody>" +
                filas + "</tbody></table></div>";
        };
        r.link = function (href, titulo, texto) {
            href = href || "";
            if (href.charAt(0) === "#") {
                return '<a href="#" data-ancla="' + esc(slug(decodeURIComponent(href.slice(1)))) + '">' + texto + "</a>";
            }
            if (/^[a-z]+:/i.test(href)) {
                return '<a href="' + esc(href) + '" target="_blank" rel="noopener">' + texto + "</a>";
            }
            var ancla = "";
            var i = href.indexOf("#");
            if (i >= 0) { ancla = href.slice(i + 1); href = href.slice(0, i); }
            var destino = resolver(actual ? actual.ruta : "docs/README.md", href);
            var g = guiaPorRuta(destino);
            if (g) {
                return '<a href="#" data-guia="' + esc(g.id) + '"' +
                    (ancla ? ' data-ancla="' + esc(slug(decodeURIComponent(ancla))) + '"' : "") + ">" + texto + "</a>";
            }
            return '<a href="' + esc(REPO_WEB + destino) + '" target="_blank" rel="noopener" title="Se abre en GitHub">' +
                texto + "</a>";
        };
        marked.setOptions({ renderer: r, gfm: true, breaks: false });
    }

    // ---------- interfaz ----------
    function crearInterfaz() {
        boton = document.createElement("button");
        boton.type = "button";
        boton.id = "svGuiaBtn";
        boton.className = "sv-guia-boton";
        boton.title = "Prácticas y manuales en un panel al lado";
        boton.innerHTML = '<span aria-hidden="true">▤</span> Guía';

        panel = document.createElement("aside");
        panel.className = "sv-guia";
        panel.setAttribute("aria-label", "Guía");
        panel.hidden = true;
        panel.innerHTML =
            '<div class="sv-guia-asa" title="Arrastra para cambiar el ancho"></div>' +
            '<header class="sv-guia-cabeza">' +
            '  <div class="sv-guia-fila">' +
            '    <span class="sv-guia-marca">Guía</span>' +
            '    <select class="sv-guia-doc" aria-label="Documento"></select>' +
            '    <button type="button" class="sv-guia-icono" data-accion="cerrar" aria-label="Cerrar la guía">×</button>' +
            "  </div>" +
            '  <div class="sv-guia-fila">' +
            '    <select class="sv-guia-seccion" aria-label="Ir a la sección"></select>' +
            '    <button type="button" class="sv-guia-icono" data-accion="menos" title="Letra más pequeña">A−</button>' +
            '    <button type="button" class="sv-guia-icono" data-accion="mas" title="Letra más grande">A+</button>' +
            "  </div>" +
            "</header>" +
            '<article class="sv-guia-cuerpo" tabindex="0"></article>';

        document.body.appendChild(boton);
        document.body.appendChild(panel);
        cuerpo = panel.querySelector(".sv-guia-cuerpo");
        selDoc = panel.querySelector(".sv-guia-doc");
        selSeccion = panel.querySelector(".sv-guia-seccion");
        asa = panel.querySelector(".sv-guia-asa");

        boton.addEventListener("click", abrir);
        panel.addEventListener("click", alPulsar);
        selDoc.addEventListener("change", function () { cargar(selDoc.value, null, true); });
        selSeccion.addEventListener("change", function () {
            if (selSeccion.value) irA(selSeccion.value);
        });
        cuerpo.addEventListener("scroll", function () {
            clearTimeout(guardarScroll);
            guardarScroll = setTimeout(function () {
                if (actual) escribir("scroll_" + actual.id, Math.round(cuerpo.scrollTop));
                marcarSeccion();
            }, 150);
        }, { passive: true });
        panel.addEventListener("keydown", function (ev) { if (ev.key === "Escape") cerrar(); });
        prepararAsa();
        window.addEventListener("resize", aplicarAncho);
        aplicarLetra();
    }

    function alPulsar(ev) {
        var b = ev.target.closest("button");
        if (b && b.dataset.accion === "cerrar") { cerrar(); return; }
        if (b && b.dataset.accion === "mas") { cambiarLetra(1); return; }
        if (b && b.dataset.accion === "menos") { cambiarLetra(-1); return; }
        if (b && b.classList.contains("sv-guia-copiar")) { copiar(b); return; }
        var a = ev.target.closest("a");
        if (!a) return;
        if (a.dataset.guia) { ev.preventDefault(); cargar(a.dataset.guia, a.dataset.ancla || null, true); return; }
        if (a.dataset.ancla) { ev.preventDefault(); irA(a.dataset.ancla); }
    }

    function copiar(b) {
        var code = b.parentNode.querySelector("code");
        var texto = code.textContent;
        var hecho = function () { b.textContent = "Copiado"; setTimeout(function () { b.textContent = "Copiar"; }, 1400); };
        var seleccionar = function () {
            // Ultimo recurso: deja el texto seleccionado para copiarlo con Ctrl+C.
            var rango = document.createRange();
            rango.selectNodeContents(code);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(rango);
            b.textContent = "Pulsa Ctrl+C";
        };
        var alternativo = function () {
            var t = document.createElement("textarea");
            t.value = texto;
            t.setAttribute("readonly", "");
            t.style.position = "fixed";
            t.style.opacity = "0";
            document.body.appendChild(t);
            t.select();
            var ok = false;
            try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
            t.remove();
            if (ok) hecho(); else seleccionar();
        };
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(texto).then(hecho, alternativo);
        } else {
            alternativo();
        }
    }

    // ---------- ancho, acople y letra ----------
    function anchoGuardado() {
        var w = parseInt(leer("ancho", "520"), 10);
        return isNaN(w) ? 520 : w;
    }

    function aplicarAncho() {
        var vw = window.innerWidth;
        var w = Math.max(ANCHO_MIN, Math.min(anchoGuardado(), Math.round(vw * 0.6)));
        document.documentElement.style.setProperty("--sv-guia-ancho", w + "px");
        var acoplar = !panel.hidden && vw >= ANCHO_ACOPLE;
        document.body.classList.toggle("sv-guia-acoplada", acoplar);
        panel.classList.toggle("movil", vw < ANCHO_MOVIL);
    }

    function prepararAsa() {
        var arrastrando = false;
        asa.addEventListener("pointerdown", function (ev) {
            arrastrando = true; asa.setPointerCapture(ev.pointerId); document.body.classList.add("sv-guia-redimension");
        });
        asa.addEventListener("pointermove", function (ev) {
            if (!arrastrando) return;
            escribir("ancho", Math.round(window.innerWidth - ev.clientX));
            aplicarAncho();
        });
        asa.addEventListener("pointerup", function () {
            arrastrando = false; document.body.classList.remove("sv-guia-redimension");
            avisarCambioTamano();
        });
    }

    function aplicarLetra() {
        var n = parseInt(leer("letra", "15"), 10);
        cuerpo.style.fontSize = (isNaN(n) ? 15 : n) + "px";
    }

    function cambiarLetra(d) {
        var n = parseInt(leer("letra", "15"), 10) + d;
        escribir("letra", Math.max(12, Math.min(20, n)));
        aplicarLetra();
    }

    // Graficos de la pagina (mapa, modelo 3D) recalculan su tamano con 'resize'.
    function avisarCambioTamano() {
        setTimeout(function () { window.dispatchEvent(new Event("resize")); }, 60);
    }

    // ---------- abrir, cerrar, cargar ----------
    function abrir() {
        panel.hidden = false;
        boton.hidden = true;
        escribir("abierta", "1");
        aplicarAncho();
        avisarCambioTamano();
        if (!actual) cargar(leer("doc", "guia-rapida"), null, false);
        cuerpo.focus({ preventScroll: true });
    }

    function cerrar() {
        panel.hidden = true;
        boton.hidden = false;
        escribir("abierta", "0");
        aplicarAncho();
        avisarCambioTamano();
        boton.focus({ preventScroll: true });
    }

    function llenarSelector() {
        var grupos = {};
        catalogo.forEach(function (g) { (grupos[g.grupo] = grupos[g.grupo] || []).push(g); });
        selDoc.innerHTML = Object.keys(grupos).map(function (nombre) {
            return '<optgroup label="' + esc(nombre) + '">' + grupos[nombre].map(function (g) {
                return '<option value="' + esc(g.id) + '"' + (g.disponible ? "" : " disabled") + ">" +
                    esc(g.titulo) + "</option>";
            }).join("") + "</optgroup>";
        }).join("");
    }

    function llenarSecciones() {
        var titulos = cuerpo.querySelectorAll("h2, h3");
        selSeccion.innerHTML = '<option value="">Ir a la sección…</option>' +
            Array.prototype.map.call(titulos, function (h) {
                return '<option value="' + esc(h.id) + '">' + (h.tagName === "H3" ? " " : "") +
                    esc(h.textContent) + "</option>";
            }).join("");
    }

    function marcarSeccion() {
        var titulos = cuerpo.querySelectorAll("h2, h3"), elegido = "";
        var tope = cuerpo.getBoundingClientRect().top + 40;
        Array.prototype.forEach.call(titulos, function (h) {
            if (h.getBoundingClientRect().top <= tope) elegido = h.id;
        });
        selSeccion.value = elegido;
    }

    function irA(id) {
        var el = cuerpo.querySelector("#" + CSS.escape(id));
        if (el) cuerpo.scrollTop = el.offsetTop - 8;
    }

    async function cargar(id, ancla, desdeArriba) {
        var g = catalogo.filter(function (x) { return x.id === id; })[0] || catalogo[0];
        if (!g) return;
        cuerpo.innerHTML = '<p class="sv-guia-aviso">Cargando…</p>';
        try {
            var r = await fetch("/api/guias/" + encodeURIComponent(g.id));
            var d = await r.json();
            if (!d.ok) throw new Error(d.message || "No disponible");
            actual = g;
            escribir("doc", g.id);
            selDoc.value = g.id;
            cuerpo.innerHTML = marked.parse(d.markdown) +
                '<p class="sv-guia-fuente">Fuente: <code>' + esc(d.ruta) + "</code></p>";
            llenarSecciones();
            if (ancla) irA(ancla);
            else cuerpo.scrollTop = desdeArriba ? 0 : parseInt(leer("scroll_" + g.id, "0"), 10) || 0;
            marcarSeccion();
        } catch (e) {
            cuerpo.innerHTML = '<p class="sv-guia-aviso">No se pudo abrir la guía: ' + esc(e.message) + "</p>";
        }
    }

    async function iniciar() {
        if (typeof marked === "undefined") return;   // falta static/vendor/marked.min.js
        configurarMarked();
        crearInterfaz();
        try {
            var r = await fetch("/api/guias");
            catalogo = (await r.json()).guias || [];
        } catch (e) {
            catalogo = [];
        }
        if (!catalogo.length) { boton.hidden = true; return; }
        llenarSelector();
        if (leer("abierta", "0") === "1") abrir();
        else aplicarAncho();
    }

    window.SafeVisionGuia = { abrir: function () { if (panel) abrir(); } };

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
    else iniciar();
})();
