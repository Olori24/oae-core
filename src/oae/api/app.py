from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from oae.api.config import settings
from oae.api.routes import router


def create_app() -> FastAPI:
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
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/v1/") else "no-cache"
        return response

    app.include_router(router)
    return app


app = create_app()


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "oae", "status": "online", "docs": "/docs"}
