from oae.core.authentication_generator import (
    AuthenticationGenerator,
)


def test_generate(tmp_path):
    AuthenticationGenerator().generate(tmp_path)

    assert (
        tmp_path
        / "src"
        / "auth"
        / "security.py"
    ).exists()

    assert (
        tmp_path
        / "src"
        / "models"
        / "user.py"
    ).exists()

    assert (
        tmp_path
        / "src"
        / "api"
        / "auth.py"
    ).exists()
