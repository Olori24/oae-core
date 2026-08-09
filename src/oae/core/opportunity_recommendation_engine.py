class OpportunityRecommendationEngine:
    """Generate advisory recommendations from ranked opportunities."""

    PRIORITIZE_THRESHOLD = 80
    REVIEW_THRESHOLD = 50

    def recommend(self, ranked_opportunities):
        """Return an advisory recommendation for the highest-ranked opportunity."""

        if not ranked_opportunities:
            return {
                "recommendation": "review",
                "opportunity": None,
                "reason": "no_opportunities_available",
                "confidence": 0.0,
            }

        opportunity = ranked_opportunities[0]

        intelligence = opportunity.get("intelligence") or {}

        score = self._score(opportunity)
        eligible = intelligence.get("eligible", False)
        deadline_status = intelligence.get(
            "deadline_status",
            "unknown",
        )

        if not eligible:
            recommendation = "deprioritize"
            reason = "opportunity_is_not_eligible"

        elif deadline_status == "expired":
            recommendation = "deprioritize"
            reason = "opportunity_deadline_has_expired"

        elif deadline_status != "open":
            recommendation = "review"
            reason = "opportunity_deadline_is_unknown"

        elif score >= self.PRIORITIZE_THRESHOLD:
            recommendation = "prioritize"
            reason = "high_intelligence_score"

        elif score >= self.REVIEW_THRESHOLD:
            recommendation = "review"
            reason = "moderate_intelligence_score"

        else:
            recommendation = "deprioritize"
            reason = "low_intelligence_score"

        confidence = self._confidence(
            score=score,
            eligible=eligible,
            deadline_status=deadline_status,
        )

        return {
            "recommendation": recommendation,
            "opportunity": opportunity,
            "reason": reason,
            "confidence": confidence,
        }

    def _score(self, opportunity):
        try:
            intelligence = opportunity.get("intelligence") or {}

            return float(
                opportunity.get(
                    "intelligence_score",
                    intelligence.get("score", 0),
                )
            )

        except (TypeError, ValueError):
            return 0.0

    def _confidence(self, score, eligible, deadline_status):
        if not eligible:
            return 1.0

        if deadline_status == "expired":
            return 1.0

        if deadline_status != "open":
            return 0.0

        confidence = abs(score - 50) / 50

        return round(
            min(max(confidence, 0.0), 1.0),
            2,
        )
