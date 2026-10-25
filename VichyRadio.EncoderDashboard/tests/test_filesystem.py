import pytest

from app import app
from services import filesystem


@pytest.fixture
def root(tmp_path, monkeypatch):
    allowed = tmp_path / "autorise"
    (allowed / "emissions").mkdir(parents=True)
    (allowed / ".cache").mkdir()
    (tmp_path / "interdit").mkdir()

    monkeypatch.setattr(filesystem, "ALLOWED_ROOTS", [allowed.resolve()])

    return allowed


@pytest.fixture
def client():
    app.config["TESTING"] = True

    return app.test_client()


def test_chemin_sous_racine_autorise(root):
    assert filesystem.is_allowed_path(root / "emissions")


def test_chemin_hors_racine_refuse(root):
    assert not filesystem.is_allowed_path(root.parent / "interdit")


def test_remontee_par_dotdot_refusee(root):
    assert not filesystem.is_allowed_path(root / ".." / "interdit")


def test_dossier_cache_refuse(root):
    assert not filesystem.is_allowed_path(root / ".cache")


def test_liste_hors_racine_refusee(root):
    result = filesystem.list_directories(str(root.parent / "interdit"))

    assert result["error"] == "permission_denied"


def test_liste_racine_sans_parent_ni_cache(root):
    result = filesystem.list_directories(str(root))

    assert result["success"]
    assert result["parent"] is None
    assert [d["name"] for d in result["directories"]] == ["emissions"]


def test_creation_hors_racine_refusee(root):
    result = filesystem.create_directory(str(root.parent), "pirate")

    assert result["error"] == "permission_denied"
    assert not (root.parent / "pirate").exists()


def test_creation_sous_racine(root):
    result = filesystem.create_directory(str(root), "nouveau")

    assert result["success"]
    assert (root / "nouveau").is_dir()


def test_enregistrement_hors_racine_refuse(root, client):
    response = client.post(
        "/api/recording/start",
        json={"directory": str(root.parent / "interdit")}
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "permission_denied"
