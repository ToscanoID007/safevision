(() => {

    if (window.safeVisionPilotadaV2Installed) {
        return;
    }

    window.safeVisionPilotadaV2Installed = true;

    const pv2 = {
        runtime: null,
        lastSignature: null,
        switching: false,
        pollTimer: null,
        navTimer: null
    };

    const el = id =>
        document.getElementById(id);

    function activity(message) {
        const box = el("log");

        if (!box) {
            return;
        }

        const now = new Date().toLocaleTimeString();
        const line = `[${now}] Runtime · ${message}`;

        if (
            !box.textContent
            ||
            box.textContent.trim() === "SafeVision Pilotada preparada."
        ) {
            box.textContent = line;
            return;
        }

        box.textContent = line + "\n" + box.textContent;
    }

    function resourceState(name) {
        if (
            !pv2.runtime
            ||
            !pv2.runtime.resources
            ||
            !pv2.runtime.resources[name]
        ) {
            return false;
        }

        return Boolean(
            pv2.runtime.resources[name].active
        );
    }

    function setStatus(
        id,
        active,
        activeText = "ACTIVO",
        inactiveText = "OFF"
    ) {
        const node = el(id);

        if (!node) {
            return;
        }

        node.textContent =
            active
                ? activeText
                : inactiveText;

        node.classList.toggle(
            "pv2-status-ok",
            active
        );

        node.classList.toggle(
            "pv2-status-off",
            !active
        );
    }

    function selectedMap() {
        const select = el("mapSelect");

        if (select && select.value) {
            return select.value;
        }

        if (
            pv2.runtime
            &&
            pv2.runtime.profile
            &&
            pv2.runtime.profile.map
        ) {
            return pv2.runtime.profile.map;
        }

        return null;
    }

    function syncMapSelection() {
        const select = el("mapSelect");

        const runtimeMap =
            pv2.runtime
            &&
            pv2.runtime.profile
                ? pv2.runtime.profile.map
                : null;

        if (
            !select
            ||
            !runtimeMap
            ||
            select.value === runtimeMap
        ) {
            return;
        }

        const option =
            Array.from(select.options).find(
                item =>
                    item.value === runtimeMap
            );

        if (option) {
            select.value = runtimeMap;
        }
    }

    function runtimeSignature(runtime) {
        const resources = runtime.resources || {};

        return JSON.stringify({
            profile:
                runtime.profile
                &&
                runtime.profile.requested,

            inferred:
                runtime.profile
                &&
                runtime.profile.inferred,

            map:
                runtime.profile
                &&
                runtime.profile.map,

            control:
                runtime.control_mode,

            lidar:
                Boolean(
                    resources.lidar
                    &&
                    resources.lidar.active
                ),

            localization:
                Boolean(
                    resources.localization
                    &&
                    resources.localization.active
                ),

            navigation:
                Boolean(
                    resources.navigation
                    &&
                    resources.navigation.active
                ),

            nav_queue:
                Boolean(
                    resources.nav_queue
                    &&
                    resources.nav_queue.active
                ),

            mapping:
                Boolean(
                    resources.mapping
                    &&
                    resources.mapping.active
                )
        });
    }

    function renderRuntime(runtime) {
        pv2.runtime = runtime;

        const requested =
            runtime.profile
            &&
            runtime.profile.requested
                ? runtime.profile.requested
                : "desconocido";

        const pilotada = requested === "pilotada";
        const libre = requested === "libre";

        const libreButton = el("profileLibreButton");
        const pilotButton = el("profilePilotadaButton");

        if (libreButton) {
            libreButton.classList.toggle(
                "is-active",
                libre
            );

            libreButton.disabled = pv2.switching;
        }

        if (pilotButton) {
            pilotButton.classList.toggle(
                "is-active",
                pilotada
            );

            pilotButton.disabled = pv2.switching;
        }

        const profileText = el("pv2ProfileText");

        if (profileText) {
            profileText.textContent =
                requested.toUpperCase();
        }

        const badge = el("pv2ProfileBadge");

        if (badge) {
            badge.textContent =
                pilotada
                    ? "PILOTADA"
                    : libre
                        ? "LIBRE"
                        : requested.toUpperCase();
        }

        const mapMode = el("pv2MapMode");

        if (mapMode) {
            mapMode.textContent =
                pilotada
                    ? "OPERATIVO"
                    : "SOLO LECTURA";
        }

        const gate = el("pilotMapGate");

        if (gate) {
            gate.hidden = pilotada;
        }

        const mapName = el("pv2MapName");

        if (mapName) {
            mapName.textContent =
                `Mapa ${runtime.profile.map || "—"}`;
        }

        const version = el("pv2RuntimeVersion");

        if (version) {
            version.textContent =
                runtime.manager_version
                    ? `v${runtime.manager_version}`
                    : "—";
        }

        setStatus(
            "pv2MandoStatus",
            resourceState("mando"),
            "ACTIVO",
            "OFF"
        );

        setStatus(
            "pv2KeyboardStatus",
            resourceState("teclado"),
            "ACTIVO",
            "OFF"
        );

        setStatus(
            "pv2LocalizationStatus",
            resourceState("localization"),
            "ACTIVA",
            "OFF"
        );

        setStatus(
            "pv2NavigationStatus",
            resourceState("navigation")
            &&
            resourceState("nav_queue"),
            "LISTA",
            "OFF"
        );

        const signature = runtimeSignature(runtime);

        if (
            pv2.lastSignature !== null
            &&
            pv2.lastSignature !== signature
        ) {
            activity(
                (
                    `${requested.toUpperCase()}`
                    +
                    ` · ${String(runtime.control_mode || "—").toUpperCase()}`
                    +
                    ` · mapa ${runtime.profile.map || "—"}`
                    +
                    ` · navegación ${resourceState("navigation") ? "activa" : "off"}`
                )
            );
        }

        pv2.lastSignature = signature;

        syncMapSelection();
    }

    async function refreshRuntime() {
        try {
            const response =
                await fetch(
                    "/runtime/status",
                    {
                        cache: "no-store"
                    }
                );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message
                    ||
                    data.error
                    ||
                    "Runtime no disponible."
                );
            }

            renderRuntime(data);

        } catch (error) {
            const badge = el("pv2ProfileBadge");

            if (badge) {
                badge.textContent = "SIN RUNTIME";
            }
        }
    }

    async function changeProfile(profile) {
        if (
            pv2.switching
            ||
            !pv2.runtime
        ) {
            return;
        }

        const control =
            pv2.runtime.control_mode
            ||
            "mando";

        const payload = {
            profile: profile,
            control: control
        };

        if (profile === "pilotada") {
            const map = selectedMap();

            if (!map) {
                activity(
                    "Selecciona un mapa antes de activar Misión Pilotada."
                );
                return;
            }

            payload.map = map;
        }

        pv2.switching = true;
        renderRuntime(pv2.runtime);

        activity(
            `Solicitando perfil ${profile.toUpperCase()}...`
        );

        try {
            const response =
                await fetch(
                    "/runtime/profile",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify(payload)
                    }
                );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error
                    ||
                    data.message
                    ||
                    "Cambio de perfil rechazado."
                );
            }

            const status =
                data.status
                ||
                data;

            renderRuntime(status);

            activity(
                `Perfil ${profile.toUpperCase()} confirmado.`
            );

        } catch (error) {
            activity(
                `Perfil: ${error.message}`
            );

        } finally {
            pv2.switching = false;
            await refreshRuntime();
        }
    }

    async function refreshNavState() {
        try {
            const response =
                await fetch(
                    "/nav/status",
                    {
                        cache: "no-store"
                    }
                );

            const data = await response.json();
            const target = el("pv2QueueState");

            if (!target) {
                return;
            }

            if (
                response.ok
                &&
                data
                &&
                data.ok
            ) {
                const running =
                    Boolean(
                        data.running
                        ||
                        data.active
                    );

                target.textContent =
                    running
                        ? "Cola EN CURSO"
                        : "Cola LISTA";

            } else {
                target.textContent = "Cola —";
            }

        } catch (_) {
            // El Runtime principal tiene prioridad.
        }
    }

    function install() {
        const libreButton = el("profileLibreButton");
        const pilotButton = el("profilePilotadaButton");

        if (libreButton) {
            libreButton.addEventListener(
                "click",
                () => {
                    changeProfile("libre");
                }
            );
        }

        if (pilotButton) {
            pilotButton.addEventListener(
                "click",
                () => {
                    changeProfile("pilotada");
                }
            );
        }

        const select = el("mapSelect");

        if (select) {
            select.addEventListener(
                "change",
                () => {
                    const map = selectedMap();

                    if (map) {
                        activity(
                            `Mapa seleccionado: ${map}.`
                        );
                    }
                }
            );
        }

        refreshRuntime();
        refreshNavState();

        pv2.pollTimer =
            window.setInterval(
                refreshRuntime,
                1000
            );

        pv2.navTimer =
            window.setInterval(
                refreshNavState,
                1500
            );
    }

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            install
        );

    } else {
        install();
    }

})();

