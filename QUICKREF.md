# Quick Reference Guide

## Common Commands

### Docker

Start the application:
```bash
cd src
docker-compose up
```

Rebuild after code changes:
```bash
docker-compose up --build
```

Stop the application:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

### Local Development

Activate virtual environment:
```bash
cd src/app
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run application:
```bash
python app.py
```

### Database

View database contents:
```bash
sqlite3 data/timstapaper.db
.tables
SELECT * FROM users;
SELECT * FROM articles;
.quit
```

Backup database:
```bash
cp data/timstapaper.db data/timstapaper_backup_$(date +%Y%m%d).db
```

## Environment Variables

Required:
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `SECRET_KEY` - Random string for session encryption

Optional:
- `PORT` - Default: 8000
- `DATABASE_PATH` - Default: /data/timstapaper.db
- `DEBUG` - Set to 'development' for debug mode

## Troubleshooting

### OAuth redirect_uri_mismatch
Check Google Cloud Console → Credentials → Your OAuth Client → Authorized redirect URIs
Should match: `http://localhost:8000/auth/google/callback`

### Database locked error
SQLite doesn't handle high concurrency well. Consider PostgreSQL for production.

### Can't fetch article
- Check if website blocks automated requests
- Verify internet connection
- Try a different article URL

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Redirect to dashboard or login |
| `/login` | GET | Login page |
| `/auth/google` | GET | Initiate Google OAuth |
| `/auth/google/callback` | GET | OAuth callback |
| `/logout` | GET | Logout user |
| `/dashboard` | GET | Main dashboard |
| `/article/<id>` | GET | View article |
| `/article/save` | POST | Save new article |
| `/article/<id>/toggle-favorite` | POST | Toggle favorite |
| `/article/<id>/toggle-archive` | POST | Toggle archive |
| `/article/<id>/delete` | POST | Delete article |
| `/health` | GET | Health check |

## Database Schema

### users
- `id` - INTEGER PRIMARY KEY
- `email` - TEXT UNIQUE NOT NULL
- `name` - TEXT
- `created_at` - TIMESTAMP

### articles
- `id` - INTEGER PRIMARY KEY
- `user_id` - INTEGER (foreign key)
- `url` - TEXT NOT NULL
- `title` - TEXT
- `content` - TEXT
- `excerpt` - TEXT
- `image_url` - TEXT
- `is_archived` - INTEGER (0 or 1)
- `is_favorite` - INTEGER (0 or 1)
- `created_at` - TIMESTAMP

## Technology Stack

- **Backend**: Python 3.14, FastAPI 3.0
- **Database**: SQLite 3
- **Auth**: Google OAuth 2.0 (authlib)
- **HTML Parsing**: Newspaper4k
- **Frontend**: HTML5, Tailwind CSS, HTMX
- **Server**: Gunicorn (production)
- **Container**: Docker

## Useful Links

- [FastAPI Documentation](https://fastapi.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [HTMX](https://htmx.org/)
- [Google OAuth Setup](https://console.cloud.google.com/)
- [Newspaper4k Docs](https://github.com/AndyTheFactory/newspaper4k)
