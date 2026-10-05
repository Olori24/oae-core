from pathlib import Path

import pytest

from oae.core.coding_brain import CodingProposal
from oae.core.coding_executor import CodingExecutionError, apply_coding_proposal


def test_apply_coding_proposal_uses_governed_callbacks(tmp_path: Path):
    calls = []
    proposal = CodingProposal(
        objective="change",
        summary="change",
        mutations=(
            {"operation": "write", "path": "src/a.py", "content": "x", "reason": "test"},
            {"operation": "delete", "path": "src/b.py", "content": "", "reason": "test"},
        ),
        verification=("pytest",),
        risks=(),
        audit={},
    )
    result = apply_coding_proposal(
        proposal=proposal,
        workspace=tmp_path,
        write_file=lambda path, content: calls.append(("write", path, content)),
        delete_file=lambda path: calls.append(("delete", path)),
    )
    assert result[0]["path"] == "src/a.py"
    assert calls == [("write", "src/a.py", "x"), ("delete", "src/b.py")]


def test_apply_coding_proposal_rejects_unvalidated_input(tmp_path: Path):
    with pytest.raises(CodingExecutionError):
        apply_coding_proposal(
            proposal=object(),
            workspace=tmp_path,
            write_file=lambda *_: None,
            delete_file=lambda *_: None,
        )
