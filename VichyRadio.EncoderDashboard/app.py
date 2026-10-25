from flask import Flask, render_template, jsonify, request

from config import MODE, HOST, PORT, DEBUG

from services.audio import get_audio_status
from services.audio_meter import (
    get_audio_levels,
    get_waveform
)
from services.system import (
    get_system_status,
    get_network_status
)
from services.stream import (
    get_stream_status,
    get_now_playing
)
from services.watchdog import (
    get_watchdog_status
)
from services.recording import (
    get_recording_status,
    start_recording,
    pause_recording,
    resume_recording,
    stop_recording
)
from services.filesystem import (
    list_directories,
    create_directory
)


app = Flask(__name__)


# ---------------------------------------------------------------------------
# Protection CSRF
#
# Un site tiers ouvert dans le navigateur d'un poste de la régie peut
# envoyer un POST vers le dashboard (formulaire, fetch "no-cors"…), mais
# jamais avec un Content-Type JSON sans requête CORS préalable, que Flask
# refuse par défaut. Exiger du JSON suffit donc à bloquer ces requêtes.
# ---------------------------------------------------------------------------

@app.before_request
def require_json_post():

    if request.method == "POST" and not request.is_json:
        return jsonify({
            "success": False,
            "error": "json_required"
        }), 415


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

@app.route("/api/audio")
def audio():

    if MODE == "DEV":
        status = get_audio_status()

        return jsonify({
            "left_db": status["left_db"],
            "right_db": status["right_db"],
            "signal": status["signal"],
            "source_available": status["source_available"]
        })

    return jsonify(
        get_audio_levels()
    )

@app.route("/api/audio/waveform")
def audio_waveform():

    return jsonify(
        get_waveform()
    )


# ---------------------------------------------------------------------------
# État général
# ---------------------------------------------------------------------------

@app.route("/api/status")
def status():

    audio_status = get_audio_status()
    network_status = get_network_status()
    system_status = get_system_status()
    stream_status = get_stream_status()
    watchdog_status = get_watchdog_status()
    recording_status = get_recording_status()
    now_playing = get_now_playing()

    ready = (
        audio_status["device_present"]
        and audio_status["easyeffects"]
        and audio_status["source_available"]
        and network_status["connected"]
    )

    return jsonify({
        "mode": MODE,
        "ready": ready,

        "audio": audio_status,
        "network": network_status,
        "stream": stream_status,
        "system": system_status,
        "watchdog": watchdog_status,
        "recording": recording_status,
        "now_playing": now_playing
    })


# ---------------------------------------------------------------------------
# Enregistrement manuel
# ---------------------------------------------------------------------------

@app.route(
    "/api/recording/status",
    methods=["GET"]
)
def recording_status():

    return jsonify(
        get_recording_status()
    )


@app.route(
    "/api/recording/start",
    methods=["POST"]
)
def recording_start():

    data = request.get_json(
        silent=True
    ) or {}

    directory = data.get(
        "directory"
    )

    filename = data.get(
        "filename"
    )

    audio_format = data.get(
        "format",
        "wav"
    )

    collision = data.get(
        "collision",
        "error"
    )

    result = start_recording(
        directory=directory,
        filename=filename,
        audio_format=audio_format,
        collision=collision
    )

    if result.get("success"):
        return jsonify(result), 200

    error = result.get("error")

    if error == "file_exists":
        return jsonify(result), 409

    if error in (
        "unsupported_format",
        "invalid_collision_mode"
    ):
        return jsonify(result), 400

    if error == "recording_already_running":
        return jsonify(result), 409

    if error == "permission_denied":
        return jsonify(result), 403

    return jsonify(result), 500


@app.route(
    "/api/recording/pause",
    methods=["POST"]
)
def recording_pause():

    result = pause_recording()

    if result.get("success"):
        return jsonify(result), 200

    if result.get("error") in (
        "no_recording",
        "not_recording"
    ):
        return jsonify(result), 409

    return jsonify(result), 500


@app.route(
    "/api/recording/resume",
    methods=["POST"]
)
def recording_resume():

    result = resume_recording()

    if result.get("success"):
        return jsonify(result), 200

    if result.get("error") in (
        "no_recording",
        "not_paused"
    ):
        return jsonify(result), 409

    return jsonify(result), 500


@app.route(
    "/api/recording/stop",
    methods=["POST"]
)
def recording_stop():

    result = stop_recording()

    if result.get("success"):
        return jsonify(result), 200

    if result.get("error") == "no_recording":
        return jsonify(result), 409

    return jsonify(result), 500


# ---------------------------------------------------------------------------
# Explorateur de dossiers
# ---------------------------------------------------------------------------

@app.route(
    "/api/filesystem/directories",
    methods=["GET"]
)
def filesystem_directories():

    result = list_directories(
        request.args.get("path")
    )

    if result.get("success"):
        return jsonify(result), 200

    if result.get("error") == "permission_denied":
        return jsonify(result), 403

    return jsonify(result), 500


@app.route(
    "/api/filesystem/directories",
    methods=["POST"]
)
def filesystem_create_directory():

    data = request.get_json(
        silent=True
    ) or {}

    result = create_directory(
        data.get("parent"),
        data.get("name")
    )

    if result.get("success"):
        return jsonify(result), 201

    error = result.get("error")

    if error == "invalid_name":
        return jsonify(result), 400

    if error == "already_exists":
        return jsonify(result), 409

    if error == "permission_denied":
        return jsonify(result), 403

    return jsonify(result), 500


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def resolve_bind_host(host, debug):

    # Debugger actif : on n'écoute qu'en local, quel que soit HOST
    if debug and host not in LOOPBACK_HOSTS:
        return "127.0.0.1"

    return host


if __name__ == "__main__":

    app.run(
        host=resolve_bind_host(HOST, DEBUG),
        port=PORT,
        debug=DEBUG
    )