// =========================================================
// SAFEVISION ETAPA 7B - PILOTADA V2 UX
// =========================================================

(() => {
    "use strict";

    if (window.safeVisionPilotadaEtapa7B) {
        return;
    }

    window.safeVisionPilotadaEtapa7B = true;

    const UI_KEY =
        "safevision.pilotada.ui.v2";

    const SELECTED_KEY =
        "safevision.pilotada.nav.selected.v2";

    let selectedPointId = null;
    let queueDecorating = false;


    function byId(id) {
        return document.getElementById(id);
    }


    function norm(value) {
        return String(value || "")
            .replace(/\s+/g, " ")
            .trim()
            .toLowerCase();
    }


    function readUi() {
        try {
            const raw = sessionStorage.getItem(UI_KEY);
            return raw ? (JSON.parse(raw) || {}) : {};
        } catch (_) {
            return {};
        }
    }


    function writeUi(patch) {
        try {
            sessionStorage.setItem(
                UI_KEY,
                JSON.stringify(
                    Object.assign(
                        {},
                        readUi(),
                        patch
                    )
                )
            );
        } catch (_) {
            // opcional
        }
    }


    function findByText(selector, variants) {
        const wanted = variants.map(norm);

        return Array.from(
            document.querySelectorAll(selector)
        ).find(
            item => {
                const text = norm(item.textContent);

                return wanted.some(
                    value =>
                        text === value
                        || text.includes(value)
                );
            }
        ) || null;
    }


    function rowButton(row, variants) {
        if (!row) {
            return null;
        }

        const wanted = variants.map(norm);

        return Array.from(
            row.querySelectorAll("button")
        ).find(
            button => {
                const text = norm(button.textContent);

                return wanted.some(
                    value =>
                        text === value
                        || text.includes(value)
                );
            }
        ) || null;
    }


    async function getJson(url, options) {
        const response =
            await fetch(
                url,
                Object.assign(
                    {cache: "no-store"},
                    options || {}
                )
            );

        let data = {};

        try {
            data = await response.json();
        } catch (_) {
            data = {};
        }

        return {response, data};
    }


    function requestedProfile(status) {
        return (
            status
            && status.profile
            && status.profile.requested
        )
            ? String(status.profile.requested).toLowerCase()
            : "";
    }


    function controlMode(status) {
        return (
            status
            && status.control_mode
        )
            ? String(status.control_mode).toLowerCase()
            : "";
    }


    function mappingActive(status) {
        return Boolean(
            (
                status
                && status.resources
                && status.resources.mapping
                && status.resources.mapping.active
            )
            || requestedProfile(status) === "mapear"
        );
    }


    async function runtimeStatus() {
        try {
            const result = await getJson("/runtime/status");

            return result.response.ok
                ? result.data
                : null;
        } catch (_) {
            return null;
        }
    }


    async function restoreRuntimePreference() {

        /* SAFVision 7D - Runtime source of truth */
        try {
            const runtimeResponse =
                await fetch(
                    "/runtime/status",
                    {
                        cache:
                            "no-store"
                    }
                );

            const runtimeStatus =
                await runtimeResponse.json();

            const runtimeProfile =
                runtimeStatus
                &&
                runtimeStatus.profile
                    ? runtimeStatus.profile.requested
                    : null;

            if (
                runtimeResponse.ok
                &&
                (
                    runtimeProfile === "libre"
                    ||
                    runtimeProfile === "pilotada"
                )
            ) {
                let stored =
                    {};

                try {
                    const raw =
                        sessionStorage.getItem(
                            UI_KEY
                        );

                    if (raw) {
                        const parsed =
                            JSON.parse(
                                raw
                            );

                        if (
                            parsed
                            &&
                            typeof parsed === "object"
                        ) {
                            stored =
                                parsed;
                        }
                    }
                } catch (_) {
                    stored =
                        {};
                }

                stored.profile =
                    runtimeProfile;

                stored.control =
                    runtimeStatus.control_mode === "teclado"
                        ? "teclado"
                        : "mando";

                const runtimeMap =
                    runtimeStatus.profile
                    &&
                    typeof runtimeStatus.profile.map === "string"
                        ? runtimeStatus.profile.map.trim()
                        : "";

                if (runtimeMap) {
                    stored.map =
                        runtimeMap;

                    stored.mapName =
                        runtimeMap;

                    stored.selectedMap =
                        runtimeMap;
                }

                try {
                    sessionStorage.setItem(
                        UI_KEY,
                        JSON.stringify(
                            stored
                        )
                    );
                } catch (_) {
                    // sessionStorage no disponible.
                }

                return;
            }

        } catch (_) {
            // Si Runtime no responde, conservar el fallback anterior.
        }

        const saved = readUi();

        const hasSaved =
            saved.profile === "libre"
            || saved.profile === "pilotada";

        const profile =
            hasSaved
                ? saved.profile
                : "libre";

        const control =
            saved.control === "teclado"
                ? "teclado"
                : "mando";

        const status = await runtimeStatus();

        if (!status || mappingActive(status)) {
            return;
        }

        const map =
            saved.map
            || (
                status.profile
                && status.profile.map
            )
            || "";

        if (
            profile === "pilotada"
            && !map
        ) {
            return;
        }

        if (
            requestedProfile(status) === profile
            && controlMode(status) === control
            && (
                profile !== "pilotada"
                || (
                    status.profile
                    && status.profile.map === map
                )
            )
        ) {
            if (!hasSaved) {
                writeUi({profile, control});
            }
            return;
        }

        const payload = {profile, control};

        if (profile === "pilotada") {
            payload.map = map;
        }

        try {
            const result =
                await getJson(
                    "/runtime/profile",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify(payload)
                    }
                );

            if (
                result.response.ok
                && result.data
                && result.data.ok
            ) {
                writeUi({profile, control});
            }
        } catch (_) {
            // no bloquea la ventana
        }
    }


    function captureRuntimeAfterClick() {
        window.setTimeout(
            async () => {
                const status = await runtimeStatus();

                if (!status || mappingActive(status)) {
                    return;
                }

                const profile =
                    requestedProfile(status);

                const control =
                    controlMode(status);

                if (
                    profile !== "libre"
                    && profile !== "pilotada"
                ) {
                    return;
                }

                writeUi({profile, control});
            },
            700
        );
    }


    function installRuntimePersistence() {
        [
            ["modo libre"],
            ["misión pilotada", "mision pilotada"],
            ["mando"],
            ["teclado"]
        ].forEach(
            names => {
                const button =
                    findByText(
                        "button",
                        names
                    );

                if (button) {
                    button.addEventListener(
                        "click",
                        captureRuntimeAfterClick
                    );
                }
            }
        );
    }


    function installBackButton() {
        if (byId("pv2BackMenu")) {
            return;
        }

        const topbar =
            document.querySelector(
                ".pv2-topbar, .topbar, header"
            );

        if (!topbar) {
            return;
        }

        const link = document.createElement("a");
        link.id = "pv2BackMenu";
        link.href = "/";
        link.textContent = "← Regresar a menú";
        link.title = "Volver al menú SafeVision";

        const target =
            topbar.querySelector(
                ".pv2-top-status, .top-status"
            )
            ||
            topbar;

        target.prepend(link);
    }


    function installCameraHeader() {
        const video = byId("videoFeed");
        const confidence = byId("confidence");
        const confidenceValue = byId("confidenceValue");

        if (!video) {
            return;
        }

        const panel =
            video.closest(
                ".pv2-camera-card, .viewer-panel, .panel, section"
            );

        if (!panel) {
            return;
        }

        const title =
            panel.querySelector(
                ".pv2-view-header, .viewer-title"
            );

        if (!title) {
            return;
        }

        const h2 = title.querySelector("h2");

        if (h2) {
            h2.textContent = "RoscamerX3CAM";
        }

        const eyebrow =
            title.querySelector(
                ".pv2-eyebrow"
            );

        if (eyebrow) {
            eyebrow.remove();
        }

        let row = byId("pv2CameraTitleRow");

        if (!row) {
            row = document.createElement("div");
            row.id = "pv2CameraTitleRow";
            row.className = "pv2-camera-title-row";

            if (h2) {
                row.appendChild(h2);
            }

            const firstBlock =
                title.querySelector("div");

            if (firstBlock) {
                firstBlock.replaceChildren(row);
            } else {
                title.prepend(row);
            }
        }

        if (
            confidence
            && !byId("pv2CameraConfidence")
        ) {
            const oldBox =
                confidence.closest(
                    ".pv2-confidence, .confidence-row"
                )
                || confidence.parentElement;

            const holder =
                document.createElement("div");

            holder.id = "pv2CameraConfidence";
            holder.className =
                "pv2-camera-confidence";

            const label =
                document.createElement("span");

            label.textContent =
                "Confianza";

            holder.appendChild(label);
            holder.appendChild(confidence);

            if (confidenceValue) {
                holder.appendChild(confidenceValue);
            }

            row.appendChild(holder);

            if (
                oldBox
                && oldBox !== holder
                && oldBox.childElementCount === 0
            ) {
                oldBox.remove();
            }
        }
    }


    function installGuideLabel() {
        const button =
            findByText(
                "button",
                [
                    "abrir teclado",
                    "ver teclado",
                    "guía de teclado",
                    "guia de teclado"
                ]
            );

        if (button) {
            button.textContent =
                "Ver guía de teclado";

            button.title =
                "La guía es solo ayuda visual; no cambia el control.";
        }
    }


    function applyRotation(value, persist) {
        let rotation = Number(value);

        if (!Number.isFinite(rotation)) {
            rotation = 0;
        }

        rotation =
            Math.max(
                -180,
                Math.min(180, rotation)
            );

        if (typeof mapView !== "undefined") {
            mapView.rotation = rotation;
        }

        const slider = byId("pv2MapRotation");
        const output = byId("pv2MapRotationValue");

        if (slider) {
            slider.value =
                String(Math.round(rotation));
        }

        if (output) {
            output.textContent =
                Math.round(rotation) + "°";
        }

        if (typeof applyMapView === "function") {
            applyMapView();
        }

        if (
            typeof updateRobotMarker
            === "function"
        ) {
            window.requestAnimationFrame(
                () => {
                    try {
                        updateRobotMarker();
                    } catch (_) {
                        // no-op
                    }
                }
            );
        }

        if (persist) {
            writeUi({rotation});
        }
    }

    // SAFEVISION ROTACION MINIMA API V1.2
    window.safeVisionPilotadaRotationApi = {
        set:
            value => {
                applyRotation(
                    value,
                    true
                );
            },

        get:
            () => {
                if (
                    typeof mapView !== "undefined"
                    &&
                    Number.isFinite(
                        Number(
                            mapView.rotation
                        )
                    )
                ) {
                    return Number(
                        mapView.rotation
                    );
                }

                return 0;
            }
    };



    function installRotation() {
        if (byId("pv2MapRotationControl")) {
            return;
        }

        const toolbar =
            document.querySelector(
                ".pv2-map-toolbar, .map-toolbar"
            );

        if (!toolbar) {
            return;
        }

        const label =
            document.createElement("label");

        label.id = "pv2MapRotationControl";
        label.innerHTML = `
            <span>Girar</span>
            <input
                id="pv2MapRotation"
                type="range"
                min="-180"
                max="180"
                step="1"
                value="0"
            >
            <output id="pv2MapRotationValue">0°</output>
        `;

        toolbar.appendChild(label);

        const slider = byId("pv2MapRotation");

        slider.addEventListener(
            "input",
            () => applyRotation(
                slider.value,
                true
            )
        );

        const saved = Number(readUi().rotation);

        applyRotation(
            Number.isFinite(saved)
                ? saved
                : 0,
            false
        );
    }


    function restoreConfidence() {
        const input = byId("confidence");

        if (!input) {
            return;
        }

        const saved =
            Number(readUi().confidence);

        if (Number.isFinite(saved)) {
            input.value = String(saved);

            input.dispatchEvent(
                new Event(
                    "input",
                    {bubbles: true}
                )
            );
        }

        input.addEventListener(
            "input",
            () => writeUi({
                confidence:
                    Number(input.value)
            })
        );
    }


    function restoreMap() {
        const select = byId("mapSelect");

        if (!select) {
            return;
        }

        const desired =
            String(readUi().map || "");

        let done = false;

        function attempt() {
            if (done || !desired) {
                return;
            }

            const exists =
                Array.from(select.options)
                .some(
                    option =>
                        option.value === desired
                );

            if (!exists) {
                return;
            }

            select.value = desired;
            done = true;

            const show = byId("loadMapButton");

            if (show) {
                window.setTimeout(
                    () => show.click(),
                    80
                );
            }
        }

        select.addEventListener(
            "change",
            () => writeUi({
                map: select.value
            })
        );

        const observer =
            new MutationObserver(attempt);

        observer.observe(
            select,
            {childList: true}
        );

        attempt();
        window.setTimeout(attempt, 500);

        window.setTimeout(
            () => {
                attempt();
                observer.disconnect();
            },
            5000
        );
    }


    function readSelected() {
        try {
            return sessionStorage.getItem(SELECTED_KEY);
        } catch (_) {
            return null;
        }
    }


    function saveSelected(id) {
        selectedPointId = id || null;

        try {
            if (selectedPointId) {
                sessionStorage.setItem(
                    SELECTED_KEY,
                    selectedPointId
                );
            } else {
                sessionStorage.removeItem(
                    SELECTED_KEY
                );
            }
        } catch (_) {
            // opcional
        }
    }


    function selectedRow() {
        const body = byId("mapNavQueueBody");

        if (!body || !selectedPointId) {
            return null;
        }

        return Array.from(
            body.querySelectorAll("tr")
        ).find(
            row =>
                row.dataset.pointId
                === selectedPointId
        ) || null;
    }


    function updateQueueActions() {
        const orient =
            byId("pv2NavOrientationAction");

        const remove =
            byId("pv2NavDeleteAction");

        if (!orient || !remove) {
            return;
        }

        const row = selectedRow();

        if (!row) {
            orient.textContent = "Orientar";
            orient.disabled = true;
            remove.disabled = true;
            return;
        }

        const cells = row.children;

        const yaw =
            cells.length >= 5
                ? norm(cells[4].textContent)
                : "auto";

        orient.textContent =
            yaw === "auto"
                ? "Orientar"
                : "Auto";

        orient.disabled = false;
        remove.disabled = false;
    }


    function selectRow(row) {
        const body = byId("mapNavQueueBody");

        if (!body || !row) {
            return;
        }

        Array.from(
            body.querySelectorAll("tr")
        ).forEach(
            item => item.classList.toggle(
                "pv2-selected",
                item === row
            )
        );

        saveSelected(row.dataset.pointId);
        updateQueueActions();
    }


    function ensureQueueActions() {
        const panel = byId("mapNavQueuePanel");

        if (!panel) {
            return null;
        }

        const header =
            panel.querySelector(
                ".map-nav-table-header"
            );

        if (!header) {
            return null;
        }

        let actions = byId("pv2NavQueueActions");

        if (actions) {
            return actions;
        }

        actions = document.createElement("div");
        actions.id = "pv2NavQueueActions";

        actions.innerHTML = `
            <button
                id="pv2NavOrientationAction"
                type="button"
                disabled
            >Orientar</button>

            <button
                id="pv2NavDeleteAction"
                type="button"
                disabled
            >Eliminar</button>

            <button
                id="pv2NavClearAction"
                type="button"
            >Limpiar</button>
        `;

        header.appendChild(actions);

        byId("pv2NavOrientationAction")
            .addEventListener(
                "click",
                () => {
                    const row = selectedRow();

                    if (!row) {
                        return;
                    }

                    const makeAuto =
                        norm(
                            byId(
                                "pv2NavOrientationAction"
                            ).textContent
                        )
                        === "auto";

                    const target =
                        makeAuto
                            ? rowButton(row, ["auto"])
                            : rowButton(
                                row,
                                [
                                    "orientar",
                                    "orientación",
                                    "orientacion"
                                ]
                            );

                    if (target) {
                        target.click();
                    }
                }
            );

        byId("pv2NavDeleteAction")
            .addEventListener(
                "click",
                () => {
                    const target =
                        rowButton(
                            selectedRow(),
                            ["eliminar"]
                        );

                    if (target) {
                        target.click();
                    }
                }
            );

        byId("pv2NavClearAction")
            .addEventListener(
                "click",
                () => {
                    const legacy =
                        byId("mapNavClearButton");

                    if (legacy) {
                        legacy.click();
                    }
                }
            );

        return actions;
    }


    function decorateRow(row) {
        if (
            !row
            || row.dataset.pv2Decorated === "1"
        ) {
            return;
        }

        const cells =
            Array.from(row.children);

        /*
         * Original:
         * # | Punto | X | Y | Orientación | Estado | Acciones
         */
        if (cells.length < 7) {
            return;
        }

        const point = cells[1];
        const xCell = cells[2];
        const yCell = cells[3];
        const yawCell = cells[4];
        const stateCell = cells[5];
        const actionsCell = cells[6];

        const x = Number(xCell.textContent);
        const y = Number(yCell.textContent);

        xCell.textContent =
            (
                Number.isFinite(x)
                && Number.isFinite(y)
            )
                ? `(${x.toFixed(2)}, ${y.toFixed(2)})`
                : `(${xCell.textContent}, ${yCell.textContent})`;

        yCell.remove();

        /* # Punto Coordenadas Estado Orientación Acciones */
        row.insertBefore(stateCell, yawCell);

        row.dataset.pointId =
            String(point.textContent || "").trim();

        row.dataset.pv2Decorated = "1";

        Array.from(
            actionsCell.querySelectorAll("button")
        ).forEach(
            button => {
                const text = norm(button.textContent);

                if (text !== "↑" && text !== "↓") {
                    button.style.display = "none";
                }
            }
        );

        const down = rowButton(row, ["↓"]);
        const up = rowButton(row, ["↑"]);

        if (down) {
            down.style.order = "1";
        }

        if (up) {
            up.style.order = "2";
        }

        row.addEventListener(
            "click",
            event => {
                if (
                    event.target
                    && event.target.closest("button")
                ) {
                    return;
                }

                selectRow(row);
            }
        );

        if (
            selectedPointId
            && row.dataset.pointId === selectedPointId
        ) {
            row.classList.add("pv2-selected");
        }
    }


    function decorateQueue() {
        if (queueDecorating) {
            return;
        }

        queueDecorating = true;

        try {
            ensureQueueActions();

            const table = byId("mapNavQueueTable");
            const body = byId("mapNavQueueBody");

            if (!table || !body) {
                return;
            }

            const head =
                table.querySelector("thead tr");

            if (
                head
                && head.dataset.pv2Decorated !== "1"
            ) {
                head.innerHTML = `
                    <th>#</th>
                    <th>Punto</th>
                    <th>Coordenadas</th>
                    <th>Estado</th>
                    <th>Orientación</th>
                    <th>Orden</th>
                `;

                head.dataset.pv2Decorated = "1";
            }

            Array.from(
                body.querySelectorAll("tr")
            ).forEach(decorateRow);

            if (
                selectedPointId
                && !selectedRow()
            ) {
                saveSelected(null);
            }

            updateQueueActions();

        } finally {
            queueDecorating = false;
        }
    }


    function installQueueObserver() {
        selectedPointId = readSelected();

        function waitPanel() {
            const panel = byId("mapNavQueuePanel");

            if (!panel) {
                window.setTimeout(waitPanel, 250);
                return;
            }

            decorateQueue();

            const observer =
                new MutationObserver(
                    () => window.requestAnimationFrame(
                        decorateQueue
                    )
                );

            observer.observe(
                panel,
                {
                    childList: true,
                    subtree: true
                }
            );
        }

        waitPanel();
    }


    function install() {
        installBackButton();
        installCameraHeader();
        installGuideLabel();
        installRotation();
        restoreConfidence();
        restoreMap();
        installRuntimePersistence();
        installQueueObserver();

        /*
         * Primera entrada en la sesión: Libre + Mando.
         * Volver desde menú: restaura la elección de esta pestaña.
         * Nunca pisa Mapear.
         */
        restoreRuntimePreference();
    }


    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            install,
            {once: true}
        );
    } else {
        install();
    }
})();

