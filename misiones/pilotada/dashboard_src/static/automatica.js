// =========================================================
// SAFEVISION MISION AUTOMATICA - PAGINA INDEPENDIENTE
// =========================================================

(() => {

    const connectionState = {
        connected:
            false
    };


    const autoMissionState = {
        loaded:
            null,

        simulation:
            null,

        prepared:
            false,

        running:
            false,

        busy:
            false,

        pollTimer:
            null,

        listLoaded:
            false
    };


    const connectionBadge =
        document.getElementById(
            "autoConnectionBadge"
        );


    const missionSelect =
        document.getElementById(
            "autoMissionSelect"
        );

    const refreshButton =
        document.getElementById(
            "autoMissionRefresh"
        );

    const startButton =
        document.getElementById(
            "autoMissionStart"
        );

    const cancelButton =
        document.getElementById(
            "autoMissionCancel"
        );

    const missionMap =
        document.getElementById(
            "autoMissionMap"
        );

    const missionInitial =
        document.getElementById(
            "autoMissionInitial"
        );

    const missionPoints =
        document.getElementById(
            "autoMissionPoints"
        );

    const missionActions =
        document.getElementById(
            "autoMissionActions"
        );

    const missionProgress =
        document.getElementById(
            "autoMissionProgress"
        );

    const missionCurrentAction =
        document.getElementById(
            "autoMissionCurrentAction"
        );

    const missionCode =
        document.getElementById(
            "autoMissionCode"
        );

    const missionStatus =
        document.getElementById(
            "autoMissionStatus"
        );


    if (
        !connectionBadge
        ||
        !missionSelect
        ||
        !startButton
        ||
        !cancelButton
        ||
        !missionProgress
        ||
        !missionCurrentAction
    ) {
        return;
    }


    function setMissionStatus(
        message,
        state=""
    ) {

        missionStatus.textContent =
            message;

        missionStatus.className =
            "auto-mission-status";

        if (state) {
            missionStatus.classList.add(
                state
            );
        }
    }


    function renderConnectionState(
        connected
    ) {

        connectionState.connected =
            connected;


        if (connected) {

            connectionBadge.textContent =
                "CONECTADO";

            connectionBadge.className =
                "badge badge-on";

        } else {

            connectionBadge.textContent =
                "DESCONECTADO";

            connectionBadge.className =
                "badge badge-off";
        }
    }


    async function initializeAutomaticPage() {

        missionSelect.innerHTML =
            "";


        const option =
            document.createElement(
                "option"
            );

        option.value =
            "";

        option.textContent =
            "Conecta el robot para continuar";

        missionSelect.appendChild(
            option
        );


        renderConnectionState(
            false
        );

        updateMissionControls();


        try {

            await requestJson(
                "/robot_status"
            );


            renderConnectionState(
                true
            );


            await loadMissionList();


        } catch (error) {

            renderConnectionState(
                false
            );

            setMissionStatus(
                "Conecta el robot para preparar una misión."
            );

            updateMissionControls();
        }
    }


    function stopMissionPolling() {

        if (
            autoMissionState.pollTimer
            !==
            null
        ) {

            clearTimeout(
                autoMissionState.pollTimer
            );

            autoMissionState.pollTimer =
                null;
        }
    }


    function currentActionLabel(
        action
    ) {

        if (!action) {
            return "—";
        }


        if (
            typeof action
            ===
            "string"
        ) {
            return action;
        }


        if (
            typeof action
            !==
            "object"
        ) {
            return "—";
        }


        const name =
            action.name
            ||
            "acción";


        if (
            action.point
            &&
            typeof action.point
            ===
            "object"
            &&
            action.point.id
        ) {

            return (
                name
                +
                " "
                +
                action.point.id
            );
        }


        if (action.reference_id) {

            return (
                name
                +
                " "
                +
                action.reference_id
            );
        }


        return name;
    }


    function updateMissionControls() {

        const running =
            autoMissionState.running;

        const busy =
            autoMissionState.busy;

        const connected =
            connectionState.connected;


        const controlsLocked =
            (
                running
                ||
                busy
                ||
                !connected
            );


        missionSelect.disabled =
            controlsLocked;

        refreshButton.disabled =
            controlsLocked;


        startButton.disabled =
            (
                controlsLocked
                ||
                !autoMissionState.prepared
            );


        cancelButton.disabled =
            (
                !connected
                ||
                !running
                ||
                busy
            );


        startButton.title =
            running
                ?
                "La misión está en ejecución."
                :
                (
                    autoMissionState.prepared
                        ?
                        "Iniciar misión preparada."
                        :
                        "La misión debe estar preparada antes de iniciar."
                );


        cancelButton.title =
            running
                ?
                "Cancelar la misión en ejecución."
                :
                "No hay una misión en ejecución.";
    }


    function applyMissionRuntimeStatus(
        status
    ) {

        const count =
            Number(
                status.action_count
            );

        const index =
            Number(
                status.action_index
            );


        const safeCount =
            Number.isFinite(
                count
            )
                ?
                count
                :
                0;

        const safeIndex =
            Number.isFinite(
                index
            )
                ?
                index
                :
                0;


        missionProgress.textContent =
            (
                String(safeIndex)
                +
                " / "
                +
                String(safeCount)
            );


        missionCurrentAction.textContent =
            currentActionLabel(
                status.current_action
            );


        autoMissionState.running =
            Boolean(
                status.running
            );


        const state =
            status.state
            ||
            "";


        const message =
            status.message
            ||
            state
            ||
            "Estado desconocido.";


        if (state === "completed") {

            autoMissionState.prepared =
                false;

            setMissionStatus(
                message,
                "ready"
            );

        } else if (
            state === "error"
        ) {

            autoMissionState.prepared =
                false;

            setMissionStatus(
                message,
                "error"
            );

        } else if (
            state === "cancelled"
        ) {

            autoMissionState.prepared =
                false;

            setMissionStatus(
                message
            );

        } else if (
            autoMissionState.running
        ) {

            setMissionStatus(
                message,
                "loading"
            );

        } else if (
            state === "ready"
        ) {

            autoMissionState.prepared =
                true;

            setMissionStatus(
                message,
                "ready"
            );

        } else {

            setMissionStatus(
                message
            );
        }


        updateMissionControls();
    }


    async function pollMissionStatus() {

        stopMissionPolling();


        try {

            const status =
                await requestJson(
                    "/mission/status"
                );


            applyMissionRuntimeStatus(
                status
            );


            if (
                autoMissionState.running
            ) {

                autoMissionState.pollTimer =
                    setTimeout(
                        pollMissionStatus,
                        250
                    );
            }


        } catch (error) {

            setMissionStatus(
                error.message
                ||
                "No se pudo consultar el estado de la misión.",
                "error"
            );


            if (
                autoMissionState.running
            ) {

                autoMissionState.pollTimer =
                    setTimeout(
                        pollMissionStatus,
                        1000
                    );
            }
        }
    }


    function clearMissionDetails() {

        stopMissionPolling();

        autoMissionState.loaded =
            null;

        autoMissionState.simulation =
            null;

        autoMissionState.prepared =
            false;

        autoMissionState.running =
            false;

        missionMap.textContent =
            "—";

        missionInitial.textContent =
            "—";

        missionPoints.textContent =
            "—";

        missionActions.textContent =
            "—";

        missionProgress.textContent =
            "0 / 0";

        missionCurrentAction.textContent =
            "—";

        missionCode.textContent =
            "Selecciona una misión.";

        updateMissionControls();
    }


    async function requestJson(
        url,
        options={}
    ) {

        const response =
            await fetch(
                url,
                options
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (error) {

            data = {};
        }


        if (!response.ok) {

            throw new Error(
                data.message
                ||
                data.error
                ||
                `HTTP ${response.status}`
            );
        }


        return data;
    }


    async function simulateMission(
        mission
    ) {

        const result =
            await requestJson(
                "/programar/simulate",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            code:
                                mission.code
                                ||
                                "",

                            points:
                                Array.isArray(
                                    mission.points
                                )
                                    ?
                                    mission.points
                                    :
                                    []
                        })
                }
            );


        if (!result.ok) {

            const errors =
                Array.isArray(
                    result.errors
                )
                    ?
                    result.errors
                    :
                    [];


            throw new Error(
                errors.length
                    ?
                    (
                        errors[0].message
                        ||
                        "La simulación rechazó la misión."
                    )
                    :
                    "La simulación rechazó la misión."
            );
        }


        return result;
    }


    async function loadMissionDetails(
        name
    ) {

        if (
            !connectionState.connected
        ) {

            setMissionStatus(
                "Conecta el robot antes de preparar una misión.",
                "error"
            );

            updateMissionControls();

            return;
        }


        autoMissionState.busy =
            true;

        clearMissionDetails();


        if (!name) {

            autoMissionState.busy =
                false;

            updateMissionControls();

            setMissionStatus(
                "Esperando selección."
            );

            return;
        }


        setMissionStatus(
            "Cargando misión...",
            "loading"
        );


        missionSelect.disabled =
            true;


        try {

            const data =
                await requestJson(
                    "/missions/load?name="
                    +
                    encodeURIComponent(
                        name
                    )
                );


            const mission =
                data.mission;


            if (
                !mission
                ||
                typeof mission
                !==
                "object"
            ) {

                throw new Error(
                    "El servidor no devolvió una misión válida."
                );
            }


            const simulation =
                await simulateMission(
                    mission
                );


            if (
                !Array.isArray(
                    simulation.trace
                )
            ) {

                throw new Error(
                    "La simulación no devolvió una traza válida."
                );
            }


            autoMissionState.loaded =
                mission;

            autoMissionState.simulation =
                simulation;

            autoMissionState.prepared =
                false;


            missionMap.textContent =
                mission.map
                ||
                "—";


            missionInitial.textContent =
                mission.initial_point_id
                ||
                "—";


            missionPoints.textContent =
                Array.isArray(
                    mission.points
                )
                    ?
                    String(
                        mission.points.length
                    )
                    :
                    "0";


            missionActions.textContent =
                String(
                    simulation.action_count == null
                        ?
                        0
                        :
                        simulation.action_count
                );


            missionProgress.textContent =
                (
                    "0 / "
                    +
                    String(
                        simulation.action_count == null
                            ?
                            0
                            :
                            simulation.action_count
                    )
                );


            missionCurrentAction.textContent =
                "—";


            missionCode.textContent =
                (
                    typeof mission.code
                    ===
                    "string"
                    &&
                    mission.code.trim()
                )
                    ?
                    mission.code
                    :
                    "Sin programa.";


            autoMissionState.prepared =
                false;

            autoMissionState.running =
                false;

            updateMissionControls();


            setMissionStatus(
                "Preparando misión en el robot...",
                "loading"
            );


            try {

                const prepared =
                    await requestJson(
                        "/mission/prepare",
                        {
                            method:
                                "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    mission:
                                        mission,

                                    trace:
                                        simulation.trace
                                })
                        }
                    );


                if (
                    prepared.state
                    !==
                    "ready"
                ) {

                    throw new Error(
                        prepared.message
                        ||
                        "El robot no dejó la misión en estado ready."
                    );
                }


                autoMissionState.prepared =
                    true;

                autoMissionState.running =
                    false;

                applyMissionRuntimeStatus(
                    prepared
                );


                setMissionStatus(
                    "Misión preparada en el robot.",
                    "ready"
                );


                if (
                    typeof log
                    ===
                    "function"
                ) {

                    log(
                        `Misión automática preparada: ${mission.name}`
                    );
                }


            } catch (prepareError) {

                autoMissionState.prepared =
                    false;

                autoMissionState.running =
                    false;

                updateMissionControls();


                setMissionStatus(
                    prepareError.message
                    ||
                    "No se pudo preparar la misión en el robot.",
                    "error"
                );


                if (
                    typeof log
                    ===
                    "function"
                ) {

                    log(
                        `Misión automática no preparada: ${mission.name}`
                    );
                }


                return;
            }


        } catch (error) {

            clearMissionDetails();

            setMissionStatus(
                error.message
                ||
                "No se pudo cargar la misión.",
                "error"
            );

        } finally {

            autoMissionState.busy =
                false;

            updateMissionControls();
        }
    }


    async function loadMissionList() {

        if (
            !connectionState.connected
        ) {

            setMissionStatus(
                "Conecta el robot para consultar las misiones."
            );

            updateMissionControls();

            return;
        }


        const previous =
            missionSelect.value;


        autoMissionState.busy =
            true;


        missionSelect.disabled =
            true;

        refreshButton.disabled =
            true;


        missionSelect.innerHTML =
            "";


        const loadingOption =
            document.createElement(
                "option"
            );

        loadingOption.value =
            "";

        loadingOption.textContent =
            "Cargando misiones...";

        missionSelect.appendChild(
            loadingOption
        );


        clearMissionDetails();

        setMissionStatus(
            "Consultando biblioteca...",
            "loading"
        );


        try {

            const data =
                await requestJson(
                    "/missions"
                );


            const missions =
                Array.isArray(
                    data.missions
                )
                    ?
                    data.missions
                    :
                    [];


            missionSelect.innerHTML =
                "";


            if (!missions.length) {

                const emptyOption =
                    document.createElement(
                        "option"
                    );

                emptyOption.value =
                    "";

                emptyOption.textContent =
                    "No hay misiones guardadas";

                missionSelect.appendChild(
                    emptyOption
                );


                setMissionStatus(
                    "Biblioteca de misiones vacía."
                );

                autoMissionState.listLoaded =
                    true;

                return;
            }


            const placeholder =
                document.createElement(
                    "option"
                );

            placeholder.value =
                "";

            placeholder.textContent =
                "Seleccionar misión...";

            missionSelect.appendChild(
                placeholder
            );


            missions.forEach(
                item => {

                    const option =
                        document.createElement(
                            "option"
                        );


                    option.value =
                        item.name;

                    option.textContent =
                        item.name;


                    missionSelect.appendChild(
                        option
                    );
                }
            );


            autoMissionState.listLoaded =
                true;


            const names =
                missions.map(
                    item =>
                        item.name
                );


            if (
                previous
                &&
                names.includes(
                    previous
                )
            ) {

                missionSelect.value =
                    previous;

                await loadMissionDetails(
                    previous
                );

            } else {

                missionSelect.value =
                    "";

                setMissionStatus(
                    `${missions.length} misión(es) disponible(s).`
                );
            }


        } catch (error) {

            missionSelect.innerHTML =
                "";


            const errorOption =
                document.createElement(
                    "option"
                );

            errorOption.value =
                "";

            errorOption.textContent =
                "Error al consultar misiones";

            missionSelect.appendChild(
                errorOption
            );


            setMissionStatus(
                error.message
                ||
                "No se pudieron consultar las misiones.",
                "error"
            );

        } finally {

            autoMissionState.busy =
                false;

            updateMissionControls();
        }
    }


    missionSelect.addEventListener(
        "change",
        () => {

            loadMissionDetails(
                missionSelect.value
            );
        }
    );


    startButton.addEventListener(
        "click",
        async () => {

            if (
                !autoMissionState.prepared
                ||
                autoMissionState.running
            ) {
                return;
            }


            autoMissionState.busy =
                true;

            updateMissionControls();

            setMissionStatus(
                "Iniciando misión...",
                "loading"
            );


            try {

                const started =
                    await requestJson(
                        "/mission/start",
                        {
                            method:
                                "POST"
                        }
                    );


                applyMissionRuntimeStatus(
                    started
                );


                autoMissionState.busy =
                    false;

                updateMissionControls();


                if (
                    autoMissionState.running
                ) {

                    pollMissionStatus();
                }


                if (
                    typeof log
                    ===
                    "function"
                ) {

                    log(
                        "Misión automática iniciada."
                    );
                }


            } catch (error) {

                autoMissionState.running =
                    false;

                autoMissionState.busy =
                    false;

                setMissionStatus(
                    error.message
                    ||
                    "No se pudo iniciar la misión.",
                    "error"
                );

                updateMissionControls();
            }
        }
    );


    cancelButton.addEventListener(
        "click",
        async () => {

            if (
                !autoMissionState.running
            ) {
                return;
            }


            autoMissionState.busy =
                true;

            updateMissionControls();

            setMissionStatus(
                "Cancelando misión...",
                "loading"
            );


            try {

                const cancelled =
                    await requestJson(
                        "/mission/cancel",
                        {
                            method:
                                "POST"
                        }
                    );


                applyMissionRuntimeStatus(
                    cancelled
                );


                autoMissionState.busy =
                    false;

                updateMissionControls();


                if (
                    autoMissionState.running
                ) {

                    pollMissionStatus();
                }


            } catch (error) {

                autoMissionState.busy =
                    false;

                setMissionStatus(
                    error.message
                    ||
                    "No se pudo cancelar la misión.",
                    "error"
                );

                updateMissionControls();
            }
        }
    );


    refreshButton.addEventListener(
        "click",
        loadMissionList
    );


    initializeAutomaticPage();

})();
