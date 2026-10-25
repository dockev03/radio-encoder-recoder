import os

MODE = os.getenv("VICHY_DASHBOARD_MODE", "DEV").upper()

IS_DEV = MODE == "DEV"
IS_PROD = MODE == "PROD"