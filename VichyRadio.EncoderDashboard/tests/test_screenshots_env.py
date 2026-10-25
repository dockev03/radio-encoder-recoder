import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "screenshots.py"


@pytest.fixture
def screenshots(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("screenshots", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "FAKE_HOME", tmp_path / "vichyradio")

    # Variables restaurées par monkeypatch à la fin du test
    monkeypatch.setenv("HOME", "/home/reel")
    monkeypatch.setenv("USERPROFILE", r"C:\Users\reel")
    monkeypatch.setenv("VICHY_DASHBOARD_MODE", "PROD")
    monkeypatch.delenv("VICHY_DASHBOARD_ALLOWED_ROOTS", raising=False)

    return module


def test_dossier_fictif_pour_linux_et_windows(screenshots):
    screenshots._prepare_environment()

    assert os.environ["HOME"] == str(screenshots.FAKE_HOME)
    assert os.environ["USERPROFILE"] == str(screenshots.FAKE_HOME)


def test_dossier_reel_restaure(screenshots):
    real_home = screenshots._prepare_environment()
    screenshots._restore_home(real_home)

    assert os.environ["HOME"] == "/home/reel"
    assert os.environ["USERPROFILE"] == r"C:\Users\reel"


def test_variable_absente_reste_absente(screenshots, monkeypatch):
    monkeypatch.delenv("USERPROFILE")

    real_home = screenshots._prepare_environment()
    screenshots._restore_home(real_home)

    assert "USERPROFILE" not in os.environ
