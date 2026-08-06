from oae.core.unified_diff_generator import UnifiedDiffGenerator


def test_generate_diff():
    generator = UnifiedDiffGenerator()

    original = """def hello():
    return 1
"""

    modified = """def hello():
    return 2
"""

    diff = generator.generate(original, modified)

    assert "--- a/file.py" in diff
    assert "+++ b/file.py" in diff
    assert "-    return 1" in diff
    assert "+    return 2" in diff


def test_empty_diff():
    generator = UnifiedDiffGenerator()

    text = "print('hello')\n"

    diff = generator.generate(text, text)

    assert diff == ""
