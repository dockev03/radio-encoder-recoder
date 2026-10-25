/* =========================
   CONVERSION dB
   ========================= */

function dbToPercent(db) {

    const minDb = -60;
    const maxDb = 0;

    db = Math.max(
        minDb,
        Math.min(maxDb, db)
    );

    return (
        (db - minDb) /
        (maxDb - minDb)
    ) * 100;
}


/* =========================
   ÉTAT VU
   ========================= */

const meterState = {

    left: {
        displayed: -60,
        peak: -60,
        peakTime: 0
    },

    right: {
        displayed: -60,
        peak: -60,
        peakTime: 0
    }

};


/* =========================
   VU-MÈTRE
   ========================= */

function updateMeter(
    channel,
    targetDb
) {

    const state =
        meterState[channel];

    const now =
        performance.now();


    if (
        targetDb >
        state.displayed
    ) {

        state.displayed =
            targetDb;

    } else {

        state.displayed -= 2.0;

        if (
            state.displayed <
            targetDb
        ) {

            state.displayed =
                targetDb;
        }
    }


    if (
        targetDb >=
        state.peak
    ) {

        state.peak =
            targetDb;

        state.peakTime =
            now;

    } else if (
        now -
        state.peakTime >
        1000
    ) {

        state.peak -= 1.0;

        if (
            state.peak <
            state.displayed
        ) {

            state.peak =
                state.displayed;
        }
    }


    const meter =
        document.getElementById(
            `meter-${channel}`
        );


    const peak =
        document.getElementById(
            `peak-${channel}`
        );


    const value =
        document.getElementById(
            `${channel}-db`
        );


    if (meter) {

        meter.style.width =
            `${dbToPercent(
                state.displayed
            )}%`;
    }


    if (peak) {

        peak.style.left =
            `${dbToPercent(
                state.peak
            )}%`;
    }


    if (value) {

        value.textContent =
            `${targetDb.toFixed(1)} dB`;
    }
}


function resetMeter(channel) {

    const state =
        meterState[channel];


    state.displayed =
        -60;

    state.peak =
        -60;

    state.peakTime =
        0;


    const meter =
        document.getElementById(
            `meter-${channel}`
        );


    const peak =
        document.getElementById(
            `peak-${channel}`
        );


    const value =
        document.getElementById(
            `${channel}-db`
        );


    if (meter) {
        meter.style.width = "0%";
    }


    if (peak) {
        peak.style.left = "0%";
    }


    if (value) {
        value.textContent = "-60.0 dB";
    }
}


/* =========================
   FORMAT UPTIME
   ========================= */

function formatUptime(seconds) {

    if (
        seconds === null ||
        seconds === undefined
    ) {
        return "N/D";
    }


    const days =
        Math.floor(
            seconds / 86400
        );


    const hours =
        Math.floor(
            (seconds % 86400) /
            3600
        );


    const minutes =
        Math.floor(
            (seconds % 3600) /
            60
        );


    if (days > 0) {

        return (
            `${days}j ` +
            `${hours}h ` +
            `${minutes}m`
        );
    }


    return (
        `${hours}h ` +
        `${minutes}m`
    );
}


/* =========================
   FORMAT DATE
   ========================= */

function formatIncidentDate(
    isoDate
) {

    if (!isoDate) {

        return null;
    }


    const date =
        new Date(
            isoDate
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return null;
    }


    const now =
        new Date();


    const sameDay =
        date.getFullYear() ===
            now.getFullYear()
        &&
        date.getMonth() ===
            now.getMonth()
        &&
        date.getDate() ===
            now.getDate();


    const time =
        date.toLocaleTimeString(
            "fr-FR",
            {
                hour:
                    "2-digit",

                minute:
                    "2-digit"
            }
        );


    if (sameDay) {

        return (
            `AUJOURD'HUI ${time}`
        );
    }


    const day =
        date.toLocaleDateString(
            "fr-FR",
            {
                day:
                    "2-digit",

                month:
                    "2-digit"
            }
        );


    return (
        `${day} ${time}`
    );
}


/* =========================
   STATUS SERVICE
   ========================= */

function setStatus(
    elementId,
    dotId,
    active,
    activeText,
    inactiveText
) {

    const element =
        document.getElementById(
            elementId
        );


    const dot =
        document.getElementById(
            dotId
        );


    if (element) {

        element.textContent =
            active
                ? activeText
                : inactiveText;


        element.classList.toggle(
            "green-text",
            active
        );


        element.classList.toggle(
            "red-text",
            !active
        );
    }


    if (dot) {

        dot.classList.toggle(
            "green",
            active
        );


        dot.classList.toggle(
            "red",
            !active
        );
    }
}


/* =========================
   FORMAT DÉBIT RÉSEAU
   ========================= */

function formatBitrate(
    bitsPerSecond
) {

    if (
        bitsPerSecond === null ||
        bitsPerSecond === undefined ||
        Number.isNaN(
            bitsPerSecond
        )
    ) {

        return "--";
    }


    if (
        bitsPerSecond >=
        1000000000
    ) {

        return (
            (
                bitsPerSecond /
                1000000000
            ).toFixed(2)
            +
            " Gb/s"
        );
    }


    if (
        bitsPerSecond >=
        1000000
    ) {

        return (
            (
                bitsPerSecond /
                1000000
            ).toFixed(2)
            +
            " Mb/s"
        );
    }


    if (
        bitsPerSecond >=
        1000
    ) {

        return (
            (
                bitsPerSecond /
                1000
            ).toFixed(1)
            +
            " Kb/s"
        );
    }


    return (
        Math.round(
            bitsPerSecond
        )
        +
        " b/s"
    );
}


