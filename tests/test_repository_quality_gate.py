from pathlib import Path

from oae.core.repository_quality_gate import RepositoryQualityGate


def test_python_gate_discovers_standard_checks(tmp_path: Path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()

    calls = []

    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, *, cwd=None):
        calls.append((command, cwd))
        return Result()

    monkeypatch.setattr(
        "oae.core.repository_quality_gate.run_allowed_test_command",
        fake_run,
    )

    result = RepositoryQualityGate().run(tmp_path)

    assert result["verified"] is True
    assert result["production_ready"] is True
    assert [call[0][0] for call in calls] == ["pytest", "ruff", "mypy"]


def test_gate_does_not_claim_readiness_without_contract(tmp_path: Path, monkeypatch):
    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(
        "oae.core.repository_quality_gate.run_allowed_test_command",
        lambda command, *, cwd=None: Result(),
    )

    result = RepositoryQualityGate().run(tmp_path)

    assert result["verified"] is True
    assert result["production_ready"] is False
    assert result["verdict"] == "blocked"


def test_node_contract_is_detected_without_executing_scripts(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"name":"demo"}', encoding="utf-8")

    result = RepositoryQualityGate().run(tmp_path)

    assert result["production_ready"] is True
    assert result["checks"][0]["name"] == "node-project-contract"
