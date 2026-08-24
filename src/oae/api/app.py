import json
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from oae.api.config import settings
from oae.api.observability import configure_error_tracking
from oae.api.postgres_pool import close_pool
from oae.api.routes import router
from oae.api.ui_mission_control_v2 import page


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


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_pool()


app = FastAPI(
    title="Open Autonomous Engineer API",
    version="0.6.0",
    description="Multi-tenant API for autonomous repository engineering.",
    lifespan=lifespan,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
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
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/v1/") else "no-cache"
    return response


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    message = str(exc)
    logger.exception("runtime_error", extra={"path": request.url.path})
    if "database" in message.lower() or "postgres" in message.lower() or "pool" in message.lower():
        detail = "Database capacity is temporarily unavailable. Retry the request shortly."
    else:
        detail = "The service could not complete this request."
    return JSONResponse(
        status_code=503,
        content={"error": "service_unavailable", "detail": detail},
        headers={"Cache-Control": "no-store", "Retry-After": "5"},
    )


app.include_router(router)


@app.get("/", include_in_schema=False)
def landing_page():
    return page()
