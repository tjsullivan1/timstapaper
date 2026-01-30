"""
User service - business logic for user operations.

Handles user lookup and creation from OAuth data.
"""

import logging

from core.database import get_db
from schemas.user import UserSession

logger = logging.getLogger(__name__)


def get_user_by_email(email: str):
    """
    Get a user by email address.

    Args:
        email: User's email address.

    Returns:
        User row if found, None otherwise.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, email, name FROM users WHERE email = ?",
        (email,),
    )

    user = cursor.fetchone()
    db.close()

    return user


def create_user(email: str, name: str | None = None) -> int:
    """
    Create a new user.

    Args:
        email: User's email address.
        name: User's display name.

    Returns:
        ID of the newly created user.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO users (email, name) VALUES (?, ?)",
        (email, name or ""),
    )

    db.commit()
    user_id = cursor.lastrowid
    db.close()

    logger.info(f"Created new user: {email}")
    return user_id


def get_or_create_user(email: str, name: str | None = None) -> UserSession:
    """
    Get an existing user or create a new one.

    This is the main entry point for OAuth callback handling.

    Args:
        email: User's email address.
        name: User's display name (used if creating new user).

    Returns:
        UserSession for the user.
    """
    user = get_user_by_email(email)

    if user:
        user_id = user["id"]
        user_name = user["name"]
    else:
        user_id = create_user(email, name)
        user_name = name or ""

    return UserSession(
        id=user_id,
        email=email,
        name=user_name,
    )
