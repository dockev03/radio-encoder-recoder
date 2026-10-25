import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    return app.test_client()


@pytest.mark.parametrize("url", [
    "/api/recording/start",
    "/api/recording/pause",
    "/api/recording/resume",
    "/api/recording/stop",
    "/api/filesystem/directories",
])
def test_post_sans_json_refuse(client, url):
    response = client.post(url, data={"directory": "/tmp"})

    assert response.status_code == 415
    assert response.get_json()["error"] == "json_required"


def test_post_json_accepte(client):
    response = client.post("/api/recording/stop", json={})

    assert response.status_code == 409
    assert response.get_json()["error"] == "no_recording"


def test_get_non_concerne(client):
    assert client.get("/api/recording/status").status_code == 200
