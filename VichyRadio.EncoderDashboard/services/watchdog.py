import json
import os


STATE_FILE = (
    "/tmp/vichy-audio-watchdog.json"
)


def get_watchdog_status():

    default_status = {
        "active": False,
        "recovery_count": 0,
        "last_incident": None,
        "last_recovery": None
    }

    try:

        if not os.path.exists(
            STATE_FILE
        ):
            return default_status


        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)


        return {
            "active":
                data.get(
                    "active",
                    False
                ),

            "recovery_count":
                data.get(
                    "recovery_count",
                    0
                ),

            "last_incident":
                data.get(
                    "last_incident"
                )
                or None,

            "last_recovery":
                data.get(
                    "last_recovery"
                )
                or None
        }


    except Exception:

        return default_status