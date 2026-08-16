from urllib.parse import urlparse


class OpportunitySourceTrust:
    """Evaluate the baseline trustworthiness of an opportunity source."""

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

    def evaluate(self, source_url):
        """Return a reliability classification for a source URL."""

        if not source_url:
            return {
                "reliability": "unknown",
                "score": 0,
                "confidence": 0.0,
            }

        try:
            parsed = urlparse(source_url)
            hostname = (parsed.hostname or "").lower().rstrip(".")
        except ValueError:
            return {
                "reliability": "unknown",
                "score": 0,
                "confidence": 0.0,
            }

        if not hostname:
            return {
                "reliability": "unknown",
                "score": 0,
                "confidence": 0.0,
            }

        if self._is_official_domain(hostname):
            return {
                "reliability": "official",
                "score": 100,
                "confidence": 1.0,
            }

        return {
            "reliability": "unknown",
            "score": 25,
            "confidence": 0.25,
        }

    def _is_official_domain(self, hostname):
        return any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in self.OFFICIAL_DOMAINS
        )
