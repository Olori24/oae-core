import json
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from oae.api.ai_routes import router as ai_router
from oae.api.config import settings
from oae.api.continuity_routes import router as continuity_router
from oae.api.conversation_routes import router as conversation_router
from oae.api.engineering_routes import router as engineering_router
from oae.api.history_routes import router as history_router
from oae.api.observability import configure_error_tracking
from oae.api.product_routes import router as product_router
from oae.api.routes import router
from oae.api.worker_routes import router as worker_router


class JsonFormatter(logging.Formatter):
    """Emit compact JSON logs suitable for production aggregation."""

    def format(self, record):
        return json.dumps(
            {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        )


_handler = logging.StreamHandler()
_handler.setFormatter(JsonFormatter())
logging.getLogger("oae").handlers.clear()
logging.getLogger("oae").addHandler(_handler)
logging.getLogger("oae").setLevel(logging.INFO)
logger = logging.getLogger("oae.api")
configure_error_tracking(settings.sentry_dsn)


app = FastAPI(
    title="Open Autonomous Engineer API",
    version="0.6.0",
    description="Multi-tenant API for autonomous repository engineering.",
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    raw_request_id = request.headers.get("X-Request-ID", "")
    if 1 <= len(raw_request_id) <= 128 and all(32 <= ord(char) <= 126 for char in raw_request_id):
        request_id = raw_request_id
    else:
        request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    if request.url.path in {"/docs", "/redoc"}:
        # FastAPI's Swagger/ReDoc pages load their UI bundle from jsDelivr and include
        # a small inline bootstrap script. Keep this exception scoped to documentation.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'; connect-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/v1/") else "no-cache"
    return response


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    error_type = type(exc).__name__
    logger.error("runtime_error", extra={"path": request.url.path, "error_type": error_type})
    message = str(exc)
    if "database" in message.lower() or "postgres" in message.lower():
        detail = "Database configuration is unavailable. Check the production database integration."
    else:
        detail = "The service could not complete this request."
    return JSONResponse(
        status_code=503,
        content={"error": "service_unavailable", "detail": detail},
        headers={"Cache-Control": "no-store"},
    )


app.include_router(router)
app.include_router(engineering_router)
app.include_router(conversation_router)
app.include_router(continuity_router)
app.include_router(history_router)
app.include_router(ai_router)
app.include_router(product_router)
app.include_router(worker_router)


_FRONTEND = Path(__file__).resolve().parents[3] / "frontend" / "index.html"
app.mount("/assets", StaticFiles(directory=_FRONTEND.parent), name="frontend-assets")


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest_file():
    path = _FRONTEND.parent / "manifest.webmanifest"
    return FileResponse(path, media_type="application/manifest+json", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/sw.js", include_in_schema=False)
def service_worker_file():
    path = _FRONTEND.parent / "sw.js"
    return FileResponse(path, media_type="application/javascript", headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@app.get("/", include_in_schema=False)
def landing_page():
    """Serve the OAE evidence-first workspace from the repository frontend bundle."""
    if not _FRONTEND.is_file():
        return HTMLResponse(
            "<h1>OAE frontend unavailable</h1><p>frontend/index.html is missing.</p>",
            status_code=503,
        )
    return HTMLResponse(_FRONTEND.read_text(encoding="utf-8"))
