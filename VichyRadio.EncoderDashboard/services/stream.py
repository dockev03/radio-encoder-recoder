import subprocess

from config import IS_DEV


def is_process_running(process_name):
    try:
        result = subprocess.run(
            ["pgrep", "-x", process_name],
            capture_output=True,
            text=True,
            timeout=2
        )

        return result.returncode == 0

    except Exception:
        return False


def get_stream_status():

    if IS_DEV:
        return {
            "butt": True,
            "connected": True,
            "received": True,
            "server": "AzuraCast",
            "codec": "MP3",
            "bitrate": 192
        }

    butt_running = is_process_running("butt")

    return {
        "butt": butt_running,

        # On ne sait PAS encore si BUTT est connecté.
        "connected": False,

        # Et encore moins si AzuraCast reçoit réellement le flux.
        "received": False,

        "server": "AzuraCast",
        "codec": None,
        "bitrate": None
    }


def get_now_playing():

    if IS_DEV:
        return {
            "artist": "Queen",
            "title": "Another One Bites the Dust"
        }

    return {
        "artist": None,
        "title": None
    }