"""
Database connection and initialization.

Provides database connection management using SQLModel with PostgreSQL.
"""

import logging

from sqlmodel import Session, SQLModel, create_engine

from core.config import get_settings

logger = logging.getLogger(__name__)

engine = None


def get_engine():
    """Get or create the database engine (singleton)."""
    global engine
    if engine is None:
        settings = get_settings()
        engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return engine


def init_db() -> None:
    """
    Initialize database schema.

    Creates all tables defined in SQLModel models.
    Safe to call multiple times - only creates tables that don't exist.
    """
    # Import models to register them with SQLModel.metadata
    from sqlalchemy import inspect

    from core.models import Article, User  # noqa: F401

    engine = get_engine()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    tables_to_create = [
        table
        for table in SQLModel.metadata.sorted_tables
        if table.name not in existing_tables
    ]

    if tables_to_create:
        SQLModel.metadata.create_all(engine, tables=tables_to_create)
        logger.info("Created tables: %s", [t.name for t in tables_to_create])
    else:
        logger.info("All tables already exist, skipping creation")


def get_session():
    """FastAPI dependency that provides a database session."""
    session = Session(get_engine())
    try:
        yield session
    finally:
        session.close()
