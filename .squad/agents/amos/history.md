# Amos — History

## Project Context

- **Project:** timstapaper — Personal reading list application
- **Stack:** Python, FastAPI, HTML, Tailwind CSS, HTMX, Google OAuth
- **User:** Tim Sullivan

## Learnings

### Test Structure (reviewed 2025)
- 6 test files under `tests/`: test_api_endpoints.py, test_api_v1.py, test_article_extraction.py, test_database.py, test_schemas.py, test_ssrf_protection.py
- conftest.py at `tests/conftest.py` — mocks newspaper4k globally, sets up PostgreSQL with transaction rollback
- pytest.ini at repo root — uses `-v --tb=short`, testpaths=tests
- Tests run via `make test` (starts Postgres via docker-compose, then `uv run pytest`)
- All tests use class-based organization with `Test` prefix and descriptive docstrings

### Key Fixtures (tests/conftest.py)
- `test_engine` (session-scoped): creates/drops all tables once per session
- `session`: per-test transaction that rolls back — fast and isolated
- `client`: unauthenticated TestClient with DB session override
- `authenticated_client`: client with both DB and auth overrides (UNDERUSED — no test file references it)
- `test_user`: creates User in DB, returns UserSession
- `mock_article`: factory for newspaper Article mocks
- `sample_article`: creates Article in DB (UNDERUSED — never referenced in tests)

### Coverage Gaps
- **user_service.py**: no direct unit tests (get_user_by_email, create_user, get_or_create_user)
- **core/security.py**: no tests for DB-wipe recovery path or ID mismatch path in require_login
- **api/routes/v1/deps.py**: no tests for DB-wipe recovery or ID mismatch in require_api_auth
- **auth.py**: OAuth initiation/callback not tested; logout session-clearing not verified
- **pages.py**: authenticated-user redirect on `/` and `/login` not tested; HTMX response paths not tested; empty URL on save_article not tested
- **article_service.py**: list_articles filter="archived" not tested; toggle/delete with non-existent article (False return) not tested
- **Cross-user isolation**: no tests verifying user A can't access user B's articles
- **No coverage measurement**: no pytest-cov configured

### Test Quality Notes
- Heavy boilerplate duplication: tests in test_api_endpoints.py and test_api_v1.py manually set up dependency overrides instead of using the authenticated_client fixture
- SSRF tests are excellent — thorough parametrized coverage of localhost, private IPs, non-HTTP schemes, boundary cases
- Article extraction tests are solid with good edge case coverage
- Schema tests are comprehensive for all Pydantic models
- Health endpoint tested redundantly in both test_api_endpoints.py and test_api_v1.py

### Key File Paths
- Production app: src/app/app.py
- Core: src/app/core/{config,database,models,security}.py
- Services: src/app/services/{article_service,user_service}.py
- Schemas: src/app/schemas/{article,user}.py
- API routes: src/app/api/routes/{auth,pages}.py, src/app/api/routes/v1/{articles,deps,health}.py
- Templates: src/app/templates/

