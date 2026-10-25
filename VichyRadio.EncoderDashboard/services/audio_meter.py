import array
import math
import subprocess
import threading
import time
from collections import deque


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_NAME = "easyeffects_source"

SAMPLE_RATE = 48000
CHANNELS = 2

CHUNK_FRAMES = 960

SILENCE_THRESHOLD_DB = -60.0
SIGNAL_TIMEOUT = 2.0

RECONNECT_DELAY = 1.0
SOURCE_CHECK_INTERVAL = 0.5


# Waveform
#
# 100 points correspondent approximativement
# à 2 secondes puisque chaque bloc contient
# 960 frames à 48 kHz = 20 ms.
#
# On garde davantage de points en mémoire afin
# de pouvoir faire évoluer l'affichage plus tard.

WAVEFORM_MAX_POINTS = 300


# ============================================================
# ETAT
# ============================================================

_lock = threading.Lock()

_left_db = SILENCE_THRESHOLD_DB
_right_db = SILENCE_THRESHOLD_DB

_last_audio_time = 0.0

_thread = None
_stop_event = threading.Event()

_process = None

_waveform = deque(
    maxlen=WAVEFORM_MAX_POINTS
)


# ============================================================
# OUTILS
# ============================================================

def amplitude_to_db(amplitude):
    if amplitude <= 0:
        return SILENCE_THRESHOLD_DB

    db = 20.0 * math.log10(amplitude)

    return max(
        SILENCE_THRESHOLD_DB,
        db
    )


