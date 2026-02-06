"""
SQLModel database models.

Defines the database tables using SQLModel for PostgreSQL.
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class User(SQLModel, table=True):
    """User account from OAuth authentication."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Article(SQLModel, table=True):
    """Saved article with extracted content."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    url: str
    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    image_url: str | None = None
    is_archived: bool = False
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=utc_now, index=True)
