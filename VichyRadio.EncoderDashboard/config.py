import os

MODE = os.getenv("VICHY_DASHBOARD_MODE", "DEV").upper()

IS_DEV = MODE == "DEV"
IS_PROD = MODE == "PROD"

HOST = os.getenv("VICHY_DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.getenv("VICHY_DASHBOARD_PORT", "8080"))

# Le debugger Werkzeug permet d'exécuter du code Python à distance :
# il doit être demandé explicitement et n'est jamais actif en PROD.
DEBUG = IS_DEV and os.getenv("VICHY_DASHBOARD_DEBUG", "0") == "1"
