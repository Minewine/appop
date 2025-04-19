# --- START OF FILE app.py ---

# --- Imports ---
from flask import Flask, render_template, redirect, url_for, current_app # Keep current_app for context processor if needed elsewhere, but using 'app' in inject_app_root is better
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
# Assuming these services/utils/database modules exist and are correctly imported
from services.pdf_service import extract_pdf_text
from services.ai_service import query_openrouter
from services.utils import allowed_file, generate_report_id
from services.database import db, migrate_json_to_db # Assuming db and migrate_json_to_db are used elsewhere
from blueprints.analysis import analysis_bp
# Import auth blueprint
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.dashboard import dashboard_bp
from blueprints.contact_routes import contact_bp # Assuming contact_routes blueprint is named contact_bp


# --- Load Environment Variables ---
load_dotenv() # Load variables from .env file

def is_running_under_passenger():
    """Check if app is running under Passenger or if APPLICATION_ROOT is set"""
    # Check if Passenger env var is set OR if APPLICATION_ROOT env var is set and not '/'
    return 'PASSENGER_APP_ENV' in os.environ or ('APPLICATION_ROOT' in os.environ and os.environ.get('APPLICATION_ROOT') != '/')


# --- Flask App Setup ---
# Initialize extensions *outside* create_app if they need to be accessed globally
# This matches the pattern in your original file, though initializing inside
# create_app and returning them is also a common pattern.
# Ensure these extensions are correctly initialized with the 'app' instance later if needed.
migrate = Migrate() # Assuming Migrate is used globally or initialized later


def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app instance *inside* create_app
    # This is generally the recommended pattern in Flask applications
    # db.init_app(app) # Example initialization if db needs app context
    # migrate.init_app(app, db) # Example initialization if migrate needs app and db

    # Determine app_root based on config or environment
    # Let Flask's built-in APPLICATION_ROOT handling work
    # The config file or Passenger should set APPLICATION_ROOT correctly
    app_root_config = app.config.get('APPLICATION_ROOT', '/')
    app_root_env = os.environ.get('APPLICATION_ROOT', '/')
    # Use the env var if set and not '/', otherwise use config value, defaulting to '/'
    effective_app_root = app_root_env if app_root_env and app_root_env != '/' else app_root_config
    # Ensure APPLICATION_ROOT ends with a slash if it's not the root path '/'
    if effective_app_root != '/' and not effective_app_root.endswith('/'):
        effective_app_root += '/'
    # Ensure APPLICATION_ROOT starts with a slash
    if not effective_app_root.startswith('/'):
        effective_app_root = '/' + effective_app_root

    app.config['APPLICATION_ROOT'] = effective_app_root # Ensure config reflects effective root


    # Register blueprints with relative paths
    # Flask will prefix these with APPLICATION_ROOT automatically
    # The main_bp should be at the root *relative to the application root*
    app.register_blueprint(main_bp, url_prefix='/') # e.g., /appop/
    # Other blueprints are subpaths relative to the application root
    app.register_blueprint(auth_bp, url_prefix='/auth') # e.g., /appop/auth/
    app.register_blueprint(contact_bp, url_prefix='/contact') # e.g., /appop/contact/
    app.register_blueprint(analysis_bp, url_prefix='/analysis') # e.g., /appop/analysis/
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard') # e.g., /appop/dashboard/


    # Add context processor to inject app_root into all templates
    @app.context_processor
    def inject_app_root():
        # Access the app's config directly, using the 'app' instance
        app_root_value = app.config.get('APPLICATION_ROOT', '')
        # Ensure it's an empty string if it's just '/' for cleaner template usage (e.g., <a href="{{ app_root }}/some_path">)
        # If APPLICATION_ROOT is '/', url_for handles it correctly without a prefix,
        # so passing '' to the template works well.
        if app_root_value == '/':
             app_root_value = ''
        # Also pass a flag if running under passenger for conditional logic if needed
        is_passenger = is_running_under_passenger() # You can still use this helper
        return dict(app_root=app_root_value, is_passenger=is_passenger)


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
        # Ensure text is not None or empty before processing
        if not text:
            return ""
        return markdown(text, extensions=['tables', 'fenced_code'])

    @app.template_filter('format_date')
    def format_date(date_str):
        """Format ISO date string to readable date"""
        try:
            # Attempt to parse various formats or handle non-string inputs
            if isinstance(date_str, datetime):
                 date = date_str
            else: # Assume string
                date = datetime.fromisoformat(str(date_str))
            return date.strftime('%d %b %Y, %H:%M')
        except Exception as e:
            # Log the error for debugging
            app.logger.error(f"Error formatting date string '{date_str}': {e}")
            return str(date_str) # Return original or error message if parsing fails

    # You might need to initialize other extensions here as well, e.g.:
    # cache.init_app(app)
    # limiter.init_app(app)
    # ProxyFix middleware might be needed depending on Passenger/web server setup
    # app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_prefix=1) # Adjust parameters as needed


    return app

# Create the app instance by calling create_app()
app = create_app()
application = app # Standard name for WSGI entry point (used by Passenger)

# If you initialized db/migrate outside create_app, you might need to do
# init_app here if they weren't initialized inside create_app.
# db.init_app(app) # If not done in create_app
# migrate.init_app(app, db) # If not done in create_app

# Example route *outside* a blueprint (e.g., for health checks or debugging)
# This route would be handled directly by the Flask app instance *after*
# APPLICATION_ROOT is processed. So if APPLICATION_ROOT is /appop,
# this route responds to /appop/show_app_root.
@app.route('/show_app_root')
def show_app_root():
    app_root_config = app.config.get('APPLICATION_ROOT')
    env_root = os.environ.get('APPLICATION_ROOT', 'not set')
    passenger_env = os.environ.get('PASSENGER_APP_ENV', 'not set')
    return f"Flask app.config['APPLICATION_ROOT']: '{app_root_config}'<br>" \
           f"Environment APPLICATION_ROOT: '{env_root}'<br>" \
           f"PASSENGER_APP_ENV: '{passenger_env}'<br>" \
           f"is_running_under_passenger() helper: {is_running_under_passenger()}"


# --- Main Execution Block ---
if __name__ == '__main__':
    # This block runs only when you execute app.py directly (e.g., python app.py)
    # It does NOT run when Passenger or a production WSGI server starts the app.
    print(f"🚀 Starting Flask App (Development Server)...")
    print(f"📂 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📝 Log file: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log')}")
    # print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}") # Be cautious printing sensitive URIs
    print(f"🔧 Configured APPLICATION_ROOT: {app.config.get('APPLICATION_ROOT', '/')}")
    print(f"🌐 Server Host: {app.config.get('SERVER_NAME', '0.0.0.0')}")
    print(f"🔌 Server Port: {os.environ.get('PORT', 5000)}")


    # Ensure logs directory exists for development
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging for development server
    handler = RotatingFileHandler(os.path.join(log_dir, 'app.log'), maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('App startup (development server)')

    # Runs the Flask development server.
    # Use a production server (like Gunicorn/Waitress) for deployment.
    # Set debug=False for production!
    # Use 0.0.0.0 to be accessible externally if needed in dev
    # Port can be configured via env var or config
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=app.config.get('DEBUG', False))

# --- END OF FILE app.py --- 