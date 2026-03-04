# Naomi — History

## Project Context

- **Project:** timstapaper — Personal reading list application
- **Stack:** Python, FastAPI, HTML, Tailwind CSS, HTMX, Google OAuth
- **User:** Tim Sullivan

## Learnings

### Architecture Overview (reviewed 2025)

- **Framework:** FastAPI with factory pattern (`create_app()` in `src/app/app.py`)
- **ORM:** SQLModel (SQLAlchemy + Pydantic hybrid) — models in `src/app/core/models.py`
- **Database:** PostgreSQL (production & docker-compose), test DB: `timstapaper_test`
- **Auth:** Google OAuth via Authlib, session-based (Starlette `SessionMiddleware`)
- **Article extraction:** newspaper4k library with SSRF protection
- **Frontend:** Jinja2 templates + HTMX for partial page updates, Tailwind CSS
- **Package manager:** uv, defined in `src/app/pyproject.toml`

### Key File Paths

| Purpose | Path |
|---------|------|
| App entrypoint | `src/app/app.py` |
| Config (pydantic-settings) | `src/app/core/config.py` |
| DB engine & session | `src/app/core/database.py` |
| Models (User, Article) | `src/app/core/models.py` |
| Auth dependency | `src/app/core/security.py` |
| OAuth routes | `src/app/api/routes/auth.py` |
| Template (page) routes | `src/app/api/routes/pages.py` |
| API v1 articles | `src/app/api/routes/v1/articles.py` |
| API v1 auth dep | `src/app/api/routes/v1/deps.py` |
| Health check | `src/app/api/routes/v1/health.py` |
| Article service | `src/app/services/article_service.py` |
| User service | `src/app/services/user_service.py` |
| Schemas | `src/app/schemas/article.py`, `src/app/schemas/user.py` |
| Tests | `tests/` dir with conftest.py (mocks newspaper4k, PostgreSQL with rollback) |
| Docker | `src/Dockerfile`, `src/docker-compose.yml` |

### Database Schema

- **User:** id (PK), email (unique, indexed), name (nullable), created_at
- **Article:** id (PK), user_id (FK→user.id, indexed), url, title, content, excerpt, image_url, is_archived, is_favorite, created_at (indexed)

### Route Layout

- Page routes: `/`, `/login`, `/dashboard`, `/article/{id}`, `/article/save`, `/article/{id}/toggle-favorite`, `/article/{id}/toggle-archive`, `/article/{id}/delete`
- Auth routes: `/auth/google`, `/auth/google/callback`, `/logout`
- API v1: `/api/v1/articles` (GET, POST), `/api/v1/articles/{id}` (GET, PATCH, DELETE), `/api/v1/health`
- Root health: `/health`

### Auth Patterns

- Two auth dependencies: `require_login` (303 redirect for pages) and `require_api_auth` (401 JSON for API)
- Both verify user exists in DB; auto-recreate if DB was wiped but session still valid
- Session stores `UserSession` (id, email, name) as dict

### Security

- SSRF protection in `validate_url_for_ssrf()`: blocks localhost, RFC 1918, non-HTTP schemes
- `ProxyHeadersMiddleware` with `trusted_hosts=["*"]` — should be restricted in production
- URL validation via Pydantic `HttpUrl` on API create endpoint
- Ownership check on all article operations (user_id filter)

### Testing

- pytest with PostgreSQL, transaction-rollback per test for isolation
- newspaper4k mocked at module level in conftest.py to avoid segfaults
- FastAPI dependency overrides for auth and DB session
- Test files: test_api_endpoints.py, test_api_v1.py, test_article_extraction.py, test_database.py, test_schemas.py, test_ssrf_protection.py
- Run: `make test` (starts test DB, runs pytest)
- Lint: `make lint` (ruff check + format)

### Observations & Potential Improvements

- `ProxyHeadersMiddleware(trusted_hosts=["*"])` trusts all proxies — should whitelist in production
- `require_login` and `require_api_auth` share duplicated logic — could extract shared verification
- The Dockerfile comment says Python 3.12/3.13 but uses `python:3.14-slim`
- `.env.example` references Flask (`SECRET_KEY`, `PORT=5000`) — stale from migration
- `list_articles` filter param is unvalidated string — could use an enum
- No pagination on article list endpoints
- No rate limiting on article save (extraction hits external URLs)
- Session cookie settings (secure, httponly, samesite) not explicitly configured beyond default

