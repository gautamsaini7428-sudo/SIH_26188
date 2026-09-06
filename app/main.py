"""
FastAPI Application Entry Point

SIH26188 - AI-Based Fake Identity & Document Screening System (Ministry of Home Affairs)
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, close_db, async_session_maker
from app.routers import verify, tampering, history, stats, auth, assistant, ocr, alerts
from app.routers.audit_log import router as audit_router
from app.services.face_match import warm_up_face_model
from app.engines import get_ocr_engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup DB init & migrations
    await init_db()

    # Warm up ArcFace model on startup
    warm_up_face_model()

    # Pre-initialize OCR engine if configured
    try:
        get_ocr_engine()
    except Exception as e:
        pass

    yield

    # Shutdown
    await close_db()


app = FastAPI(
    title="SIH26188 - Document Verification API",
    description="AI-Based Fake Identity & Document Screening System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
cors_origins = [o for o in settings.cors_origin_list if o != "*"]
if not cors_origins:
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.trycloudflare\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep uploaded identity documents private.  Verification responses carry the
# generated heatmap inline; raw uploads must never be published as static files.
os.makedirs(settings.upload_dir, exist_ok=True)

# Routers
app.include_router(auth.router)
app.include_router(verify.router)
app.include_router(ocr.router)
app.include_router(tampering.router)
app.include_router(history.router)
app.include_router(stats.router)
app.include_router(assistant.router)
app.include_router(audit_router)
app.include_router(alerts.router)



@app.get("/health")
async def health_check():
    """Health check endpoint."""
    engine_name = getattr(settings, "ocr_engine", "auto")
    try:
        from app import engines
        if getattr(engines, "_active_engine", None) is not None:
            engine_name = engines._active_engine.name
        else:
            engine_name = getattr(settings, "ocr_engine", "easyocr")
    except Exception:
        pass

    gpu_available = False
    try:
        import torch
        gpu_available = bool(torch.cuda.is_available())
    except Exception:
        gpu_available = False

    face_model_available = False
    try:
        from app.services.face_match import FACE_MODEL_AVAILABLE
        face_model_available = bool(FACE_MODEL_AVAILABLE)
    except Exception:
        face_model_available = False

    return {
        "status": "ok",
        "service": "SIH26188 Document Verification API",
        "version": "1.0.0",
        "engine": engine_name,
        "ocr_engine_available": engine_name is not None and engine_name != "none",
        "face_model_available": face_model_available,
        "face_embedding_dim": 512 if face_model_available else None,
        "gpu_available": gpu_available,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    import logging
    logger = logging.getLogger("app.main")
    logger.exception(f"Unhandled exception during {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the request."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