def source_exists():
    try:
        result = subprocess.run(
            [
                "pactl",
                "list",
                "short",
                "sources"
            ],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            return False

        for line in result.stdout.splitlines():

            columns = line.split()

            if len(columns) >= 2:
                if columns[1] == SOURCE_NAME:
                    return True

        return False

    except Exception:
        return False


# ============================================================
# RESET
# ============================================================

def _reset_levels():
    global _left_db
    global _right_db
    global _last_audio_time

    with _lock:

        _left_db = SILENCE_THRESHOLD_DB
        _right_db = SILENCE_THRESHOLD_DB

        _last_audio_time = 0.0


def _reset_waveform():
    with _lock:
        _waveform.clear()


# ============================================================
# PROCESSUS PW-CAT
# ============================================================

def _stop_pw_cat():
    global _process

    process = _process

    if process is None:
        return

    try:

        if process.poll() is None:
            process.terminate()

            try:
                process.wait(
                    timeout=2
                )

            except subprocess.TimeoutExpired:
                process.kill()

                process.wait(
                    timeout=2
                )

    except Exception:
        pass

    finally:
        _process = None


# ============================================================
# WATCHDOG SOURCE
# ============================================================

def _source_watchdog(process):
    while (
        not _stop_event.is_set()
        and
        process.poll() is None
    ):

        time.sleep(
            SOURCE_CHECK_INTERVAL
        )

        if not source_exists():

            try:
                process.terminate()
            except Exception:
                pass

            return


# ============================================================
# ANALYSE AUDIO
# ============================================================

def _analyse_audio_chunk(samples):
    """
    Analyse un bloc PCM float32 stéréo.

    Retourne :
        left_db
        right_db
        waveform_left
        waveform_right

    Le DC offset est supprimé indépendamment
    pour chaque canal avant toute mesure.
    """

    if len(samples) < 2:
        return (
            SILENCE_THRESHOLD_DB,
            SILENCE_THRESHOLD_DB,
            0.0,
            0.0
        )


    left_samples = samples[0::2]
    right_samples = samples[1::2]


    if not left_samples or not right_samples:
        return (
            SILENCE_THRESHOLD_DB,
            SILENCE_THRESHOLD_DB,
            0.0,
            0.0
        )


    # --------------------------------------------------------
    # Moyenne / DC offset
    # --------------------------------------------------------

    left_mean = (
        sum(left_samples)
        /
        len(left_samples)
    )

    right_mean = (
        sum(right_samples)
        /
        len(right_samples)
    )


    # --------------------------------------------------------
    # Peak après suppression du DC
    # --------------------------------------------------------

    left_peak = 0.0
    right_peak = 0.0


    # Pour la waveform, on utilise une moyenne
    # de la valeur absolue du signal corrigé.
    #
    # Cela donne un affichage stable et beaucoup
    # plus lisible qu'un simple peak instantané.

    left_sum = 0.0
    right_sum = 0.0


    for sample in left_samples:

        corrected = (
            sample
            -
            left_mean
        )

        absolute = abs(
            corrected
        )

        if absolute > left_peak:
            left_peak = absolute

        left_sum += absolute


    for sample in right_samples:

        corrected = (
            sample
            -
            right_mean
        )

        absolute = abs(
            corrected
        )

        if absolute > right_peak:
            right_peak = absolute

        right_sum += absolute


    waveform_left = (
        left_sum
        /
        len(left_samples)
    )

    waveform_right = (
        right_sum
        /
        len(right_samples)
    )


    return (
        amplitude_to_db(
            left_peak
        ),

        amplitude_to_db(
            right_peak
        ),

        waveform_left,

        waveform_right
    )


# ============================================================
# CAPTURE AUDIO
# ============================================================

def _capture_audio():
    global _process
    global _left_db
    global _right_db
    global _last_audio_time


    if not source_exists():
        return


    command = [
        "pw-cat",
        "--record",
        f"--target={SOURCE_NAME}",
        "--format=f32",
        f"--rate={SAMPLE_RATE}",
        f"--channels={CHANNELS}",
        "--raw",
        "-"
    ]


    process = None


    try:

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

        _process = process


        watchdog = threading.Thread(
            target=_source_watchdog,
            args=(process,),
            daemon=True
        )

        watchdog.start()


        bytes_per_sample = 4

        chunk_size = (
            CHUNK_FRAMES
            *
            CHANNELS
            *
            bytes_per_sample
        )


        while not _stop_event.is_set():

            if process.poll() is not None:
                break


            raw_data = process.stdout.read(
                chunk_size
            )


            if not raw_data:
                break


            samples = array.array(
                "f"
            )

            samples.frombytes(
                raw_data
            )


            (
                left_db,
                right_db,
                waveform_left,
                waveform_right
            ) = _analyse_audio_chunk(
                samples
            )


            now = time.time()


            with _lock:

                _left_db = round(
                    left_db,
                    1
                )

                _right_db = round(
                    right_db,
                    1
                )

                _last_audio_time = now


                _waveform.append({
                    "left": round(
                        waveform_left,
                        6
                    ),

                    "right": round(
                        waveform_right,
                        6
                    )
                })


    except Exception:
        pass


    finally:

        if process is not None:

            try:

                if process.poll() is None:
                    process.terminate()

            except Exception:
                pass


        _process = None

        _reset_levels()


# ============================================================
# THREAD PRINCIPAL
# ============================================================

def _meter_worker():

    while not _stop_event.is_set():

        if source_exists():

            _capture_audio()

        else:

            _reset_levels()
            _reset_waveform()


        if not _stop_event.is_set():

            time.sleep(
                RECONNECT_DELAY
            )


# ============================================================
# API INTERNE
# ============================================================

def start_audio_meter():
    global _thread


    if (
        _thread is not None
        and
        _thread.is_alive()
    ):
        return


    _stop_event.clear()


    _thread = threading.Thread(
        target=_meter_worker,
        daemon=True,
        name="vichy-audio-meter"
    )


    _thread.start()


def stop_audio_meter():

    _stop_event.set()

    _stop_pw_cat()


# ============================================================
# NIVEAUX AUDIO
# ============================================================

def get_audio_levels():
    global _process

    with _lock:

        left_db = _left_db
        right_db = _right_db
        last_audio_time = _last_audio_time


    source_available = source_exists()


    signal_present = (
        source_available
        and
        last_audio_time > 0
        and
        (
            time.time()
            -
            last_audio_time
        ) < SIGNAL_TIMEOUT
    )


    return {
        "left_db": left_db,
        "right_db": right_db,
        "signal": signal_present,
        "source_available": source_available
    }


# ============================================================
# WAVEFORM
# ============================================================

def get_waveform():
    """
    Retourne une copie légère de l'historique
    destiné à l'affichage web.

    Exemple :

    {
        "source_available": true,
        "points": [
            {
                "left": 0.012,
                "right": 0.010
            },
            ...
        ]
    }
    """

    source_available = source_exists()


    with _lock:

        points = list(
            _waveform
        )


    return {
        "source_available":
            source_available,

        "sample_rate":
            SAMPLE_RATE,

        "chunk_frames":
            CHUNK_FRAMES,

        "points":
            points
    }