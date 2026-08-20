"""Independently deployable worker loop for PostgreSQL-leased OAE jobs."""

import argparse
import logging
import socket
import threading
import time

from oae.api.config import settings
from oae.api.durable_jobs import DurableJobRepository, LeaseLost
from oae.api.job_runner import JobRunner

logger = logging.getLogger("oae.api.durable_worker")


class DurableWorker:
    def __init__(self, repository: DurableJobRepository, worker_id: str):
        self.repository = repository
        self.worker_id = worker_id
        self.runner = JobRunner()

    def run_once(self) -> bool:
        lease = self.repository.claim_next(self.worker_id)
        if not lease:
            return False
        stop_heartbeat = threading.Event()
        lease_lost = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat,
            args=(lease, stop_heartbeat, lease_lost),
            daemon=True,
        )
        heartbeat.start()
        try:
            result = self.runner._dispatch(lease.operation, lease.payload, lease.job_id)
        except Exception:
            logger.exception("durable_job_execution_failed job_id=%s", lease.job_id)
            if lease_lost.is_set():
                logger.warning("durable_job_lease_lost job_id=%s", lease.job_id)
            else:
                self._record_failure(lease)
        else:
            if lease_lost.is_set():
                logger.warning("durable_job_lease_lost job_id=%s", lease.job_id)
            else:
                try:
                    self.repository.complete(lease, result)
                except LeaseLost:
                    logger.warning("durable_job_lease_lost job_id=%s", lease.job_id)
                except Exception:
                    logger.exception("durable_job_completion_persistence_failed job_id=%s", lease.job_id)
        finally:
            stop_heartbeat.set()
            heartbeat.join(timeout=1)
        return True

    def _record_failure(self, lease) -> None:
        try:
            if lease.attempt_number < lease.max_attempts:
                self.repository.retry(lease, "worker_execution_failed")
            else:
                self.repository.fail(lease, "worker_execution_failed")
        except LeaseLost:
            logger.warning("durable_job_lease_lost job_id=%s", lease.job_id)
        except Exception:
            logger.exception("durable_job_failure_persistence_failed job_id=%s", lease.job_id)

    def _heartbeat(
        self,
        lease,
        stop_heartbeat: threading.Event,
        lease_lost: threading.Event,
    ) -> None:
        interval = max(settings.durable_job_lease_seconds / 3, 1)
        while not stop_heartbeat.wait(interval):
            try:
                self.repository.renew_lease(lease)
            except LeaseLost:
                lease_lost.set()
                return
            except Exception:
                logger.exception("durable_job_lease_heartbeat_failed job_id=%s", lease.job_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one OAE durable engineering worker.")
    parser.add_argument("--name", default=f"{socket.gethostname()}-worker")
    parser.add_argument("--pool", default="engineering")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    args = parser.parse_args()
    repository = DurableJobRepository()
    worker_id = repository.register_worker(worker_name=args.name, pool=args.pool)
    worker = DurableWorker(repository, worker_id)
    while True:
        recovered = repository.recover_expired_leases()
        ran = worker.run_once()
        if args.once:
            return 0
        if not ran and recovered == 0:
            time.sleep(max(args.poll_seconds, 0.1))
