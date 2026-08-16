from fastapi import FastAPI


app = FastAPI(title="OAE Runtime Probe")


@app.get("/")
def root():
    return {"status": "ok", "runtime": "fastapi"}
