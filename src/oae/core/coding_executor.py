"""Apply validated coding proposals through the existing governed worktree boundary."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from oae.core.coding_brain import CodingProposal, CodingBrainError


class CodingExecutionError(ValueError):
    """Raised when a coding proposal cannot be safely executed."""


def apply_coding_proposal(
    *,
    proposal: CodingProposal,
    workspace: Path,
    write_file: Callable[[str, str], Any],
    delete_file: Callable[[str], Any],
) -> list[dict[str, Any]]:
    if not isinstance(proposal, CodingProposal):
        raise CodingExecutionError("Only validated CodingProposal instances may execute.")

    evidence: list[dict[str, Any]] = []
    for mutation in proposal.mutations:
        operation = mutation["operation"]
        path = mutation["path"]
        if operation == "write":
            write_file(path, mutation["content"])
        elif operation == "delete":
            delete_file(path)
        else:
            raise CodingExecutionError("Proposal contains an unsupported mutation.")
        evidence.append({
            "operation": operation,
            "path": path,
            "reason": mutation.get("reason", ""),
        })
    return evidence
