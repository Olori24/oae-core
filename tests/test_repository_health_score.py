from oae.core.repository_health_score import (
    RepositoryHealthScore,
)


def test_creation():
    score = RepositoryHealthScore()

    assert score is not None


def test_perfect_score():
    score = RepositoryHealthScore()

    result = score.calculate()

    assert result["overall"] == 100


def test_average_score():
    score = RepositoryHealthScore()

    result = score.calculate(
        security=90,
        testing=80,
        architecture=70,
        performance=60,
        documentation=50,
    )

    assert result["overall"] == 70


def test_good_recommendation():
    score = RepositoryHealthScore()

    result = score.calculate(
        security=90,
        testing=90,
        architecture=90,
        performance=90,
        documentation=90,
    )

    assert "excellent" in score.recommendation(result).lower()


def test_low_recommendation():
    score = RepositoryHealthScore()

    result = score.calculate(
        security=40,
        testing=50,
        architecture=60,
        performance=55,
        documentation=45,
    )

    recommendation = score.recommendation(result)

    assert (
        "immediate" in recommendation.lower()
        or "attention" in recommendation.lower()
    )