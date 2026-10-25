import pytest

from app import app
from services.recording import DEFAULT_DIRECTORY


@pytest.fixture
def client():
    app.config["TESTING"] = True

    return app.test_client()


def test_forme_onde_simulee_en_dev(client):
    result = client.get("/api/audio/waveform").get_json()

    assert result["source_available"]
    assert len(result["points"]) == 300
    assert all(
        0 < point["left"] < 1 and 0 < point["right"] < 1
        for point in result["points"]
    )


def test_page_utilise_dossier_par_defaut_du_serveur(client):
    html = client.get("/").get_data(as_text=True)

    assert f'value="{DEFAULT_DIRECTORY}"' in html
