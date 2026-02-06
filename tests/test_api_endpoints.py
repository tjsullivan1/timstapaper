"""
Tests for API endpoints.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    def test_health_returns_200(self, client):
        """Should return 200 OK at /api/v1/health."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Should return healthy status in JSON."""
        response = client.get("/api/v1/health")

        assert response.json() == {"status": "healthy"}

    def test_health_also_available_at_root(self, client):
        """Should also be available at /health for convenience."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestLoginPage:
    """Test suite for login page."""

    def test_login_page_returns_200(self, client):
        """Should return login page for unauthenticated users."""
        response = client.get("/login")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_login_page_contains_google_auth(self, client):
        """Should contain Google OAuth link."""
        response = client.get("/login")

        assert "Google" in response.text or "google" in response.text.lower()


class TestIndexRedirect:
    """Test suite for index page redirects."""

    def test_index_redirects_to_login_when_not_authenticated(self, client):
        """Should redirect unauthenticated users to login."""
        # Follow redirects to final destination
        response = client.get("/", follow_redirects=True)

        # Should end up at login page
        assert response.status_code == 200
        assert "Login" in response.text or "login" in response.text.lower()


class TestDashboard:
    """Test suite for dashboard endpoint."""

    def test_dashboard_redirects_when_not_authenticated(self, client):
        """Should redirect to login when not authenticated."""
        response = client.get("/dashboard", follow_redirects=False)

        assert response.status_code == 303

    def test_dashboard_returns_200_when_authenticated(self, session, test_user):
        """Should return dashboard when authenticated."""
        from core.database import get_session
        from core.security import require_login

        from app import app

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                response = client.get("/dashboard")

                assert response.status_code == 200
                assert "text/html" in response.headers["content-type"]
        finally:
            app.dependency_overrides.clear()


class TestArticleOperations:
    """Test suite for article CRUD operations."""

    def test_save_article_requires_auth(self, client):
        """Should require authentication to save article."""
        response = client.post(
            "/article/save",
            data={"url": "https://example.com/article"},
            follow_redirects=False,
        )

        assert response.status_code == 303

    def test_save_article_creates_article(self, session, test_user):
        """Should save article when authenticated."""
        from core.database import get_session
        from core.models import Article
        from core.security import require_login
        from schemas.article import ArticleExtracted
        from sqlmodel import select

        from app import app

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                with patch(
                    "services.article_service.extract_article_content"
                ) as mock_extract:
                    mock_extract.return_value = ArticleExtracted(
                        title="Test Article",
                        content="Test content",
                        excerpt="Test...",
                        image_url="https://example.com/img.jpg",
                    )

                    response = client.post(
                        "/article/save",
                        data={"url": "https://example.com/article"},
                        follow_redirects=False,
                    )

                    assert response.status_code == 303

                    # Verify article was saved
                    article = session.exec(
                        select(Article).where(Article.user_id == test_user["id"])
                    ).first()

                    assert article is not None
                    assert article.title == "Test Article"
        finally:
            app.dependency_overrides.clear()

    def test_toggle_favorite_requires_auth(self, client):
        """Should require authentication to toggle favorite."""
        response = client.post("/article/1/toggle-favorite", follow_redirects=False)

        assert response.status_code == 303

    def test_toggle_favorite_updates_status(self, session, test_user):
        """Should toggle favorite status."""
        from core.database import get_session
        from core.models import Article
        from core.security import require_login

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/article/{article_id}/toggle-favorite", follow_redirects=False
                )

                assert response.status_code == 303

                # Verify status changed
                session.refresh(article)
                assert article.is_favorite is True
        finally:
            app.dependency_overrides.clear()

    def test_toggle_archive_updates_status(self, session, test_user):
        """Should toggle archive status."""
        from core.database import get_session
        from core.models import Article
        from core.security import require_login

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/article/{article_id}/toggle-archive", follow_redirects=False
                )

                assert response.status_code == 303

                # Verify status changed
                session.refresh(article)
                assert article.is_archived is True
        finally:
            app.dependency_overrides.clear()

    def test_delete_article_removes_from_db(self, session, test_user):
        """Should delete article from database."""
        from core.database import get_session
        from core.models import Article
        from core.security import require_login
        from sqlmodel import select

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/article/{article_id}/delete", follow_redirects=False
                )

                assert response.status_code == 303

                # Verify article was deleted
                result = session.exec(
                    select(Article).where(Article.id == article_id)
                ).first()
                assert result is None
        finally:
            app.dependency_overrides.clear()


class TestViewArticle:
    """Test suite for viewing individual articles."""

    def test_view_article_requires_auth(self, client):
        """Should require authentication to view article."""
        response = client.get("/article/1", follow_redirects=False)

        assert response.status_code == 303

    def test_view_article_returns_404_for_nonexistent(self, session, test_user):
        """Should redirect for non-existent article."""
        from core.database import get_session
        from core.security import require_login

        from app import app

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                response = client.get("/article/99999", follow_redirects=False)

                # Should redirect to dashboard with error
                assert response.status_code == 303
        finally:
            app.dependency_overrides.clear()

    def test_view_article_shows_content(self, session, test_user):
        """Should display article content."""
        from core.database import get_session
        from core.models import Article
        from core.security import require_login

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test Article Title",
            content="Article content",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        def override_get_session():
            yield session

        def override_require_login():
            return test_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_login] = override_require_login

        try:
            with TestClient(app) as client:
                response = client.get(f"/article/{article_id}")

                assert response.status_code == 200
                assert "Test Article Title" in response.text
        finally:
            app.dependency_overrides.clear()


class TestLogout:
    """Test suite for logout functionality."""

    def test_logout_redirects_to_login(self, client):
        """Should redirect to login page after logout."""
        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/login"
