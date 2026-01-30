"""
Article schemas for request/response validation.

These Pydantic models define the structure for article data
used in API requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ArticleExtracted(BaseModel):
    """Data extracted from a URL by newspaper4k."""

    title: str
    content: str
    excerpt: str
    image_url: str | None = None


class ArticleCreate(BaseModel):
    """Data required to save a new article."""

    url: HttpUrl = Field(..., description="URL of the article to save")


class ArticleResponse(BaseModel):
    """Article data returned in API responses."""

    id: int
    user_id: int
    url: str
    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    image_url: str | None = None
    is_archived: bool = False
    is_favorite: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    """Response containing a list of articles."""

    articles: list[ArticleResponse]
    count: int


class ArticleUpdate(BaseModel):
    """Fields that can be updated on an article."""

    is_archived: bool | None = None
    is_favorite: bool | None = None
