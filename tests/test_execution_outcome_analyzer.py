from oae.core.execution_outcome_analyzer import ExecutionOutcomeAnalyzer


def test_creation():
    analyzer = ExecutionOutcomeAnalyzer()
    assert analyzer is not None


def test_empty_records():
    analyzer = ExecutionOutcomeAnalyzer()

    result = analyzer.analyze([])

    assert result["total"] == 0
    assert result["completed"] == 0
    assert result["failed"] == 0
    assert result["recovery_required"] == 0
    assert result["success_rate"] == 0


def test_completed_records():
    analyzer = ExecutionOutcomeAnalyzer()

    records = [
        {"status": "completed"},
        {"status": "completed"},
        {"status": "failed"},
    ]

    result = analyzer.analyze(records)

    assert result["total"] == 3
    assert result["completed"] == 2
    assert result["failed"] == 1
    assert result["recovery_required"] == 0
    assert result["success_rate"] == 2 / 3


def test_recovery_records():
    analyzer = ExecutionOutcomeAnalyzer()

    records = [
        {"status": "completed"},
        {"status": "recovery_required"},
        {"status": "failed"},
    ]

    result = analyzer.analyze(records)

    assert result["total"] == 3
    assert result["completed"] == 1
    assert result["failed"] == 1
    assert result["recovery_required"] == 1
    assert result["success_rate"] == 1 / 3
