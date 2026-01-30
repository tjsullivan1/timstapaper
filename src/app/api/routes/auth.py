"""
Authentication routes - Google OAuth login/logout.
"""

import logging

from authlib.integrations.starlette_client import OAuth
from core.config import get_settings
from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse
from services import user_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Configure OAuth
oauth = OAuth()
_settings = get_settings()
google = oauth.register(
    name="google",
    client_id=_settings.google_client_id,
    client_secret=_settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth login."""
    redirect_uri = request.url_for("google_callback")
    return await google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request):
    """Google OAuth callback - creates or retrieves user and starts session."""
    try:
        token = await google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if user_info:
            # Get or create user via service
            user_session = user_service.get_or_create_user(
                email=user_info["email"],
                name=user_info.get("name"),
            )

            # Store user in session
            request.session["user"] = user_session.model_dump()

            return RedirectResponse(
                url="/dashboard", status_code=status.HTTP_303_SEE_OTHER
            )
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        request.session["flash_message"] = "Authentication failed. Please try again."
        request.session["flash_category"] = "error"

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    request.session.pop("user", None)
    request.session["flash_message"] = "You have been logged out."
    request.session["flash_category"] = "success"
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
