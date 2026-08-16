class OpportunityIntelligenceExplanation:
    """
    Generate a deterministic, explainable summary from
    an opportunity's existing intelligence signals.

    This class does not calculate a new score and does not
    make a recommendation. It only explains existing evidence.
    """

    SIGNAL_LABELS = {
        "fit": "fit",
        "funding": "funding",
        "verification": "verification",
        "type": "opportunity type",
        "completeness": "completeness",
        "source_reliability": "source reliability",
        "deadline": "deadline",
    }

    POSITIVE_THRESHOLD = 80

    def explain(self, opportunity):
        """
        Return a deterministic explanation of an opportunity.
        """

        if not opportunity:
            return {
                "score": 0,
                "positive_signals": [],
                "eligibility": "unknown",
                "deadline": "unknown",
                "summary": (
                    "No opportunity data is available for analysis."
                ),
            }

        intelligence = opportunity.get("intelligence") or {}

        score = self._score(opportunity, intelligence)
        signals = intelligence.get("signals") or {}

        eligibility = self._eligibility(intelligence)
        deadline = self._deadline(intelligence)

        positive_signals = [
            label
            for signal, label in self.SIGNAL_LABELS.items()
            if self._number(signals.get(signal)) >= self.POSITIVE_THRESHOLD
        ]

        summary = self._summary(
            score=score,
            positive_signals=positive_signals,
            eligibility=eligibility,
            deadline=deadline,
        )

        return {
            "score": score,
            "positive_signals": positive_signals,
            "eligibility": eligibility,
            "deadline": deadline,
            "summary": summary,
        }

    def _score(self, opportunity, intelligence):
        value = opportunity.get(
            "intelligence_score",
            intelligence.get("score", 0),
        )

        return self._number(value)

    def _eligibility(self, intelligence):
        eligible = intelligence.get("eligible")

        if eligible is True:
            return "eligible"

        if eligible is False:
            return "ineligible"

        return "unknown"

    def _deadline(self, intelligence):
        status = intelligence.get(
            "deadline_status",
            "unknown",
        )

        if status in {
            "open",
            "expired",
            "unknown",
        }:
            return status

        return "unknown"

    def _summary(
        self,
        score,
        positive_signals,
        eligibility,
        deadline,
    ):
        if eligibility == "ineligible":
            return (
                f"Intelligence score: {score}. "
                "The opportunity is not eligible for the target country."
            )

        if deadline == "expired":
            return (
                f"Intelligence score: {score}. "
                "The opportunity deadline has expired."
            )

        if deadline == "unknown":
            if positive_signals:
                signals = ", ".join(positive_signals)
                return (
                    f"Intelligence score: {score}. "
                    f"Strong signals: {signals}. "
                    "The deadline status is unknown and requires review."
                )

            return (
                f"Intelligence score: {score}. "
                "The deadline status is unknown and requires review."
            )

        if positive_signals:
            signals = ", ".join(positive_signals)

            return (
                f"Intelligence score: {score}. "
                f"Strong signals: {signals}. "
                "The opportunity is eligible and the deadline is open."
            )

        return (
            f"Intelligence score: {score}. "
            "The opportunity is eligible and the deadline is open."
        )

    def _number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0
