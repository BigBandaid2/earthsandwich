from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import structlog.stdlib
import structlog.dev
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.ingestion.scheduler import scheduler


# ── Logging ───────────────────────────────────────────────────────────────────

def _configure_logging() -> None:
    shared_processors: list = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.environment == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


_configure_logging()
log = structlog.get_logger(__name__)


# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("starting scheduler")
    scheduler.start()
    yield
    log.info("shutting down scheduler")
    scheduler.shutdown(wait=False)


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ClubSandwich API",
    lifespan=lifespan,
    # Do not expose internal details in generated error responses
    openapi_url="/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "Not Found", "detail": str(exc)})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred."},
    )
