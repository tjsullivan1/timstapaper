"""
Timstapaper - An Instapaper Clone
Main FastAPI application with Google OAuth authentication
"""

import logging
import os
from contextlib import asynccontextmanager

from authlib.integrations.starlette_client import OAuth
from core.config import get_settings
from core.database import init_db
from core.security import get_current_user, require_login
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services import article_service, user_service

# from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    settings = get_settings()
    # Startup: Initialize database
    db_dir = os.path.dirname(settings.database_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown: Cleanup (if needed)
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        # TODO: this description should become a setting too.
        description="An Instapaper Clone",
        lifespan=lifespan,
        root_path=settings.root_path,
    )

    # Add proxy headers middleware (must be first to set scheme correctly)
    application.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

    # Add session middleware
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
    )

    return application


app = create_app()

# Configure templates
templates = Jinja2Templates(directory="templates")


# This function adds 'session' to every template automatically
def global_context(request: Request):
    return {"session": request.session}


templates.context_processors.append(global_context)

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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page - redirect to dashboard if logged in"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = request.url_for("google_callback")
    return await google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """Google OAuth callback"""
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
        logger.error(f"OAuth error: {str(e)}")
        request.session["flash_message"] = "Authentication failed. Please try again."
        request.session["flash_category"] = "error"

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
async def logout(request: Request):
    """Logout user"""
    request.session.pop("user", None)
    request.session["flash_message"] = "You have been logged out."
    request.session["flash_category"] = "success"
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, filter: str = "all", user: dict = Depends(require_login)
):
    """Main dashboard showing saved articles"""
    # Get articles via service
    articles = article_service.list_articles(user["id"], filter)

    # Get flash messages
    flash_message = request.session.pop("flash_message", None)
    flash_category = request.session.pop("flash_category", None)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "articles": articles,
            "filter_type": filter,
            "session": {"user": user},
            "flash_message": flash_message,
            "flash_category": flash_category,
        },
    )


@app.get("/article/{article_id}", response_class=HTMLResponse)
async def view_article(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """View a single article"""
    article = article_service.get_article_by_id(article_id, user["id"])

    if not article:
        request.session["flash_message"] = "Article not found."
        request.session["flash_category"] = "error"
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "article.html",
        {"request": request, "article": article, "session": {"user": user}},
    )


@app.post("/article/save")
async def save_article(
    request: Request, url: str = Form(...), user: dict = Depends(require_login)
):
    """Save a new article"""
    url = url.strip()

    if not url:
        request.session["flash_message"] = "URL is required."
        request.session["flash_category"] = "error"
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    # Extract content from URL using service
    article_data = article_service.extract_article_content(url)

    # Save to database using service
    article_service.create_article(
        user_id=user["id"],
        url=url,
        title=article_data.title,
        content=article_data.content,
        excerpt=article_data.excerpt,
        image_url=article_data.image_url,
    )

    request.session["flash_message"] = "Article saved successfully!"
    request.session["flash_category"] = "success"
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/article/{article_id}/toggle-favorite")
async def toggle_favorite(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """Toggle article favorite status"""
    article_service.toggle_favorite(article_id, user["id"])

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/article/{article_id}/toggle-archive")
async def toggle_archive(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """Toggle article archive status"""
    article_service.toggle_archive(article_id, user["id"])

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/article/{article_id}/delete")
async def delete_article(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """Delete an article"""
    article_service.delete_article(article_id, user["id"])

    request.session["flash_message"] = "Article deleted."
    request.session["flash_category"] = "success"

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(content={"status": "healthy"}, status_code=200)


@app.get("/debug/headers")
async def debug_headers(request: Request):
    """Debug endpoint to inspect incoming headers - REMOVE IN PRODUCTION"""
    headers = dict(request.headers)
    return JSONResponse(
        content={
            "headers": headers,
            "scheme": request.url.scheme,
            "url": str(request.url),
        },
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
