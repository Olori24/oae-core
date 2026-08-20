import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "check_coverage_threshold.py"


def run_checker(tmp_path, payload, threshold=70):
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--coverage-file",
            str(report),
            "--threshold",
            str(threshold),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_coverage_checker_passes_at_threshold(tmp_path):
    result = run_checker(tmp_path, {"totals": {"percent_covered": 70.0}})

    assert result.returncode == 0
    assert "Coverage threshold check passed" in result.stdout


def test_coverage_checker_fails_below_threshold(tmp_path):
    result = run_checker(tmp_path, {"totals": {"percent_covered": 69.99}})

    assert result.returncode == 1
    assert "Coverage threshold check failed" in result.stdout


def test_coverage_checker_rejects_invalid_report(tmp_path):
    result = run_checker(tmp_path, {"totals": {}})

    assert result.returncode == 2
    assert "Coverage check error" in result.stdout
