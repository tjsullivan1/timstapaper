"""
Pytest configuration and fixtures for Timstapaper tests.

IMPORTANT: newspaper4k requires system libraries (libxml2-dev, libxslt-dev).
If tests segfault, either:
1. Install: sudo apt-get install libxml2-dev libxslt-dev libmagic1
2. Or the mock below will prevent loading the real library
"""

import os
import sys
import tempfile
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

# Set DATABASE_PATH to a temp directory BEFORE app module is imported
# The app module reads this at import time for the DATABASE constant
_test_data_dir = tempfile.mkdtemp(prefix="timstapaper_test_")
os.environ["DATABASE_PATH"] = os.path.join(_test_data_dir, "test.db")

import pytest
from fastapi.testclient import TestClient

# Change to app directory so templates can be found
_original_cwd = os.getcwd()
os.chdir(APP_DIR)


@pytest.fixture(scope="session", autouse=True)
def restore_cwd():
    """Restore original working directory after tests."""
    yield
    os.chdir(_original_cwd)


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Set the environment variable
    os.environ["DATABASE_PATH"] = db_path

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db(temp_db):
    """Initialize database with schema and return connection."""
    from app import get_db, init_db

    init_db()
    db = get_db()
    yield db
    db.close()


@pytest.fixture
def client(temp_db):
    """Create a test client with initialized database."""
    from app import app, init_db

    init_db()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(test_db):
    """Create a test user and return user data."""
    cursor = test_db.cursor()
    cursor.execute(
        "INSERT INTO users (email, name) VALUES (?, ?)",
        ("test@example.com", "Test User"),
    )
    test_db.commit()
    user_id = cursor.lastrowid

    return {
        "id": user_id,
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def authenticated_client(temp_db, test_user):
    """Create a test client with an authenticated session."""
    from app import app, init_db

    init_db()

    with TestClient(app) as test_client:
        # Manually set up session with user
        with test_client.session_transaction() as session:
            session["user"] = test_user
        yield test_client


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
def sample_article(test_db, test_user):
    """Create a sample article in the database."""
    cursor = test_db.cursor()
    cursor.execute(
        """
        INSERT INTO articles (user_id, url, title, content, excerpt, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            test_user["id"],
            "https://example.com/article",
            "Sample Article",
            "This is the content of the sample article.",
            "This is the content...",
            "https://example.com/image.jpg",
        ),
    )
    test_db.commit()
    article_id = cursor.lastrowid

    return {
        "id": article_id,
        "user_id": test_user["id"],
        "url": "https://example.com/article",
        "title": "Sample Article",
        "content": "This is the content of the sample article.",
        "excerpt": "This is the content...",
        "image_url": "https://example.com/image.jpg",
        "is_archived": 0,
        "is_favorite": 0,
    }
