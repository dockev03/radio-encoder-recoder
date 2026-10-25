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


def _prepare_environment():
    shutil.rmtree(FAKE_HOME, ignore_errors=True)

    for name in ("emissions", "podcasts", "recordings/manual"):
        (FAKE_HOME / name).mkdir(parents=True)

    os.environ["HOME"] = str(FAKE_HOME)
    os.environ["VICHY_DASHBOARD_MODE"] = "DEV"
    os.environ.pop("VICHY_DASHBOARD_ALLOWED_ROOTS", None)

    sys.path.insert(0, str(PROJECT_DIRECTORY))


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
    _prepare_environment()

    from playwright.sync_api import sync_playwright

    server, base_url = _start_server()
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
            page.fill(
                "#recording-directory",
                str(FAKE_HOME / "recordings" / "manual")
            )
            page.locator("#recording-directory").blur()
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