/* =========================
   AUDIO TEMPS RÉEL
   ========================= */

async function updateAudioMeters() {

    try {

        const response =
            await fetch(
                "/api/audio",
                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const audio =
            await response.json();


        if (
            audio.signal !==
            true
        ) {

            resetMeter(
                "left"
            );

            resetMeter(
                "right"
            );

            return;
        }


        const leftDb =
            audio.left_db ??
            -60;


        const rightDb =
            audio.right_db ??
            -60;


        updateMeter(
            "left",
            leftDb
        );


        updateMeter(
            "right",
            rightDb
        );


    } catch (error) {

        console.error(
            "Erreur VU-mètre :",
            error
        );


        resetMeter(
            "left"
        );


        resetMeter(
            "right"
        );
    }
}


/* =========================
   DASHBOARD
   ========================= */

async function updateDashboard() {

    try {

        const response =
            await fetch(
                "/api/status",
                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();



        /* =====================
           AUREON
           ===================== */

        const aureonPresent =
            data.audio
                ?.device_present ===
            true;


        setStatus(
            "aureon-status",
            "aureon-dot",
            aureonPresent,
            "OK",
            "ABSENTE"
        );



        /* =====================
           EASYEFFECTS
           ===================== */

        const easyeffectsActive =
            data.audio
                ?.easyeffects ===
            true;


        setStatus(
            "easyeffects",
            "easyeffects-dot",
            easyeffectsActive,
            "ACTIF",
            "ARRÊTÉ"
        );



        /* =====================
           SOURCE AUDIO
           ===================== */

        const sourceAvailable =
            data.audio
                ?.source_available ===
            true;


        setStatus(
            "source-status",
            "source-dot",
            sourceAvailable,
            "DISPONIBLE",
            "INDISPONIBLE"
        );



        /* =====================
           SIGNAL
           ===================== */

        const signalPresent =
            data.audio
                ?.signal ===
            true;


        const signalStatus =
            document.getElementById(
                "signal-status"
            );


        const signalDot =
            document.getElementById(
                "signal-dot"
            );


        if (signalStatus) {

            signalStatus.textContent =
                signalPresent
                    ? "PRÉSENT"
                    : "SILENCE";


            signalStatus
                .classList
                .toggle(
                    "green-text",
                    signalPresent
                );


            signalStatus
                .classList
                .toggle(
                    "yellow-text",
                    !signalPresent
                );


            signalStatus
                .classList
                .remove(
                    "red-text"
                );
        }


        if (signalDot) {

            signalDot
                .classList
                .toggle(
                    "green",
                    signalPresent
                );


            signalDot
                .classList
                .toggle(
                    "yellow",
                    !signalPresent
                );


            signalDot
                .classList
                .remove(
                    "red"
                );
        }



        /* =====================
           WATCHDOG
           ===================== */

        const watchdogActive =
            data.watchdog
                ?.active ===
            true;


        setStatus(
            "watchdog-status",
            "watchdog-dot",
            watchdogActive,
            "ACTIF",
            "INACTIF"
        );


        const recoveryCount =
            Number(
                data.watchdog
                    ?.recovery_count ??
                0
            );


        const watchdogRecoveries =
            document.getElementById(
                "watchdog-recoveries"
            );


        if (watchdogRecoveries) {

            if (
                recoveryCount === 1
            ) {

                watchdogRecoveries
                    .textContent =
                    "1 RÉCUPÉRATION";

            } else {

                watchdogRecoveries
                    .textContent =
                    `${recoveryCount} RÉCUPÉRATIONS`;
            }
        }


        const watchdogIncident =
            document.getElementById(
                "watchdog-last-incident"
            );


        if (watchdogIncident) {

            const incidentDate =
                formatIncidentDate(
                    data.watchdog
                        ?.last_incident
                );


            watchdogIncident
                .textContent =
                incidentDate

                    ? `DERNIER INCIDENT : ${incidentDate}`

                    : "AUCUN INCIDENT";
        }



        /* =====================
           BUTT
           ===================== */

        const buttActive =
            data.stream
                ?.butt ===
            true;


        setStatus(
            "butt",
            "butt-dot",
            buttActive,
            "ACTIF",
            "ARRÊTÉ"
        );



        /* =====================
           ÉTAT GLOBAL
           ===================== */

        const systemOperational =
            data.ready ===
            true;


        const globalStatus =
            document.getElementById(
                "global-status"
            );


        const globalStatusDot =
            document.getElementById(
                "global-status-dot"
            );


        const globalStatusText =
            document.getElementById(
                "global-status-text"
            );


        if (globalStatusText) {

            globalStatusText
                .textContent =
                systemOperational
                    ? "PRÊT POUR LE DIRECT"
                    : "NON PRÊT";
        }


        if (globalStatusDot) {

            globalStatusDot
                .classList
                .toggle(
                    "green",
                    systemOperational
                );


            globalStatusDot
                .classList
                .toggle(
                    "red",
                    !systemOperational
                );
        }


        if (globalStatus) {

            globalStatus
                .classList
                .toggle(
                    "green-text",
                    systemOperational
                );
        }



        /* =====================
           STREAM
           ===================== */

        const streamReceived =
            data.stream
                ?.received ===
            true;


        const streamStatus =
            document.getElementById(
                "stream-status"
            );


        if (streamStatus) {

            if (
                streamReceived
            ) {

                streamStatus.innerHTML =
                    '<span class="dot green"></span>' +
                    'DIRECT REÇU';


                streamStatus
                    .classList
                    .add(
                        "online"
                    );

            } else {

                streamStatus.innerHTML =
                    '<span class="dot red"></span>' +
                    'HORS ANTENNE';


                streamStatus
                    .classList
                    .remove(
                        "online"
                    );
            }
        }



        /* =====================
           ON AIR
           ===================== */

        const onAir =
            document.getElementById(
                "on-air"
            );


        const onAirText =
            document.getElementById(
                "on-air-text"
            );


        if (onAir) {

            onAir
                .classList
                .toggle(
                    "online",
                    streamReceived
                );


            onAir
                .classList
                .toggle(
                    "offline",
                    !streamReceived
                );
        }


        if (onAirText) {

            onAirText.textContent =
                streamReceived
                    ? "ON AIR"
                    : "OFF AIR";
        }



        /* =====================
           SERVEUR
           ===================== */

        const server =
            document.getElementById(
                "server"
            );


        if (server) {

            server.textContent =
                data.stream
                    ?.server ??
                "N/D";
        }



        /* =====================
           CODEC
           ===================== */

        const codecElement =
            document.getElementById(
                "codec"
            );


        const codec =
            data.stream
                ?.codec;


        const bitrate =
            data.stream
                ?.bitrate;


        if (codecElement) {

            if (
                codec &&
                bitrate
            ) {

                codecElement
                    .textContent =
                    `${codec} ${bitrate} kb/s`;

            } else {

                codecElement
                    .textContent =
                    "NON CONNECTÉ";
            }
        }



        /* =====================
           CONNEXION STREAM
           ===================== */

        const connectionStatus =
            document.getElementById(
                "connection-status"
            );


        if (connectionStatus) {

            const connected =
                data.stream
                    ?.connected ===
                true;


            connectionStatus
                .textContent =
                connected
                    ? "CONNECTÉ"
                    : "NON CONNECTÉ";


            connectionStatus
                .classList
                .toggle(
                    "green-text",
                    connected
                );


            connectionStatus
                .classList
                .toggle(
                    "red-text",
                    !connected
                );
        }



        /* =====================
           NOW PLAYING
           ===================== */

        const artist =
            document.getElementById(
                "artist"
            );


        const title =
            document.getElementById(
                "title"
            );


        if (artist) {

            artist.textContent =
                data.now_playing
                    ?.artist ??
                "Aucun titre";
        }


        if (title) {

            title.textContent =
                data.now_playing
                    ?.title ??
                "Hors antenne";
        }



        /* =====================
           SYSTÈME
           ===================== */

        const cpu =
            document.getElementById(
                "cpu"
            );


        if (cpu) {

            cpu.textContent =
                data.system?.cpu !==
                    null
                &&
                data.system?.cpu !==
                    undefined

                    ? `${data.system.cpu.toFixed(1)} %`

                    : "N/D";
        }


        const ram =
            document.getElementById(
                "ram"
            );


        if (ram) {

            ram.textContent =
                data.system?.ram !==
                    null
                &&
                data.system?.ram !==
                    undefined

                    ? `${data.system.ram.toFixed(1)} %`

                    : "N/D";
        }


        const temperature =
            data.system
                ?.temperature;


        const temperatureElement =
            document.getElementById(
                "temperature"
            );


        if (temperatureElement) {

            temperatureElement
                .textContent =
                temperature !== null &&
                temperature !== undefined

                    ? `${temperature} °C`

                    : "N/D";
        }


        const uptime =
            document.getElementById(
                "uptime"
            );


        if (uptime) {

            uptime.textContent =
                formatUptime(
                    data.system
                        ?.uptime
                );
        }



        /* =====================
           RÉSEAU
           ===================== */

        const networkConnected =
            data.network
                ?.connected ===
            true;


        const networkStatus =
            document.getElementById(
                "network-status"
            );


        const networkDetails =
            document.getElementById(
                "network-details"
            );


        const networkSpeed =
            document.getElementById(
                "network-speed"
            );


        if (networkStatus) {

            networkStatus.textContent =
                networkConnected
                    ? "● CONNECTÉ"
                    : "● DÉCONNECTÉ";


            networkStatus
                .classList
                .toggle(
                    "green-text",
                    networkConnected
                );


            networkStatus
                .classList
                .toggle(
                    "red-text",
                    !networkConnected
                );
        }


        if (networkDetails) {

            networkDetails.textContent =
                networkConnected

                    ? `${data.network?.interface ?? "N/D"} • ${data.network?.ip ?? "N/D"}`

                    : "AUCUNE CONNEXION";
        }


        if (networkSpeed) {

            if (
                networkConnected
            ) {

                const download =
                    formatBitrate(
                        data.network
                            ?.download_bps
                    );


                const upload =
                    formatBitrate(
                        data.network
                            ?.upload_bps
                    );


                networkSpeed.innerHTML =
                    '<span class="download">' +
                    '↓ ' +
                    download +
                    '</span>' +

                    '<span class="upload">' +
                    '↑ ' +
                    upload +
                    '</span>';

            } else {

                networkSpeed.innerHTML =
                    '<span class="download">' +
                    '↓ --' +
                    '</span>' +

                    '<span class="upload">' +
                    '↑ --' +
                    '</span>';
            }
        }


    } catch (error) {

        console.error(
            "Erreur dashboard :",
            error
        );
    }
}


/* =========================
   HORLOGE
   ========================= */

function updateClock() {

    const now =
        new Date();


    const clock =
        document.getElementById(
            "clock"
        );


    if (clock) {

        clock.textContent =
            now.toLocaleTimeString(
                "fr-FR",
                {
                    hour:
                        "2-digit",

                    minute:
                        "2-digit",

                    second:
                        "2-digit"
                }
            );
    }
}


/* =========================
   DÉMARRAGE
   ========================= */

updateClock();

setInterval(
    updateClock,
    1000
);


updateAudioMeters();

setInterval(
    updateAudioMeters,
    100
);


updateDashboard();

setInterval(
    updateDashboard,
    1000
);


/* ============================================================
   NAVIGATION
   ============================================================ */

const navigationButtons =
    document.querySelectorAll(
        ".nav-button"
    );

const pages =
    document.querySelectorAll(
        ".page"
    );


navigationButtons.forEach(
    (button) => {

        button.addEventListener(
            "click",
            () => {

                const pageId =
                    button.dataset.page;


                navigationButtons.forEach(
                    (item) => {

                        item.classList.remove(
                            "active"
                        );
                    }
                );


                pages.forEach(
                    (page) => {

                        page.classList.remove(
                            "active"
                        );
                    }
                );


                button.classList.add(
                    "active"
                );


                const targetPage =
                    document.getElementById(
                        pageId
                    );


                if (targetPage) {

                    targetPage.classList.add(
                        "active"
                    );
                }
            }
        );
    }
);


/* ============================================================
   ENREGISTREMENT MANUEL
   ============================================================ */

const recordingElements = {

    status:
        document.getElementById(
            "manual-recording-status"
        ),

    statusText:
        document.getElementById(
            "manual-recording-state-text"
        ),

    start:
        document.getElementById(
            "record-start"
        ),

    pause:
        document.getElementById(
            "record-pause"
        ),

    resume:
        document.getElementById(
            "record-resume"
        ),

    stop:
        document.getElementById(
            "record-stop"
        ),

    filename:
        document.getElementById(
            "recording-filename"
        ),

    format:
        document.getElementById(
            "recording-format"
        ),

    directory:
        document.getElementById(
            "recording-directory"
        ),

    directoryBrowse:
        document.getElementById(
            "recording-directory-browse"
        ),

    timer:
        document.getElementById(
            "recording-timer"
        ),

    duration:
        document.getElementById(
            "recording-duration"
        ),

    segments:
        document.getElementById(
            "recording-segments"
        ),

    size:
        document.getElementById(
            "recording-size"
        ),

    diskFree:
        document.getElementById(
            "recording-disk-free"
        ),

    currentFile:
        document.getElementById(
            "recording-current-file"
        ),

    errorMessage:
        document.getElementById(
            "recording-error-message"
        ),

    collisionModal:
        document.getElementById(
            "file-collision-modal"
        ),

    collisionFile:
        document.getElementById(
            "collision-file"
        ),

    collisionOverwrite:
        document.getElementById(
            "collision-overwrite"
        ),

    collisionCopy:
        document.getElementById(
            "collision-copy"
        ),

    collisionCancel:
        document.getElementById(
            "collision-cancel"
        )
};


let pendingRecordingRequest = null;


/* ============================================================
   FORMATAGE
   ============================================================ */

function formatRecordingDuration(
    seconds
) {

    seconds = Math.max(
        0,
        Math.floor(
            Number(seconds) || 0
        )
    );


    const hours =
        Math.floor(
            seconds / 3600
        );


    const minutes =
        Math.floor(
            (seconds % 3600) /
            60
        );


    const remainingSeconds =
        seconds % 60;


    return (
        String(hours)
            .padStart(
                2,
                "0"
            )
        +
        ":"
        +
        String(minutes)
            .padStart(
                2,
                "0"
            )
        +
        ":"
        +
        String(remainingSeconds)
            .padStart(
                2,
                "0"
            )
    );
}


function formatRecordingSize(
    bytes
) {

    bytes =
        Number(bytes) || 0;


    if (
        bytes >=
        1073741824
    ) {

        return (
            (
                bytes /
                1073741824
            ).toFixed(2)
            +
            " Go"
        );
    }


    if (
        bytes >=
        1048576
    ) {

        return (
            (
                bytes /
                1048576
            ).toFixed(1)
            +
            " Mo"
        );
    }


    if (
        bytes >=
        1024
    ) {

        return (
            (
                bytes /
                1024
            ).toFixed(1)
            +
            " Ko"
        );
    }


    return (
        bytes +
        " o"
    );
}


function getRecordingFilenameFromPath(
    path
) {

    if (!path) {

        return "Aucun";
    }


    return (
        path.split("/")
            .pop()
        ||
        path
    );
}


/* ============================================================
   ETAT VISUEL
   ============================================================ */

function setRecordingVisualState(
    status
) {

    const state =
        recordingElements.status;


    const text =
        recordingElements.statusText;


    if (
        !state ||
        !text
    ) {

        return;
    }


    state.classList.remove(
        "stopped",
        "recording",
        "paused"
    );


    switch (status) {

        case "recording":

            state.classList.add(
                "recording"
            );


            text.textContent =
                "ENREGISTREMENT";

            break;


        case "paused":

            state.classList.add(
                "paused"
            );


            text.textContent =
                "EN PAUSE";

            break;


        case "finalizing":

            state.classList.add(
                "paused"
            );


            text.textContent =
                "FINALISATION";

            break;


        case "error":

            state.classList.add(
                "recording"
            );


            text.textContent =
                "ERREUR ENREGISTREMENT";

            break;


        default:

            state.classList.add(
                "stopped"
            );


            text.textContent =
                "PRÊT";

            break;
    }
}


/* ============================================================
   ACTIVATION DES COMMANDES
   ============================================================ */

function updateRecordingControls(
    status
) {

    const stopped =
        status === "stopped";


    const recording =
        status === "recording";


    const paused =
        status === "paused";


    const finalizing =
        status === "finalizing";


    const error =
        status === "error";


    recordingElements.start.disabled =
        !stopped;


    recordingElements.pause.disabled =
        !recording;


    recordingElements.resume.disabled =
        !paused;


    /*
     * En cas d'erreur, STOP reste disponible.
     *
     * Cela permet de demander au backend de
     * finaliser les segments déjà enregistrés.
     */

    recordingElements.stop.disabled =
        !recording &&
        !paused &&
        !error;


    /*
     * Les paramètres restent verrouillés tant
     * que la session n'est pas complètement
     * terminée.
     */

    const lockSettings =
        recording ||
        paused ||
        finalizing ||
        error;


    recordingElements.filename.disabled =
        lockSettings;


    recordingElements.format.disabled =
        lockSettings;


    recordingElements.directory.disabled =
        lockSettings;


    recordingElements.directoryBrowse.disabled =
        lockSettings;
}


/* ============================================================
   AFFICHAGE ETAT
   ============================================================ */

function renderRecordingStatus(
    data
) {

    const status =
        data.status ||
        "stopped";


    setRecordingVisualState(
        status
    );


    updateRecordingControls(
        status
    );


    /*
     * Message de panne.
     */

    if (
        recordingElements.errorMessage
    ) {

        recordingElements
            .errorMessage
            .hidden =
            status !== "error";
    }


    /*
     * Durée.
     */

    const duration =
        Number(
            data.duration
        ) || 0;


    const formattedDuration =
        formatRecordingDuration(
            duration
        );


    recordingElements.timer.textContent =
        formattedDuration;


    recordingElements.duration.textContent =
        formattedDuration;


    /*
     * Nombre de segments.
     */

    recordingElements.segments.textContent =
        Number(
            data.segment_count
        ) || 0;


    /*
     * Taille cumulée de tous les segments.
     */

    recordingElements.size.textContent =
        formatRecordingSize(
            data.total_size
        );


    /*
     * Espace disque disponible.
     */

    recordingElements.diskFree.textContent =
        data.disk_free !== null &&
        data.disk_free !== undefined

            ? formatRecordingSize(
                data.disk_free
            )

            : "--";


    /*
     * Fichier final.
     */

    recordingElements.currentFile.textContent =
        getRecordingFilenameFromPath(
            data.file
        );
}


/* ============================================================
   LECTURE ETAT API
   ============================================================ */

async function updateRecordingStatus() {

    try {

        const response =
            await fetch(
                "/api/recording/status",
                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        renderRecordingStatus(
            data
        );


    } catch (error) {

        console.error(
            "Erreur statut enregistrement :",
            error
        );
    }
}


/* ============================================================
   REQUETE START
   ============================================================ */

function buildRecordingRequest(
    collision = "error"
) {

    let filename =
        recordingElements
            .filename
            .value
            .trim();


    /*
     * Nom automatique si le champ est vide.
     */

    if (!filename) {

        const now =
            new Date();


        const pad =
            (value) =>
                String(value)
                    .padStart(
                        2,
                        "0"
                    );


        filename =
            "enregistrement_"
            +
            pad(
                now.getDate()
            )
            +
            pad(
                now.getMonth() + 1
            )
            +
            now.getFullYear()
            +
            "-"
            +
            pad(
                now.getHours()
            )
            +
            pad(
                now.getMinutes()
            )
            +
            pad(
                now.getSeconds()
            );


        recordingElements
            .filename
            .value =
            filename;
    }


    return {

        directory:
            recordingElements
                .directory
                .value
                .trim(),

        filename:
            filename,

        format:
            recordingElements
                .format
                .value,

        collision:
            collision
    };
}


async function startManualRecording(
    collision = "error"
) {

    const requestData =
        buildRecordingRequest(
            collision
        );


    pendingRecordingRequest =
        requestData;


    try {

        const response =
            await fetch(
                "/api/recording/start",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            requestData
                        )
                }
            );


        const result =
            await response.json();


        /*
         * Collision de fichier.
         */

        if (
            response.status === 409 &&
            result.error === "file_exists"
        ) {

            recordingElements
                .collisionFile
                .textContent =
                result.file ||
                "--";


            recordingElements
                .collisionModal
                .hidden =
                false;


            return;
        }


        if (!response.ok) {

            throw new Error(
                result.error ||
                `HTTP ${response.status}`
            );
        }


        recordingElements
            .collisionModal
            .hidden =
            true;


        pendingRecordingRequest =
            null;


        await updateRecordingStatus();


    } catch (error) {

        console.error(
            "Erreur démarrage enregistrement :",
            error
        );


        alert(
            "Impossible de démarrer l'enregistrement.\n\n"
            +
            error.message
        );
    }
}


/* ============================================================
   PAUSE
   ============================================================ */

async function pauseManualRecording() {

    try {

        const response =
            await fetch(
                "/api/recording/pause",
                {
                    method:
                        "POST"
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                `HTTP ${response.status}`
            );
        }


        await updateRecordingStatus();


    } catch (error) {

        console.error(
            "Erreur pause :",
            error
        );


        alert(
            "Impossible de mettre l'enregistrement en pause."
        );
    }
}


/* ============================================================
   REPRISE
   ============================================================ */

async function resumeManualRecording() {

    try {

        const response =
            await fetch(
                "/api/recording/resume",
                {
                    method:
                        "POST"
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                `HTTP ${response.status}`
            );
        }


        await updateRecordingStatus();


    } catch (error) {

        console.error(
            "Erreur reprise :",
            error
        );


        alert(
            "Impossible de reprendre l'enregistrement."
        );
    }
}


/* ============================================================
   STOP
   ============================================================ */

async function stopManualRecording() {

    try {

        /*
         * On affiche immédiatement la finalisation.
         */

        setRecordingVisualState(
            "finalizing"
        );


        updateRecordingControls(
            "finalizing"
        );


        const response =
            await fetch(
                "/api/recording/stop",
                {
                    method:
                        "POST"
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.error ||
                `HTTP ${response.status}`
            );
        }


        await updateRecordingStatus();


    } catch (error) {

        console.error(
            "Erreur arrêt :",
            error
        );


        alert(
            "Erreur pendant la finalisation de l'enregistrement.\n\n"
            +
            error.message
        );


        /*
         * Important :
         *
         * si la finalisation a échoué, le backend
         * reste en état error. On recharge donc son
         * véritable état afin de réactiver STOP et
         * d'afficher le message d'incident.
         */

        await updateRecordingStatus();
    }
}


/* ============================================================
   COLLISION
   ============================================================ */

recordingElements
    .collisionOverwrite
    .addEventListener(
        "click",
        async () => {

            recordingElements
                .collisionModal
                .hidden =
                true;


            await startManualRecording(
                "overwrite"
            );
        }
    );


recordingElements
    .collisionCopy
    .addEventListener(
        "click",
        async () => {

            recordingElements
                .collisionModal
                .hidden =
                true;


            await startManualRecording(
                "copy"
            );
        }
    );


recordingElements
    .collisionCancel
    .addEventListener(
        "click",
        () => {

            recordingElements
                .collisionModal
                .hidden =
                true;


            pendingRecordingRequest =
                null;
        }
    );


/* ============================================================
   CHOIX DU DOSSIER
   ============================================================ */

/*
 * Le dashboard est consulté depuis un navigateur,
 * souvent sur un autre poste que l'encodeur :
 * on parcourt donc les dossiers du serveur via
 * l'API plutôt qu'avec l'explorateur du poste.
 */

const directoryPicker = {

    modal:
        document.getElementById(
            "directory-picker-modal"
        ),

    shortcuts:
        document.getElementById(
            "directory-picker-shortcuts"
        ),

    path:
        document.getElementById(
            "directory-picker-path"
        ),

    list:
        document.getElementById(
            "directory-picker-list"
        ),

    error:
        document.getElementById(
            "directory-picker-error"
        ),

    up:
        document.getElementById(
            "directory-picker-up"
        ),

    create:
        document.getElementById(
            "directory-picker-new"
        ),

    cancel:
        document.getElementById(
            "directory-picker-cancel"
        ),

    select:
        document.getElementById(
            "directory-picker-select"
        ),

    currentPath:
        null,

    parentPath:
        null
};


function showDirectoryPickerError(
    message
) {

    directoryPicker.error.textContent =
        message || "";

    directoryPicker.error.hidden =
        !message;
}


function renderDirectoryShortcuts(
    shortcuts
) {

    directoryPicker.shortcuts.replaceChildren();


    (shortcuts || []).forEach(
        (shortcut) => {

            const button =
                document.createElement(
                    "button"
                );

            button.type =
                "button";

            button.className =
                "directory-picker-shortcut";

            button.textContent =
                shortcut.label;

            button.title =
                shortcut.path;

            button.addEventListener(
                "click",
                () => loadDirectory(
                    shortcut.path
                )
            );

            directoryPicker.shortcuts.appendChild(
                button
            );
        }
    );
}


function renderDirectoryList(
    directories
) {

    directoryPicker.list.replaceChildren();


    if (!directories.length) {

        const empty =
            document.createElement(
                "li"
            );

        empty.className =
            "directory-picker-empty";

        empty.textContent =
            "Aucun sous-dossier";

        directoryPicker.list.appendChild(
            empty
        );

        return;
    }


    directories.forEach(
        (directory) => {

            const item =
                document.createElement(
                    "li"
                );

            item.textContent =
                directory.name;

            item.title =
                directory.path;

            item.addEventListener(
                "click",
                () => loadDirectory(
                    directory.path
                )
            );

            directoryPicker.list.appendChild(
                item
            );
        }
    );
}


async function loadDirectory(
    path
) {

    showDirectoryPickerError(
        ""
    );


    try {

        const response =
            await fetch(
                "/api/filesystem/directories?path="
                +
                encodeURIComponent(
                    path || ""
                )
            );


        const result =
            await response.json();


        if (!response.ok) {

            showDirectoryPickerError(
                result.error === "permission_denied"
                    ? "Accès refusé à ce dossier."
                    : "Impossible de lire ce dossier."
            );

            return;
        }


        directoryPicker.currentPath =
            result.path;

        directoryPicker.parentPath =
            result.parent;


        directoryPicker.path.textContent =
            result.path;

        directoryPicker.up.disabled =
            !result.parent;


        renderDirectoryShortcuts(
            result.shortcuts
        );

        renderDirectoryList(
            result.directories
        );


        if (!result.writable) {

            showDirectoryPickerError(
                "Attention : ce dossier n'est pas accessible en écriture."
            );
        }


    } catch (error) {

        console.error(
            "Erreur lecture dossier :",
            error
        );

        showDirectoryPickerError(
            "Impossible de contacter l'encodeur."
        );
    }
}


function openDirectoryPicker() {

    directoryPicker.modal.hidden =
        false;


    loadDirectory(
        recordingElements
            .directory
            .value
            .trim()
    );
}


function closeDirectoryPicker() {

    directoryPicker.modal.hidden =
        true;
}


async function createDirectoryInPicker() {

    const name =
        prompt(
            "Nom du nouveau dossier :"
        );


    if (
        name === null ||
        !name.trim()
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/filesystem/directories",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            parent:
                                directoryPicker.currentPath,

                            name:
                                name.trim()
                        })
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            const messages = {
                invalid_name:
                    "Nom de dossier invalide.",

                already_exists:
                    "Un dossier portant ce nom existe déjà.",

                permission_denied:
                    "Accès refusé : impossible de créer le dossier ici."
            };

            showDirectoryPickerError(
                messages[result.error] ||
                "Impossible de créer le dossier."
            );

            return;
        }


        await loadDirectory(
            result.path
        );


    } catch (error) {

        console.error(
            "Erreur création dossier :",
            error
        );

        showDirectoryPickerError(
            "Impossible de contacter l'encodeur."
        );
    }
}


