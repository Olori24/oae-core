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
    assert "job-123" in caplog.text
