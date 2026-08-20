"""Keep test execution deterministic when host-level deployment variables are present."""

import os

pytest_plugins = ["tests.postgres_integration"]

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./.pytest-oae.db"
os.environ["SECRET_KEY"] = "test-only-secret-not-for-production"
os.environ.pop("SENTRY_DSN", None)
os.environ.pop("VERCEL", None)
