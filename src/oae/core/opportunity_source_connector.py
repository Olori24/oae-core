from urllib.parse import urlparse


class OpportunitySourceConnector:
    """
    Safe boundary between external opportunity sources
    and the Opportunity Radar pipeline.

    The transport is injected so network access can be
    tested without making real HTTP requests.
    """

    def __init__(self, transport):
        self.transport = transport

    def fetch(self, url):
        """
        Fetch a list of raw opportunities from a source.

        Invalid URLs, transport failures, and malformed responses
        return an empty list rather than crashing the Radar.
        """

        if not self._valid_url(url):
            return []

        try:
            response = self.transport.fetch(url)
        except Exception:
            return []

        if not isinstance(response, list):
            return []

        return [
            dict(opportunity)
            for opportunity in response
            if isinstance(opportunity, dict)
        ]

    def _valid_url(self, url):
        if not isinstance(url, str):
            return False

        url = url.strip()

        if not url:
            return False

        try:
            parsed = urlparse(url)
        except ValueError:
            return False

        return parsed.scheme in {"http", "https"} and bool(
            parsed.netloc
        )
