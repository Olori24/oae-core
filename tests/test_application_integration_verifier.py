from oae.core.application_integration_verifier import ApplicationIntegrationVerifier
from oae.core.executable_application_generator import ExecutableApplicationGenerator
from oae.core.project_specification import ProjectSpecification


class _LoopbackHealthResponse:
    status = 200

    def getheader(self, name, default=None):
        return "application/json" if name == "Content-Type" else default

    def read(self, _size):
        return b'{"status":"healthy"}'


class _LoopbackHealthConnection:
    def __init__(self):
        self.requested = None
        self.closed = False

    def request(self, method, path, headers):
        self.requested = (method, path, headers)

    def getresponse(self):
        return _LoopbackHealthResponse()

    def close(self):
        self.closed = True


def spec():
    return ProjectSpecification(
        name="Integration Demo",
        description="Live integration target",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )


def test_health_endpoint_is_live(tmp_path):
    root = tmp_path / "demo"
    ExecutableApplicationGenerator().generate(root, spec())

    result = ApplicationIntegrationVerifier().verify(root, spec())

    assert result["passed"] is True
    assert result["status"] == "passed"
    assert '"status":"healthy"' in result["detail"].replace(" ", "")


def test_health_reader_uses_only_the_fixed_loopback_health_contract(monkeypatch):
    import oae.core.application_integration_verifier as module

    connection = _LoopbackHealthConnection()
    monkeypatch.setattr(module.http.client, "HTTPConnection", lambda host, port, timeout: connection)

    response = ApplicationIntegrationVerifier._read_loopback_health()

    assert response == '{"status":"healthy"}'
    assert connection.requested == ("GET", "/health", {"Accept": "application/json"})
    assert connection.closed is True
