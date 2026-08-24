import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

GITHUB_WEB_ORIGIN = "github.com"
GITHUB_API_ORIGIN = "api.github.com"
GITHUB_API_PREFIX = "/repos/"
MAX_GITHUB_RESPONSE_BYTES = 2_000_000


class _NoRedirect(HTTPRedirectHandler):
    """Fail closed when an API response attempts to redirect a repository read."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class GitHubPublicAnalyzer:
    """Read-only analyzer for public GitHub repositories."""

    def __init__(self, opener=None):
        self._opener = opener or build_opener(_NoRedirect())

    def analyze(self, repository_url: str) -> dict:
        parsed = urlparse(repository_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != GITHUB_WEB_ORIGIN
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("repository_url must be an https GitHub URL")
        try:
            if parsed.port is not None:
                raise ValueError("repository_url must not specify a port")
        except ValueError as exc:
            raise ValueError("repository_url must be an https GitHub URL") from exc
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) != 2 or any(p in {".", ".."} for p in parts):
            raise ValueError("repository_url must point to github.com/owner/repository")

        owner, repo = parts
        repo = repo.removesuffix(".git")
        base = f"https://api.github.com/repos/{owner}/{repo}"
        metadata = self._get(base)
        tree = self._get(f"{base}/git/trees/{metadata['default_branch']}?recursive=1")
        entries = [e for e in tree.get("tree", []) if e.get("type") == "blob"]
        python_files = [e["path"] for e in entries if e.get("path", "").endswith(".py")]
        test_files = [p for p in python_files if p.startswith("test") or "/test" in p]
        config_files = [
            p for p in entries
            if p.get("path", "").endswith(("pyproject.toml", "package.json", "requirements.txt"))
        ]
        return {
            "repository": metadata["full_name"],
            "default_branch": metadata["default_branch"],
            "private": metadata["private"],
            "stars": metadata.get("stargazers_count", 0),
            "forks": metadata.get("forks_count", 0),
            "files": len(entries),
            "python_files": len(python_files),
            "test_files": len(test_files),
            "config_files": config_files[:20],
            "tree_truncated": bool(tree.get("truncated")),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get(self, url: str) -> dict:
        self._validate_api_url(url)
        token = os.getenv("GITHUB_TOKEN", "").strip()
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "oae-core/0.6",
            "X-GitHub-Api-Version": "2026-03-10",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        request = Request(url, headers=headers)
        try:
            with self._opener.open(request, timeout=15) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/json" not in content_type:
                    raise RuntimeError("GitHub API response was not JSON")
                body = response.read(MAX_GITHUB_RESPONSE_BYTES + 1)
                if len(body) > MAX_GITHUB_RESPONSE_BYTES:
                    raise RuntimeError("GitHub API response exceeded the size limit")
                return json.loads(body.decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 403:
                raise RuntimeError(
                    "GitHub API access is rate-limited. Configure GITHUB_TOKEN for the beta."
                ) from exc
            raise RuntimeError(f"GitHub request failed: HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"GitHub request failed: {exc}") from exc

    @staticmethod
    def _validate_api_url(url: str) -> None:
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != GITHUB_API_ORIGIN
            or parsed.username
            or parsed.password
            or not parsed.path.startswith(GITHUB_API_PREFIX)
            or parsed.fragment
        ):
            raise ValueError("GitHub API URL must target the expected HTTPS repository endpoint")
        try:
            if parsed.port is not None:
                raise ValueError("GitHub API URL must not specify a port")
        except ValueError as exc:
            raise ValueError("GitHub API URL must target the expected HTTPS repository endpoint") from exc
