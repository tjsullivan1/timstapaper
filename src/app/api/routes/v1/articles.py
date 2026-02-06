"""
API v1 articles routes - JSON API for article operations.

Provides RESTful endpoints for article CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from api.routes.v1.deps import require_api_auth
from core.database import get_session
from schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from schemas.user import UserSession
from services import article_service

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get(
    "",
    response_model=ArticleListResponse,
    summary="List articles",
    description="Get all articles for the authenticated user with optional filtering.",
)
def list_articles(
    filter: str = "all",
    user: UserSession = Depends(require_api_auth),
    session: Session = Depends(get_session),
) -> ArticleListResponse:
    """
    List articles for the current user.

    Args:
        filter: Filter type - 'all', 'favorites', or 'archived'.
        user: Authenticated user from dependency.
        session: Database session.

    Returns:
        List of articles matching the filter.
    """
    articles = article_service.list_articles(session, user.id, filter)
    return ArticleListResponse(
        articles=[ArticleResponse.model_validate(a) for a in articles],
        count=len(articles),
    )


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create article",
    description="Save a new article by extracting content from the provided URL.",
)
def create_article(
    article_in: ArticleCreate,
    user: UserSession = Depends(require_api_auth),
    session: Session = Depends(get_session),
) -> ArticleResponse:
    """
    Create a new article from a URL.

    Extracts title, content, and image from the URL using newspaper4k.

    Args:
        article_in: URL to save.
        user: Authenticated user from dependency.
        session: Database session.

    Returns:
        The created article.
    """
    url = str(article_in.url)

    # Extract content from URL
    extracted = article_service.extract_article_content(url)

    # Save to database
    article = article_service.create_article(
        session,
        user_id=user.id,
        url=url,
        title=extracted.title,
        content=extracted.content,
        excerpt=extracted.excerpt,
        image_url=extracted.image_url,
    )

    return ArticleResponse.model_validate(article)


@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
    summary="Get article",
    description="Get a specific article by ID.",
)
def get_article(
    article_id: int,
    user: UserSession = Depends(require_api_auth),
    session: Session = Depends(get_session),
) -> ArticleResponse:
    """
    Get a specific article.

    Args:
        article_id: ID of the article.
        user: Authenticated user from dependency.
        session: Database session.

    Returns:
        The requested article.

    Raises:
        HTTPException: 404 if article not found or not owned by user.
    """
    article = article_service.get_article_by_id(session, article_id, user.id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return ArticleResponse.model_validate(article)


@router.patch(
    "/{article_id}",
    response_model=ArticleResponse,
    summary="Update article",
    description="Update article fields (favorite/archive status).",
)
def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    user: UserSession = Depends(require_api_auth),
    session: Session = Depends(get_session),
) -> ArticleResponse:
    """
    Update an article's favorite or archive status.

    Args:
        article_id: ID of the article.
        article_in: Fields to update.
        user: Authenticated user from dependency.
        session: Database session.

    Returns:
        The updated article.

    Raises:
        HTTPException: 404 if article not found or not owned by user.
    """
    # Check article exists
    article = article_service.get_article_by_id(session, article_id, user.id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # Apply updates - toggle if the desired state differs from current
    if article_in.is_favorite is not None:
        if article.is_favorite != article_in.is_favorite:
            article_service.toggle_favorite(session, article_id, user.id)

    if article_in.is_archived is not None:
        if article.is_archived != article_in.is_archived:
            article_service.toggle_archive(session, article_id, user.id)

    # Return updated article
    updated = article_service.get_article_by_id(session, article_id, user.id)
    return ArticleResponse.model_validate(updated)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete article",
    description="Delete an article permanently.",
)
def delete_article(
    article_id: int,
    user: UserSession = Depends(require_api_auth),
    session: Session = Depends(get_session),
) -> None:
    """
    Delete an article.

    Args:
        article_id: ID of the article.
        user: Authenticated user from dependency.
        session: Database session.

    Raises:
        HTTPException: 404 if article not found or not owned by user.
    """
    success = article_service.delete_article(session, article_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
