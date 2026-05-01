# -*- coding: utf-8 -*-
"""
FOR-BAZI FastAPI backend — application entry point.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Or via the CLI:
    python -m backend.main
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path bootstrap — make project-root packages importable.
# This must happen before any project imports.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.chart import router as chart_router
from backend.api.chat import router as chat_router
from backend.api.texts import router as texts_router
from backend.api.compatibility import router as compatibility_router
from backend.api.entertainment import router as entertainment_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FOR-BAZI API",
    description=(
        "专业八字命理 API — 提供排盘、五行精算、格局判定、"
        "古籍查询、AI 流式对话等功能。"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# -- CORS -----------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# -- Routers --------------------------------------------------------------

app.include_router(chart_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(texts_router, prefix="/api/v1")
app.include_router(compatibility_router, prefix="/api/v1")
app.include_router(entertainment_router, prefix="/api/v1")

# -- Health check ---------------------------------------------------------


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """
    Liveness probe.  Returns ``{"status": "ok"}`` when the server is running.
    """
    return {"status": "ok"}


# -- Direct execution -----------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
