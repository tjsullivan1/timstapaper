"""
Tests for database functions.
"""

import os
import sqlite3

import pytest


class TestDatabaseInitialization:
    """Test suite for database initialization."""

    def test_init_db_creates_users_table(self, test_db):
        """Should create users table with correct schema."""
        cursor = test_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["name"] == "users"

    def test_init_db_creates_articles_table(self, test_db):
        """Should create articles table with correct schema."""
        cursor = test_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["name"] == "articles"

    def test_users_table_has_correct_columns(self, test_db):
        """Should create users table with id, email, name, created_at columns."""
        cursor = test_db.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = {row["name"] for row in cursor.fetchall()}

        assert "id" in columns
        assert "email" in columns
        assert "name" in columns
        assert "created_at" in columns

    def test_articles_table_has_correct_columns(self, test_db):
        """Should create articles table with all required columns."""
        cursor = test_db.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row["name"] for row in cursor.fetchall()}

        expected_columns = {
            "id",
            "user_id",
            "url",
            "title",
            "content",
            "excerpt",
            "image_url",
            "is_archived",
            "is_favorite",
            "created_at",
        }
        assert expected_columns.issubset(columns)

    def test_creates_indexes(self, test_db):
        """Should create indexes on articles table."""
        cursor = test_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='articles'"
        )
        indexes = {row["name"] for row in cursor.fetchall()}

        assert "idx_articles_user_id" in indexes
        assert "idx_articles_created_at" in indexes


class TestDatabaseConnection:
    """Test suite for database connection function."""

    def test_get_db_returns_connection(self, temp_db):
        """Should return a database connection."""
        from core.database import get_db

        db = get_db()

        assert db is not None
        assert isinstance(db, sqlite3.Connection)
        db.close()

    def test_get_db_uses_row_factory(self, temp_db):
        """Should configure row factory for dict-like access."""
        from core.database import get_db, init_db

        init_db()
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("test@example.com", "Test"),
        )
        db.commit()

        cursor.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
        row = cursor.fetchone()

        # Row factory allows dict-like access
        assert row["email"] == "test@example.com"
        assert row["name"] == "Test"
        db.close()

    def test_get_db_creates_directory(self, tmp_path):
        """Should create database directory if it doesn't exist."""
        from core.config import get_settings
        from core.database import get_db

        db_path = str(tmp_path / "subdir" / "test.db")
        os.environ["DATABASE_PATH"] = db_path
        get_settings.cache_clear()

        db = get_db()
        db.close()

        assert os.path.exists(os.path.dirname(db_path))
        get_settings.cache_clear()


class TestDatabaseOperations:
    """Test suite for database CRUD operations."""

    def test_insert_user(self, test_db):
        """Should insert a new user."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("user@example.com", "New User"),
        )
        test_db.commit()

        cursor.execute("SELECT * FROM users WHERE email = ?", ("user@example.com",))
        user = cursor.fetchone()

        assert user is not None
        assert user["email"] == "user@example.com"
        assert user["name"] == "New User"

    def test_user_email_unique_constraint(self, test_db):
        """Should enforce unique email constraint."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            ("duplicate@example.com", "User 1"),
        )
        test_db.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO users (email, name) VALUES (?, ?)",
                ("duplicate@example.com", "User 2"),
            )

    def test_insert_article(self, test_db, test_user):
        """Should insert a new article."""
        cursor = test_db.cursor()
        cursor.execute(
            """
            INSERT INTO articles (user_id, url, title, content, excerpt, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                test_user["id"],
                "https://example.com/post",
                "Test Post",
                "Content here",
                "Content...",
                "https://example.com/img.jpg",
            ),
        )
        test_db.commit()

        cursor.execute("SELECT * FROM articles WHERE user_id = ?", (test_user["id"],))
        article = cursor.fetchone()

        assert article is not None
        assert article["url"] == "https://example.com/post"
        assert article["title"] == "Test Post"
        assert article["is_archived"] == 0
        assert article["is_favorite"] == 0

    def test_article_default_values(self, test_db, test_user):
        """Should set default values for is_archived and is_favorite."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO articles (user_id, url, title) VALUES (?, ?, ?)",
            (test_user["id"], "https://example.com", "Test"),
        )
        test_db.commit()

        cursor.execute("SELECT * FROM articles WHERE user_id = ?", (test_user["id"],))
        article = cursor.fetchone()

        assert article["is_archived"] == 0
        assert article["is_favorite"] == 0

    def test_toggle_favorite(self, test_db, test_user):
        """Should toggle article favorite status."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO articles (user_id, url, title) VALUES (?, ?, ?)",
            (test_user["id"], "https://example.com", "Test"),
        )
        test_db.commit()
        article_id = cursor.lastrowid

        # Toggle to favorite
        cursor.execute(
            """
            UPDATE articles 
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (article_id,),
        )
        test_db.commit()

        cursor.execute("SELECT is_favorite FROM articles WHERE id = ?", (article_id,))
        assert cursor.fetchone()["is_favorite"] == 1

        # Toggle back
        cursor.execute(
            """
            UPDATE articles 
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (article_id,),
        )
        test_db.commit()

        cursor.execute("SELECT is_favorite FROM articles WHERE id = ?", (article_id,))
        assert cursor.fetchone()["is_favorite"] == 0

    def test_delete_article(self, test_db, test_user):
        """Should delete an article."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO articles (user_id, url, title) VALUES (?, ?, ?)",
            (test_user["id"], "https://example.com", "Test"),
        )
        test_db.commit()
        article_id = cursor.lastrowid

        cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        test_db.commit()

        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        assert cursor.fetchone() is None
