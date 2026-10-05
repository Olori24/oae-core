from contextlib import contextmanager

from oae.api.job_runner import JobRunner


class _Result:
    def fetchone(self):
        return ("unsupported", "{}")


class _Connection:
    def execute(self, *_args):
        return _Result()


@contextmanager
def _fake_db():
    yield _Connection()


def test_failed_job_emits_log(monkeypatch, caplog):
    import oae.api.job_runner as module

    monkeypatch.setattr(module, "db", _fake_db)
    monkeypatch.setattr(JobRunner, "_dispatch", lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")))

    with caplog.at_level("ERROR", logger="oae.api.job_runner"):
        JobRunner().run("job-123")

    assert "job_execution_failed" in caplog.text
    assert any(
        record.message == "job_execution_failed" and record.__dict__.get("job_id") == "job-123"
        for record in caplog.records
    )


def test_failed_job_result_is_redacted(monkeypatch):
    import oae.api.job_runner as module

    updates = []

    class Result:
        def __init__(self, row=None):
            self._row = row

        def fetchone(self):
            return self._row

    class Connection:
        def execute(self, query, params=()):
            if query.startswith("SELECT operation,payload"):
                return Result(("unsupported", "{}"))
            if query.startswith("UPDATE jobs SET status=?,result=?"):
                updates.append(params)
            return Result()

    @contextmanager
    def fake_db():
        yield Connection()

    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(
        JobRunner,
        "_dispatch",
        lambda *_args: (_ for _ in ()).throw(
            RuntimeError("secret=super-secret database=postgresql://user:pass@internal/db")
        ),
    )

    JobRunner().run("job-redacted")

    assert updates
    result = updates[-1][1]
    assert "super-secret" not in result
    assert "postgresql://" not in result
    assert "mission_execution_failed" in result
