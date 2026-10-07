from oae.core import ai_gateway
from oae.core.product_builder import build_product_brief


def test_ai_gateway_adds_requested_language(monkeypatch):
    captured = {}

    class FakeResponse:
        def read(self):
            return b'{"choices":[{"message":{"content":"Ciao"}}]}'
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout):
        captured["body"] = req.data.decode()
        return FakeResponse()

    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test")
    monkeypatch.setattr(ai_gateway.request, "urlopen", fake_urlopen)
    result = ai_gateway.generate_engineering_response(
        messages=[{"role": "user", "content": "Build a school app"}],
        language="it",
    )
    assert result == "Ciao"
    assert "Rispondi interamente in italiano." in captured["body"]


def test_product_brief_passes_language_to_model(monkeypatch):
    captured = {}

    def fake_generate(*, messages, system, model=None, language="en"):
        captured["system"] = system
        captured["language"] = language
        return '{"product_name":"Scuola","problem":"Gestione scolastica","users":["Amministratori"],"core_workflows":["Iscrizione"],"screens":["Dashboard"],"entities":["Studente"],"auth":"Email","integrations":[],"payments":false,"notifications":false,"deployment":"Web","build_ready":false,"missing":["Ambito MVP"]}'

    monkeypatch.setattr("oae.core.product_builder.generate_engineering_response", fake_generate)
    brief = build_product_brief("Build a school management app.", language="it")
    assert brief["product_name"] == "Scuola"
    assert captured["language"] == "it"
    assert "Requested language: it" in captured["system"]
