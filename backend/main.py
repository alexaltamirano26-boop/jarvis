"""
Startpunkt von JARVIS.

Starten (im Projektordner):  python -m uvicorn backend.main:app
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.channels import web
from backend.config import BASE_DIR, settings
from backend.memory.models import init_db

# Server-Log: Konsole + Datei logs/jarvis.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(BASE_DIR / "logs" / "jarvis.log", encoding="utf-8")],
)

FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    (BASE_DIR / "data").mkdir(exist_ok=True)
    init_db()
    logging.getLogger("jarvis").info("JARVIS ist online. Modell: %s", settings.model)
    yield


app = FastAPI(title="JARVIS", lifespan=lifespan, docs_url=None, redoc_url=None)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="jarvis_session",
    max_age=60 * 60 * 24 * 30,  # 30 Tage eingeloggt bleiben
    same_site="strict",
    https_only=settings.secure_cookies,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Zusätzliche Schutz-Header gegen typische Web-Angriffe."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:"
    return response


app.include_router(web.router)


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login")
def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
