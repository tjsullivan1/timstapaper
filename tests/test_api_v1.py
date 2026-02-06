"""
Tests for API v1 endpoints.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestAPIv1Health:
    """Test suite for API v1 health endpoint."""

    def test_health_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Should return healthy status in JSON."""
        response = client.get("/api/v1/health")

        assert response.json() == {"status": "healthy"}


class TestAPIv1ArticlesAuth:
    """Test authentication requirements for API v1 articles."""

    def test_list_articles_requires_auth(self, client):
        """Should return 401 when not authenticated."""
        response = client.get("/api/v1/articles")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_create_article_requires_auth(self, client):
        """Should return 401 when not authenticated."""
        response = client.post(
            "/api/v1/articles",
            json={"url": "https://example.com/article"},
        )

        assert response.status_code == 401

    def test_get_article_requires_auth(self, client):
        """Should return 401 when not authenticated."""
        response = client.get("/api/v1/articles/1")

        assert response.status_code == 401

    def test_update_article_requires_auth(self, client):
        """Should return 401 when not authenticated."""
        response = client.patch(
            "/api/v1/articles/1",
            json={"is_favorite": True},
        )

        assert response.status_code == 401

    def test_delete_article_requires_auth(self, client):
        """Should return 401 when not authenticated."""
        response = client.delete("/api/v1/articles/1")

        assert response.status_code == 401


class TestAPIv1ArticlesList:
    """Test suite for listing articles via API."""

    def test_list_articles_returns_empty_list(self, session, test_user):
        """Should return empty list when no articles."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from schemas.user import UserSession

        from app import app

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/articles")

                assert response.status_code == 200
                data = response.json()
                assert data["articles"] == []
                assert data["count"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_list_articles_returns_user_articles(self, session, test_user):
        """Should return articles for authenticated user."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from core.models import Article
        from schemas.user import UserSession

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test Article",
            content="Content",
            excerpt="Excerpt",
        )
        session.add(article)
        session.commit()

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/articles")

                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 1
                assert data["articles"][0]["title"] == "Test Article"
        finally:
            app.dependency_overrides.clear()

    def test_list_articles_filters_by_favorites(self, session, test_user):
        """Should filter articles by favorites."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from core.models import Article
        from schemas.user import UserSession

        from app import app

        # Create one favorite and one non-favorite
        article1 = Article(
            user_id=test_user["id"],
            url="https://example.com/1",
            title="Favorite",
            is_favorite=True,
        )
        article2 = Article(
            user_id=test_user["id"],
            url="https://example.com/2",
            title="Not Favorite",
            is_favorite=False,
        )
        session.add(article1)
        session.add(article2)
        session.commit()

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/articles?filter=favorites")

                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 1
                assert data["articles"][0]["title"] == "Favorite"
        finally:
            app.dependency_overrides.clear()


class TestAPIv1ArticlesCreate:
    """Test suite for creating articles via API."""

    def test_create_article_success(self, session, test_user):
        """Should create article and return it."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from schemas.article import ArticleExtracted
        from schemas.user import UserSession

        from app import app

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                with patch("services.article_service.extract_article_content") as mock:
                    mock.return_value = ArticleExtracted(
                        title="Created Article",
                        content="Article content",
                        excerpt="Article...",
                        image_url="https://example.com/img.jpg",
                    )

                    response = client.post(
                        "/api/v1/articles",
                        json={"url": "https://example.com/article"},
                    )

                    assert response.status_code == 201
                    data = response.json()
                    assert data["title"] == "Created Article"
                    assert data["url"] == "https://example.com/article"
        finally:
            app.dependency_overrides.clear()

    def test_create_article_invalid_url(self, session, test_user):
        """Should return 422 for invalid URL."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from schemas.user import UserSession

        from app import app

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/articles",
                    json={"url": "not-a-valid-url"},
                )

                assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestAPIv1ArticlesGet:
    """Test suite for getting a single article via API."""

    def test_get_article_success(self, session, test_user):
        """Should return article by ID."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from core.models import Article
        from schemas.user import UserSession

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test Article",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/articles/{article_id}")

                assert response.status_code == 200
                assert response.json()["title"] == "Test Article"
        finally:
            app.dependency_overrides.clear()

    def test_get_article_not_found(self, session, test_user):
        """Should return 404 for non-existent article."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from schemas.user import UserSession

        from app import app

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/articles/9999")

                assert response.status_code == 404
                assert response.json()["detail"] == "Article not found"
        finally:
            app.dependency_overrides.clear()


class TestAPIv1ArticlesUpdate:
    """Test suite for updating articles via API."""

    def test_update_article_favorite(self, session, test_user):
        """Should update article favorite status."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from core.models import Article
        from schemas.user import UserSession

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
            is_favorite=False,
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.patch(
                    f"/api/v1/articles/{article_id}",
                    json={"is_favorite": True},
                )

                assert response.status_code == 200
                assert response.json()["is_favorite"] is True
        finally:
            app.dependency_overrides.clear()

    def test_update_article_archive(self, session, test_user):
        """Should update article archive status."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from core.models import Article
        from schemas.user import UserSession

        from app import app

        # Create article
        article = Article(
            user_id=test_user["id"],
            url="https://example.com",
            title="Test",
            is_archived=False,
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        article_id = article.id

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.patch(
                    f"/api/v1/articles/{article_id}",
                    json={"is_archived": True},
                )

                assert response.status_code == 200
                assert response.json()["is_archived"] is True
        finally:
            app.dependency_overrides.clear()

    def test_update_article_not_found(self, session, test_user):
        """Should return 404 for non-existent article."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from schemas.user import UserSession

        from app import app

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.patch(
                    "/api/v1/articles/9999",
                    json={"is_favorite": True},
                )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestAPIv1ArticlesDelete:
    """Test suite for deleting articles via API."""

    def test_delete_article_success(self, session, test_user):
        """Should delete article and return 204."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from core.models import Article
        from schemas.user import UserSession
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

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/articles/{article_id}")

                assert response.status_code == 204

                # Verify article is deleted
                result = session.exec(
                    select(Article).where(Article.id == article_id)
                ).first()
                assert result is None
        finally:
            app.dependency_overrides.clear()

    def test_delete_article_not_found(self, session, test_user):
        """Should return 404 for non-existent article."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_session
        from schemas.user import UserSession

        from app import app

        test_user_session = UserSession(
            id=test_user["id"],
            email=test_user["email"],
            name=test_user["name"],
        )

        def override_get_session():
            yield session

        def override_auth():
            return test_user_session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.delete("/api/v1/articles/9999")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
