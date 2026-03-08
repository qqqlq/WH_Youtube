"""
AVAP Web Server — FastAPI application.
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server.routers import chat, script, video, projects, upload

app = FastAPI(
    title="AVAP — Video Automation Pipeline",
    version="0.4.0",
)

# ── CORS ──
_cors_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # alt dev port
]
_extra_origin = os.getenv("CORS_ORIGIN", "")
if _extra_origin:
    _cors_origins.append(_extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(chat.router, prefix="/api")
app.include_router(script.router, prefix="/api")
app.include_router(video.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(upload.router, prefix="/api")

# ── Static file serving for generated outputs ──
WORKSPACE = Path(__file__).resolve().parent.parent / "workspace" / "projects"
WORKSPACE.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(WORKSPACE)), name="outputs")


@app.get("/api/health")
def health():
    return {"status": "ok"}
