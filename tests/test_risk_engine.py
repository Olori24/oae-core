from oae.core.risk_engine import RiskEngine


def test_low_risk():
    engine = RiskEngine()

    result = engine.assess("read")

    assert result.level == "LOW"
    assert result.score == 10


def test_medium_risk():
    engine = RiskEngine()

    result = engine.assess("refactor")

    assert result.level == "MEDIUM"
    assert result.score == 50


def test_high_risk():
    engine = RiskEngine()

    result = engine.assess("delete")

    assert result.level == "HIGH"
    assert result.score == 90


def test_unknown_risk():
    engine = RiskEngine()

    result = engine.assess("something_new")

    assert result.level == "UNKNOWN"
    assert result.score == 75