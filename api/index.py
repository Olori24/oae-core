"""Vercel production entrypoint for the OAE FastAPI application."""

from pathlib import Path
import sys


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from oae.api.app import app

__all__ = ["app"]
