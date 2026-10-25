import random
import subprocess

from config import IS_DEV


if not IS_DEV:

    from services.audio_meter import (
        start_audio_meter,
        get_audio_levels
    )


AUREON_USB_ID = "0ccd:0028"


# ============================================================
# DÉTECTION AUREON
# ============================================================

def is_aureon_present():

    try:

        result = subprocess.run(
            ["lsusb"],
            capture_output=True,
            text=True,
            timeout=2
        )

        return (
            AUREON_USB_ID.lower()
            in result.stdout.lower()
        )

    except Exception:
        return False


# ============================================================
# DÉTECTION PROCESSUS
# ============================================================

def is_process_running(process_name):

    try:

        result = subprocess.run(
            [
                "pgrep",
                "-x",
                process_name
            ],
            capture_output=True,
            text=True,
            timeout=2
        )

        return result.returncode == 0

    except Exception:
        return False


# ============================================================
# DÉMARRAGE DU VU
# ============================================================

if not IS_DEV:

    start_audio_meter()


# ============================================================
# ÉTAT AUDIO
# ============================================================

def get_audio_status():

    # --------------------------------------------------------
    # MODE DEV
    # --------------------------------------------------------

    if IS_DEV:

        left = random.uniform(
            -18,
            -3
        )

        right = (
            left
            + random.uniform(
                -2,
                2
            )
        )

        return {
            "left_db": round(left, 1),
            "right_db": round(right, 1),
            "signal": True,

            "device": "Aureon 5.1 MkII",
            "device_present": True,

            "sample_rate": 48000,

            "easyeffects": True,
            "source_available": True
        }

    # --------------------------------------------------------
    # MODE PROD
    # --------------------------------------------------------

    aureon_present = (
        is_aureon_present()
    )

    easyeffects_running = (
        is_process_running(
            "easyeffects"
        )
    )

    levels = (
        get_audio_levels()
    )

    return {
        "left_db": levels["left_db"],
        "right_db": levels["right_db"],

        "signal": levels["signal"],

        "device": "Aureon 5.1 MkII",
        "device_present": aureon_present,

        "sample_rate": 48000,

        "easyeffects": easyeffects_running,

        "source_available":
            levels["source_available"]
    }