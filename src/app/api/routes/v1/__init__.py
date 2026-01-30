"""
API v1 routes - JSON API for programmatic access.

Provides versioned REST endpoints for articles and health checks.
"""

from fastapi import APIRouter

from api.routes.v1 import articles, health

router = APIRouter(prefix="/api/v1")
router.include_router(articles.router)
router.include_router(health.router)

__all__ = ["router"]
