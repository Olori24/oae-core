import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class GitHubPublicAnalyzer:
    """Read-only analyzer for public GitHub repositories."""

    def analyze(self, repository_url: str) -> dict:
        parsed = urlparse(repository_url)
        if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
            raise ValueError("repository_url must be an https GitHub URL")
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

    @staticmethod
    def _get(url: str) -> dict:
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
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 403:
                raise RuntimeError(
                    "GitHub API access is rate-limited. Configure GITHUB_TOKEN for the beta."
                ) from exc
            raise RuntimeError(f"GitHub request failed: HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"GitHub request failed: {exc}") from exc
