class OpportunityHttpTransport:
    """
    HTTP transport for Opportunity Radar.

    The HTTP client is injected so network behaviour can be
    tested without making real external requests.
    """

    def __init__(self, client):
        self.client = client

    def fetch(self, url):
        """
        Fetch a JSON list from an HTTP endpoint.

        Network errors, non-success responses, invalid JSON,
        and unexpected payloads return an empty list.
        """

        try:
            response = self.client.get(url)
        except Exception:
            return []

        if getattr(response, "status_code", None) != 200:
            return []

        try:
            payload = response.json()
        except Exception:
            return []

        if not isinstance(payload, list):
            return []

        return [
            dict(item)
            for item in payload
            if isinstance(item, dict)
        ]
