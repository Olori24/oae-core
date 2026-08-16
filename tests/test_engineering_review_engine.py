from oae.capabilities.engineering_review_engine import (
    EngineeringReviewEngine,
)


def test_review(tmp_path):

    review = EngineeringReviewEngine()

    report = review.review(tmp_path)

    assert report["repository"] == tmp_path.name

    assert "health_score" in report

    assert isinstance(
        report["missions"],
        list,
    )
