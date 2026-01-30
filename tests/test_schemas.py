"""
Tests for Pydantic schemas.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError


class TestUserSchemas:
    """Test suite for user schemas."""

    def test_user_session_valid(self):
        """Should create UserSession with valid data."""
        from schemas.user import UserSession

        user = UserSession(id=1, email="test@example.com", name="Test User")

        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    def test_user_session_from_dict(self):
        """Should create UserSession from dict using model_validate."""
        from schemas.user import UserSession

        data = {"id": 1, "email": "test@example.com", "name": "Test User"}
        user = UserSession.model_validate(data)

        assert user.id == 1
        assert user.email == "test@example.com"

    def test_user_session_missing_required_field(self):
        """Should raise ValidationError for missing required fields."""
        from schemas.user import UserSession

        with pytest.raises(ValidationError):
            UserSession(id=1, email="test@example.com")  # missing name

    def test_user_response_from_attributes(self):
        """Should support from_attributes for ORM-like objects."""
        from schemas.user import UserResponse

        class MockUser:
            id = 1
            email = "test@example.com"
            name = "Test"
            created_at = datetime.now()

        user = UserResponse.model_validate(MockUser())
        assert user.id == 1
        assert user.email == "test@example.com"

    def test_user_create_validates_email(self):
        """Should validate email format."""
        from schemas.user import UserCreate

        # Valid email
        user = UserCreate(email="valid@example.com", name="Test")
        assert user.email == "valid@example.com"

        # Invalid email
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", name="Test")


class TestArticleSchemas:
    """Test suite for article schemas."""

    def test_article_create_valid_url(self):
        """Should accept valid HTTP URLs."""
        from schemas.article import ArticleCreate

        article = ArticleCreate(url="https://example.com/article")
        assert str(article.url) == "https://example.com/article"

    def test_article_create_invalid_url(self):
        """Should reject invalid URLs."""
        from schemas.article import ArticleCreate

        with pytest.raises(ValidationError):
            ArticleCreate(url="not-a-url")

    def test_article_extracted_all_fields(self):
        """Should create ArticleExtracted with all fields."""
        from schemas.article import ArticleExtracted

        extracted = ArticleExtracted(
            title="Test Title",
            content="Test content",
            excerpt="Test...",
            image_url="https://example.com/image.jpg",
        )

        assert extracted.title == "Test Title"
        assert extracted.image_url == "https://example.com/image.jpg"

    def test_article_extracted_optional_image(self):
        """Should allow None for image_url."""
        from schemas.article import ArticleExtracted

        extracted = ArticleExtracted(
            title="Test",
            content="Content",
            excerpt="Excerpt",
            image_url=None,
        )

        assert extracted.image_url is None

    def test_article_response_boolean_conversion(self):
        """Should handle is_archived and is_favorite as booleans."""
        from schemas.article import ArticleResponse

        # SQLite stores booleans as 0/1
        article = ArticleResponse(
            id=1,
            user_id=1,
            url="https://example.com",
            is_archived=True,
            is_favorite=False,
        )

        assert article.is_archived is True
        assert article.is_favorite is False

    def test_article_list_response(self):
        """Should create list response with count."""
        from schemas.article import ArticleListResponse, ArticleResponse

        articles = [
            ArticleResponse(id=1, user_id=1, url="https://example.com/1"),
            ArticleResponse(id=2, user_id=1, url="https://example.com/2"),
        ]

        response = ArticleListResponse(articles=articles, count=2)

        assert len(response.articles) == 2
        assert response.count == 2

    def test_article_update_partial(self):
        """Should allow partial updates."""
        from schemas.article import ArticleUpdate

        # Only update favorite
        update = ArticleUpdate(is_favorite=True)
        assert update.is_favorite is True
        assert update.is_archived is None

        # Only update archived
        update = ArticleUpdate(is_archived=True)
        assert update.is_archived is True
        assert update.is_favorite is None
