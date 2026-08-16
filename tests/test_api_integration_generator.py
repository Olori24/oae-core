from pathlib import Path

from oae.core.api_integration_generator import (
    ApiIntegrationGenerator,
)


def test_generate(tmp_path):
    src = tmp_path / "src"
    src.mkdir()

    (src / "main.py").write_text("")

    ApiIntegrationGenerator().generate(tmp_path)

    assert (
        src / "main.py"
    ).exists()
