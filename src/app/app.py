"""
Timstapaper - An Instapaper Clone
Main Flask application with Google OAuth authentication
"""
import os
import sqlite3
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from authlib.integrations.flask_client import OAuth
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Configure OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Database configuration
DATABASE = os.environ.get("DATABASE_PATH", "/data/timstapaper.db")


def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize database schema"""
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            excerpt TEXT,
            image_url TEXT,
            is_archived INTEGER DEFAULT 0,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_articles_user_id ON articles(user_id);
        CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
    ''')
    db.commit()
    db.close()


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def extract_article_content(url):
    """Extract article content from URL"""
    try:
        # Validate URL to prevent SSRF attacks
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Only allow http and https schemes
        if parsed.scheme not in ('http', 'https'):
            app.logger.error(f"Invalid URL scheme: {parsed.scheme}")
            return {
                'title': parsed.netloc or 'Invalid URL',
                'content': '',
                'excerpt': 'Invalid URL scheme',
                'image_url': None
            }
        
        # Prevent requests to localhost and private IP ranges
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            # Block localhost and private networks
            if (hostname_lower in ('localhost', '127.0.0.1', '0.0.0.0') or
                hostname_lower.startswith('192.168.') or
                hostname_lower.startswith('10.') or
                hostname_lower.startswith('172.16.') or
                hostname_lower.startswith('172.17.') or
                hostname_lower.startswith('172.18.') or
                hostname_lower.startswith('172.19.') or
                hostname_lower.startswith('172.20.') or
                hostname_lower.startswith('172.21.') or
                hostname_lower.startswith('172.22.') or
                hostname_lower.startswith('172.23.') or
                hostname_lower.startswith('172.24.') or
                hostname_lower.startswith('172.25.') or
                hostname_lower.startswith('172.26.') or
                hostname_lower.startswith('172.27.') or
                hostname_lower.startswith('172.28.') or
                hostname_lower.startswith('172.29.') or
                hostname_lower.startswith('172.30.') or
                hostname_lower.startswith('172.31.')):
                app.logger.error(f"Blocked request to private network: {hostname}")
                return {
                    'title': 'Security Error',
                    'content': '',
                    'excerpt': 'Cannot fetch content from private networks',
                    'image_url': None
                }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = None
        if soup.title:
            title = soup.title.string
        elif soup.find('h1'):
            title = soup.find('h1').get_text()
        else:
            title = urlparse(url).netloc
            
        # Extract image
        image_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image.get('content')
        elif soup.find('img'):
            img = soup.find('img')
            image_url = img.get('src')
            
        # Extract content
        content = ""
        excerpt = ""
        
        # Try to find main content
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        
        if main_content:
            # Remove script and style elements
            for script in main_content(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            content = main_content.get_text(separator='\n', strip=True)
        else:
            # Fallback: get all paragraphs
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
            
        # Create excerpt (first 200 characters)
        excerpt = content[:200] + "..." if len(content) > 200 else content
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'image_url': image_url
        }
    except Exception as e:
        app.logger.error(f"Error extracting content from URL: {str(e)}")
        return {
            'title': urlparse(url).netloc,
            'content': '',
            'excerpt': 'Failed to extract content',
            'image_url': None
        }


@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    """Login page"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/auth/google')
def google_login():
    """Initiate Google OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    """Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            # Store or update user in database
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('SELECT id, email, name FROM users WHERE email = ?', (user_info['email'],))
            user = cursor.fetchone()
            
            if user:
                user_id = user['id']
            else:
                cursor.execute(
                    'INSERT INTO users (email, name) VALUES (?, ?)',
                    (user_info['email'], user_info.get('name', ''))
                )
                db.commit()
                user_id = cursor.lastrowid
            
            db.close()
            
            # Store user in session
            session['user'] = {
                'id': user_id,
                'email': user_info['email'],
                'name': user_info.get('name', '')
            }
            
            return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"OAuth error: {str(e)}")
        flash('Authentication failed. Please try again.', 'error')
    
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing saved articles"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter from query params
    filter_type = request.args.get('filter', 'all')
    
    if filter_type == 'favorites':
        cursor.execute('''
            SELECT * FROM articles 
            WHERE user_id = ? AND is_archived = 0 AND is_favorite = 1
            ORDER BY created_at DESC
        ''', (session['user']['id'],))
    elif filter_type == 'archived':
        cursor.execute('''
            SELECT * FROM articles 
            WHERE user_id = ? AND is_archived = 1
            ORDER BY created_at DESC
        ''', (session['user']['id'],))
    else:
        cursor.execute('''
            SELECT * FROM articles 
            WHERE user_id = ? AND is_archived = 0
            ORDER BY created_at DESC
        ''', (session['user']['id'],))
    
    articles = cursor.fetchall()
    db.close()
    
    return render_template('dashboard.html', articles=articles, filter_type=filter_type)


@app.route('/article/<int:article_id>')
@login_required
def view_article(article_id):
    """View a single article"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM articles 
        WHERE id = ? AND user_id = ?
    ''', (article_id, session['user']['id']))
    
    article = cursor.fetchone()
    db.close()
    
    if not article:
        flash('Article not found.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('article.html', article=article)


@app.route('/article/save', methods=['POST'])
@login_required
def save_article():
    """Save a new article"""
    url = request.form.get('url', '').strip()
    
    if not url:
        flash('URL is required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Extract content from URL
    article_data = extract_article_content(url)
    
    # Save to database
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO articles (user_id, url, title, content, excerpt, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session['user']['id'],
        url,
        article_data['title'],
        article_data['content'],
        article_data['excerpt'],
        article_data['image_url']
    ))
    
    db.commit()
    db.close()
    
    flash('Article saved successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/article/<int:article_id>/toggle-favorite', methods=['POST'])
@login_required
def toggle_favorite(article_id):
    """Toggle article favorite status"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        UPDATE articles 
        SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND user_id = ?
    ''', (article_id, session['user']['id']))
    
    db.commit()
    db.close()
    
    if request.headers.get('HX-Request'):
        return '', 200
    
    return redirect(url_for('dashboard'))


@app.route('/article/<int:article_id>/toggle-archive', methods=['POST'])
@login_required
def toggle_archive(article_id):
    """Toggle article archive status"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        UPDATE articles 
        SET is_archived = CASE WHEN is_archived = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND user_id = ?
    ''', (article_id, session['user']['id']))
    
    db.commit()
    db.close()
    
    if request.headers.get('HX-Request'):
        return '', 200
    
    return redirect(url_for('dashboard'))


@app.route('/article/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    """Delete an article"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        DELETE FROM articles 
        WHERE id = ? AND user_id = ?
    ''', (article_id, session['user']['id']))
    
    db.commit()
    db.close()
    
    flash('Article deleted.', 'success')
    
    if request.headers.get('HX-Request'):
        return '', 200
    
    return redirect(url_for('dashboard'))


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Initialize database on startup
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    init_db()
    
    # Run app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
