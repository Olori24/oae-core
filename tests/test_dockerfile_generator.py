from oae.core.dockerfile_generator import DockerfileGenerator


def test_generate(tmp_path):
    path = DockerfileGenerator().generate(tmp_path)

    assert path.exists()
    assert "FROM python" in path.read_text()