recordingElements
    .directoryBrowse
    .addEventListener(
        "click",
        openDirectoryPicker
    );


directoryPicker
    .up
    .addEventListener(
        "click",
        () => {

            if (directoryPicker.parentPath) {

                loadDirectory(
                    directoryPicker.parentPath
                );
            }
        }
    );


directoryPicker
    .create
    .addEventListener(
        "click",
        createDirectoryInPicker
    );


directoryPicker
    .cancel
    .addEventListener(
        "click",
        closeDirectoryPicker
    );


directoryPicker
    .select
    .addEventListener(
        "click",
        () => {

            if (directoryPicker.currentPath) {

                recordingElements
                    .directory
                    .value =
                    directoryPicker.currentPath;
            }


            closeDirectoryPicker();
        }
    );


document.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Escape" &&
            !directoryPicker.modal.hidden
        ) {
            closeDirectoryPicker();
        }
    }
);


/* ============================================================
   BOUTONS
   ============================================================ */

recordingElements
    .start
    .addEventListener(
        "click",
        () => {

            startManualRecording(
                "error"
            );
        }
    );


recordingElements
    .pause
    .addEventListener(
        "click",
        pauseManualRecording
    );


recordingElements
    .resume
    .addEventListener(
        "click",
        resumeManualRecording
    );


