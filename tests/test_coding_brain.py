import json
from pathlib import Path

import pytest

from oae.core.coding_brain import CodingBrain, CodingBrainError, RepositoryContextAssembler


class Audit:
    def __init__(self):
        self.__dict__.update({"provider": "test", "operation": "code_proposal"})


class Response:
    content = json.dumps({
        "summary": "Add the requested behavior.",
        "mutations": [{
            "operation": "write",
            "path": "src/example.py",
            "content": "def example():\n    return 1\n",
            "reason": "Implement the requested behavior.",
        }],
        "verification": ["pytest"],
        "risks": [],
    })
    audit = Audit()


class Gateway:
    def __init__(self, response=Response()):
        self.response = response
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_context_assembler_is_bounded_and_skips_generated_directories(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "secret").write_text("ignore")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')")
    context = RepositoryContextAssembler(tmp_path).assemble()
    assert "FILE: src/main.py" in context
    assert "secret" not in context


def test_coding_brain_produces_structured_proposal(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')")
    gateway = Gateway()
    proposal = CodingBrain(gateway, "approved-model").propose(
        tenant_id="tenant-a",
        workspace=tmp_path,
        objective="Add a function.",
    )
    assert proposal.mutations[0]["operation"] == "write"
    assert proposal.mutations[0]["path"] == "src/example.py"
    assert gateway.calls[0]["operation"] == "code_proposal"


@pytest.mark.parametrize(
    "mutation",
    [
        {"operation": "write", "path": "../escape.py", "content": "x"},
        {"operation": "write", "path": ".git/config", "content": "x"},
        {"operation": "execute", "path": "x.py", "content": "x"},
    ],
)
def test_coding_brain_rejects_unsafe_mutations(mutation):
    raw = json.dumps({"summary": "bad", "mutations": [mutation], "verification": [], "risks": []})
    with pytest.raises(CodingBrainError):
        CodingBrain._parse(raw, "objective", {})


def test_coding_brain_rejects_unsupported_verification():
    raw = json.dumps({
        "summary": "bad",
        "mutations": [],
        "verification": ["bash"],
        "risks": [],
    })
    with pytest.raises(CodingBrainError):
        CodingBrain._parse(raw, "objective", {})
