from oae.core.requirements_generator import RequirementsGenerator


def test_generate(tmp_path):
    generator = RequirementsGenerator()

    path = generator.generate(tmp_path)

    assert path.exists()
    assert "pytest" in path.read_text()
