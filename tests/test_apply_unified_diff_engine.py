from oae.core.apply_unified_diff_engine import (
    ApplyUnifiedDiffEngine,
)


def test_apply(tmp_path):
    file = tmp_path / "example.py"

    file.write_text("print(1)\n")

    engine = ApplyUnifiedDiffEngine()

    result = engine.apply(
        file,
        "print(2)\n",
    )

    assert result["status"] == "applied"
    assert file.read_text() == "print(2)\n"


def test_file_recorded(tmp_path):
    file = tmp_path / "sample.py"

    file.write_text("a")

    engine = ApplyUnifiedDiffEngine()

    result = engine.apply(file, "b")

    assert result["file"].endswith("sample.py")


def test_size(tmp_path):
    file = tmp_path / "size.py"

    file.write_text("")

    engine = ApplyUnifiedDiffEngine()

    result = engine.apply(file, "hello")

    assert result["size"] == 5
