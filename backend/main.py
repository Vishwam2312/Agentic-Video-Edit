import sys
import asyncio
import logging
from contextlib import asynccontextmanager

# ── Windows asyncio fix ───────────────────────────────────────────────────────
# Python 3.12 on Windows defaults to ProactorEventLoop which breaks Motor's
# async SSL handshake with MongoDB Atlas.  SelectorEventLoop works correctly.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import settings
from backend.services.database import connect_db, disconnect_db
from backend.routers import (
    upload_router,
    script_router,
    export_router,
    project_router,
    render_pipeline_router,
)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class _InterceptHandler(logging.Handler):
    """Route standard-library logging records through Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _setup_logging() -> None:
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
        format=log_format,
    )

    # Intercept uvicorn / fastapi standard-library loggers
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for _name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        _log = logging.getLogger(_name)
        _log.handlers = [_InterceptHandler()]
        _log.propagate = False


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ExplainAI Video Engine starting up ...")
    await connect_db()
    yield
    await disconnect_db()
    logger.info("ExplainAI Video Engine shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    _setup_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Orchestrates multiple AI agents to convert research papers "
            "into explainable videos."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    _V1 = "/api/v1"
    app.include_router(upload_router,          prefix=f"{_V1}/upload")
    app.include_router(script_router,          prefix=f"{_V1}/scripts")
    app.include_router(export_router,          prefix=f"{_V1}/render")
    app.include_router(project_router,         prefix=f"{_V1}/projects")
    app.include_router(render_pipeline_router, prefix=f"{_V1}/render")

    return app


app = create_app()


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"])
async def root():
    """API root — links to interactive docs."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe."""
    return {"status": "ok", "version": settings.app_version}
