"""
Pytest configuration and fixtures for Timstapaper tests.

Uses PostgreSQL with transaction rollback for fast, isolated tests.

IMPORTANT: newspaper4k requires system libraries (libxml2-dev, libxslt-dev).
If tests segfault, either:
1. Install: sudo apt-get install libxml2-dev libxslt-dev libmagic1
2. Or the mock below will prevent loading the real library
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# =============================================================================
# CRITICAL: Mock newspaper BEFORE anything else imports it
# This must happen before pytest collects test files that import 'app'
# =============================================================================
mock_article_instance = MagicMock()
mock_article_instance.title = "Test Article Title"
mock_article_instance.text = "Test article content for testing purposes."
mock_article_instance.top_image = "https://example.com/image.jpg"
mock_article_instance.download = MagicMock()
mock_article_instance.parse = MagicMock()

mock_article_class = MagicMock(return_value=mock_article_instance)
mock_newspaper = MagicMock()
mock_newspaper.Article = mock_article_class

sys.modules["newspaper"] = mock_newspaper

# =============================================================================
# Now safe to set up paths and import other modules
# =============================================================================

# Add the app directory to Python path
APP_DIR = Path(__file__).parent.parent / "src" / "app"
sys.path.insert(0, str(APP_DIR))

# Set test environment variables before importing app
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"

# Use test database
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://timstapaper:timstapaper@localhost:5432/timstapaper_test",
)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

# Change to app directory so templates can be found
_original_cwd = os.getcwd()
os.chdir(APP_DIR)


@pytest.fixture(scope="session", autouse=True)
def restore_cwd():
    """Restore original working directory after tests."""
    yield
    os.chdir(_original_cwd)


@pytest.fixture(scope="session")
def test_engine():
    """Create tables once per test session."""
    from core.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url)

    # Import models to register them
    from core.models import Article, User  # noqa: F401

    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session(test_engine):
    """Each test gets a transaction that rolls back - fast and isolated."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session):
    """Test client with overridden database session."""
    from core.database import get_session

    from app import app

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(session):
    """Create a test user and return UserSession object."""
    from core.models import User
    from schemas.user import UserSession

    user = User(email="test@example.com", name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserSession(
        id=user.id,
        email=user.email,
        name=user.name,
    )


@pytest.fixture
def authenticated_client(session, test_user):
    """Create a test client with an authenticated session."""
    from core.database import get_session

    from app import app

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        # Set up session cookie with user data
        test_client.cookies.set("session", "")
        # Use dependency override for auth
        from core.security import require_login

        def override_require_login():
            return test_user

        app.dependency_overrides[require_login] = override_require_login

        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_article():
    """Mock newspaper Article for testing article extraction."""

    def _create_mock(
        title="Test Article Title",
        text="This is the test article content. " * 20,
        top_image="https://example.com/image.jpg",
    ):
        mock = MagicMock()
        mock.title = title
        mock.text = text
        mock.top_image = top_image
        mock.download = MagicMock()
        mock.parse = MagicMock()
        return mock

    return _create_mock


@pytest.fixture
def sample_article(session, test_user):
    """Create a sample article in the database."""
    from core.models import Article

    article = Article(
        user_id=test_user.id,
        url="https://example.com/article",
        title="Sample Article",
        content="This is the content of the sample article.",
        excerpt="This is the content...",
        image_url="https://example.com/image.jpg",
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    return {
        "id": article.id,
        "user_id": article.user_id,
        "url": article.url,
        "title": article.title,
        "content": article.content,
        "excerpt": article.excerpt,
        "image_url": article.image_url,
        "is_archived": article.is_archived,
        "is_favorite": article.is_favorite,
    }
