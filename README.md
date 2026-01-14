# 📚 Timstapaper - Instapaper Clone

A personal reading list application that lets you save articles for later reading. Built with Python FastAPI, HTML, Tailwind CSS, HTMX, and Google OAuth authentication.

## ✨ Features

- **Google OAuth Authentication**: Secure login with your Google account
- **Save Articles**: Save articles from any website with a simple URL
- **Clean Reading Experience**: Distraction-free article reading view
- **Article Management**: Organize with favorites and archives
- **Responsive Design**: Works on desktop and mobile devices
- **Docker Support**: Easy deployment with Docker containers

## 🏗️ Repository Structure

```
├── .github/
│   ├── workflows/              # CI/CD pipelines
│   └── dependabot.yml         # Dependency updates
├── infra/
│   └── terraform/             # Infrastructure as Code
├── src/
│   ├── Dockerfile             # Container configuration
│   ├── docker-compose.yml     # Local development setup
│   ├── .env.example           # Environment variables template
│   └── app/
│       ├── app.py             # Main FastAPI application
│       ├── requirements.txt   # Python dependencies
│       └── templates/         # HTML templates
│           ├── base.html
│           ├── login.html
│           ├── dashboard.html
│           └── article.html
└── README.md
```

## 🛠️ Technology Stack

### Backend
- **Python 3.11**: Main programming language
- **FastAPI 3.0**: Web framework
- **SQLite**: Database for storing articles
- **Authlib**: Google OAuth integration
- **BeautifulSoup4**: Article content extraction
- **Gunicorn**: Production WSGI server

### Frontend
- **HTML5**: Markup
- **Tailwind CSS**: Styling (via CDN)
- **HTMX**: Dynamic interactions without heavy JavaScript
- **Vanilla JavaScript**: Minimal client-side logic

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Local development
- **GitHub Actions**: CI/CD pipelines
- **Terraform**: Infrastructure as Code

## 🏁 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Google Cloud Console account (for OAuth credentials)

### Google OAuth Setup

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google+ API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application"
   - Add authorized redirect URIs:
     - For local: `http://localhost:8000/auth/google/callback`
     - For production: `https://yourdomain.com/auth/google/callback`
   - Save your Client ID and Client Secret

### Local Development with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/tjsullivan1/timstapaper.git
   cd timstapaper/src
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google OAuth credentials
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Open your browser to `http://localhost:8000`
   - Click "Sign in with Google"
   - Start saving articles!

### Local Development without Docker

1. **Create a virtual environment**
   ```bash
   cd src/app
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   export GOOGLE_CLIENT_ID="your-client-id"
   export GOOGLE_CLIENT_SECRET="your-client-secret"
   export SECRET_KEY="your-secret-key"
   export DATABASE_PATH="./timstapaper.db"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser to `http://localhost:8000`

## 📖 Usage

### Saving Articles

1. After logging in, you'll see the dashboard
2. Paste any article URL in the input field
3. Click "Save" to add it to your reading list
4. The app will automatically extract the article content

### Managing Articles

- **Read**: Click on any article to view it in a clean, readable format
- **Favorite**: Click the star icon to mark articles as favorites
- **Archive**: Click the archive icon to move articles to your archive
- **Delete**: Click the trash icon to permanently delete an article

### Filtering

Use the tabs at the top of the dashboard to filter your articles:
- **All Articles**: Shows all unarchived articles
- **Favorites**: Shows only favorited articles
- **Archived**: Shows archived articles

## 🏭 Deployment

### Docker Deployment

1. **Build the Docker image**
   ```bash
   cd src
   docker build -t timstapaper:latest .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e GOOGLE_CLIENT_ID="your-client-id" \
     -e GOOGLE_CLIENT_SECRET="your-client-secret" \
     -e SECRET_KEY="your-secret-key" \
     -v $(pwd)/data:/data \
     --name timstapaper \
     timstapaper:latest
   ```

### Infrastructure Setup

1. **Configure Terraform backend**
   
   The `infra/terraform/backend.hcl` should pull your Azure container details from env variables.

2. **Initialize and deploy infrastructure**
   ```bash
   cd infra/terraform
   terraform init -backend-config=backend.hcl
   terraform plan
   terraform apply
   ```

