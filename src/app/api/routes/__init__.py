"""Route handlers for the API.

- pages: Template routes for browser users
- auth: OAuth authentication routes
- v1/: Versioned JSON API (Phase 6)
"""

from api.routes import auth, pages

__all__ = ["auth", "pages"]
