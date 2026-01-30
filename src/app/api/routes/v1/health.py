"""
API v1 health routes - Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is healthy and responding.",
)
async def health() -> dict:
    """
    Health check endpoint.

    Returns:
        Status indicating the API is healthy.
    """
    return {"status": "healthy"}
