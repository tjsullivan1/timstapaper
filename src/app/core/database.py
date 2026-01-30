"""
Database connection and initialization.

Provides database connection management and schema initialization.
Currently uses SQLite, with planned migration to PostgreSQL.
"""

import logging
import os
import sqlite3

from core.config import get_settings

logger = logging.getLogger(__name__)


def get_db() -> sqlite3.Connection:
    """
    Get a database connection.

    Returns:
        sqlite3.Connection: Database connection with Row factory configured.
    """
    settings = get_settings()
    db_path = settings.database_path

    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    """
    Initialize database schema.

    Creates all required tables and indexes if they don't exist.
    Safe to call multiple times.
    """
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            excerpt TEXT,
            image_url TEXT,
            is_archived INTEGER DEFAULT 0,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_articles_user_id ON articles(user_id);
        CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
    """
    )
    db.commit()
    db.close()
    logger.info("Database schema initialized")
