/* =========================================================
   SafeVision - indicador de espera para las acciones
   Envuelve fetch: cada accion que se manda al robot (POST/PUT/DELETE y
   algunas consultas lentas) muestra arriba una rueda con que se esta haciendo
   y cuantos segundos lleva, y marca el boton que la lanzo. Las consultas
   periodicas de estado y los envios continuos (teclado, velocidad) no.
   Se carga en <head>, antes que los scripts de cada pagina.
   ========================================================= */
(function () {
    "use strict";
    if (window.__svEspera) return;
    window.__svEspera = true;

    var EXCLUIR = [/^\/runtime\/keyboard/, /^\/runtime\/speed/, /^\/api\/guias/, /^\/static\//];
    var CONSULTAS_LENTAS = [/^\/api\/wifi\/scan/];
    var TEXTOS = [
        [/^\/runtime\/profile/, "Activando el modo en el robot", "puede tardar hasta 2 minutos"],
        [/^\/runtime\/control/, "Cambiando el tipo de control", ""],
        [/^\/runtime\/resource\//, "Arrancando o deteniendo la parte del robot", "puede tardar hasta 1 minuto"],
        [/^\/mapping\/session\/start/, "Iniciando el mapeo", "puede tardar hasta 2 minutos"],
        [/^\/mapping\/session\/save/, "Guardando el mapa y volviendo al modo anterior", "puede tardar hasta 2 minutos"],
        [/^\/mapping\/session\/discard/, "Descartando el mapeo y volviendo al modo anterior", "puede tardar hasta 2 minutos"],
        [/^\/api\/wifi\/scan/, "Buscando redes Wi-Fi", "unos segundos"],
        [/^\/api\/wifi\//, "Configurando el Wi-Fi del robot", ""],
        [/^\/connect/, "Conectando con el robot", ""],
        [/^\/nav\//, "Enviando la orden de navegación", ""],
        [/^\/mission/, "Preparando la misión", ""],
        [/^\/maps/, "Trabajando con los mapas del robot", ""],
        [/^\/models/, "Trabajando con los modelos", ""]
    ];
    var RETARDO_MS = 250;      // no parpadea en acciones instantaneas

    var nativo = window.fetch.bind(window);
    var panel = null, lista = null, siguienteId = 1;
    var activos = {};
    var ultimoBoton = null, ultimoClic = 0;

    document.addEventListener("click", function (ev) {
        var b = ev.target.closest && ev.target.closest("button, [role=button], input[type=submit]");
        if (b) { ultimoBoton = b; ultimoClic = Date.now(); }
    }, true);

    function ruta(entrada) {
        try {
            var u = new URL(typeof entrada === "string" ? entrada : entrada.url, window.location.href);
            return u.origin === window.location.origin ? u.pathname : null;
        } catch (e) { return null; }
    }

    function metodo(entrada, opciones) {
        var m = (opciones && opciones.method) || (entrada && entrada.method) || "GET";
        return String(m).toUpperCase();
    }

    function vigilar(path, m) {
        if (!path) return false;
        if (EXCLUIR.some(function (r) { return r.test(path); })) return false;
        if (m !== "GET" && m !== "HEAD") return true;
        return CONSULTAS_LENTAS.some(function (r) { return r.test(path); });
    }

    function texto(path) {
        for (var i = 0; i < TEXTOS.length; i++) {
            if (TEXTOS[i][0].test(path)) return { t: TEXTOS[i][1], d: TEXTOS[i][2] };
        }
        return { t: "Comunicándose con el robot", d: "" };
    }

    function asegurarPanel() {
        if (panel || !document.body) return;
        panel = document.createElement("div");
        panel.className = "sv-espera";
        panel.setAttribute("role", "status");
        panel.setAttribute("aria-live", "polite");
        lista = document.createElement("div");
        panel.appendChild(lista);
        document.body.appendChild(panel);
    }

    function pintar() {
        asegurarPanel();
        if (!panel) return;
        var ids = Object.keys(activos).filter(function (k) { return activos[k].visible; });
        panel.classList.toggle("visible", ids.length > 0);
        lista.innerHTML = ids.map(function (k) {
            var a = activos[k];
            var seg = Math.floor((Date.now() - a.inicio) / 1000);
            var icono = a.fin === "ok" ? '<span class="sv-espera-ok">✓</span>'
                      : a.fin === "error" ? '<span class="sv-espera-error">✗</span>'
                      : '<span class="sv-espera-rueda" aria-hidden="true"></span>';
            var linea = a.fin === "ok" ? "Listo" : a.fin === "error" ? "No se completó (revisa el mensaje de la página)"
                      : (a.d ? a.d + " · " : "") + seg + " s";
            return '<div class="sv-espera-item' + (a.fin ? " " + a.fin : "") + '">' + icono +
                "<div><strong>" + a.t + "</strong><small>" + linea + "</small></div></div>";
        }).join("");
    }

    setInterval(function () { if (Object.keys(activos).length) pintar(); }, 500);

    function marcarBoton(b, si) {
        if (!b) return;
        if (si) {
            b.dataset.svEsperas = String((parseInt(b.dataset.svEsperas || "0", 10)) + 1);
            b.classList.add("sv-ocupado");
            b.setAttribute("aria-busy", "true");
        } else {
            var n = parseInt(b.dataset.svEsperas || "1", 10) - 1;
            b.dataset.svEsperas = String(Math.max(0, n));
            if (n <= 0) { b.classList.remove("sv-ocupado"); b.removeAttribute("aria-busy"); }
        }
    }

    window.fetch = function (entrada, opciones) {
        var path = ruta(entrada);
        var m = metodo(entrada, opciones);
        if (!vigilar(path, m)) return nativo(entrada, opciones);

        var id = siguienteId++;
        var info = texto(path);
        var boton = Date.now() - ultimoClic < 600 ? ultimoBoton : null;
        activos[id] = { t: info.t, d: info.d, inicio: Date.now(), visible: false, fin: null };
        marcarBoton(boton, true);
        var temporizador = setTimeout(function () {
            if (activos[id]) { activos[id].visible = true; pintar(); }
        }, RETARDO_MS);

        function terminar(ok) {
            clearTimeout(temporizador);
            marcarBoton(boton, false);
            var a = activos[id];
            if (!a) return;
            if (!a.visible) { delete activos[id]; return; }   // fue instantaneo
            a.fin = ok ? "ok" : "error";
            pintar();
            setTimeout(function () { delete activos[id]; pintar(); }, ok ? 2000 : 3500);
        }

        return nativo(entrada, opciones).then(function (r) {
            terminar(r.ok);
            return r;
        }, function (e) {
            terminar(false);
            throw e;
        });
    };
})();
