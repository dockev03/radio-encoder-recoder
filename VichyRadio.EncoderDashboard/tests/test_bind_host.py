from app import resolve_bind_host


def test_debug_force_ecoute_locale():
    assert resolve_bind_host("0.0.0.0", debug=True) == "127.0.0.1"


def test_debug_conserve_hote_local():
    assert resolve_bind_host("::1", debug=True) == "::1"


def test_sans_debug_conserve_hote():
    assert resolve_bind_host("0.0.0.0", debug=False) == "0.0.0.0"