// =========================================================
// SAFEVISION ETAPA 7C - AJUSTE VISUAL FINAL
// =========================================================

(() => {
    "use strict";

    if (window.safeVisionPilotadaEtapa7C) {
        return;
    }

    window.safeVisionPilotadaEtapa7C = true;


    function applyEtapa7CVisuals() {
        const video =
            document.getElementById(
                "videoFeed"
            );

        if (video) {
            const card =
                video.closest(
                    ".pv2-camera-card"
                );

            if (card) {
                const title =
                    card.querySelector(
                        ".pv2-view-header h2"
                    );

                if (title) {
                    title.textContent =
                        "RoscamerX3CAM";
                }
            }
        }


        /*
         * Etapa 7B movió input + porcentaje a la cabecera.
         * Eliminamos el cascarón que quedó con el texto
         * "Confianza" en el panel izquierdo.
         */
        document.querySelectorAll(
            ".pv2-model-card .pv2-confidence"
        ).forEach(
            box => {
                if (
                    !box.querySelector(
                        "#confidence"
                    )
                ) {
                    box.remove();
                }
            }
        );


        const back =
            document.getElementById(
                "pv2BackMenu"
            );

        if (back) {
            back.setAttribute(
                "aria-label",
                "Regresar a menú"
            );
        }
    }


    function install() {
        applyEtapa7CVisuals();

        window.requestAnimationFrame(
            applyEtapa7CVisuals
        );

        window.setTimeout(
            applyEtapa7CVisuals,
            250
        );
    }


    if (
        document.readyState
        ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            install,
            {
                once:
                    true
            }
        );

    } else {
        install();
    }

})();


