# --- Imports --- 
from flask import Flask, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import requests
import fitz  # PyMuPDF library
from textwrap import dedent
from datetime import datetime
import uuid
import json
import logging
from logging.handlers import RotatingFileHandler
from markdown import markdown # For rendering Markdown to HTML
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate

# Import configuration and blueprints
from config import Config
from services.pdf_service import extract_pdf_text
from services.ai_service import query_openrouter
from services.utils import allowed_file, generate_report_id
from services.database import db, migrate_json_to_db
from blueprints.analysis import analysis_bp
# Import auth blueprint
from blueprints.auth import auth_bp  # Auth blueprint is now uncommented
from blueprints.main import main_bp
from blueprints.dashboard import dashboard_bp
from blueprints.contact_routes import contact_bp

# --- Load Environment Variables ---
load_dotenv() # Load variables from .env file

def is_running_under_passenger():
    """Check if app is running under Passenger"""
    return 'PASSENGER_APP_ENV' in os.environ


# --- Flask App Setup ---
migrate = Migrate()

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register blueprints
    # In production (Passenger), the web server adds /appop to all URLs
    # In development, we need to add it ourselves
    if is_running_under_passenger():
        # For production - blueprints mounted at root level since Passenger/cPanel adds /appop
        app.register_blueprint(main_bp, url_prefix='')
        app.register_blueprint(auth_bp, url_prefix='/appop/auth')  # Use full path including /appop for auth
        app.register_blueprint(contact_bp, url_prefix='')  # Blueprint URL will be /appop after server routing
        app.register_blueprint(analysis_bp, url_prefix='/analysis')  # Blueprint URL will be /appop/analysis after server routing
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')  # Blueprint URL will be /appop/dashboard after server routing
    else:
        # For development - explicitly include /appop prefix
        app_root = app.config['APPLICATION_ROOT']
        app.register_blueprint(main_bp, url_prefix=app_root)
        app.register_blueprint(auth_bp, url_prefix=f"{app_root}/auth")  # Uncommented now that auth_bp is imported
        app.register_blueprint(contact_bp, url_prefix=app_root)  # Fix: Use app_root directly for contact
        app.register_blueprint(analysis_bp, url_prefix=f"{app_root}/analysis")
        app.register_blueprint(dashboard_bp, url_prefix=f"{app_root}/dashboard")
    
    # Add context processor to inject app_root into all templates
    @app.context_processor
    def inject_app_root():
        is_passenger = is_running_under_passenger()
        app_root = '' if is_passenger else app.config['APPLICATION_ROOT']
        return dict(app_root=app_root, is_passenger=is_passenger)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 error: {str(e)}")
        return render_template('errors/500.html'), 500
    
    # Add template filters
    @app.template_filter('markdown')
    def render_markdown(text):
        """Convert markdown to HTML"""
        return markdown(text, extensions=['tables', 'fenced_code'])
    
    @app.template_filter('format_date')
    def format_date(date_str):
        """Format ISO date string to readable date"""
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime('%d %b %Y, %H:%M')
        except:
            return date_str
    
    return app

app = create_app()
application = app

@app.route('/')
def redirect_to_main():
    # Redirect to main.index without adding another /appop prefix
    return redirect(url_for('main.index', _external=True))

@app.route('/show_app_root')
def show_app_root():
    app_root = app.config.get('APPLICATION_ROOT')
    return f"app_root: {app_root} (from environment: {os.environ.get('APPLICATION_ROOT', 'not set')})"

# --- Main Execution Block ---
if __name__ == '__main__':
    print(f"🚀 Starting Flask App...")
    print(f"📂 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📝 Log file: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log')}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # Runs the Flask development server.
    # Use a production server (like Gunicorn/Waitress) for deployment.
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True for development ONLY!