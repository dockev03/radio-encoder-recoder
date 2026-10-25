import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    return app.test_client()


@pytest.mark.parametrize("url", [
    "/",
    "/api/status",
    "/api/audio",
    "/api/recording/status",
])
def test_route_repond(client, url):
    assert client.get(url).status_code == 200
