"""Bounded process-local rate limiting for control-plane writes.

This guard reduces accidental or single-process abuse in every runtime. It is not a substitute
for a shared edge or Redis-backed limiter in a horizontally scaled deployment.
"""

import threading
import time
from collections import defaultdict, deque


class RateLimitExceeded(RuntimeError):
    """Raised when a principal or unauthenticated origin exceeds its control-plane budget."""


class ProcessRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def enforce(self, *, scope: str, subject: str, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            return
        now = time.monotonic()
        key = (scope, subject)
        with self._lock:
            events = self._events[key]
            cutoff = now - window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                raise RateLimitExceeded("Control-plane rate limit exceeded. Retry after the current window.")
            events.append(now)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


rate_limiter = ProcessRateLimiter()
