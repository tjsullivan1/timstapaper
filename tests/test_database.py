"""
Tests for database models and operations.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select


class TestDatabaseModels:
    """Test suite for SQLModel database models."""

    def test_user_model_fields(self, session):
        """Should create User with correct fields."""
        from core.models import User

        user = User(email="test@example.com", name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.created_at is not None

    def test_article_model_fields(self, session, test_user):
        """Should create Article with correct fields."""
        from core.models import Article

        article = Article(
            user_id=test_user["id"],
            url="https://example.com/post",
            title="Test Post",
            content="Content here",
            excerpt="Content...",
            image_url="https://example.com/img.jpg",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.id is not None
        assert article.user_id == test_user["id"]
        assert article.url == "https://example.com/post"
        assert article.title == "Test Post"
        assert article.is_archived is False
        assert article.is_favorite is False
        assert article.created_at is not None


class TestDatabaseConstraints:
    """Test suite for database constraints."""

    def test_user_email_unique_constraint(self, session):
        """Should enforce unique email constraint."""
        from core.models import User

        user1 = User(email="duplicate@example.com", name="User 1")
        session.add(user1)
        session.commit()

        user2 = User(email="duplicate@example.com", name="User 2")
        session.add(user2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_article_user_foreign_key(self, session):
        """Should enforce foreign key on user_id."""
        from core.models import Article

        article = Article(
            user_id=99999,  # Non-existent user
            url="https://example.com",
            title="Test",
        )
        session.add(article)

        with pytest.raises(IntegrityError):
            session.commit()


class TestDatabaseOperations:
    """Test suite for database CRUD operations."""

    def test_insert_user(self, session):
        """Should insert a new user."""
        from core.models import User

        user = User(email="newuser@example.com", name="New User")
        session.add(user)
        session.commit()

        result = session.exec(
            select(User).where(User.email == "newuser@example.com")
        ).first()

        assert result is not None
        assert result.email == "newuser@example.com"
        assert result.name == "New User"

    def test_insert_article(self, session, test_user):
        """Should insert a new article."""
        from core.models import Article

        article = Article(
            user_id=test_user["id"],
            url="https://example.com/post",
            title="Test Post",
            content="Content here",
            excerpt="Content...",
            image_url="https://example.com/img.jpg",
        )
        session.add(article)
        session.commit()

        result = session.exec(
            select(Article).where(Article.user_id == test_user["id"])
        ).first()

        assert result is not None
        assert result.url == "https://example.com/post"
        assert result.title == "Test Post"

    def test_article_default_values(self, session, test_user):
        """Should set default values for is_archived and is_favorite."""
        from core.models import Article

        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.is_archived is False
        assert article.is_favorite is False

    def test_toggle_favorite(self, session, test_user):
        """Should toggle article favorite status."""
        from core.models import Article

        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
        )
        session.add(article)
        session.commit()

        # Toggle to favorite
        article.is_favorite = not article.is_favorite
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.is_favorite is True

        # Toggle back
        article.is_favorite = not article.is_favorite
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.is_favorite is False

    def test_delete_article(self, session, test_user):
        """Should delete an article."""
        from core.models import Article

        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
        )
        session.add(article)
        session.commit()
        article_id = article.id

        session.delete(article)
        session.commit()

        result = session.exec(select(Article).where(Article.id == article_id)).first()
        assert result is None
