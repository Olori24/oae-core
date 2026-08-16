"""Vercel production entrypoint for the OAE FastAPI application."""

from oae.api.app import app

__all__ = ["app"]
