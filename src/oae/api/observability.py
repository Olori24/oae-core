"""Structured operational logging and optional error-tracking configuration."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """Render standard-library log records as compact JSON for aggregation."""

    context_fields = ("job_id", "operation", "method", "path", "request_id")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.context_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


class _OaeJsonHandler(logging.StreamHandler):
    """Marker handler used to avoid duplicate OAE JSON handlers."""


def configure_logging(app_env: str) -> None:
    """Configure JSON logs once while preserving host-provided handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if app_env == "development" else logging.INFO)
    if any(isinstance(handler, _OaeJsonHandler) for handler in root_logger.handlers):
        return

    handler = _OaeJsonHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root_logger.addHandler(handler)


def configure_error_tracking(sentry_dsn: str) -> None:
    """Initialize Sentry only when an explicit deployment DSN is provided."""
    if not sentry_dsn:
        return

    import sentry_sdk

    sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.0)
