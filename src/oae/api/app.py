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
from oae.api.conversation_routes import router as conversation_router
from oae.api.engineering_routes import router as engineering_router
from oae.api.observability import configure_error_tracking
from oae.api.product_routes import router as product_router
from oae.api.routes import router
from oae.api.worker_routes import router as worker_router
