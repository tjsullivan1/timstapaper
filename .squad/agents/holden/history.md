# Holden — History

## Project Context

- **Project:** timstapaper — Personal reading list application
- **Stack:** Python, FastAPI, HTML, Tailwind CSS, HTMX, Google OAuth
- **User:** Tim Sullivan

## Learnings

### Architecture & Structure

**Stack & Components:**
- Backend: FastAPI 0.129.0 with Uvicorn (ASGI), SQLModel + PostgreSQL
- Frontend: HTML5 + Tailwind CSS (CDN) + HTMX + vanilla JS
- Auth: Google OAuth via Authlib 1.6.8, session-based storage
- Article extraction: Newspaper4k 0.9.4.1

**Directory Layout:**
- `src/app/` — FastAPI application root (entry: app.py)
- `src/app/api/routes/` — Route handlers (v1/ for versioned API, auth.py, pages.py)
- `src/app/core/` — Config, database, security, models
- `src/app/services/` — Business logic (user_service, article_service)
- `src/app/schemas/` — Pydantic models for validation
- `tests/` — pytest-based test suite (1692 LOC, 108 tests, all passing)

**Deployment & DevOps:**
- Docker: Python 3.14 slim base, uv for dependency mgmt, non-root appuser, healthcheck
- Docker Compose: PostgreSQL 16-alpine + web service
- CI: GitHub Actions (ci.yml for PR builds, squad-* workflows for team ops)
- Infrastructure: Terraform (infra/) for IaC (not fully reviewed here)

### Code Quality Findings

**Positive:**
- ✅ Tests comprehensive: 108 passing, covers SSRF protection, DB constraints, auth, extraction
- ✅ Security: Strong SSRF validation (blocks localhost, RFC 1918 ranges, non-http schemes)
- ✅ DB design clean: User/Article models with proper relationships, UTC timestamps
- ✅ Config management: Pydantic Settings with .env, sensible defaults
- ✅ Error handling: Proper HTTP redirects for auth, logging throughout
- ✅ Docker setup solid: Healthcheck, non-root user, cache layers
- ✅ Documentation: README and SETUP guides are complete and accurate

**Issues (Minor):**
- ⚠️ **Linting failures** (7 errors, no fixable):
  - 4× E712: Boolean comparisons in article_service.py line 187–191 (`== True` → use truthiness)
  - 3× E402: Import ordering in conftest.py (imports after module-level config)
- ⚠️ **Docker Compose ENV bug**: Dockerfile hardcodes `DATABASE_URL=postgresql://...@localhost:5432/...` but docker-compose correctly overrides it with `@db:5432`. No actual runtime issue, but misleading default.

### Architectural Observations

1. **Versioned API Design**: Routes in `v1/` folder but only one version. Good pattern for future expansion.
2. **Session-based Auth**: User stored in FastAPI session (not tokens). Simpler for monolithic, requires sticky sessions in distributed setup.
3. **DB Initialization**: Uses SQLModel's `create_all()` with inspection to skip existing tables. Safe and Idempotent.
4. **Article Filtering**: Service layer handles filter_type logic (all/favorites/archived) cleanly.
5. **No ORM Migrations**: Tables created on app startup. Fine for small projects; would need Alembic for production schema evolution.

### Documentation Accuracy

- README describes Python 3.14 (actually 3.12+ supported, uses 3.14 in Docker)
- SETUP guide is clear and actionable
- OAuth instructions are correct and complete
- Tech stack list matches actual dependencies

### Recommendations for Next Phase

1. Fix linting errors (7 errors are quick fixes: drop bool comparisons, move imports)
2. Consider adding Alembic for migration tracking (if DB schema changes become frequent)
3. Add CORS/CSP headers if API expands beyond single domain
4. Session management: doc sticky sessions requirement if scaling to multiple replicas
5. Improve Dockerfile default (remove hardcoded localhost from DATABASE_URL)

