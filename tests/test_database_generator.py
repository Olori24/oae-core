from oae.core.database_generator import DatabaseGenerator


def test_generate(tmp_path):
    DatabaseGenerator().generate(tmp_path)

    assert (
        tmp_path
        / "src"
        / "database"
        / "database.py"
    ).exists()
