from fastapi.responses import HTMLResponse

PAGE = '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>OAE Mission Control</title></head><body><main><h1>OAE Mission Control</h1><p>Governed autonomous engineering.</p></main></body></html>'

def page() -> HTMLResponse:
    return HTMLResponse(PAGE)
