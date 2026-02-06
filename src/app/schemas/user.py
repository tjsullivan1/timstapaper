"""
User schemas for request/response validation.

These Pydantic models define the structure for user data
throughout the application.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserSession(BaseModel):
    """
    User data stored in session after authentication.

    This is the primary user type used throughout the app
    for authenticated user context.
    """

    id: int
    email: str
    name: str | None = None


class UserResponse(BaseModel):
    """User data returned in API responses."""

    id: int
    email: EmailStr
    name: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Data required to create a new user (from OAuth)."""

    email: EmailStr
    name: str | None = None
