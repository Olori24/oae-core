import pytest

from oae.core.opportunity_source_connector import (
    OpportunitySourceConnector,
)


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)

        if self.error:
            raise self.error

        return self.response


def test_connector_fetches_source():
    transport = FakeTransport(
        response=[
            {"title": "Grant A"},
            {"title": "Grant B"},
        ]
    )

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    result = connector.fetch(
        "https://example.org/opportunities"
    )

    assert len(result) == 2
    assert result[0]["title"] == "Grant A"
    assert result[1]["title"] == "Grant B"
    assert transport.calls == [
        "https://example.org/opportunities"
    ]


def test_connector_returns_empty_list_for_empty_response():
    transport = FakeTransport(response=[])

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    assert connector.fetch(
        "https://example.org/opportunities"
    ) == []


def test_connector_rejects_missing_url():
    transport = FakeTransport(response=[])

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    assert connector.fetch("") == []
    assert transport.calls == []


def test_connector_handles_transport_failure():
    transport = FakeTransport(
        error=RuntimeError("network failure")
    )

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    assert connector.fetch(
        "https://example.org/opportunities"
    ) == []


def test_connector_does_not_mutate_transport_data():
    source = [
        {"title": "Grant A"},
    ]

    transport = FakeTransport(response=source)

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    connector.fetch(
        "https://example.org/opportunities"
    )

    assert source == [
        {"title": "Grant A"},
    ]


def test_connector_rejects_non_list_response():
    transport = FakeTransport(
        response={"title": "Invalid"}
    )

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    assert connector.fetch(
        "https://example.org/opportunities"
    ) == []


def test_connector_rejects_invalid_url_scheme():
    transport = FakeTransport(response=[])

    connector = OpportunitySourceConnector(
        transport=transport,
    )

    assert connector.fetch(
        "ftp://example.org/opportunities"
    ) == []

    assert transport.calls == []
