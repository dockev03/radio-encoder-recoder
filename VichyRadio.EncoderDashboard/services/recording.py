import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

from services.filesystem import is_allowed_path


SOURCE_NAME = "easyeffects_source"
SAMPLE_RATE = 48000
CHANNELS = 2

DEFAULT_DIRECTORY = os.path.expanduser("~/recordings/manual")
DEFAULT_FORMAT = "wav"

SUPPORTED_FORMATS = {
    "wav": {
        "extension": ".wav"
    },
    "flac": {
        "extension": ".flac"
    },
    "mp3": {
        "extension": ".mp3"
    }
}


_lock = threading.RLock()

_process = None
_status = "stopped"

_current_file = None
_audio_format = None

_started_at = None
_segment_started_at = None
_recorded_seconds = 0.0

_temp_directory = None
_segments = []
_segment_number = 0


# ---------------------------------------------------------------------------
# Fichiers
# ---------------------------------------------------------------------------

def _safe_filename(filename):
    filename = (filename or "").strip()

    if not filename:
        filename = datetime.now().strftime(
            "enregistrement_%d%m%Y-%H%M%S"
        )

    # Empêche d'injecter un chemin dans le nom du fichier
    filename = os.path.basename(filename)

    return filename


def _build_path(directory, filename, audio_format):
    directory = os.path.expanduser(directory)

    directory_path = Path(directory)

    directory_path.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = _safe_filename(filename)

    extension = SUPPORTED_FORMATS[audio_format]["extension"]

    # On retire une éventuelle extension connue
    for format_info in SUPPORTED_FORMATS.values():
        known_extension = format_info["extension"]

        if filename.lower().endswith(known_extension):
            filename = filename[:-len(known_extension)]
            break

    filename += extension

    return directory_path / filename


def _find_available_copy(path):
    path = Path(path)

    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    counter = 1

    while True:
        candidate = parent / (
            f"{stem}_{counter}{suffix}"
        )

        if not candidate.exists():
            return str(candidate)

        counter += 1


# ---------------------------------------------------------------------------
# FFmpeg
# ---------------------------------------------------------------------------

def _build_capture_command(segment_path):
    return [
        "ffmpeg",

        "-hide_banner",
        "-loglevel",
        "warning",

        "-f",
        "pulse",

        "-i",
        SOURCE_NAME,

        "-ac",
        str(CHANNELS),

        "-ar",
        str(SAMPLE_RATE),

        "-c:a",
        "pcm_s24le",

        "-y",

        str(segment_path)
    ]


def _start_segment():
    global _process
    global _segment_started_at
    global _segment_number

    if _temp_directory is None:
        raise RuntimeError(
            "Temporary directory is not initialized"
        )

    _segment_number += 1

    segment_path = Path(_temp_directory) / (
        f"segment_{_segment_number:04d}.wav"
    )

    command = _build_capture_command(
        segment_path
    )

    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Petite vérification : FFmpeg ne doit pas mourir immédiatement.
    time.sleep(0.15)

    if process.poll() is not None:
        raise RuntimeError(
            "FFmpeg failed to start recording"
        )

    _process = process
    _segment_started_at = time.monotonic()

    _segments.append(
        str(segment_path)
    )


def _stop_segment():
    global _process
    global _segment_started_at
    global _recorded_seconds

    if _process is None:
        return

    process = _process

    try:
        process.send_signal(
            signal.SIGINT
        )

        try:
            process.wait(
                timeout=10
            )

        except subprocess.TimeoutExpired:
            process.terminate()

            try:
                process.wait(
                    timeout=5
                )

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    finally:

        if _segment_started_at is not None:
            _recorded_seconds += max(
                0,
                time.monotonic()
                - _segment_started_at
            )

        _process = None
        _segment_started_at = None


# ---------------------------------------------------------------------------
# Assemblage final
# ---------------------------------------------------------------------------

def _create_concat_file():
    concat_path = (
        Path(_temp_directory)
        / "segments.txt"
    )

    with open(
        concat_path,
        "w",
        encoding="utf-8"
    ) as file:

        for segment in _segments:

            # Les segments sont générés par nous-mêmes.
            escaped = segment.replace(
                "'",
                "'\\''"
            )

            file.write(
                f"file '{escaped}'\n"
            )

    return concat_path


