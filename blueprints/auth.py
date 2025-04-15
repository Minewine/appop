from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

# Create the blueprint instance
auth_bp = Blueprint('auth', __name__)

# Path to the JSON file storing user data
def get_users_file():
    users_dir = os.path.join(current_app.root_path, 'data')
    os.makedirs(users_dir, exist_ok=True)
    return os.path.join(users_dir, 'users.json')

# Helper functions for user management
def load_users():
    users_file = get_users_file()
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def save_user(email, password, name=""):
    users = load_users()
    if email in users:
        return False
    
    users[email] = {
        'password': generate_password_hash(password),
        'name': name,
        'created_at': datetime.now().isoformat(),
        'reports': []
    }
    
    with open(get_users_file(), 'w') as f:
        json.dump(users, f, indent=4)
    
    return True

def verify_user(email, password):
    users = load_users()
    if email in users and check_password_hash(users[email]['password'], password):
        return users[email]
    return None

def add_report_to_user(email, report_id):
    users = load_users()
    if email in users:
        if 'reports' not in users[email]:
            users[email]['reports'] = []
        users[email]['reports'].append(report_id)
        
        with open(get_users_file(), 'w') as f:
            json.dump(users, f, indent=4)
        
        return True
    return False

# Routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Get language preference from query param or session
    lang = request.args.get('lang', session.get('lang', 'en'))
    session['lang'] = lang

    # If user is already logged in, redirect to destination
    if 'user_email' in session:
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('analysis.upload', lang=lang))

    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')

        user = verify_user(email, password)

        if user:
            # Store user information in session
            session['user_email'] = email
            session['user_name'] = user.get('name', '')
            current_app.logger.info(f"User logged in: {email}")

            next_page = request.args.get('next', url_for('analysis.upload', lang=lang))
            return redirect(next_page)
        else:
            flash('Invalid email or password. Please try again.', 'error')
            current_app.logger.warning(f"Failed login attempt for email: {email}")

    return render_template('auth/login.html', lang=lang)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    # Get language preference from query param or session
    lang = request.args.get('lang', session.get('lang', 'en'))
    session['lang'] = lang
    
    # If user is already logged in, redirect to destination
    if 'user_email' in session:
        next_page = request.args.get('next', url_for('analysis.upload', lang=lang))
        return redirect(next_page)
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        name = request.form.get('name', '')
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Basic validation
        if not email or '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'error')
        elif not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        elif password != password_confirm:
            flash('Passwords do not match.', 'error')
        else:
            # Try to save the new user
            if save_user(email, password, name):
                session['user_email'] = email
                session['user_name'] = name
                
                flash('Account created successfully!', 'success')
                next_page = request.args.get('next', url_for('analysis.upload', lang=lang))
                return redirect(next_page)
            else:
                flash('Email already registered. Please use a different email.', 'error')
    
    return render_template('auth/signup.html', lang=lang)

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    # Get language preference from session
    lang = session.get('lang', 'en')
    
    # Clear user-specific session data
    session.pop('user_email', None)
    session.pop('user_name', None)
    
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index', lang=lang))

@auth_bp.route('/profile')
def profile():
    """Display user profile page"""
    # Get language preference from session
    lang = session.get('lang', 'en')
    
    # Check if user is logged in
    if 'user_email' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('auth.login', next=request.url, lang=lang))
    
    # Get user data
    users = load_users()
    user_email = session['user_email']
    user_data = users.get(user_email, {})
    
    # Get user's reports
    reports = []
    report_ids = user_data.get('reports', [])
    reports_dir = current_app.config['REPORTS_FOLDER']
    
    for report_id in report_ids:
        report_path = os.path.join(reports_dir, f"{report_id}.json")
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report_data = json.load(f)
                reports.append({
                    'id': report_id,
                    'cv_filename': report_data.get('cv_filename', 'Unknown'),
                    'jd_filename': report_data.get('jd_filename', 'Unknown'),
                    'analysis_type': report_data.get('analysis_type', 'Unknown'),
                    'timestamp': report_data.get('timestamp', datetime.now().isoformat())
                })
    
    # Sort reports by timestamp, newest first
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('auth/profile.html', 
                          user=user_data, 
                          reports=reports, 
                          email=user_email,
                          lang=lang)