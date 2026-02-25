# Alex — History

## Project Context

- **Project:** timstapaper — Personal reading list application
- **Stack:** Python, FastAPI, HTML, Tailwind CSS, HTMX, Google OAuth
- **User:** Tim Sullivan

## Learnings

### Template Structure (reviewed 2025-07-15)
- 4 templates total: `base.html`, `login.html`, `dashboard.html`, `article.html`
- All live in `src/app/templates/`
- Standard Jinja2 inheritance: `base.html` defines `{% block title %}` and `{% block content %}`
- All three child templates use `{% extends "base.html" %}`
- No partials/includes — all markup is inline in each template
- `base.html` includes: nav (conditional on `session.user`), flash messages, main content block, footer
- Flash message system uses `request.session` pop pattern with `flash_message` / `flash_category`

### Styling Approach
- **Tailwind CSS via CDN** (`cdn.tailwindcss.com` script tag in `base.html`) — no build step, no `tailwind.config.js`
- No separate CSS files; only a small `<style>` block in `base.html` for `.article-content` typography
- Color palette: indigo-600 primary, gray tones, yellow-500 for favorites, green-500 for checkmarks, red for errors/delete
- Responsive breakpoints used: `sm:` (image visibility, padding), `md:` (article hero height), `lg:` (padding)
- No dark mode support
- No custom Tailwind config or theme extensions

### HTMX Interactions
- **HTMX 1.9.10** loaded via unpkg CDN in `base.html`
- Two HTMX-powered actions on article cards (dashboard) and article view page:
  - `hx-post="/article/{id}/toggle-favorite"` with `hx-swap="none"` — server returns `HX-Refresh: true` header
  - `hx-post="/article/{id}/toggle-archive"` with `hx-swap="none"` — server returns `HX-Refresh: true` header
- Pattern: HTMX fires POST, backend detects `HX-Request` header, responds with empty body + `HX-Refresh: true` to reload page
- Delete uses a standard `<form>` POST (not HTMX) with `confirm()` dialog
- Article save uses a standard `<form>` POST to `/article/save`
- No HTMX loading indicators, no optimistic UI, no partial swaps — full page refresh on every action

### JavaScript
- Zero custom JavaScript — only the HTMX and Tailwind CDN scripts
- Delete confirmation uses inline `onclick="return confirm(...)"` — no JS files

### Static Assets
- No `/static/` directory — no custom images, icons, fonts, or CSS files
- All icons are inline SVGs (Google logo, star, archive box, trash, checkmarks, document icon)
- App icon is the 📚 emoji in the nav

### Accessibility
- `lang="en"` set on `<html>`
- Viewport meta tag present
- SVG buttons have `title` attributes for tooltips (favorite, archive, delete)
- Missing: no `aria-label` on icon-only buttons, no skip-nav link, no focus-visible styles, form inputs lack explicit `<label>` elements
- Color contrast appears adequate (indigo-600 on white, gray-700 text)

### Key Observations & Improvement Opportunities
- Favorite/archive button markup is duplicated between `dashboard.html` and `article.html` — candidate for a Jinja2 partial/include
- HTMX `hx-swap="none"` + `HX-Refresh: true` causes full page reloads — defeats purpose of HTMX; should use partial swaps for snappier UX
- Delete could be HTMX-ified with `hx-delete` + `hx-target` to remove the card without reload
- CDN approach for Tailwind is fine for dev but not production-ready (no purging, no caching control)
- No loading/spinner feedback when saving articles (extraction can be slow)
- No error handling UI for failed HTMX requests
- Article content rendered with `|replace('\n', '<br>')|safe` — potential XSS vector if content isn't sanitized server-side

### Key File Paths
- Templates: `src/app/templates/{base,login,dashboard,article}.html`
- Page routes (serves templates): `src/app/api/routes/pages.py`
- Auth routes: `src/app/api/routes/auth.py`
- API v1 routes (JSON): `src/app/api/routes/v1/articles.py`
- App entry: `src/app/app.py`

