"""RiskLens FastAPI application entry point."""

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import auth, dashboard, entities, risks, search, timeline, watchlist, websocket
from app.core.config import settings
from app.db.session import close_redis, engine, get_redis
from app.db.models import Base

logger = structlog.get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="RiskLens — Risk Intelligence Platform",
    description=(
        "AI-powered global business risk intelligence. "
        "Monitors news, SEC filings, market data, and social signals "
        "to surface risk before it becomes a crisis."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup() -> None:
    """Initialise database tables and Redis on startup."""
    logger.info("RiskLens starting up", environment=settings.environment)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Warm up Redis connection
    await get_redis()
    logger.info("RiskLens startup complete")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up connections on shutdown."""
    await close_redis()
    await engine.dispose()
    logger.info("RiskLens shutdown complete")


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a clean error response — never expose raw stack traces."""
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(entities.router, prefix=API_PREFIX)
app.include_router(risks.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(timeline.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(watchlist.router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "healthy", "service": "RiskLens", "version": "1.0.0"}

