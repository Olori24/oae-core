from datetime import date
from urllib.parse import urlparse


class OpportunityIntelligenceScorer:
    """
    Deterministic intelligence scorer for funding opportunities.

    The scorer evaluates:
    - country eligibility
    - fit
    - funding
    - verification
    - opportunity type
    - data completeness
    - source reliability
    - deadline status
    """

    OFFICIAL_DOMAINS = {
        "worldbank.org",
        "imf.org",
        "afdb.org",
        "un.org",
        "who.int",
        "unesco.org",
        "europa.eu",
        "gov.ng",
        "gov.za",
        "gov.ke",
        "gov.gh",
    }

    def score(self, opportunity, country=None):
        """
        Score an opportunity.

        `country` is optional so the scorer can be used both for:
        - country-specific eligibility checks
        - general opportunity intelligence scoring
        """

        eligible = True

        if country is not None:
            eligible = self._is_eligible(
                opportunity.get("eligible_countries"),
                country,
            )

        fit_score = self._number(
            opportunity.get("fit_score"),
            default=0,
            minimum=0,
            maximum=100,
        )

        funding_score = self._funding_score(
            opportunity.get("funding_amount")
        )

        verification_score = self._verification_score(
            opportunity.get("verification_status")
        )

        type_score = self._type_score(
            opportunity.get("opportunity_type")
        )

        completeness_score = self._completeness_score(
            opportunity
        )

        source_reliability_score = self._source_reliability_score(
            opportunity.get("source_reliability"),
            opportunity.get("source_url"),
        )

        deadline_status = self._deadline_status(
            opportunity.get("deadline")
        )

        deadline_score = self._deadline_score(
            deadline_status
        )

        score = (
            fit_score * 0.30
            + funding_score * 0.15
            + verification_score * 0.25
            + type_score * 0.05
            + completeness_score * 0.10
            + source_reliability_score * 0.05
            + deadline_score * 0.10
        )

        if not eligible:
            score *= 0.25

        if deadline_status == "expired":
            score *= 0.50

        return {
            "score": round(score, 2),
            "eligible": eligible,
            "deadline_status": deadline_status,
            "signals": {
                "fit": fit_score,
                "funding": funding_score,
                "verification": verification_score,
                "type": type_score,
                "completeness": completeness_score,
                "source_reliability": source_reliability_score,
                "deadline": deadline_score,
            },
        }

    def _is_eligible(self, eligible_countries, country):
        if not eligible_countries or not country:
            return False

        if isinstance(eligible_countries, str):
            countries = [
                item.strip().lower()
                for item in eligible_countries.split(",")
                if item.strip()
            ]
        elif isinstance(eligible_countries, (list, tuple, set)):
            countries = [
                str(item).strip().lower()
                for item in eligible_countries
                if str(item).strip()
            ]
        else:
            countries = [
                str(eligible_countries).strip().lower()
            ]

        return str(country).strip().lower() in countries

    def _number(
        self,
        value,
        default=0,
        minimum=None,
        maximum=None,
    ):
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = default

        if minimum is not None:
            number = max(minimum, number)

        if maximum is not None:
            number = min(maximum, number)

        return number

    def _funding_score(self, funding_amount):
        amount = self._number(funding_amount)

        if amount <= 0:
            return 0

        if amount >= 50000:
            return 100

        if amount >= 25000:
            return 80

        if amount >= 10000:
            return 60

        if amount >= 5000:
            return 40

        return 20

    def _verification_score(self, verification_status):
        status = str(
            verification_status or ""
        ).strip().lower()

        if status == "verified":
            return 100

        if status in {
            "partially_verified",
            "partial",
        }:
            return 60

        if status == "unverified":
            return 20

        return 0

    def _type_score(self, opportunity_type):
        value = str(
            opportunity_type or ""
        ).strip().lower()

        if value == "grant":
            return 100

        if value in {
            "accelerator",
            "fellowship",
            "incubator",
        }:
            return 80

        if value:
            return 60

        return 0

    def _completeness_score(self, opportunity):
        fields = (
            "eligible_countries",
            "opportunity_type",
            "funding_amount",
            "application_url",
            "source_url",
            "verification_status",
            "fit_score",
        )

        present = sum(
            1
            for field in fields
            if opportunity.get(field) not in (None, "")
        )

        return round(
            (present / len(fields)) * 100,
            2,
        )

    def _source_reliability_score(
        self,
        source_reliability=None,
        source_url=None,
    ):
        """
        Determine source reliability.

        Explicit reliability classification takes precedence.
        If absent, derive the baseline classification from source_url.
        """

        if source_reliability:
            value = str(
                source_reliability
            ).strip().lower()

            if value == "official":
                return 100

            if value in {
                "reputable",
                "trusted",
                "verified_directory",
            }:
                return 75

            if value in {
                "secondary",
                "aggregator",
            }:
                return 50

            if value in {
                "unknown",
                "unverified",
            }:
                return 20

        return self._source_url_score(source_url)

    def _source_url_score(self, source_url):
        if not source_url:
            return 0

        try:
            parsed = urlparse(str(source_url).strip())
            hostname = (
                parsed.hostname or ""
            ).lower().rstrip(".")
        except ValueError:
            return 0

        if not hostname:
            return 0

        if any(
            hostname == domain
            or hostname.endswith("." + domain)
            for domain in self.OFFICIAL_DOMAINS
        ):
            return 100

        return 20

    def _deadline_status(self, deadline):
        if not deadline:
            return "unknown"

        try:
            deadline_date = date.fromisoformat(
                str(deadline).strip()
            )
        except (TypeError, ValueError):
            return "unknown"

        if deadline_date < date.today():
            return "expired"

        return "open"

    def _deadline_score(self, deadline_status):
        if deadline_status == "open":
            return 100

        if deadline_status == "unknown":
            return 25

        if deadline_status == "expired":
            return 0

        return 0
