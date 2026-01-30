---
description: Testing conventions and patterns for pytest
applyTo: '**/tests/**/*.py'
---

# Testing Conventions

## Framework & Tools

- Use **pytest** as the testing framework
- Use FastAPI's `TestClient` for endpoint testing
- Use `unittest.mock` for mocking (`patch`, `MagicMock`)

## Test Organization

- Group related tests in classes prefixed with `Test` (e.g., `TestHealthEndpoint`)
- Use descriptive test method names: `test_<action>_<expected_outcome>`
- One assertion concept per test when practical

## FastAPI Testing Patterns

### Authentication Mocking

Use FastAPI's dependency override system, not `patch`:

```python
from app import app, require_login

def test_authenticated_endpoint(temp_db):
    test_user = {"id": 1, "email": "test@example.com", "name": "Test User"}
    
    def override_require_login():
        return test_user
    
    app.dependency_overrides[require_login] = override_require_login
    
    try:
        with TestClient(app) as client:
            response = client.get("/dashboard")
            assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
```

### Database Testing

- Use the `temp_db` fixture for tests requiring database access
- Always close database connections after use
- Each test should set up its own test data

### Mocking External Services

Use `patch` for external calls like article extraction:

```python
with patch("app.extract_article_content") as mock_extract:
    mock_extract.return_value = {
        "title": "Test Article",
        "content": "Test content",
        "excerpt": "Test...",
        "image_url": "https://example.com/img.jpg",
    }
    # ... test code
```

## Fixtures

- Define shared fixtures in `conftest.py`
- Use `temp_db` for temporary database
- Use `client` for unauthenticated TestClient
- Use `test_user` for creating test user records

## Assertions

- Use plain `assert` statements (pytest style)
- Check status codes explicitly: `assert response.status_code == 200`
- For redirects, use `follow_redirects=False` and check `response.headers["location"]`
- Check response content with `response.json()` or `response.text`

## Test Categories

- **Unit tests**: Test functions in isolation with mocked dependencies
- **Integration tests**: Test API endpoints with database
- **Security tests**: Verify auth requirements and input validation