/* SAFEVISION 7D - PERSISTENCIA DE VISTA */
(() => {
    const KEY =
        "safevision.pilotada.ui.v2";

    function readStoredUi() {
        try {
            const raw =
                sessionStorage.getItem(
                    KEY
                );

            if (!raw) {
                return {};
            }

            const parsed =
                JSON.parse(
                    raw
                );

            return (
                parsed
                &&
                typeof parsed === "object"
            )
                ? parsed
                : {};

        } catch (_) {
            return {};
        }
    }


    function writeStoredUi(
        value
    ) {
        try {
            sessionStorage.setItem(
                KEY,
                JSON.stringify(
                    value
                )
            );
        } catch (_) {
            // sessionStorage no disponible.
        }
    }


    function capturePilotadaView() {
        const stored =
            readStoredUi();

        const map =
            document.getElementById(
                "mapSelect"
            );

        if (
            map
            &&
            typeof map.value === "string"
            &&
            map.value.trim()
        ) {
            const mapName =
                map.value.trim();

            stored.map =
                mapName;

            stored.mapName =
                mapName;

            stored.selectedMap =
                mapName;
        }

        const rotation =
            (
                document.getElementById(
                    "mapRotationSlider"
                )
                ||
                document.getElementById(
                    "pv2MapRotation"
                )
                ||
                document.getElementById(
                    "rotationSlider"
                )
            );

        if (
            rotation
            &&
            rotation.value !== undefined
        ) {
            stored.rotation =
                Number(
                    rotation.value
                );
        }

        const confidence =
            document.getElementById(
                "confidence"
            );

        if (
            confidence
            &&
            confidence.value !== undefined
        ) {
            stored.confidence =
                Number(
                    confidence.value
                );
        }

        writeStoredUi(
            stored
        );
    }


    document.addEventListener(
        "DOMContentLoaded",
        () => {
            const map =
                document.getElementById(
                    "mapSelect"
                );

            const rotation =
                (
                    document.getElementById(
                        "mapRotationSlider"
                    )
                    ||
                    document.getElementById(
                        "pv2MapRotation"
                    )
                    ||
                    document.getElementById(
                        "rotationSlider"
                    )
                );

            const confidence =
                document.getElementById(
                    "confidence"
                );

            for (
                const element
                of [
                    map,
                    rotation,
                    confidence
                ]
            ) {
                if (!element) {
                    continue;
                }

                element.addEventListener(
                    "change",
                    capturePilotadaView
                );
            }

            window.setInterval(
                capturePilotadaView,
                1500
            );
        }
    );

    window.addEventListener(
        "pagehide",
        capturePilotadaView
    );

    window.addEventListener(
        "beforeunload",
        capturePilotadaView
    );
})();

