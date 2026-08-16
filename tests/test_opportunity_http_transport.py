from oae.core.opportunity_http_transport import (
    OpportunityHttpTransport,
)


class FakeHttpClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, url):
        self.calls.append(url)

        if self.error:
            raise self.error

        return self.response


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_transport_returns_json_payload():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=200,
            payload=[
                {"title": "Grant A"},
            ],
        )
    )

    transport = OpportunityHttpTransport(
        client=client,
    )

    result = transport.fetch(
        "https://example.org/opportunities"
    )

    assert result == [
        {"title": "Grant A"},
    ]


def test_transport_returns_empty_list_for_non_200():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=404,
            payload={"error": "not found"},
        )
    )

    transport = OpportunityHttpTransport(
        client=client,
    )

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_transport_handles_http_failure():
    client = FakeHttpClient(
        error=RuntimeError("connection failed")
    )

    transport = OpportunityHttpTransport(
        client=client,
    )

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_transport_handles_invalid_json():
    class InvalidJsonResponse:
        status_code = 200

        def json(self):
            raise ValueError("invalid json")

    client = FakeHttpClient(
        response=InvalidJsonResponse()
    )

    transport = OpportunityHttpTransport(
        client=client,
    )

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_transport_rejects_non_list_payload():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=200,
            payload={"title": "Not a list"},
        )
    )

    transport = OpportunityHttpTransport(
        client=client,
    )

    assert transport.fetch(
        "https://example.org/opportunities"
    ) == []


def test_transport_calls_expected_url():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=200,
            payload=[],
        )
    )

    transport = OpportunityHttpTransport(
        client=client,
    )

    transport.fetch(
        "https://example.org/opportunities"
    )

    assert client.calls == [
        "https://example.org/opportunities"
    ]
