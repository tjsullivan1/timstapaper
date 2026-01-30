---
description: FastAPI architecture and coding standards
applyTo: '**/*.py'
---

# FastAPI Architecture & Coding Standards

You are an expert Python Backend Engineer and Software Architect. When generating code for this FastAPI project, adhere to the following architectural patterns and standards.

## 1. Project Structure & Layering

Target directory structure:
```
src/app/
├── app.py              # FastAPI app initialization only
├── api/
│   └── routes/
│       ├── pages.py    # Template routes (/, /login, /dashboard, /article/{id})
│       └── v1/         # Versioned JSON API
│           ├── articles.py
│           └── health.py
├── core/
│   ├── config.py       # Pydantic Settings
│   ├── security.py     # Auth dependencies
│   └── database.py     # DB connection management
├── services/
│   ├── article_service.py
│   └── user_service.py
├── schemas/
│   ├── article.py
│   └── user.py
└── templates/          # Jinja2 templates
```

- **Strict Separation of Concerns**: Maintain a clear boundary between the API layer (routes), Service layer (business logic), and Data layer (models/schemas).
- **Thin Routes**: Controllers in `app/api/` should only handle HTTP concerns (status codes, dependency injection, routing).
- **Service Layer**: All business logic, third-party integrations, and complex data manipulation must reside in `app/services/`.
- **Schemas**: Use Pydantic v2 models in `app/schemas/` for all request/response validation. Use `model_validate` and `model_dump`.

## 2. Hybrid Routing Pattern

This app uses **two routing patterns**:

### User-Facing Routes (Templates)
Clean, friendly URLs for browser users with server-rendered HTML:
```
GET  /                → Redirect to dashboard or login
GET  /login           → Login page (HTML)
GET  /dashboard       → Dashboard page (HTML)
GET  /article/{id}    → Article view page (HTML)
POST /article/save    → Save article (form submit, redirect)
```

### API Routes (JSON)
Versioned endpoints for programmatic access (mobile apps, CLI, HTMX):
```
GET    /api/v1/articles         → List articles (JSON)
POST   /api/v1/articles         → Create article (JSON)
GET    /api/v1/articles/{id}    → Get article (JSON)
PATCH  /api/v1/articles/{id}    → Update article (JSON)
DELETE /api/v1/articles/{id}    → Delete article (JSON)
GET    /api/v1/health           → Health check (JSON)
```

Both route types share the same **services layer** - no code duplication.

## 3. Pythonic Standards & Modern Syntax
- **Python 3.10+**: Use modern type hinting. Prefer `list[str]` over `List[str]` and `str | None` over `Optional[str]`.
- **Asynchronous Patterns**: Use `async def` for endpoints and I/O-bound service methods. Utilize `anyio` or `asyncio` appropriately.
- **Dependency Injection**: Use FastAPI's `Depends` for database sessions, authentication, and shared logic. Avoid global state.
- **Pydantic v2**: Utilize `model_validate`, `model_dump`, and `Field` for all schemas.

## 4. API Design
- **Versioning**: JSON API routes use `/api/v1` prefix. Template routes have no prefix.
- **Response Models**: Explicitly define `response_model` in route decorators to ensure data filtering and documentation accuracy.
- **Error Handling**: Raise `fastapi.HTTPException` within the service or API layer. Use custom exception handlers for domain-specific errors.

## 5. Documentation & Configuration
- **Pydantic Settings**: Manage all environment variables using `pydantic-settings` in `core/config.py`.
- **Docstrings**: Provide Google-style docstrings for complex service methods.
- **Typing**: Every function signature must have complete type hints for arguments and return values.
- **OpenAPI**: Provide clear `summary`, `description`, and `response_model` for every route to ensure high-quality Swagger/Redoc output.

## 6. Performance & Security
- **Lifespan**: Use the `lifespan` context manager for startup and shutdown logic (e.g., DB connection pooling).
- **User Authentication**: Google OAuth with session-based auth for web UI. Security logic in `app/core/security.py`.
- **SSRF Protection**: URL validation and private IP blocking for article extraction.

## 7. Timstapaper-Specific Context
- **Article Extraction**: Uses `newspaper4k` library to fetch and parse article content from URLs
- **Templates**: Jinja2 templates in `templates/` directory for server-side rendering
- **Frontend**: HTMX for interactive features (toggle favorite/archive)
- **Database**: Currently SQLite, planned migration to PostgreSQL (keep DB logic abstracted)
