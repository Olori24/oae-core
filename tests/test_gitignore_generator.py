from oae.core.gitignore_generator import GitignoreGenerator


def test_generate(tmp_path):
    generator = GitignoreGenerator()

    path = generator.generate(tmp_path)

    assert path.exists()
    assert "__pycache__" in path.read_text()
