class OpportunityIngestion:
    """
    Normalize raw opportunity data into a predictable structure.

    This class does not fetch remote data, score opportunities,
    rank them, or make recommendations.
    """

    FIELDS = (
        "title",
        "organization",
        "country",
        "category",
        "deadline",
        "url",
        "description",
        "eligible_countries",
        "opportunity_type",
        "funding_amount",
        "application_url",
        "source_url",
        "verification_status",
        "fit_score",
    )

    def normalize(self, raw):
        """
        Return a normalized copy of one opportunity.

        Invalid or missing input produces a safe empty structure.
        The input object is never mutated.
        """

        if not isinstance(raw, dict):
            raw = {}

        result = {}

        for field in self.FIELDS:
            value = raw.get(field, "")

            if value is None:
                value = ""

            if isinstance(value, str):
                value = value.strip()

            result[field] = value

        return result

    def normalize_many(self, opportunities):
        """
        Normalize multiple opportunities while preserving order.
        """

        if not opportunities:
            return []

        return [
            self.normalize(opportunity)
            for opportunity in opportunities
        ]