def _build_final_command(
    concat_file,
    output_file,
    audio_format
):
    command = [
        "ffmpeg",

        "-hide_banner",
        "-loglevel",
        "warning",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-vn"
    ]

    if audio_format == "wav":

        command.extend([
            "-c:a",
            "pcm_s24le",

            "-ar",
            str(SAMPLE_RATE),

            "-ac",
            str(CHANNELS)
        ])

    elif audio_format == "flac":

        command.extend([
            "-c:a",
            "flac",

            "-compression_level",
            "5",

            "-ar",
            str(SAMPLE_RATE),

            "-ac",
            str(CHANNELS)
        ])

    elif audio_format == "mp3":

        command.extend([
            "-c:a",
            "libmp3lame",

            "-b:a",
            "320k",

            "-ar",
            str(SAMPLE_RATE),

            "-ac",
            str(CHANNELS)
        ])

    command.extend([
        "-y",
        str(output_file)
    ])

    return command


def _finalize_recording():
    if not _segments:
        raise RuntimeError(
            "No recording segments available"
        )

    concat_file = _create_concat_file()

    command = _build_final_command(
        concat_file,
        _current_file,
        _audio_format
    )

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        error = result.stderr.strip()

        raise RuntimeError(
            error or "FFmpeg finalization failed"
        )

    final_path = Path(_current_file)

    if (
        not final_path.exists()
        or
        final_path.stat().st_size == 0
    ):
        raise RuntimeError(
            "Final recording file was not created"
        )


# ---------------------------------------------------------------------------
# Nettoyage
# ---------------------------------------------------------------------------

def _cleanup_temp_files():
    global _temp_directory

    if (
        _temp_directory
        and
        os.path.isdir(_temp_directory)
    ):
        shutil.rmtree(
            _temp_directory,
            ignore_errors=True
        )

    _temp_directory = None


def _reset_state():
    global _process
    global _status
    global _current_file
    global _audio_format
    global _started_at
    global _segment_started_at
    global _recorded_seconds
    global _temp_directory
    global _segments
    global _segment_number

    _process = None
    _status = "stopped"

    _current_file = None
    _audio_format = None

    _started_at = None
    _segment_started_at = None
    _recorded_seconds = 0.0

    _temp_directory = None

    _segments = []
    _segment_number = 0


# ---------------------------------------------------------------------------
# API du moteur
# ---------------------------------------------------------------------------

def start_recording(
    directory=None,
    filename=None,
    audio_format=DEFAULT_FORMAT,
    collision="error"
):
    global _status
    global _current_file
    global _audio_format
    global _started_at
    global _recorded_seconds
    global _temp_directory
    global _segments
    global _segment_number

    with _lock:

        if _status != "stopped":
            return {
                "success": False,
                "error": "recording_already_running"
            }

        audio_format = (
            audio_format
            or DEFAULT_FORMAT
        ).lower()

        if audio_format not in SUPPORTED_FORMATS:
            return {
                "success": False,
                "error": "unsupported_format"
            }

        if directory is None:
            directory = DEFAULT_DIRECTORY

        if not is_allowed_path(directory):
            return {
                "success": False,
                "error": "permission_denied",
                "directory": directory
            }

        if filename is None:
            filename = datetime.now().strftime(
                "enregistrement_%d%m%Y-%H%M%S"
            )

        path = _build_path(
            directory,
            filename,
            audio_format
        )

        if path.exists():

            if collision == "error":
                return {
                    "success": False,
                    "error": "file_exists",
                    "file": str(path)
                }

            if collision == "copy":
                path = _find_available_copy(
                    path
                )

            elif collision != "overwrite":
                return {
                    "success": False,
                    "error": "invalid_collision_mode"
                }

        _current_file = str(path)
        _audio_format = audio_format

        _started_at = time.time()
        _recorded_seconds = 0.0

        _segments = []
        _segment_number = 0

        _temp_directory = tempfile.mkdtemp(
            prefix="vichyradio-recording-"
        )

        try:
            _start_segment()

        except Exception as exception:

            _cleanup_temp_files()
            _reset_state()

            return {
                "success": False,
                "error": str(exception)
            }

        _status = "recording"

        return {
            "success": True,
            "status": _status,
            "file": _current_file,
            "format": _audio_format
        }


