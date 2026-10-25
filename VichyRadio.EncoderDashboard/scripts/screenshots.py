"""
Génère les captures d'écran du README (docs/screenshots/).

Le dashboard est lancé en mode DEV (données simulées) avec un dossier
personnel fictif, pour que les captures soient reproductibles et ne
montrent rien de la machine qui les produit.

    pip install -r requirements-dev.txt
    playwright install chromium
    python scripts/screenshots.py
"""

import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = PROJECT_DIRECTORY.parent / "docs" / "screenshots"

VIEWPORT = {"width": 1440, "height": 900}

# Laisse le temps au VU-mètre et aux appels /api/status de se rafraîchir
SETTLE_MS = 2500


# Dossier personnel fictif, au chemin stable pour des captures identiques
FAKE_HOME = Path(tempfile.gettempdir()) / "vichy-screenshots" / "vichyradio"

# Variables lues par os.path.expanduser : HOME sous Linux et macOS,
# USERPROFILE sous Windows.
HOME_VARIABLES = ("HOME", "USERPROFILE")


def _prepare_environment():
    real_home = {
        name: os.environ.get(name)
        for name in HOME_VARIABLES
    }

    shutil.rmtree(FAKE_HOME, ignore_errors=True)

    for name in ("emissions", "podcasts", "recordings/manual"):
        (FAKE_HOME / name).mkdir(parents=True)

    for name in HOME_VARIABLES:
        os.environ[name] = str(FAKE_HOME)

    os.environ["VICHY_DASHBOARD_MODE"] = "DEV"
    os.environ.pop("VICHY_DASHBOARD_ALLOWED_ROOTS", None)

    sys.path.insert(0, str(PROJECT_DIRECTORY))

    return real_home


def _restore_home(real_home):
    for name, value in real_home.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def _start_server():
    from werkzeug.serving import make_server

    from app import app

    server = make_server("127.0.0.1", 0, app)

    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server, f"http://127.0.0.1:{server.server_port}"


def _capture(page, name, full_page=True):
    page.wait_for_timeout(SETTLE_MS)
    page.screenshot(
        path=OUTPUT_DIRECTORY / f"{name}.png",
        full_page=full_page
    )

    print(f"  docs/screenshots/{name}.png")


def main():
    real_home = _prepare_environment()

    from playwright.sync_api import sync_playwright

    server, base_url = _start_server()

    # L'application a lu le dossier fictif à l'import : on restaure le
    # vrai dossier personnel pour que Playwright retrouve ses navigateurs.
    _restore_home(real_home)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
            )

            page = browser.new_page(viewport=VIEWPORT)
            page.goto(base_url)

            _capture(page, "dashboard")

            page.click('[data-page="recording-page"]')
            _capture(page, "enregistrement")

            page.click("#recording-directory-browse")
            page.wait_for_selector("#directory-picker-modal:not([hidden])")
            page.click("#directory-picker-shortcuts >> text=Dossier personnel")

            # La fenêtre est en position fixe : capture de l'écran seul
            _capture(page, "explorateur", full_page=False)

            browser.close()

    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
