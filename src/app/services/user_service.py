"""
User service - business logic for user operations.

Handles user lookup and creation from OAuth data.
"""

import logging

from sqlmodel import Session, select

from core.models import User
from schemas.user import UserSession

logger = logging.getLogger(__name__)


def get_user_by_email(session: Session, email: str) -> User | None:
    """
    Get a user by email address.

    Args:
        session: Database session.
        email: User's email address.

    Returns:
        User if found, None otherwise.
    """
    return session.exec(select(User).where(User.email == email)).first()


def create_user(session: Session, email: str, name: str | None = None) -> User:
    """
    Create a new user.

    Args:
        session: Database session.
        email: User's email address.
        name: User's display name.

    Returns:
        The newly created User.
    """
    user = User(email=email, name=name)
    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"Created new user: {email}")
    return user


def get_or_create_user(session: Session, email: str, name: str | None = None) -> UserSession:
    """
    Get an existing user or create a new one.

    This is the main entry point for OAuth callback handling.

    Args:
        session: Database session.
        email: User's email address.
        name: User's display name (used if creating new user).

    Returns:
        UserSession for the user.
    """
    user = get_user_by_email(session, email)

    if not user:
        user = create_user(session, email, name)

    return UserSession(
        id=user.id,
        email=user.email,
        name=user.name,
    )
