from oae.core.real_patch_engine import RealPatchEngine


def test_generate_patch():
    engine = RealPatchEngine()

    original = """def hello():
    return 1
"""

    modified = """def hello():
    return 2
"""

    result = engine.generate_patch(
        original,
        modified,
    )

    assert result["status"] == "generated"
    assert "--- a/file.py" in result["patch"]
    assert "+++ b/file.py" in result["patch"]


def test_patch_structure():
    engine = RealPatchEngine()

    result = engine.generate_patch(
        "a\n",
        "b\n",
    )

    assert "status" in result
    assert "filename" in result
    assert "patch" in result


def test_empty_patch():
    engine = RealPatchEngine()

    result = engine.generate_patch(
        "print('hi')\n",
        "print('hi')\n",
    )

    assert result["patch"] == ""
