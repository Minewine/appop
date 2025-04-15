"""
Database service for AppOp Demo
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)  # Add this column
    role = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    api_key = db.Column(db.String(128), nullable=True)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cv_filename = db.Column(db.String(255), nullable=False)
    jd_filename = db.Column(db.String(255), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    result = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)  # Add this column
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    is_public = db.Column(db.Boolean, default=False)

def migrate_json_to_db(app):
    """Migrate JSON data to the database."""
    with app.app_context():
        # Example: Load users from a JSON file and add them to the database
        users_file = os.path.join(app.root_path, 'data', 'users.json')
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                users = json.load(f)
                for email, user_data in users.items():
                    if not User.query.filter_by(email=email).first():
                        user = User(
                            email=email,
                            name=user_data.get('name', ''),
                            password_hash=user_data.get('password'),
                            created_at=datetime.fromisoformat(user_data.get('created_at')),
                            role=user_data.get('role', 'user'),
                            status=user_data.get('status', 'active')  # <-- add this line
                        )
                        db.session.add(user)
            db.session.commit()