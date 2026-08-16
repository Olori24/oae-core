from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from oae.api.config import settings
from oae.api.routes import router
from oae.api.web import page


app = FastAPI(
    title="Open Autonomous Engineer API",
    version="0.6.0",
    description="Multi-tenant API for autonomous repository engineering.",
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)
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
    if (
        1 <= len(raw_request_id) <= 128
        and all(32 <= ord(char) <= 126 for char in raw_request_id)
    ):
        request_id = raw_request_id
    else:
        request_id = str(uuid4())

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = (
        "no-store" if request.url.path.startswith("/v1/") else "no-cache"
    )
    return response


app.include_router(router)


@app.get("/", include_in_schema=False)
def landing_page():
    return page()
