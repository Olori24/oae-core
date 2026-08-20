from copy import deepcopy

from oae.core.opportunity_ingestion import OpportunityIngestion
from oae.core.opportunity_intelligence_explanation import (
    OpportunityIntelligenceExplanation,
)
from oae.core.opportunity_intelligence_scorer import (
    OpportunityIntelligenceScorer,
)
from oae.core.opportunity_ranker import OpportunityRanker
from oae.core.opportunity_recommendation_engine import (
    OpportunityRecommendationEngine,
)


class OpportunityRadarEngine:
    """
    Orchestrates the Opportunity Radar intelligence pipeline.

    Pipeline:
    ingestion -> scoring -> ranking -> recommendation -> explanation
    """

    def __init__(
        self,
        scorer=None,
        ranker=None,
        recommender=None,
        explainer=None,
        ingestion=None,
    ):
        self.scorer = scorer or OpportunityIntelligenceScorer()

        self.ranker = ranker or OpportunityRanker(
            scorer=self.scorer,
        )

        self.recommender = (
            recommender
            or OpportunityRecommendationEngine()
        )

        self.explainer = (
            explainer
            or OpportunityIntelligenceExplanation()
        )

        self.ingestion = ingestion or OpportunityIngestion()

    def analyze(self, opportunities, country):
        """
        Analyze, rank, recommend, and explain normalized opportunities.
        """

        if not opportunities:
            return {
                "opportunities": [],
                "recommendation": self.recommender.recommend([]),
                "explanation": self.explainer.explain(None),
            }

        ranked = self.ranker.rank(
            deepcopy(opportunities),
            country=country,
        )

        recommendation = self.recommender.recommend(
            ranked,
        )

        recommended_opportunity = recommendation.get(
            "opportunity"
        )

        explanation = self.explainer.explain(
            recommended_opportunity
        )

        return {
            "opportunities": ranked,
            "recommendation": recommendation,
            "explanation": explanation,
        }

    def analyze_raw(self, opportunities, country):
        """
        Normalize raw opportunities before running the
        intelligence pipeline.
        """

        normalized = self.ingestion.normalize_many(
            opportunities
        )

        return self.analyze(
            normalized,
            country=country,
        )
