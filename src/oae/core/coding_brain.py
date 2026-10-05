"""Model-assisted engineering proposal engine.

The coding brain can inspect a bounded workspace and ask an approved model for a
structured mutation proposal. It never writes files, executes commands, commits,
or talks to GitHub. All consequential work remains behind OAE's governed
execution boundary.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oae.providers.open_weight import OpenWeightModelGateway

MAX_CONTEXT_FILES = 80
MAX_FILE_CHARS = 12_000
MAX_CONTEXT_CHARS = 8_000
MAX_MUTATIONS = 32
MAX_MUTATION_CHARS = 1_500_000
SAFE_PATH = re.compile(r"^[A-Za-z0-9._/-]+$")

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", ".venv", "venv", "dist", "build",
}


class CodingBrainError(ValueError):
    """Raised when a coding proposal cannot be safely produced."""


@dataclass(frozen=True)
class CodingProposal:
    objective: str
    summary: str
    mutations: tuple[dict[str, str], ...]
    verification: tuple[str, ...]
    risks: tuple[str, ...]
    audit: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "summary": self.summary,
            "mutations": list(self.mutations),
            "verification": list(self.verification),
            "risks": list(self.risks),
            "audit": self.audit,
        }


class RepositoryContextAssembler:
    """Build a bounded, deterministic source context for model planning."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def assemble(self) -> str:
        if not self.root.is_dir():
            raise CodingBrainError("Coding workspace does not exist.")

        candidates: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.root)
            if any(part in IGNORED_DIRS for part in relative.parts):
                continue
            if path.stat().st_size > MAX_FILE_CHARS * 4:
                continue
            candidates.append(path)

        candidates.sort(key=lambda p: (len(p.relative_to(self.root).parts), str(p)))
        selected = candidates[:MAX_CONTEXT_FILES]
        chunks: list[str] = []
        total = 0

        for path in selected:
            relative = path.relative_to(self.root).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            content = content[:MAX_FILE_CHARS]
            chunk = f"\n===== FILE: {relative} =====\n{content}\n"
            if total + len(chunk) > MAX_CONTEXT_CHARS:
                break
            chunks.append(chunk)
            total += len(chunk)

        return "".join(chunks)


class CodingBrain:
    """Turn a user objective plus bounded repository context into a safe proposal."""

    def __init__(self, gateway: OpenWeightModelGateway, model: str):
        self.gateway = gateway
        self.model = model

    def propose(self, *, tenant_id: str, workspace: Path, objective: str) -> CodingProposal:
        objective = objective.strip()
        if not objective or len(objective) > 4000:
            raise CodingBrainError("objective must contain 1 to 4000 characters.")

        context = RepositoryContextAssembler(workspace).assemble()
        if not context:
            raise CodingBrainError("No readable repository source was found.")

        prompt = self._prompt(objective, context)
        response = self.gateway.generate(
            tenant_id=tenant_id,
            operation="code_proposal",
            model=self.model,
            prompt=prompt,
        )
        return self._parse(response.content, objective, response.audit.__dict__)

    @staticmethod
    def _prompt(objective: str, context: str) -> str:
        return f"""Produce a minimal, implementation-ready code mutation proposal for OAE.

OBJECTIVE:
{objective}

RULES:
- Return ONLY one JSON object. No Markdown fences.
- You are proposing changes, not executing them.
- Never claim tests passed or files were changed.
- Prefer modifying existing files over creating unnecessary files.
- Every mutation must be either "write" or "delete".
- Paths are workspace-relative and must not contain "..", start with "/", or target .git.
- A write mutation must contain the COMPLETE replacement file content.
- Keep the proposal minimal and internally consistent.
- Include verification commands only from: python_compile, pytest, ruff, mypy,
  typescript_check, eslint_check, vitest_check, jest_check.
- If the objective cannot be safely implemented from the supplied context, return
  an empty mutations list and explain the blocker in risks.

JSON SHAPE:
{{
  "summary": "short implementation summary",
  "mutations": [
    {{"operation":"write","path":"src/example.py","content":"complete file","reason":"why"}},
    {{"operation":"delete","path":"src/obsolete.py","reason":"why"}}
  ],
  "verification": ["pytest"],
  "risks": ["bounded risks or blockers"]
}}

OBJECTIVE:
{objective}

REPOSITORY CONTEXT:
{context}
"""

    @staticmethod
    def _parse(raw: str, objective: str, audit: dict[str, Any]) -> CodingProposal:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CodingBrainError("Model returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise CodingBrainError("Model proposal must be a JSON object.")

        summary = payload.get("summary")
        mutations = payload.get("mutations")
        verification = payload.get("verification", [])
        risks = payload.get("risks", [])
        if not isinstance(summary, str) or not summary.strip():
            raise CodingBrainError("Model proposal requires a summary.")
        if not isinstance(mutations, list) or len(mutations) > MAX_MUTATIONS:
            raise CodingBrainError("Model proposal contains too many mutations.")
        if not isinstance(verification, list) or not all(isinstance(x, str) for x in verification):
            raise CodingBrainError("Model verification list is invalid.")
        if not isinstance(risks, list) or not all(isinstance(x, str) for x in risks):
            raise CodingBrainError("Model risks list is invalid.")

        normalized: list[dict[str, str]] = []
        for mutation in mutations:
            if not isinstance(mutation, dict):
                raise CodingBrainError("Every mutation must be an object.")
            operation = mutation.get("operation")
            path = mutation.get("path")
            reason = mutation.get("reason", "")
            if operation not in {"write", "delete"}:
                raise CodingBrainError("Mutation operation is not allowlisted.")
            if not isinstance(path, str) or not path or len(path) > 4096:
                raise CodingBrainError("Mutation path is invalid.")
            if not SAFE_PATH.fullmatch(path) or path.startswith("/") or path.startswith(".git/"):
                raise CodingBrainError("Mutation path violates the workspace path policy.")
            if ".." in Path(path).parts:
                raise CodingBrainError("Mutation path traversal is forbidden.")
            if not isinstance(reason, str) or len(reason) > 1000:
                raise CodingBrainError("Mutation reason is invalid.")
            content = mutation.get("content", "")
            if operation == "write":
                if not isinstance(content, str) or not content:
                    raise CodingBrainError("Write mutations require complete file content.")
                if len(content) > MAX_MUTATION_CHARS:
                    raise CodingBrainError("Mutation content exceeds the governed limit.")
            else:
                content = ""
            normalized.append(
                {"operation": operation, "path": path, "content": content, "reason": reason}
            )

        allowed_verification = {
            "python_compile", "pytest", "ruff", "mypy", "typescript_check",
            "eslint_check", "vitest_check", "jest_check",
        }
        if len(verification) > 8 or any(x not in allowed_verification for x in verification):
            raise CodingBrainError("Model proposed an unsupported verification command.")

        return CodingProposal(
            objective=objective,
            summary=summary[:4000],
            mutations=tuple(normalized),
            verification=tuple(verification),
            risks=tuple(r[:1000] for r in risks[:16]),
            audit=audit,
        )
