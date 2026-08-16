"""SaaS API for Open Autonomous Engineer."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oae.api.config import settings
from oae.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Open Autonomous Engineer API",
        version="0.6.0",
        description="Multi-tenant API for autonomous repository engineering.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.include_router(router)
    return app


app = create_app()


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "oae", "status": "online", "docs": "/docs"}
