"""Model-assisted repair intelligence for governed verification failures.

The repair brain receives bounded evidence from OAE's own governed verifier.
It proposes mutations only. It cannot execute commands, write files, commit, or
talk to GitHub directly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oae.core.coding_brain import (
    CodingBrain,
    CodingBrainError,
    CodingProposal,
    RepositoryContextAssembler,
)


class CodingRepairBrain(CodingBrain):
    """Turn actual governed failure evidence into a bounded repair proposal."""

    def propose_repair(
        self,
        *,
        tenant_id: str,
        workspace: Path,
        objective: str,
        failure_evidence: dict[str, Any],
    ) -> CodingProposal:
        objective = objective.strip()
        if not objective or len(objective) > 4000:
            raise CodingBrainError("objective must contain 1 to 4000 characters.")

        context = RepositoryContextAssembler(workspace).assemble()
        if not context:
            raise CodingBrainError("No readable repository source was found.")

        bounded = json.dumps(failure_evidence, ensure_ascii=False, sort_keys=True)[:3_000]
        prompt = self._repair_prompt(objective, bounded, context)
        response = self.gateway.generate(
            tenant_id=tenant_id,
            operation="code_repair",
            model=self.model,
            prompt=prompt,
        )
        return self._parse(response.content, objective, response.audit.__dict__)

    @staticmethod
    def _repair_prompt(objective: str, failure_evidence: str, context: str) -> str:
        return f"""Produce the smallest safe repair proposal for OAE.

OBJECTIVE:
{objective[:2000]}

ACTUAL GOVERNED FAILURE EVIDENCE:
{failure_evidence}

RULES:
- Return ONLY one JSON object. No Markdown fences.
- The failure evidence above comes from OAE's governed verifier. Do not invent
  test results or claim that anything has been fixed or verified.
- Diagnose from the failure evidence and supplied repository context.
- Every mutation must be either "write" or "delete".
- Paths are workspace-relative and must not contain "..", start with "/", or target .git.
- A write mutation must contain the COMPLETE replacement file content.
- Keep the repair minimal. Do not rewrite unrelated files.
- Verification commands may only be: python_compile, pytest, ruff, mypy,
  typescript_check, eslint_check, vitest_check, jest_check.
- If the evidence/context is insufficient, return an empty mutations list and
  explain the blocker in risks.

JSON SHAPE:
{{
  "summary": "short repair summary",
  "mutations": [
    {{"operation":"write","path":"src/example.py","content":"complete file","reason":"why"}},
    {{"operation":"delete","path":"src/obsolete.py","reason":"why"}}
  ],
  "verification": ["pytest"],
  "risks": ["bounded risks or blockers"]
}}

OBJECTIVE:
{objective[:2000]}

REPOSITORY CONTEXT:
{context}
"""
