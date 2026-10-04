/* =========================================================
   SafeVision - ayuda integrada
   1. Ficha informativa al pasar el raton (o primer toque) sobre cada
      tarjeta de la portada y cada enlace del menu.
   2. Tutorial guiado de lo basico (boton "Tutorial" o /?tutorial=1).
   Sin dependencias. Se incluye en la portada, Pilotada, Nodos y Wi-Fi.
   ========================================================= */
(function () {
    "use strict";

    // -----------------------------------------------------
    // Catalogo: que hace cada seccion
    // -----------------------------------------------------
    var CATALOGO = {
        "/": {
            titulo: "Inicio",
            que: "Portada: conexión con el robot, estado de sus partes y acceso a todas las secciones.",
            cuando: "Al empezar, para comprobar que el robot está conectado."
        },
        "/pilotada": {
            titulo: "Misión Pilotada",
            que: "Manejas el robot con el mando mientras ves su cámara. En el modo «Misión Pilotada» además carga un mapa, ubica al robot en él y puedes mandarlo a puntos con un clic.",
            cuando: "Para operar el robot y comprobar que todo funciona.",
            antes: "Robot conectado. Pulsa Modo Libre, o elige un mapa a la derecha y pulsa Misión Pilotada: ese clic es el que lo activa (hasta 2 minutos).",
            ojo: "Para pararlo, suelta el mando: se detiene en medio segundo. Usa un mapa del lugar donde estás."
        },
        "/automatica": {
            titulo: "Misión Automática",
            que: "Ejecuta una misión ya programada: el robot recorre solo los puntos del programa.",
            cuando: "Cuando ya escribiste y simulaste una misión en Programar.",
            antes: "Un mapa del lugar, el robot ubicado en ese mapa y la misión guardada.",
            ojo: "Área despejada y alguien con el mando en la mano para pararlo."
        },
        "/mapas/mapear": {
            titulo: "Mapear",
            que: "Dibuja el plano de un lugar nuevo mientras manejas el robot con el mando. Con ese plano el robot sabe dónde está y puede navegar solo.",
            cuando: "La primera vez que usas el robot en un sitio, por ejemplo el laboratorio.",
            antes: "En Pilotada, elige un mapa existente (HAB2 sirve) y pulsa Misión Pilotada: al terminar de mapear, el robot vuelve a él.",
            ojo: "Muévelo despacio y recorre todo el cuarto. Guarda el mapa con un nombre claro."
        },
        "/programar": {
            titulo: "Programar misión",
            que: "Escribes una misión con órdenes sencillas (ir, esperar, orientar), la validas y la simulas sobre el mapa.",
            cuando: "Para preparar recorridos automáticos.",
            antes: "Un mapa del lugar con los puntos marcados.",
            ojo: "Simular nunca mueve el robot. La misión se ejecuta en Misión Automática."
        },
        "/redes": {
            titulo: "Modelos / IA",
            que: "Gestiona los modelos que detectan objetos en la cámara (YOLO): subirlos, probarlos con una imagen y ver los que hay en el robot.",
            cuando: "Para cambiar qué objetos reconoce la cámara.",
            antes: "El archivo del modelo (.pt) y su .json con las clases.",
            ojo: "La detección se calcula en la laptop, no en el robot."
        },
        "/mapas": {
            titulo: "Mapas",
            que: "Los mapas guardados en el robot: verlos, renombrarlos, duplicarlos, editarlos, exportarlos, importarlos o borrarlos.",
            cuando: "Para ordenar mapas o pasarlos de un robot o laptop a otro.",
            antes: "Nada especial: funciona sin aplicar perfil.",
            ojo: "Borrar un mapa no se puede deshacer. Exporta antes una copia."
        },
        "/nodos": {
            titulo: "Nodos",
            que: "Muestra qué partes del robot están encendidas (driver, LiDAR, navegación…) y deja encender o apagar cada una en el orden correcto.",
            cuando: "Cuando algo no responde y quieres ver qué parte falla.",
            antes: "Robot conectado.",
            ojo: "Apagar el driver apaga todo lo que depende de él. Durante un mapeo se gestiona desde Mapear."
        },
        "/wifi": {
            titulo: "Wi-Fi",
            que: "Muestra las redes que ve el robot y lo conecta a una nueva escribiendo su contraseña.",
            cuando: "Al llevar el robot a un lugar con otra red Wi-Fi.",
            antes: "Estar conectado al robot: en su red propia SafeVision-Robot o en la misma red que él.",
            ojo: "Sólo redes de 2.4 GHz. Al cambiar, pasa tu laptop a la misma red."
        }
    };

    var NOMBRE_A_RUTA = {
        "Misión Pilotada": "/pilotada",
        "Misión Automática": "/automatica",
        "Mapear": "/mapas/mapear",
        "Programar misión": "/programar",
        "Modelos / IA": "/redes",
        "Mapas": "/mapas",
        "Nodos": "/nodos",
        "Wi-Fi": "/wifi"
    };

    var esTactil = window.matchMedia && window.matchMedia("(hover: none)").matches;

    function crear(tag, clase, html) {
        var el = document.createElement(tag);
        if (clase) el.className = clase;
        if (html != null) el.innerHTML = html;
        return el;
    }

    // -----------------------------------------------------
    // 1. Fichas informativas
    // -----------------------------------------------------
    var ficha = crear("div", "sv-ficha");
    ficha.setAttribute("role", "tooltip");
    ficha.hidden = true;
    var temporizador = null;
    var armado = null;          // en tactil: elemento que ya mostro su ficha
    var tutorialAbierto = false;

    function contenidoFicha(ruta, conBoton) {
        var c = CATALOGO[ruta];
        var filas = "";
        if (c.cuando) filas += "<dt>Cuándo</dt><dd>" + c.cuando + "</dd>";
        if (c.antes) filas += "<dt>Antes</dt><dd>" + c.antes + "</dd>";
        if (c.ojo) filas += "<dt>Ojo</dt><dd>" + c.ojo + "</dd>";
        return "<h4>" + c.titulo + "</h4><p>" + c.que + "</p>" +
            (filas ? "<dl>" + filas + "</dl>" : "") +
            (conBoton ? '<a class="sv-ficha-abrir" href="' + ruta + '">Abrir ' + c.titulo + " →</a>"
                      : '<div class="sv-ficha-pie">Clic para abrir</div>');
    }

    function colocar(caja, rect, margen) {
        var vw = window.innerWidth, vh = window.innerHeight;
        var w = caja.offsetWidth, h = caja.offsetHeight;
        var x, y;
        if (rect.left - w - margen >= 12) {                 // a la izquierda
            x = rect.left - w - margen;
            y = rect.top + rect.height / 2 - h / 2;
        } else if (rect.right + margen + w <= vw - 12) {    // a la derecha
            x = rect.right + margen;
            y = rect.top + rect.height / 2 - h / 2;
        } else if (rect.bottom + margen + h <= vh - 12) {   // debajo
            x = rect.left + rect.width / 2 - w / 2;
            y = rect.bottom + margen;
        } else {                                            // encima
            x = rect.left + rect.width / 2 - w / 2;
            y = rect.top - margen - h;
        }
        caja.style.left = Math.max(12, Math.min(x, vw - w - 12)) + "px";
        caja.style.top = Math.max(12, Math.min(y, vh - h - 12)) + "px";
    }

    function mostrarFicha(el, conBoton) {
        if (tutorialAbierto) return;
        var ruta = el.getAttribute("data-sv-ruta");
        if (!CATALOGO[ruta]) return;
        ficha.innerHTML = contenidoFicha(ruta, conBoton);
        ficha.classList.toggle("interactiva", !!conBoton);
        ficha.hidden = false;
        colocar(ficha, el.getBoundingClientRect(), 12);
    }

    function ocultarFicha() {
        clearTimeout(temporizador);
        ficha.hidden = true;
        armado = null;
    }

    function prepararFichas() {
        document.body.appendChild(ficha);
        var objetivos = [];
        document.querySelectorAll(".card[data-name]").forEach(function (el) {
            var ruta = NOMBRE_A_RUTA[el.getAttribute("data-name")];
            if (ruta) { el.setAttribute("data-sv-ruta", ruta); objetivos.push(el); }
        });
        document.querySelectorAll(".pv2-nav a[href]").forEach(function (el) {
            var ruta = el.getAttribute("href");
            if (CATALOGO[ruta] && ruta !== window.location.pathname) {
                el.setAttribute("data-sv-ruta", ruta);
                objetivos.push(el);
            }
        });

        objetivos.forEach(function (el) {
            if (!esTactil) {
                el.addEventListener("mouseenter", function () {
                    clearTimeout(temporizador);
                    temporizador = setTimeout(function () { mostrarFicha(el, false); }, 280);
                });
                el.addEventListener("mouseleave", ocultarFicha);
            }
            el.addEventListener("focus", function () { if (!esTactil) mostrarFicha(el, false); });
            el.addEventListener("blur", function () { if (!esTactil) ocultarFicha(); });
        });

        // Tactil: el primer toque muestra la ficha; el segundo (o "Abrir") entra.
        document.addEventListener("click", function (ev) {
            if (!esTactil) return;
            var el = ev.target.closest("[data-sv-ruta]");
            if (ev.target.closest(".sv-ficha")) return;
            if (!el) { ocultarFicha(); return; }
            if (armado === el) { ocultarFicha(); return; }   // segundo toque: deja pasar
            ev.preventDefault();
            ev.stopPropagation();
            mostrarFicha(el, true);
            armado = el;
        }, true);

        window.addEventListener("scroll", function () { if (!esTactil) ocultarFicha(); }, { passive: true });
        document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") ocultarFicha(); });
    }

    // -----------------------------------------------------
    // 2. Tutorial guiado
    // -----------------------------------------------------
    var PASOS = [
        {
            titulo: "Bienvenido a SafeVision",
            texto: "En unos minutos verás lo básico: encender el robot, conectarte, moverlo, " +
                   "llevarlo a otra red y apagarlo bien. Avanza con <b>Siguiente</b> o con las flechas; " +
                   "<b>Esc</b> lo cierra. Puedes volver a abrirlo con el botón <b>Tutorial</b>."
        },
        {
            titulo: "1 · Encender",
            texto: "Enciende el interruptor del robot y espera <b>2 minutos</b>. Al arrancar el robot " +
                   "queda en reposo: <b>no se mueve</b> hasta que apliques un perfil en Misión Pilotada.<br>" +
                   "Si pita sin parar es <b>batería baja</b>: apágalo bien y ponlo a cargar."
        },
        {
            titulo: "2 · Laptop y robot en la misma red",
            texto: "Si el robot conoce una red del lugar, se conecta a ella sola. Si no, crea la suya: " +
                   "<b>SafeVision-Robot</b>, siempre en la dirección <b>10.42.0.1</b>. Conecta tu laptop " +
                   "a esa misma red y arranca el dashboard con <code>./scripts/run_dashboard.sh</code>: " +
                   "encuentra al robot solo."
        },
        {
            sel: ".connection",
            titulo: "3 · Conexión",
            texto: "Esta casilla ya trae la dirección del robot. Si arriba dice <b>Desconectado</b>, pulsa " +
                   "<b>Conectar</b>. También acepta <code>yahboom.local</code>, o <code>10.42.0.1</code> " +
                   "cuando estás en la red propia del robot."
        },
        {
            sel: ".diagnostic",
            titulo: "4 · Estado del robot",
            texto: "Aquí ves qué partes están encendidas. Recién arrancado es normal ver <b>Driver</b> y " +
                   "<b>LiDAR</b> apagados: se encienden al aplicar un perfil."
        },
        {
            sel: '.card[data-name="Misión Pilotada"]',
            titulo: "5 · Mover el robot",
            texto: "Entra a <b>Misión Pilotada</b> y pulsa <b>Modo Libre</b> con el control en <b>Mando</b>. " +
                   "No hay botón Aplicar: ese clic ya lo activa (hasta 2 minutos; el cuadro Actividad " +
                   "muestra el avance). Ya puedes moverlo con el mando.<br>" +
                   "<b>Para pararlo, suelta el mando</b>: se detiene en medio segundo."
        },
        {
            sel: '.card[data-name="Mapear"]',
            titulo: "6 · Mapa de un lugar nuevo",
            texto: "Para que el robot navegue solo necesita el plano del lugar. En <b>Mapear</b> lo " +
                   "dibujas manejándolo con el mando. Antes, en Pilotada, elige un mapa (HAB2 sirve) y pulsa Misión Pilotada " +
                   "existente: el robot vuelve a él al terminar."
        },
        {
            sel: '.card[data-name="Wi-Fi"]',
            titulo: "7 · Llevar el robot a otra red",
            texto: "En un sitio nuevo, conecta la laptop a <b>SafeVision-Robot</b>, abre <b>Wi-Fi</b>, elige " +
                   "la red del lugar y escribe su contraseña. <b>Sólo redes de 2.4 GHz.</b> Luego pasa tu " +
                   "laptop a esa misma red."
        },
        {
            sel: '.card[data-name="Nodos"]',
            titulo: "8 · Si algo no responde",
            texto: "<b>Nodos</b> muestra cada parte del robot y deja encenderla o apagarla en orden. " +
                   "Pulsar otra vez el botón del modo (Modo Libre o Misión Pilotada) también reconstruye lo que falte."
        },
        {
            titulo: "9 · Apagar bien",
            texto: "<b>Nunca cortes la corriente sin apagar</b>: se daña la tarjeta de memoria. Desde la terminal:" +
                   "<pre>ssh pi@yahboom.local 'sudo shutdown -h now'</pre>" +
                   "(o <code>pi@10.42.0.1</code> en la red del robot). Espera a que se apague la luz verde y " +
                   "entonces apaga el interruptor."
        },
        {
            sel: "#svGuiaBtn",
            titulo: "10 · Prácticas y manuales",
            texto: "El botón <b>Guía</b> abre las prácticas de laboratorio y los manuales en un panel " +
                   "al lado. La página sigue funcionando: lees un paso y lo haces sin cambiar de " +
                   "ventana. El panel recuerda qué documento y qué parte estabas leyendo."
        },
        {
            sel: "#svTutorialBtn",
            titulo: "Listo",
            texto: "Pasa el ratón sobre cualquier tarjeta o enlace del menú para ver qué hace antes de " +
                   "abrirlo. La guía rápida, en el panel <b>Guía</b>, resume todo esto en una página."
        }
    ];

    var velo, foco, caja, indice = 0;

    function prepararTutorial() {
        velo = crear("div", "sv-tuto-velo");
        foco = crear("div", "sv-tuto-foco");
        caja = crear("div", "sv-tuto-caja");
        caja.setAttribute("role", "dialog");
        caja.setAttribute("aria-modal", "true");
        caja.setAttribute("aria-labelledby", "svTutoTitulo");
        [velo, foco, caja].forEach(function (el) { el.hidden = true; document.body.appendChild(el); });
        velo.addEventListener("click", cerrarTutorial);
        caja.addEventListener("click", function (ev) {
            var b = ev.target.closest("button");
            if (!b) return;
            if (b.dataset.accion === "siguiente") ir(indice + 1);
            if (b.dataset.accion === "anterior") ir(indice - 1);
            if (b.dataset.accion === "cerrar") cerrarTutorial();
        });
        document.addEventListener("keydown", function (ev) {
            if (!tutorialAbierto) return;
            if (ev.key === "Escape") cerrarTutorial();
            else if (ev.key === "ArrowRight") ir(indice + 1);
            else if (ev.key === "ArrowLeft") ir(indice - 1);
        });
        window.addEventListener("resize", function () { if (tutorialAbierto) situar(); });
        window.addEventListener("scroll", function () { if (tutorialAbierto) situar(); }, { passive: true });
    }

    function objetivo() {
        var paso = PASOS[indice];
        var el = paso.sel ? document.querySelector(paso.sel) : null;
        // Un elemento oculto (por ejemplo el boton Guia con el panel abierto) no se resalta.
        return el && el.getClientRects().length ? el : null;
    }

    function situar() {
        var el = objetivo();
        if (!el) {
            foco.hidden = true;
            velo.classList.add("oscuro");
            caja.classList.add("centrada");
            caja.style.left = caja.style.top = "";
            return;
        }
        velo.classList.remove("oscuro");
        caja.classList.remove("centrada");
        var r = el.getBoundingClientRect();
        var m = 6;
        foco.hidden = false;
        foco.style.left = (r.left - m) + "px";
        foco.style.top = (r.top - m) + "px";
        foco.style.width = (r.width + 2 * m) + "px";
        foco.style.height = (r.height + 2 * m) + "px";
        colocar(caja, { left: r.left - m, right: r.right + m, top: r.top - m, bottom: r.bottom + m,
                        width: r.width + 2 * m, height: r.height + 2 * m }, 14);
    }

    function ir(n) {
        if (n < 0) return;
        if (n >= PASOS.length) { cerrarTutorial(); return; }
        indice = n;
        var paso = PASOS[indice];
        var ultimo = indice === PASOS.length - 1;
        var puntos = PASOS.map(function (_p, i) {
            return '<i class="' + (i === indice ? "activo" : "") + '"></i>';
        }).join("");
        caja.innerHTML =
            '<div class="sv-tuto-cabeza"><span>Tutorial · ' + (indice + 1) + " de " + PASOS.length + "</span>" +
            '<button type="button" class="sv-tuto-x" data-accion="cerrar" aria-label="Cerrar">×</button></div>' +
            '<h3 id="svTutoTitulo">' + paso.titulo + "</h3>" +
            '<div class="sv-tuto-texto">' + paso.texto + "</div>" +
            '<div class="sv-tuto-pie"><div class="sv-tuto-puntos">' + puntos + "</div>" +
            '<div class="sv-tuto-botones">' +
            (indice > 0 ? '<button type="button" class="sv-tuto-btn" data-accion="anterior">Anterior</button>' : "") +
            '<button type="button" class="sv-tuto-btn primario" data-accion="siguiente">' +
            (ultimo ? "Terminar" : "Siguiente") + "</button></div></div>";
        var el = objetivo();
        if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
        situar();
        setTimeout(situar, 350);   // tras el desplazamiento suave
        var siguiente = caja.querySelector('[data-accion="siguiente"]');
        if (siguiente) siguiente.focus({ preventScroll: true });
    }

    function abrirTutorial() {
        ocultarFicha();
        tutorialAbierto = true;
        [velo, caja].forEach(function (el) { el.hidden = false; });
        document.body.classList.add("sv-tuto-activo");
        ir(0);
    }

    function cerrarTutorial() {
        tutorialAbierto = false;
        [velo, foco, caja].forEach(function (el) { el.hidden = true; });
        document.body.classList.remove("sv-tuto-activo");
        try { localStorage.setItem("sv_tutorial_visto", "1"); } catch (e) { /* sin almacenamiento */ }
        var b = document.getElementById("svTutorialBtn");
        if (b) b.classList.remove("sv-tuto-pulso");
    }

    function prepararBoton() {
        var boton = document.getElementById("svTutorialBtn");
        if (boton) {
            boton.addEventListener("click", abrirTutorial);
            var visto = false;
            try { visto = localStorage.getItem("sv_tutorial_visto") === "1"; } catch (e) { visto = false; }
            if (!visto) boton.classList.add("sv-tuto-pulso");
            if (/[?&]tutorial=1\b/.test(window.location.search)) setTimeout(abrirTutorial, 400);
            return;
        }
        // Paginas interiores: enlace al tutorial de la portada.
        var nav = document.querySelector(".pv2-nav");
        if (nav) {
            var a = crear("a", "sv-nav-tutorial", "Tutorial");
            a.href = "/?tutorial=1";
            nav.appendChild(a);
        }
    }

    function iniciar() {
        prepararFichas();
        prepararTutorial();
        prepararBoton();
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
    else iniciar();
})();