recordingElements
    .stop
    .addEventListener(
        "click",
        stopManualRecording
    );


/* ============================================================
   INITIALISATION ENREGISTREMENT
   ============================================================ */

updateRecordingStatus();


setInterval(
    updateRecordingStatus,
    500
);


/* ============================================================
   WAVEFORM TEMPS RÉEL
   ============================================================ */

const waveformCanvas =
    document.getElementById(
        "recording-waveform"
    );


const waveformContext =
    waveformCanvas
        ?.getContext(
            "2d"
        );


let waveformRequestRunning =
    false;


/* ------------------------------------------------------------
   Redimensionnement Canvas
   ------------------------------------------------------------ */

function resizeWaveformCanvas() {

    if (!waveformCanvas) {

        return;
    }


    const rect =
        waveformCanvas
            .getBoundingClientRect();


    const ratio =
        window.devicePixelRatio ||
        1;


    const width =
        Math.max(
            1,
            Math.round(
                rect.width *
                ratio
            )
        );


    const height =
        Math.max(
            1,
            Math.round(
                rect.height *
                ratio
            )
        );


    if (
        waveformCanvas.width !== width ||
        waveformCanvas.height !== height
    ) {

        waveformCanvas.width =
            width;


        waveformCanvas.height =
            height;
    }
}


