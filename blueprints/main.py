from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
import os
from datetime import datetime

# Create the blueprint instance
main_bp = Blueprint('main', __name__)

# Add context processor to make current_year available to all templates
@main_bp.app_context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@main_bp.route('/')
def index():
    """Landing page route"""
    # Get language preference from query param or session
    lang = request.args.get('lang', session.get('lang', 'en'))
    # Store language preference in session
    session['lang'] = lang
    return render_template('landing_page.html', lang=lang)

@main_bp.route('/about')
def about():
    """About page route"""
    # Get language preference from session or default to English
    lang = session.get('lang', 'en')
    return render_template('about.html', lang=lang)