### Application Deployment

The application is automatically deployed when code is pushed to the `main` branch. The deployment pipeline:

1. **CI Pipeline** (`ci.yml`): Runs tests and builds the application
2. **Infrastructure Pipeline** (`infra-plan-apply.yml`): Plans and applies infrastructure changes
3. **Deployment Pipeline** (`deploy-webapp.yml`): Builds and deploys the application

### Environment Variables

Configure the following environment variables for deployment:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | FastAPI secret key for sessions | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes |
| `DATABASE_PATH` | Path to SQLite database file | No (default: `/data/timstapaper.db`) |
| `PORT` | Application port | No (default: `8000`) |

## 🔧 Configuration

### Google OAuth Callback URLs

Make sure to add the correct callback URLs in your Google Cloud Console:

- **Development**: `http://localhost:8000/auth/google/callback`
- **Production**: `https://yourdomain.com/auth/google/callback`

### Database

The application uses SQLite for simplicity. The database is automatically created on first run. For production, consider:

- Using a persistent volume for the database
- Setting up regular backups
- Or migrating to PostgreSQL/MySQL for better concurrency

## 🧪 Testing

### Manual Testing

1. Start the application (locally or with Docker)
2. Navigate to `http://localhost:8000`
3. Test the following workflows:
   - Login with Google
   - Save an article (try different websites)
   - Mark article as favorite
   - Archive an article
   - View article content
   - Delete an article
   - Filter by favorites/archived
   - Logout

### Health Check

The application exposes a health check endpoint at `/health` for monitoring:

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

## 🏗️ Architecture

### Application Flow

1. **Authentication**: User logs in via Google OAuth
2. **Session Management**: User session stored in FastAPI session (server-side)
3. **Article Saving**: URL submitted → Content extracted → Stored in SQLite
4. **Reading**: Articles fetched from database and displayed

### Data Model

**Users Table**:
- `id`: Primary key
- `email`: User's email (unique)
- `name`: User's display name
- `created_at`: Account creation timestamp

**Articles Table**:
- `id`: Primary key
- `user_id`: Foreign key to users
- `url`: Original article URL
- `title`: Extracted article title
- `content`: Extracted article content
- `excerpt`: Short preview (200 chars)
- `image_url`: Featured image URL
- `is_archived`: Archive status
- `is_favorite`: Favorite status
- `created_at`: Save timestamp

## 📦 Dependencies

### Production Dependencies

- **FastAPI 0.109.1**: Web framework
- **Werkzeug 3.0.1**: WSGI utilities
- **Authlib 1.3.0**: OAuth client
- **Requests 2.31.0**: HTTP library
- **BeautifulSoup4 4.12.2**: HTML parsing
- **lxml 5.1.0**: XML/HTML parser
- **Gunicorn 21.2.0**: WSGI server

### Development Dependencies

For development, you may want to add:
- **pytest**: Testing framework
- **black**: Code formatter
- **flake8**: Linter
- **python-dotenv**: Environment variable management

## 🔐 Security Considerations

1. **Secret Key**: Always use a strong, random secret key in production
2. **OAuth Credentials**: Keep your Google OAuth credentials secure
3. **HTTPS**: Use HTTPS in production for secure authentication
4. **Database**: Ensure proper file permissions on the SQLite database
5. **User Isolation**: Articles are properly isolated by user_id

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure the application runs without errors
4. Test your changes thoroughly
5. Submit a pull request

## 📝 Future Enhancements

Potential features to add:

- [ ] Full-text search across articles
- [ ] Tags/categories for better organization
- [ ] Browser extension for easy saving
- [ ] Reading progress tracking
- [ ] Export articles to PDF/EPUB
- [ ] Dark mode
- [ ] Multiple authentication providers
- [ ] Sharing articles with other users
- [ ] Mobile app (PWA)
- [ ] RSS feed imports

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass and linting is clean
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

1. Check the [Issues](../../issues) page
2. Review the [Wiki](../../wiki) for additional documentation
3. Contact the maintainers listed in [CODEOWNERS](CODEOWNERS)

---

**Happy coding! 🎉**