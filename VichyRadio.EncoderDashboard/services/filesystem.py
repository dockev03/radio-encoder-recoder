import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Explorateur de dossiers
#
# Le dashboard est utilisé depuis un navigateur, souvent sur un autre poste
# que l'encodeur. Une fenêtre d'explorateur native s'ouvrirait sur la machine
# serveur : on liste donc les dossiers côté serveur et la page affiche
# son propre sélecteur.
# ---------------------------------------------------------------------------

HOME_DIRECTORY = os.path.expanduser("~")

# Emplacements proposés en raccourci (clés USB, disques montés…)
SHORTCUT_CANDIDATES = [
    ("Dossier personnel", HOME_DIRECTORY),
    ("Enregistrements", os.path.join(HOME_DIRECTORY, "recordings")),
    ("Supports amovibles", "/media"),
    ("Disques montés", "/mnt"),
]


def _resolve(path):
    path = (path or "").strip()

    if not path:
        path = HOME_DIRECTORY

    return Path(
        os.path.expanduser(path)
    ).resolve()


def _get_shortcuts():
    shortcuts = []

    for label, path in SHORTCUT_CANDIDATES:
        if os.path.isdir(path):
            shortcuts.append({
                "label": label,
                "path": path
            })

    # Les clés USB sont montées dans /media/<utilisateur>/<volume>
    user_media = os.path.join("/media", os.path.basename(HOME_DIRECTORY))

    if os.path.isdir(user_media):
        try:
            for entry in sorted(os.scandir(user_media), key=lambda e: e.name.lower()):
                if entry.is_dir():
                    shortcuts.append({
                        "label": entry.name,
                        "path": entry.path
                    })
        except OSError:
            pass

    return shortcuts


def list_directories(path=None):
    directory = _resolve(path)

    # Si le chemin saisi n'existe pas encore, on remonte jusqu'au
    # premier parent existant pour que l'utilisateur puisse naviguer.
    while not directory.is_dir() and directory != directory.parent:
        directory = directory.parent

    try:
        entries = sorted(
            (
                entry for entry in os.scandir(directory)
                if entry.is_dir() and not entry.name.startswith(".")
            ),
            key=lambda e: e.name.lower()
        )
    except PermissionError:
        return {
            "success": False,
            "error": "permission_denied",
            "path": str(directory)
        }
    except OSError as error:
        return {
            "success": False,
            "error": "unreadable_directory",
            "message": str(error),
            "path": str(directory)
        }

    parent = directory.parent

    return {
        "success": True,
        "path": str(directory),
        "parent": str(parent) if parent != directory else None,
        "writable": os.access(directory, os.W_OK),
        "directories": [
            {
                "name": entry.name,
                "path": entry.path
            }
            for entry in entries
        ],
        "shortcuts": _get_shortcuts()
    }


def create_directory(parent, name):
    name = (name or "").strip()

    if (
        not name
        or name in (".", "..")
        or "/" in name
        or "\\" in name
    ):
        return {
            "success": False,
            "error": "invalid_name"
        }

    target = _resolve(parent) / name

    if target.exists():
        return {
            "success": False,
            "error": "already_exists",
            "path": str(target)
        }

    try:
        target.mkdir(parents=False)
    except PermissionError:
        return {
            "success": False,
            "error": "permission_denied"
        }
    except OSError as error:
        return {
            "success": False,
            "error": "create_failed",
            "message": str(error)
        }

    return {
        "success": True,
        "path": str(target)
    }
