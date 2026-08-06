from oae.core.engineering_analysis_engine import EngineeringAnalysisEngine


def test_engine_creation():
    engine = EngineeringAnalysisEngine()

    assert engine is not None


def test_engine_analysis():
    engine = EngineeringAnalysisEngine()

    report = engine.analyze({})

    assert "dead_code" in report
    assert "duplicates" in report
    assert "circular_dependencies" in report
