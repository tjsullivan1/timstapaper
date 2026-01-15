# Timstapaper Setup Guide

This guide will help you set up and run Timstapaper, an Instapaper clone built with Python FastAPI.

## Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.14+ (for local development)
- Google Cloud Platform account (for OAuth)

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: "Timstapaper"
4. Click "Create"

### Step 2: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" → "OAuth consent screen"
2. Select "External" user type
3. Fill in required fields:
   - App name: "Timstapaper"
   - User support email: your email
   - Developer contact: your email
4. Click "Save and Continue"
5. Skip scopes (click "Save and Continue")
6. Add test users if needed
7. Click "Save and Continue"

### Step 3: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application"
4. Name: "Timstapaper Web Client"
5. Add Authorized redirect URIs:
   - For local development: `http://localhost:8000/auth/google/callback`
   - For production: `https://yourdomain.com/auth/google/callback`
6. Click "Create"
7. **Save your Client ID and Client Secret** - you'll need these!

## Quick Start with Docker (Recommended)

### 1. Clone and Configure

```bash
git clone https://github.com/tjsullivan1/timstapaper.git
cd timstapaper/src
cp .env.example .env
```

### 2. Edit Environment Variables

Edit `.env` file with your Google OAuth credentials:

```env
SECRET_KEY=your-random-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start the Application

```bash
docker-compose up --build
```

### 4. Access the Application

Open your browser to: `http://localhost:8000`

## Local Development (Without Docker)

### 1. Set Up Python Environment

```bash
cd timstapaper/src/app

# Install uv if you haven't already
pip install uv

# Create virtual environment and install dependencies
uv sync
```

### 2. Configure Environment Variables

```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export SECRET_KEY="your-secret-key"
export DATABASE_PATH="./timstapaper.db"
```

On Windows:
```cmd
set GOOGLE_CLIENT_ID=your-client-id
set GOOGLE_CLIENT_SECRET=your-client-secret
set SECRET_KEY=your-secret-key
set DATABASE_PATH=./timstapaper.db
```

### 3. Run the Application

```bash
uv run python app.py
```

Access at: `http://localhost:8000`

## Using the Application

### Signing In

1. Click "Sign in with Google"
2. Authorize the application with your Google account
3. You'll be redirected to the dashboard

### Saving Articles

1. Paste any article URL in the input field
2. Click "Save"
3. The app will extract the article content automatically

### Managing Articles

- **Read**: Click on any article title to view it
- **Favorite**: Click the star icon to mark as favorite
- **Archive**: Click the archive icon to move to archive
- **Delete**: Click the trash icon to permanently delete
- **Filter**: Use the tabs to view All/Favorites/Archived

### Supported Websites

The app can extract content from most websites that have:
- Standard HTML structure with `<article>`, `<main>`, or `<p>` tags
- Open Graph meta tags (for better image extraction)
- Readable text content

## Troubleshooting

### OAuth Errors

**Error: "redirect_uri_mismatch"**
- Check that the redirect URI in Google Cloud Console exactly matches your application URL
- Make sure to include `/auth/google/callback` at the end

**Error: "Access blocked: Authorization Error"**
- Add your email as a test user in Google Cloud Console
- Or publish your OAuth consent screen (requires verification)

### Application Errors

**Error: "Unable to open database file"**
- Ensure the database directory exists and has write permissions
- For Docker: Check that the volume is properly mounted

**Error: "Failed to extract content"**
- The website may block automated requests
- Try a different article URL
- Check your internet connection

### Docker Issues

**Port already in use**
- Change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "8080:8000"  # Use port 8080 instead
  ```

**Container won't start**
- Check Docker logs: `docker-compose logs`
- Ensure environment variables are set correctly
- Try rebuilding: `docker-compose up --build --force-recreate`

## Production Deployment

### Important Security Considerations

1. **Use HTTPS**: Always use HTTPS in production
2. **Secure Secret Key**: Generate a strong, random secret key
3. **Update OAuth URLs**: Add production domain to Google Cloud Console
4. **Database Backups**: Set up regular backups of the SQLite database
5. **Environment Variables**: Never commit secrets to version control

### Recommended Setup

1. Use a reverse proxy (nginx/Caddy) with SSL
2. Set up automatic database backups
3. Use a process manager (systemd/supervisor)
4. Monitor application logs
5. Consider migrating to PostgreSQL for better concurrency

### Example nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Support

For issues and questions:
- Check the [GitHub Issues](https://github.com/tjsullivan1/timstapaper/issues)
- Review this setup guide
- Check application logs for error messages

## License

MIT License - See LICENSE file for details
