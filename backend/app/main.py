"""FastAPI Application Entrypoint and Lifecycle Configuration.

Configures CORS, lifespan events (logging setup, SQLite schema initialization),
structured error handlers (strictly returning JSON detail), and registers API routes.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.config import settings
from app.db.database import init_db
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and graceful shutdown."""
    # 1. Initialize secure logging with sensitive token redaction
    setup_logging()

    # 2. Initialize database schema automatically on startup
    await init_db()

    logger.info(
        "Started %s v%s | Keys configured: %d | CORS allowed origins: %s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.keys_configured_count,
        settings.cors_origins,
    )
    yield
    logger.info("Shutting down %s.", settings.APP_NAME)


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Simulate-Failure"],
    )

    # --------------------------------------------------------------------------
    # Strict Error Handlers (Ensures detail JSON field, never HTML or tracebacks)
    # --------------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Catches 422 validation errors and returns strict JSON detail."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Fallback exception handler ensuring no raw tracebacks leak to clients."""
        logger.exception("Unhandled server exception: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    # Register API endpoints
    app.include_router(router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
