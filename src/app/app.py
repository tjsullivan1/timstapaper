"""
Timstapaper - An Instapaper Clone
Main FastAPI application with Google OAuth authentication
"""

import os
import sqlite3
from urllib.parse import urlparse
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from authlib.integrations.starlette_client import OAuth
from newspaper import Article
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE = os.environ.get("DATABASE_PATH", "/data/timstapaper.db")


def get_db():
    """Get database connection"""
    db_path = os.getenv("DATABASE_PATH", "/data/timstapaper.db")
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize database schema"""
    db = get_db()
    db.executescript("""
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
    """)
    db.commit()
    db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup: Initialize database
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown: Cleanup (if needed)
    logger.info("Application shutdown")


app = FastAPI(
    title="Timstapaper",
    description="An Instapaper Clone",
    lifespan=lifespan,
    root_path=os.environ.get("ROOT_PATH", "/"),
)

# Add proxy headers middleware (must be first to set scheme correctly)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production"),
)

# Configure templates
templates = Jinja2Templates(directory="templates")


# This function adds 'session' to every template automatically
def global_context(request: Request):
    return {"session": request.session}


templates.context_processors.append(global_context)

# Configure OAuth
oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session"""
    return request.session.get("user")


def require_login(request: Request):
    """Dependency to require login"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )
    return user


def extract_article_content(url):
    """
    Extract article content from URL using Newspaper4k library.

    This function intentionally makes HTTP requests to user-provided URLs.
    SSRF protection is implemented by:
    - Validating URL scheme (only http/https)
    - Blocking localhost and private IP ranges (RFC 1918)
    - Using Newspaper4k's built-in timeout and parsing

    Args:
        url (str): The URL to fetch and extract content from

    Returns:
        dict: Dictionary containing title, content, excerpt, and image_url
    """
    try:
        # Validate URL to prevent SSRF attacks
        parsed = urlparse(url)

        # Only allow http and https schemes
        if parsed.scheme not in ("http", "https"):
            logger.error(f"Invalid URL scheme: {parsed.scheme}")
            return {
                "title": parsed.netloc or "Invalid URL",
                "content": "",
                "excerpt": "Invalid URL scheme",
                "image_url": None,
            }

        # Prevent requests to localhost and private IP ranges (RFC 1918)
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            # Block localhost and private networks
            if (
                hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1")
                or hostname_lower.startswith("192.168.")
                or hostname_lower.startswith("10.")
                or hostname_lower.startswith("172.16.")
                or hostname_lower.startswith("172.17.")
                or hostname_lower.startswith("172.18.")
                or hostname_lower.startswith("172.19.")
                or hostname_lower.startswith("172.20.")
                or hostname_lower.startswith("172.21.")
                or hostname_lower.startswith("172.22.")
                or hostname_lower.startswith("172.23.")
                or hostname_lower.startswith("172.24.")
                or hostname_lower.startswith("172.25.")
                or hostname_lower.startswith("172.26.")
                or hostname_lower.startswith("172.27.")
                or hostname_lower.startswith("172.28.")
                or hostname_lower.startswith("172.29.")
                or hostname_lower.startswith("172.30.")
                or hostname_lower.startswith("172.31.")
            ):
                logger.error(f"Blocked request to private network: {hostname}")
                return {
                    "title": "Security Error",
                    "content": "",
                    "excerpt": "Cannot fetch content from private networks",
                    "image_url": None,
                }

        # SSRF risk acknowledged: This is the core functionality - fetching user-provided URLs
        # Protection: URL validation, private IP blocking, timeout enforcement via Newspaper4k
        article = Article(url)
        article.download()
        article.parse()

        # Extract title
        title = article.title if article.title else parsed.netloc

        # Extract image (top_image is automatically selected by Newspaper4k)
        image_url = article.top_image if article.top_image else None

        # Extract content
        content = article.text if article.text else ""

        # Create excerpt (first 200 characters)
        excerpt = content[:200] + "..." if len(content) > 200 else content

        return {
            "title": title,
            "content": content,
            "excerpt": excerpt,
            "image_url": image_url,
        }
    except Exception as e:
        logger.error(f"Error extracting content from URL: {str(e)}")
        return {
            "title": urlparse(url).netloc,
            "content": "",
            "excerpt": "Failed to extract content",
            "image_url": None,
        }


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
            # Store or update user in database
            db = get_db()
            cursor = db.cursor()

            cursor.execute(
                "SELECT id, email, name FROM users WHERE email = ?",
                (user_info["email"],),
            )
            user = cursor.fetchone()

            if user:
                user_id = user["id"]
            else:
                cursor.execute(
                    "INSERT INTO users (email, name) VALUES (?, ?)",
                    (user_info["email"], user_info.get("name", "")),
                )
                db.commit()
                user_id = cursor.lastrowid

            db.close()

            # Store user in session
            request.session["user"] = {
                "id": user_id,
                "email": user_info["email"],
                "name": user_info.get("name", ""),
            }

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
    db = get_db()
    cursor = db.cursor()

    # Get filter from query params
    filter_type = filter

    if filter_type == "favorites":
        cursor.execute(
            """
            SELECT * FROM articles 
            WHERE user_id = ? AND is_archived = 0 AND is_favorite = 1
            ORDER BY created_at DESC
        """,
            (user["id"],),
        )
    elif filter_type == "archived":
        cursor.execute(
            """
            SELECT * FROM articles 
            WHERE user_id = ? AND is_archived = 1
            ORDER BY created_at DESC
        """,
            (user["id"],),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM articles 
            WHERE user_id = ? AND is_archived = 0
            ORDER BY created_at DESC
        """,
            (user["id"],),
        )

    articles = cursor.fetchall()
    db.close()

    # Get flash messages
    flash_message = request.session.pop("flash_message", None)
    flash_category = request.session.pop("flash_category", None)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "articles": articles,
            "filter_type": filter_type,
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
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT * FROM articles 
        WHERE id = ? AND user_id = ?
    """,
        (article_id, user["id"]),
    )

    article = cursor.fetchone()
    db.close()

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

    # Extract content from URL
    article_data = extract_article_content(url)

    # Save to database
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO articles (user_id, url, title, content, excerpt, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            user["id"],
            url,
            article_data["title"],
            article_data["content"],
            article_data["excerpt"],
            article_data["image_url"],
        ),
    )

    db.commit()
    db.close()

    request.session["flash_message"] = "Article saved successfully!"
    request.session["flash_category"] = "success"
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/article/{article_id}/toggle-favorite")
async def toggle_favorite(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """Toggle article favorite status"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE articles 
        SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND user_id = ?
    """,
        (article_id, user["id"]),
    )

    db.commit()
    db.close()

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/article/{article_id}/toggle-archive")
async def toggle_archive(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """Toggle article archive status"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE articles 
        SET is_archived = CASE WHEN is_archived = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND user_id = ?
    """,
        (article_id, user["id"]),
    )

    db.commit()
    db.close()

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/article/{article_id}/delete")
async def delete_article(
    request: Request, article_id: int, user: dict = Depends(require_login)
):
    """Delete an article"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM articles 
        WHERE id = ? AND user_id = ?
    """,
        (article_id, user["id"]),
    )

    db.commit()
    db.close()

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

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
