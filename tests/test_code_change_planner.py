from oae.core.code_change_planner import CodeChangePlanner


def test_creation():
    planner = CodeChangePlanner()

    assert planner is not None


def test_empty_repository():
    planner = CodeChangePlanner()

    result = planner.plan("Fix auth", [])

    assert result["files"] == []


def test_auth_detection():
    planner = CodeChangePlanner()

    files = [
        "auth.py",
        "main.py",
    ]

    result = planner.plan("Fix auth", files)

    assert "auth.py" in result["files"]


def test_multiple_matches():
    planner = CodeChangePlanner()

    files = [
        "auth.py",
        "models.py",
        "tests.py",
        "routes.py",
    ]

    result = planner.plan("Improve project", files)

    assert len(result["files"]) == 4


def test_mission_preserved():
    planner = CodeChangePlanner()

    result = planner.plan("Improve auth", ["auth.py"])

    assert result["mission"] == "Improve auth"