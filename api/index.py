"""Vercel production entrypoint for the OAE FastAPI application."""

from pathlib import Path
import sys


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


async def _fallback(scope, receive, send):
    body = b'OAE startup import failed'
    await send({
        "type": "http.response.start",
        "status": 503,
        "headers": [
            [b"content-type", b"text/plain; charset=utf-8"],
            [b"x-oae-entrypoint", b"fallback"],
        ],
    })
    await send({"type": "http.response.body", "body": body})


try:
    from oae.api.app import app
except Exception as exc:
    print(f"OAE_ENTRYPOINT_IMPORT_ERROR: {type(exc).__name__}: {exc}")
    app = _fallback


__all__ = ["app"]