/* ------------------------------------------------------------
   Conversion amplitude -> hauteur graphique
   ------------------------------------------------------------ */

function waveformAmplitude(
    value
) {

    value =
        Math.abs(
            Number(value) || 0
        );


    /*
     * Gain purement visuel.
     *
     * Aucun impact sur le signal audio enregistré.
     */

    const visualGain =
        2.5;


    return Math.min(
        1,
        Math.sqrt(
            value
        ) *
        visualGain
    );
}


/* ------------------------------------------------------------
   Dessin
   ------------------------------------------------------------ */

function drawWaveform(
    points,
    sourceAvailable
) {

    if (
        !waveformCanvas ||
        !waveformContext
    ) {

        return;
    }


    resizeWaveformCanvas();


    const width =
        waveformCanvas.width;


    const height =
        waveformCanvas.height;


    waveformContext.clearRect(
        0,
        0,
        width,
        height
    );


    if (
        !sourceAvailable ||
        !Array.isArray(
            points
        ) ||
        points.length === 0
    ) {

        return;
    }


    const ratio =
        window.devicePixelRatio ||
        1;


    /*
     * Deux zones :
     *
     *       LEFT
     * -----------------
     *
     * -----------------
     *       RIGHT
     */

    const leftCenter =
        height *
        0.25;


    const rightCenter =
        height *
        0.75;


    const channelHeight =
        height *
        0.22;


    /*
     * Séparation L / R
     */

    waveformContext.beginPath();


    waveformContext.moveTo(
        0,
        height / 2
    );


    waveformContext.lineTo(
        width,
        height / 2
    );


    waveformContext.strokeStyle =
        "rgba(255, 255, 255, 0.08)";


    waveformContext.lineWidth =
        ratio;


    waveformContext.stroke();


    /*
     * Labels.
     */

    waveformContext.font =
        `${10 * ratio}px Consolas`;


    waveformContext.fillStyle =
        "rgba(255, 255, 255, 0.30)";


    waveformContext.fillText(
        "L",
        8 * ratio,
        16 * ratio
    );


    waveformContext.fillText(
        "R",
        8 * ratio,
        (height / 2) +
        (16 * ratio)
    );


    /*
     * Largeur disponible par point.
     */

    const pointWidth =
        width /
        Math.max(
            points.length,
            1
        );


    /*
     * Couleur du thème.
     */

    const style =
        getComputedStyle(
            document.documentElement
        );


    const waveformColor =
        style
            .getPropertyValue(
                "--green"
            )
            .trim()
        ||
        "#35d07f";


    waveformContext.strokeStyle =
        waveformColor;


    waveformContext.lineWidth =
        Math.max(
            ratio,
            1
        );


    /*
     * Canal gauche.
     */

    waveformContext.beginPath();


    points.forEach(
        (
            point,
            index
        ) => {

            const x =
                index *
                pointWidth;


            const amplitude =
                waveformAmplitude(
                    point.left
                );


            const y =
                amplitude *
                channelHeight;


            waveformContext.moveTo(
                x,
                leftCenter - y
            );


            waveformContext.lineTo(
                x,
                leftCenter + y
            );
        }
    );


    waveformContext.stroke();


    /*
     * Canal droit.
     */

    waveformContext.beginPath();


    points.forEach(
        (
            point,
            index
        ) => {

            const x =
                index *
                pointWidth;


            const amplitude =
                waveformAmplitude(
                    point.right
                );


            const y =
                amplitude *
                channelHeight;


            waveformContext.moveTo(
                x,
                rightCenter - y
            );


            waveformContext.lineTo(
                x,
                rightCenter + y
            );
        }
    );


    waveformContext.stroke();
}


