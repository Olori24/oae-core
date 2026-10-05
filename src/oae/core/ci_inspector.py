"""Read-only GitHub CI evidence inspection for OAE release gates."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

_MAX_RESPONSE = 2_000_000


class GitHubCiInspectionError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class GitHubCiInspector:
    def __init__(self, repository_url: str, opener=None):
        parsed = urlparse(repository_url)
        if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password:
            raise ValueError("repository_url must be an https GitHub URL")
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) != 2:
            raise ValueError("repository_url must point to github.com/owner/repository")
        self.owner, self.repo = parts[0], parts[1].removesuffix(".git")
        self._opener = opener or build_opener(_NoRedirect())

    def _get(self, path: str) -> dict:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            raise GitHubCiInspectionError("GitHub CI inspection requires GITHUB_TOKEN")
        request = Request(
            f"https://api.github.com{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "oae-core/0.6",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            method="GET",
        )
        try:
            with self._opener.open(request, timeout=20) as response:
                raw = response.read(_MAX_RESPONSE + 1)
                if len(raw) > _MAX_RESPONSE:
                    raise GitHubCiInspectionError("GitHub response exceeded the size limit")
                return json.loads(raw.decode()) if raw else {}
        except HTTPError as exc:
            raise GitHubCiInspectionError(f"GitHub inspection failed with HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise GitHubCiInspectionError(f"GitHub inspection failed: {type(exc).__name__}") from exc

    def inspect_commit(self, commit_sha: str) -> dict:
        if len(commit_sha) != 40 or any(c not in "0123456789abcdef" for c in commit_sha.lower()):
            raise ValueError("expected a full commit SHA")
        checks = self._get(f"/repos/{self.owner}/{self.repo}/commits/{commit_sha}/check-runs").get("check_runs", [])
        if not isinstance(checks, list) or len(checks) > 100:
            raise GitHubCiInspectionError("GitHub returned an invalid check-run collection")
        normalized = [
            {"name": str(item.get("name", ""))[:200], "status": str(item.get("status", "")),
             "conclusion": item.get("conclusion"), "url": item.get("html_url")}
            for item in checks
        ]
        pending = [x for x in normalized if x["status"] != "completed"]
        failed = [x for x in normalized if x["status"] == "completed" and x["conclusion"] not in {"success", "neutral", "skipped"}]
        passed = [x for x in normalized if x["status"] == "completed" and x["conclusion"] in {"success", "neutral", "skipped"}]
        return {
            "commit_sha": commit_sha,
            "check_count": len(normalized),
            "passed_count": len(passed),
            "pending_count": len(pending),
            "failed_count": len(failed),
            "status": "passed" if normalized and not pending and not failed else "failed" if failed else "pending",
            "checks": normalized,
        }
