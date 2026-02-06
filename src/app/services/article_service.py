"""
Article service - business logic for article operations.

Handles article extraction, CRUD operations, and filtering.
"""

import logging
from urllib.parse import urlparse

from newspaper import Article as NewspaperArticle
from sqlmodel import Session, select

from core.models import Article
from schemas.article import ArticleExtracted

logger = logging.getLogger(__name__)


def validate_url_for_ssrf(url: str) -> tuple[bool, str]:
    """
    Validate URL to prevent SSRF attacks.

    Args:
        url: The URL to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    parsed = urlparse(url)

    # Only allow http and https schemes
    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid URL scheme: {parsed.scheme}"

    # Prevent requests to localhost and private IP ranges (RFC 1918)
    hostname = parsed.hostname
    if hostname:
        hostname_lower = hostname.lower()
        # Block localhost and private networks
        if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            return False, f"Blocked request to localhost: {hostname}"

        if hostname_lower.startswith("192.168."):
            return False, f"Blocked request to private network: {hostname}"

        if hostname_lower.startswith("10."):
            return False, f"Blocked request to private network: {hostname}"

        # Check 172.16.0.0 - 172.31.255.255 range
        for i in range(16, 32):
            if hostname_lower.startswith(f"172.{i}."):
                return False, f"Blocked request to private network: {hostname}"

    return True, ""


def extract_article_content(url: str) -> ArticleExtracted:
    """
    Extract article content from URL using Newspaper4k library.

    This function intentionally makes HTTP requests to user-provided URLs.
    SSRF protection is implemented via validate_url_for_ssrf().

    Args:
        url: The URL to fetch and extract content from.

    Returns:
        ArticleExtracted with title, content, excerpt, and image_url.
    """
    parsed = urlparse(url)

    # Validate URL for SSRF
    is_valid, error_msg = validate_url_for_ssrf(url)
    if not is_valid:
        logger.error(error_msg)
        return ArticleExtracted(
            title=parsed.netloc or "Invalid URL",
            content="",
            excerpt=error_msg,
            image_url=None,
        )

    try:
        article = NewspaperArticle(url)
        article.download()
        article.parse()

        # Extract title
        title = article.title if article.title else parsed.netloc

        # Extract image
        image_url = article.top_image if article.top_image else None

        # Extract content
        content = article.text if article.text else ""

        # Create excerpt (first 200 characters)
        excerpt = content[:200] + "..." if len(content) > 200 else content

        return ArticleExtracted(
            title=title,
            content=content,
            excerpt=excerpt,
            image_url=image_url,
        )
    except Exception as e:
        logger.error(f"Error extracting content from URL: {e}")
        return ArticleExtracted(
            title=parsed.netloc,
            content="",
            excerpt="Failed to extract content",
            image_url=None,
        )


def create_article(
    session: Session,
    user_id: int,
    url: str,
    title: str,
    content: str,
    excerpt: str,
    image_url: str | None,
) -> Article:
    """
    Create a new article in the database.

    Args:
        session: Database session.
        user_id: ID of the user saving the article.
        url: Original URL of the article.
        title: Article title.
        content: Full article content.
        excerpt: Short excerpt/summary.
        image_url: URL of the article's main image.

    Returns:
        The newly created Article.
    """
    article = Article(
        user_id=user_id,
        url=url,
        title=title,
        content=content,
        excerpt=excerpt,
        image_url=image_url,
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    return article


def get_article_by_id(session: Session, article_id: int, user_id: int) -> Article | None:
    """
    Get an article by ID, ensuring it belongs to the user.

    Args:
        session: Database session.
        article_id: ID of the article.
        user_id: ID of the user (for ownership check).

    Returns:
        Article if found and owned by user, None otherwise.
    """
    return session.exec(
        select(Article).where(Article.id == article_id, Article.user_id == user_id)
    ).first()


def list_articles(session: Session, user_id: int, filter_type: str = "all") -> list[Article]:
    """
    List articles for a user with optional filtering.

    Args:
        session: Database session.
        user_id: ID of the user.
        filter_type: One of 'all', 'favorites', or 'archived'.

    Returns:
        List of Articles.
    """
    query = select(Article).where(Article.user_id == user_id)

    if filter_type == "favorites":
        query = query.where(Article.is_archived == False, Article.is_favorite == True)
    elif filter_type == "archived":
        query = query.where(Article.is_archived == True)
    else:
        query = query.where(Article.is_archived == False)

    query = query.order_by(Article.created_at.desc())

    return list(session.exec(query).all())


def toggle_favorite(session: Session, article_id: int, user_id: int) -> bool:
    """
    Toggle the favorite status of an article.

    Args:
        session: Database session.
        article_id: ID of the article.
        user_id: ID of the user (for ownership check).

    Returns:
        True if the operation succeeded.
    """
    article = get_article_by_id(session, article_id, user_id)
    if not article:
        return False

    article.is_favorite = not article.is_favorite
    session.add(article)
    session.commit()

    return True


def toggle_archive(session: Session, article_id: int, user_id: int) -> bool:
    """
    Toggle the archive status of an article.

    Args:
        session: Database session.
        article_id: ID of the article.
        user_id: ID of the user (for ownership check).

    Returns:
        True if the operation succeeded.
    """
    article = get_article_by_id(session, article_id, user_id)
    if not article:
        return False

    article.is_archived = not article.is_archived
    session.add(article)
    session.commit()

    return True


def delete_article(session: Session, article_id: int, user_id: int) -> bool:
    """
    Delete an article.

    Args:
        session: Database session.
        article_id: ID of the article.
        user_id: ID of the user (for ownership check).

    Returns:
        True if the article was deleted.
    """
    article = get_article_by_id(session, article_id, user_id)
    if not article:
        return False

    session.delete(article)
    session.commit()

    return True
