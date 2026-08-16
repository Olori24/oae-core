from fastapi import FastAPI


app = FastAPI(title="OAE Runtime Probe")


@app.get("/")
def root():
    try:
        from oae.api.app import app as oae_app
        return {
            "status": "oae-import-ok",
            "routes": len(oae_app.routes),
        }
    except Exception as exc:
        return {
            "status": "oae-import-failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
