"""
Timstapaper - An Instapaper Clone
Main FastAPI application initialization and configuration.
"""

import logging
from contextlib import asynccontextmanager

from api.routes import auth, pages
from api.routes.v1 import router as api_v1_router
from api.routes.v1 import health as health_router
from core.config import get_settings
from core.database import init_db
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Initialize database
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown: Cleanup (if needed)
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        # TODO: this description should become a setting too.
        description="An Instapaper Clone",
        lifespan=lifespan,
        root_path=settings.root_path,
    )

    # Add proxy headers middleware (must be first to set scheme correctly)
    application.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

    # Add session middleware
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
    )

    # Register routers
    application.include_router(auth.router)
    application.include_router(pages.router)
    application.include_router(api_v1_router)
    application.include_router(health_router.router)  # Also mount at /health

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
