from copy import deepcopy

from oae.core.opportunity_intelligence_scorer import (
    OpportunityIntelligenceScorer,
)


class OpportunityRanker:
    """Rank funding opportunities using intelligence scores."""

    def __init__(self, scorer=None):
        self.scorer = scorer or OpportunityIntelligenceScorer()

    def rank(self, opportunities, country):
        """Return opportunities ranked from strongest to weakest."""
        if not opportunities:
            return []

        ranked = []

        for opportunity in opportunities:
            intelligence = self.scorer.score(
                opportunity,
                country=country,
            )

            item = deepcopy(opportunity)
            item["intelligence_score"] = intelligence["score"]
            item["intelligence"] = intelligence

            ranked.append(item)

        ranked.sort(
            key=lambda opportunity: opportunity["intelligence_score"],
            reverse=True,
        )

        return ranked
