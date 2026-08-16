from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


_FALLBACK_PAGE = """
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAE — Autonomous Engineering</title></head>
<body style="font-family:system-ui;max-width:760px;margin:60px auto;padding:24px">
<h1>OAE</h1><p>The service is starting. Please try again shortly.</p>
</body></html>
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title="Open Autonomous Engineer API",
        version="0.6.0",
        description="Multi-tenant API for autonomous repository engineering.",
    )

    startup_error = None
    settings = None
    page = None

    try:
        from oae.api.config import settings as loaded_settings
        from oae.api.web import page as loaded_page

        settings = loaded_settings
        page = loaded_page
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
    except Exception as exc:
        startup_error = exc
        print(f"OAE_STARTUP_IMPORT_ERROR: {type(exc).__name__}: {exc}")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/v1/") else "no-cache"
        if startup_error is not None:
            response.headers["X-OAE-Startup-Error"] = (
                f"{type(startup_error).__name__}: {startup_error}"
            )
        return response

    if startup_error is None:
        try:
            from oae.api.routes import router

            app.include_router(router)
        except Exception as exc:
            startup_error = exc
            print(f"OAE_STARTUP_ROUTE_ERROR: {type(exc).__name__}: {exc}")

    @app.get("/", include_in_schema=False)
    def landing_page():
        if page is not None:
            return page()
        from fastapi.responses import HTMLResponse

        return HTMLResponse(_FALLBACK_PAGE, status_code=503)

    @app.get("/__startup", include_in_schema=False)
    def startup_status():
        if startup_error is None:
            return {"status": "ok"}
        return {
            "status": "degraded",
            "error_type": type(startup_error).__name__,
            "error": str(startup_error),
        }

    return app


app = create_app()
