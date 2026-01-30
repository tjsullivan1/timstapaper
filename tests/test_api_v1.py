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

    def test_list_articles_returns_empty_list(self, temp_db):
        """Should return empty list when no articles."""
        from api.routes.v1.deps import require_api_auth
        from core.database import init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        test_user = UserSession(id=1, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_list_articles_returns_user_articles(self, temp_db):
        """Should return articles for authenticated user."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        # Create user and article
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO articles (user_id, url, title, content, excerpt) VALUES (?, ?, ?, ?, ?)",
            (user_id, "https://example.com", "Test Article", "Content", "Excerpt"),
        )
        db.commit()
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_list_articles_filters_by_favorites(self, temp_db):
        """Should filter articles by favorites."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid

        # Create one favorite and one non-favorite
        cursor.execute(
            "INSERT INTO articles (user_id, url, title, is_favorite) VALUES (?, ?, ?, ?)",
            (user_id, "https://example.com/1", "Favorite", 1),
        )
        cursor.execute(
            "INSERT INTO articles (user_id, url, title, is_favorite) VALUES (?, ?, ?, ?)",
            (user_id, "https://example.com/2", "Not Favorite", 0),
        )
        db.commit()
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_create_article_success(self, temp_db):
        """Should create article and return it."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.article import ArticleExtracted
        from schemas.user import UserSession

        from app import app

        init_db()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_create_article_invalid_url(self, temp_db):
        """Should return 422 for invalid URL."""
        from api.routes.v1.deps import require_api_auth
        from core.database import init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        test_user = UserSession(id=1, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_get_article_success(self, temp_db):
        """Should return article by ID."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO articles (user_id, url, title) VALUES (?, ?, ?)",
            (user_id, "https://example.com", "Test Article"),
        )
        db.commit()
        article_id = cursor.lastrowid
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/articles/{article_id}")

                assert response.status_code == 200
                assert response.json()["title"] == "Test Article"
        finally:
            app.dependency_overrides.clear()

    def test_get_article_not_found(self, temp_db):
        """Should return 404 for non-existent article."""
        from api.routes.v1.deps import require_api_auth
        from core.database import init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        test_user = UserSession(id=1, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_update_article_favorite(self, temp_db):
        """Should update article favorite status."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO articles (user_id, url, title, is_favorite) VALUES (?, ?, ?, ?)",
            (user_id, "https://example.com", "Test", 0),
        )
        db.commit()
        article_id = cursor.lastrowid
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_update_article_archive(self, temp_db):
        """Should update article archive status."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO articles (user_id, url, title, is_archived) VALUES (?, ?, ?, ?)",
            (user_id, "https://example.com", "Test", 0),
        )
        db.commit()
        article_id = cursor.lastrowid
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_update_article_not_found(self, temp_db):
        """Should return 404 for non-existent article."""
        from api.routes.v1.deps import require_api_auth
        from core.database import init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        test_user = UserSession(id=1, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

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

    def test_delete_article_success(self, temp_db):
        """Should delete article and return 204."""
        from api.routes.v1.deps import require_api_auth
        from core.database import get_db, init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test User"),
        )
        db.commit()
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO articles (user_id, url, title) VALUES (?, ?, ?)",
            (user_id, "https://example.com", "Test"),
        )
        db.commit()
        article_id = cursor.lastrowid
        db.close()

        test_user = UserSession(id=user_id, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/articles/{article_id}")

                assert response.status_code == 204

                # Verify article is deleted
                db = get_db()
                cursor = db.cursor()
                cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
                assert cursor.fetchone() is None
                db.close()
        finally:
            app.dependency_overrides.clear()

    def test_delete_article_not_found(self, temp_db):
        """Should return 404 for non-existent article."""
        from api.routes.v1.deps import require_api_auth
        from core.database import init_db
        from schemas.user import UserSession

        from app import app

        init_db()

        test_user = UserSession(id=1, email="test@example.com", name="Test User")

        def override_auth():
            return test_user

        app.dependency_overrides[require_api_auth] = override_auth

        try:
            with TestClient(app) as client:
                response = client.delete("/api/v1/articles/9999")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