// =========================================================
// SAFEVISION ROTACION MINIMA V1
//
// - NO MutationObserver
// - NO timers
// - NO reubicar controles existentes
// - NO tocar Runtime/video/conexión
// =========================================================

(() => {
    "use strict";

    if (window.safeVisionRotationMinimaV1) {
        return;
    }

    window.safeVisionRotationMinimaV1 = true;

    const viewport =
        document.getElementById(
            "mapViewport"
        );

    const rotationApi =
        window.safeVisionPilotadaRotationApi;

    if (!viewport) {
        console.warn(
            "[SafeVision] Rotación mínima: mapViewport no encontrado."
        );
        return;
    }

    if (
        document.getElementById(
            "pv2RotationSimpleControl"
        )
    ) {
        return;
    }

    const control =
        document.createElement(
            "div"
        );

    control.id =
        "pv2RotationSimpleControl";

    control.className =
        "pv2-rotation-simple";

    control.innerHTML = `
        <span class="pv2-rotation-simple__label">
            Girar
        </span>

        <input
            id="pv2RotationSimple"
            class="pv2-rotation-simple__range"
            type="range"
            min="-180"
            max="180"
            step="1"
            value="0"
            aria-label="Girar mapa"
        >

        <output
            id="pv2RotationSimpleValue"
            class="pv2-rotation-simple__value"
        >
            0°
        </output>
    `;

    viewport.parentNode.insertBefore(
        control,
        viewport
    );

    const slider =
        document.getElementById(
            "pv2RotationSimple"
        );

    const output =
        document.getElementById(
            "pv2RotationSimpleValue"
        );

    if (!slider || !output) {
        return;
    }

    if (
        !rotationApi
        ||
        typeof rotationApi.set !== "function"
        ||
        typeof rotationApi.get !== "function"
    ) {
        slider.disabled =
            true;

        output.textContent =
            "N/D";

        console.warn(
            "[SafeVision] Rotación mínima: API de rotación no disponible."
        );

        return;
    }

    const initial =
        Number(
            rotationApi.get()
            ||
            0
        );

    slider.value =
        String(initial);

    output.textContent =
        String(
            Math.round(
                initial
            )
        )
        +
        "°";

    slider.addEventListener(
        "input",
        () => {
            const value =
                Number(
                    slider.value
                    ||
                    0
                );

            output.textContent =
                String(
                    Math.round(
                        value
                    )
                )
                +
                "°";

            rotationApi.set(
                value
            );
        }
    );

    console.info(
        "[SafeVision] Rotación mínima V1 activa."
    );
})();

