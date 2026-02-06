"""
Template routes - HTML pages for browser users.

These routes render Jinja2 templates and handle form submissions.
"""

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from core.database import get_session
from core.security import get_current_user, require_login
from services import article_service

router = APIRouter(tags=["pages"])

# Configure templates
templates = Jinja2Templates(directory="templates")


def global_context(request: Request):
    """Add session to every template context."""
    return {"session": request.session}


templates.context_processors.append(global_context)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page - redirect to dashboard if logged in."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    filter: str = "all",
    user: dict = Depends(require_login),
    session: Session = Depends(get_session),
):
    """Main dashboard showing saved articles."""
    articles = article_service.list_articles(session, user["id"], filter)

    # Get flash messages
    flash_message = request.session.pop("flash_message", None)
    flash_category = request.session.pop("flash_category", None)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "articles": articles,
            "filter_type": filter,
            "session": {"user": user},
            "flash_message": flash_message,
            "flash_category": flash_category,
        },
    )


@router.get("/article/{article_id}", response_class=HTMLResponse)
def view_article(
    request: Request,
    article_id: int,
    user: dict = Depends(require_login),
    session: Session = Depends(get_session),
):
    """View a single article."""
    article = article_service.get_article_by_id(session, article_id, user["id"])

    if not article:
        request.session["flash_message"] = "Article not found."
        request.session["flash_category"] = "error"
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "article.html",
        {"article": article, "session": {"user": user}},
    )


@router.post("/article/save")
def save_article(
    request: Request,
    url: str = Form(...),
    user: dict = Depends(require_login),
    session: Session = Depends(get_session),
):
    """Save a new article from URL."""
    url = url.strip()

    if not url:
        request.session["flash_message"] = "URL is required."
        request.session["flash_category"] = "error"
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    # Extract content from URL using service
    article_data = article_service.extract_article_content(url)

    # Save to database using service
    article_service.create_article(
        session,
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


@router.post("/article/{article_id}/toggle-favorite")
def toggle_favorite(
    request: Request,
    article_id: int,
    user: dict = Depends(require_login),
    session: Session = Depends(get_session),
):
    """Toggle article favorite status."""
    article_service.toggle_favorite(session, article_id, user["id"])

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/article/{article_id}/toggle-archive")
def toggle_archive(
    request: Request,
    article_id: int,
    user: dict = Depends(require_login),
    session: Session = Depends(get_session),
):
    """Toggle article archive status."""
    article_service.toggle_archive(session, article_id, user["id"])

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/article/{article_id}/delete")
def delete_article(
    request: Request,
    article_id: int,
    user: dict = Depends(require_login),
    session: Session = Depends(get_session),
):
    """Delete an article."""
    article_service.delete_article(session, article_id, user["id"])

    request.session["flash_message"] = "Article deleted."
    request.session["flash_category"] = "success"

    if request.headers.get("HX-Request"):
        return HTMLResponse(content="", status_code=200)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
