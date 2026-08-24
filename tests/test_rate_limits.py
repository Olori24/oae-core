import pytest

from oae.api.rate_limits import ProcessRateLimiter, RateLimitExceeded


def test_process_rate_limiter_rejects_excess_control_requests_inside_window():
    limiter = ProcessRateLimiter()
    limiter.enforce(scope="job-create", subject="tenant-1", limit=2)
    limiter.enforce(scope="job-create", subject="tenant-1", limit=2)

    with pytest.raises(RateLimitExceeded):
        limiter.enforce(scope="job-create", subject="tenant-1", limit=2)


def test_process_rate_limiter_keeps_distinct_tenants_and_scopes_independent():
    limiter = ProcessRateLimiter()
    limiter.enforce(scope="job-create", subject="tenant-1", limit=1)
    limiter.enforce(scope="job-create", subject="tenant-2", limit=1)
    limiter.enforce(scope="principal-key-create", subject="tenant-1", limit=1)
