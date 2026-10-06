"""Governed GitHub synchronization for OAE change sets."""
from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE = 2_000_000


class GitHubWriteError(RuntimeError):
    """Raised when a governed GitHub mutation cannot be completed."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class GitHubRepositoryWriter:
    """Create a reviewable GitHub branch and pull request without shell credentials."""

    def __init__(self, repository_url: str, opener=None):
        parsed = urlparse(repository_url)
        if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("repository_url must be an https GitHub URL")
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) != 2:
            raise ValueError("repository_url must point to github.com/owner/repository")
        self.owner = parts[0]
        self.repo = parts[1].removesuffix(".git")
        self._opener = opener or build_opener(_NoRedirect())

    def _request(self, method: str, path: str, payload: dict | None = None) -> Any:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            raise GitHubWriteError("GitHub synchronization requires GITHUB_TOKEN")
        body = None if payload is None else json.dumps(payload).encode()
        request = Request(
            f"https://api.github.com{path}",
            data=body,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "oae-core/0.6",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            method=method,
        )
        try:
            with self._opener.open(request, timeout=20) as response:
                raw = response.read(MAX_RESPONSE + 1)
                if len(raw) > MAX_RESPONSE:
                    raise GitHubWriteError("GitHub response exceeded the size limit")
                return json.loads(raw.decode()) if raw else {}
        except HTTPError as exc:
            raise GitHubWriteError(f"GitHub mutation failed with HTTP {exc.code}", status_code=exc.code) from exc
        except (URLError, TimeoutError) as exc:
            raise GitHubWriteError(f"GitHub request failed: {type(exc).__name__}") from exc

    def synchronize(self, *, base_sha: str, branch: str, files: list[dict], commit_message: str) -> dict:
        self._validate_sha(base_sha)
        self._validate_ref(branch)
        if not files or len(files) > 200:
            raise ValueError("change set must contain between 1 and 200 files")
        base = self._request("GET", f"/repos/{self.owner}/{self.repo}/commits/{base_sha}")
        base_tree = base.get("commit", {}).get("tree", {}).get("sha")
        if not base_tree:
            raise GitHubWriteError("GitHub did not return the base tree")
        entries = []
        for item in files:
            path = item.get("path", "")
            self._validate_path(path)
            if item.get("status") == "deleted":
                entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
                continue
            content = item.get("content")
            if not isinstance(content, str) or len(content.encode()) > 2 * 1024 * 1024:
                raise ValueError("changed file is invalid or exceeds 2 MiB")
            entries.append({"path": path, "mode": "100644", "type": "blob", "content": content})
        tree = self._request("POST", f"/repos/{self.owner}/{self.repo}/git/trees", {"base_tree": base_tree, "tree": entries})
        tree_sha = tree.get("sha")
        if not tree_sha:
            raise GitHubWriteError("GitHub did not return the tree SHA")
        commit = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/git/commits",
            {"message": commit_message[:200], "tree": tree_sha, "parents": [base_sha]},
        )
        commit_sha = commit.get("sha")
        if not commit_sha:
            raise GitHubWriteError("GitHub did not return the commit SHA")
        try:
            self._request(
                "POST",
                f"/repos/{self.owner}/{self.repo}/git/refs",
                {"ref": f"refs/heads/{branch}", "sha": commit_sha},
            )
        except GitHubWriteError as exc:
            if exc.status_code != 422:
                raise
            current = self._request(
                "GET",
                f"/repos/{self.owner}/{self.repo}/git/ref/heads/{branch}",
            )
            current_sha = current.get("object", {}).get("sha")
            if current_sha != base_sha:
                raise GitHubWriteError("GitHub branch moved since the governed base revision; refusing concurrent update.")
            self._request(
                "PATCH",
                f"/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}",
                {"sha": commit_sha, "force": False},
            )
        return {"branch": branch, "commit_sha": commit_sha, "tree_sha": tree_sha}

    def create_pull_request(self, *, branch: str, base: str, title: str, body: str) -> dict:
        self._validate_ref(branch)
        self._validate_ref(base)
        existing = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/pulls?state=open&head={self.owner}:{branch}&base={base}&per_page=10",
        )
        if isinstance(existing, list):
            for pull in existing:
                if (
                    pull.get("head", {}).get("ref") == branch
                    and pull.get("base", {}).get("ref") == base
                ):
                    return pull
        return self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/pulls",
            {"title": title[:200], "body": body[:10000], "head": branch, "base": base},
        )

    @staticmethod
    def _validate_sha(value: str) -> None:
        if len(value) != 40 or any(c not in "0123456789abcdef" for c in value.lower()):
            raise ValueError("expected a full commit SHA")

    @staticmethod
    def _validate_ref(value: str) -> None:
        if not value or len(value) > 120 or value.startswith("-") or ".." in value or "@{" in value:
            raise ValueError("invalid Git ref")

    @staticmethod
    def _validate_path(value: str) -> None:
        parts = value.split("/")
        if not value or value.startswith("/") or any(part in {"", ".", ".."} for part in parts) or value.startswith(".git/") or value == ".git":
            raise ValueError("unsafe repository path")