/* ------------------------------------------------------------
   Lecture API
   ------------------------------------------------------------ */

async function updateWaveform() {

    /*
     * On ne lance pas une nouvelle requête si
     * la précédente n'est pas terminée.
     */

    if (
        waveformRequestRunning
    ) {

        return;
    }


    /*
     * Pas besoin de solliciter le NUC si
     * l'onglet Enregistrement n'est pas visible.
     */

    const recordingPage =
        document.getElementById(
            "recording-page"
        );


    if (
        !recordingPage ||
        !recordingPage
            .classList
            .contains(
                "active"
            )
    ) {

        return;
    }


    waveformRequestRunning =
        true;


    try {

        const response =
            await fetch(
                "/api/audio/waveform",
                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        drawWaveform(
            data.points,
            data.source_available
        );


    } catch (error) {

        console.error(
            "Erreur waveform :",
            error
        );


    } finally {

        waveformRequestRunning =
            false;
    }
}


/* ------------------------------------------------------------
   Rafraîchissement
   ------------------------------------------------------------ */

/*
 * 100 ms = 10 images/seconde.
 *
 * Suffisant pour une visualisation audio fluide,
 * tout en restant très raisonnable pour le J4025.
 */

setInterval(
    updateWaveform,
    100
);


/* ------------------------------------------------------------
   Resize navigateur
   ------------------------------------------------------------ */

window.addEventListener(
    "resize",
    () => {

        resizeWaveformCanvas();
    }
);