from oae.core.env_generator import EnvGenerator


def test_generate(tmp_path):
    generator = EnvGenerator()

    path = generator.generate(tmp_path)

    assert path.exists()
    assert "DATABASE_URL" in path.read_text()
