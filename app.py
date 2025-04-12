# --- Imports --- 
from flask import Flask, request, render_template, url_for, redirect, flash, jsonify, session
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

# Import configuration and blueprints
from config import Config
from services.pdf_service import extract_pdf_text
from services.ai_service import query_openrouter
from services.utils import allowed_file, generate_report_id
from services.database import db, migrate_json_to_db

# --- Load Environment Variables ---
load_dotenv() # Load variables from .env file

# --- Flask App Setup ---
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure session to use filesystem
    app.config['SESSION_TYPE'] = 'filesystem'
    app.secret_key = app.config['SECRET_KEY']  # Make sure this is set in your config
    
    # Initialize database
    db.init_app(app)
    
    # Initialize cache
    cache = Cache(app)
    
    # Initialize rate limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[app.config['RATELIMIT_DEFAULT']],
        storage_uri=app.config['RATELIMIT_STORAGE_URI']
    )
    
    # Create required directories if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    
    # Set up logging to file
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('App startup')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Migrate existing JSON data to the database if needed
        migrate_json_to_db(app)
    
    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.analysis import analysis_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(analysis_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
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

# --- Main Execution Block ---
if __name__ == '__main__':
    print(f"🚀 Starting Flask App...")
    print(f"📂 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📝 Log file: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log')}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # Runs the Flask development server.
    # Use a production server (like Gunicorn/Waitress) for deployment.
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True for development ONLY!