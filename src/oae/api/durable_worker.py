"""Independently deployable worker loop for PostgreSQL-leased OAE jobs."""

import argparse
import logging
import socket
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor

from oae.api.config import settings
from oae.api.durable_jobs import DurableJobRepository, LeaseLost
from oae.api.job_runner import JobRunner
from oae.api.operation_policy import OperationClass, classify_operation

logger = logging.getLogger("oae.api.durable_worker")


class DurableWorker:
    """Horizontally scalable worker with bounded in-process concurrency."""

    def __init__(self, repository: DurableJobRepository, worker_id: str, concurrency: int | None = None):
        self.repository = repository
        self.worker_id = worker_id
        self.runner = JobRunner()
        self.concurrency = concurrency or settings.durable_worker_concurrency
        self._executor = ThreadPoolExecutor(
            max_workers=self.concurrency,
            thread_name_prefix=f"oae-worker-{worker_id[:8]}",
        )
        self._futures: set[Future] = set()
        self._serialized_lock = threading.Lock()

    @property
    def active_jobs(self) -> int:
        return sum(not future.done() for future in self._futures)

    def _reap(self) -> None:
        done = {future for future in self._futures if future.done()}
        for future in done:
            self._futures.remove(future)
            try:
                future.result()
            except Exception:
                logger.exception("durable_job_thread_failed")

    def run_once(self) -> bool:
        self._reap()
        if self.active_jobs >= self.concurrency:
            return False

        lease = self.repository.claim_next(self.worker_id)
        if not lease:
            return False

        classification = classify_operation(lease.operation)
        if classification == OperationClass.HUMAN_APPROVAL_REQUIRED:
            logger.warning("job_requires_human_approval job_id=%s", lease.job_id)
            self._record_failure(lease, "operation_requires_human_approval")
            return True

        if classification == OperationClass.SERIALIZED and not self._serialized_lock.acquire(blocking=False):
            # Do not leave a claimed serialized job stranded when another job
            # currently owns the operation gate.
            self._record_failure(lease, "serialized_operation_busy")
            return True

        future = self._executor.submit(self._execute_lease, lease, classification)
        self._futures.add(future)
        return True

    def _execute_lease(self, lease, classification: OperationClass) -> None:
        try:
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
                if not lease_lost.is_set():
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
        finally:
            if classification == OperationClass.SERIALIZED:
                self._serialized_lock.release()

    def _record_failure(self, lease, reason: str = "worker_execution_failed") -> None:
        try:
            if lease.attempt_number < lease.max_attempts:
                self.repository.retry(lease, reason)
            else:
                self.repository.fail(lease, reason)
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

    def close(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OAE durable engineering workers.")
    parser.add_argument("--name", default=f"{socket.gethostname()}-worker")
    parser.add_argument("--pool", default="engineering")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=settings.durable_worker_poll_seconds)
    parser.add_argument("--concurrency", type=int, default=settings.durable_worker_concurrency)
    args = parser.parse_args()
    if args.concurrency <= 0 or args.concurrency > 64:
        raise SystemExit("--concurrency must be between 1 and 64")

    repository = DurableJobRepository()
    worker_id = repository.register_worker(worker_name=args.name, pool=args.pool)
    worker = DurableWorker(repository, worker_id, concurrency=args.concurrency)
    try:
        while True:
            worker._reap()
            recovered = repository.recover_expired_leases()
            ran = worker.run_once()
            if args.once:
                while worker.active_jobs:
                    time.sleep(0.05)
                    worker._reap()
                return 0
            if not ran and recovered == 0:
                time.sleep(max(args.poll_seconds, 0.1))
    finally:
        worker.close()
