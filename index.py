"""Stable Vercel FastAPI entrypoint for the src-layout application.

Vercel imports this module from the repository root. Add the project's src/
directory explicitly so the installed application package resolves identically
in preview deployments and local tests.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oae.api.app import app  # noqa: E402

__all__ = ["app"]
