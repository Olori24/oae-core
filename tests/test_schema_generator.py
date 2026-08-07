from oae.core.schema_generator import SchemaGenerator


def test_generate(tmp_path):
    SchemaGenerator().generate(tmp_path)

    assert (
        tmp_path
        / "src"
        / "schemas"
        / "opportunity.py"
    ).exists()

    assert (
        tmp_path
        / "src"
        / "schemas"
        / "user.py"
    ).exists()