def pause_recording():
    global _status

    with _lock:

        if _status == "stopped":
            return {
                "success": False,
                "error": "no_recording"
            }

        if _status != "recording":
            return {
                "success": False,
                "error": "not_recording"
            }

        try:
            _stop_segment()

            _status = "paused"

            return {
                "success": True,
                "status": _status,
                "duration": round(
                    _recorded_seconds,
                    1
                )
            }

        except Exception as exception:
            return {
                "success": False,
                "error": str(exception)
            }


def resume_recording():
    global _status

    with _lock:

        if _status == "stopped":
            return {
                "success": False,
                "error": "no_recording"
            }

        if _status != "paused":
            return {
                "success": False,
                "error": "not_paused"
            }

        try:
            _start_segment()

            _status = "recording"

            return {
                "success": True,
                "status": _status
            }

        except Exception as exception:
            return {
                "success": False,
                "error": str(exception)
            }


def stop_recording():
    global _status

    with _lock:

        if _status == "stopped":
            return {
                "success": False,
                "error": "no_recording"
            }

        output_file = _current_file

        try:

            if _status == "recording":
                _stop_segment()

            _status = "finalizing"

            _finalize_recording()

        except Exception as exception:

            # IMPORTANT :
            # on ne supprime PAS les segments temporaires
            # en cas d'échec de finalisation.
            temp_directory = _temp_directory

            _status = "error"

            return {
                "success": False,
                "error": str(exception),
                "temporary_directory": temp_directory
            }

        final_size = 0

        try:
            final_size = os.path.getsize(
                output_file
            )
        except OSError:
            pass

        final_duration = round(
            _recorded_seconds,
            1
        )

        _cleanup_temp_files()
        _reset_state()

        return {
            "success": True,
            "status": "stopped",
            "file": output_file,
            "duration": final_duration,
            "size": final_size
        }

def _get_total_segments_size():
    total_size = 0

    for segment in _segments:
        try:
            total_size += os.path.getsize(
                segment
            )
        except OSError:
            pass

    return total_size

def _get_disk_free_space():
    try:
        if _current_file:
            path = os.path.dirname(
                _current_file
            )
        else:
            path = DEFAULT_DIRECTORY

        path = os.path.expanduser(
            path
        )

        # Le dossier peut ne pas encore exister.
        # On remonte jusqu'au premier parent existant.

        check_path = Path(path)

        while not check_path.exists():
            parent = check_path.parent

            if parent == check_path:
                return None

            check_path = parent

        usage = shutil.disk_usage(
            check_path
        )

        return usage.free

    except Exception:
        return None

def get_recording_status():
    global _process
    global _status
    global _segment_started_at
    global _recorded_seconds

    with _lock:

        # Détection d'un FFmpeg mort anormalement

        if (
            _status == "recording"
            and
            _process is not None
            and
            _process.poll() is not None
        ):
            # Conserve la durée déjà capturée avant la panne.
            if _segment_started_at is not None:
                _recorded_seconds += max(
                    0,
                    time.monotonic()
                    - _segment_started_at
                )

            _process = None
            _segment_started_at = None
            _status = "error"


        # ----------------------------------------------------
        # Durée
        # ----------------------------------------------------

        duration = _recorded_seconds

        if (
            _status == "recording"
            and
            _segment_started_at is not None
        ):
            duration += max(
                0,
                time.monotonic()
                -
                _segment_started_at
            )


        # ----------------------------------------------------
        # Taille cumulée de tous les segments
        # ----------------------------------------------------

        total_size = (
            _get_total_segments_size()
        )


        # ----------------------------------------------------
        # Espace disque disponible
        # ----------------------------------------------------

        disk_free = (
            _get_disk_free_space()
        )


        return {
            "status": _status,

            "recording": (
                _status == "recording"
            ),

            "paused": (
                _status == "paused"
            ),

            "finalizing": (
                _status == "finalizing"
            ),

            "error": (
                _status == "error"
            ),

            "file": _current_file,

            "format": _audio_format,

            "duration": round(
                duration,
                1
            ),

            "segment_count": len(
                _segments
            ),

            "total_size": total_size,

            "disk_free": disk_free
        }