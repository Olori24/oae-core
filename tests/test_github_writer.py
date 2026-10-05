import pytest

from oae.api.github_writer import GitHubRepositoryWriter, GitHubWriteError


class FakeWriter(GitHubRepositoryWriter):
    def __init__(self):
        self.owner = "acme"
        self.repo = "demo"
        self.calls = []

    def _request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "GET" and "/commits/" in path:
            return {"commit": {"tree": {"sha": "b" * 40}}}
        if method == "POST" and path.endswith("/git/trees"):
            return {"sha": "c" * 40}
        if method == "POST" and path.endswith("/git/commits"):
            return {"sha": "d" * 40}
        if method == "POST" and path.endswith("/git/refs"):
            return {"ref": "refs/heads/oae/task"}
        if method == "GET" and "/pulls?" in path:
            return []
        if method == "POST" and path.endswith("/pulls"):
            return {"number": 7, "html_url": "https://github.com/acme/demo/pull/7"}
        raise AssertionError((method, path))


def test_sync_creates_remote_tree_commit_and_branch():
    writer = FakeWriter()
    result = writer.synchronize(
        base_sha="a" * 40,
        branch="oae/task",
        files=[{"path": "src/app.py", "status": "modified", "content": "print('ok')\n"}],
        commit_message="feat: change",
    )
    assert result["commit_sha"] == "d" * 40
    assert any(call[1].endswith("/git/trees") for call in writer.calls)


def test_deleted_files_are_represented_as_tree_deletions():
    writer = FakeWriter()
    writer.synchronize(
        base_sha="a" * 40,
        branch="oae/task",
        files=[{"path": "old.txt", "status": "deleted"}],
        commit_message="chore: remove old file",
    )
    tree_call = next(call for call in writer.calls if call[1].endswith("/git/trees"))
    assert tree_call[2]["tree"][0]["sha"] is None


def test_pull_request_creation_is_bounded():
    writer = FakeWriter()
    result = writer.create_pull_request(
        branch="oae/task",
        base="main",
        title="OAE change",
        body="review",
    )
    assert result["number"] == 7


def test_pull_request_creation_is_idempotent_for_existing_open_pr():
    writer = FakeWriter()
    writer._request = lambda method, path, payload=None: (
        [{"number": 8, "head": {"ref": "oae/task"}, "base": {"ref": "main"}}]
        if method == "GET" and "/pulls?" in path
        else (_ for _ in ()).throw(AssertionError((method, path)))
    )
    result = writer.create_pull_request(branch="oae/task", base="main", title="ignored", body="ignored")
    assert result["number"] == 8


class StaleBranchWriter(FakeWriter):
    def _request(self, method, path, payload=None):
        if method == "POST" and path.endswith("/git/refs"):
            raise GitHubWriteError("GitHub mutation failed with HTTP 422", status_code=422)
        if method == "GET" and "/git/ref/heads/" in path:
            return {"object": {"sha": "e" * 40}}
        return super()._request(method, path, payload)


def test_sync_refuses_to_update_a_moved_branch():
    writer = StaleBranchWriter()
    with pytest.raises(GitHubWriteError, match="branch moved"):
        writer.synchronize(
            base_sha="a" * 40,
            branch="oae/task",
            files=[{"path": "src/app.py", "status": "modified", "content": "print('ok')
"}],
            commit_message="feat: change",
        )
