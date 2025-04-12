"""
Database service for AppOp Demo
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import enum
import uuid

db = SQLAlchemy()

class UserRole(enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    ANALYST = "analyst"  # New role for users who can only analyze data
    MANAGER = "manager"  # New role for users who can manage team members

class UserStatus(enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class AnalysisType(enum.Enum):
    """Analysis type enumeration"""
    CV_ONLY = "cv_only"
    CV_JD_COMPARISON = "cv_jd_comparison"
    CV_OPTIMIZATION = "cv_optimization"
    CAREER_PATH = "career_path"

class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=True, index=True)
    reports = db.relationship('Report', back_populates='user', lazy='dynamic')
    api_requests = db.relationship('ApiRequest', back_populates='user', lazy='dynamic')
    login_attempts = db.relationship('LoginAttempt', back_populates='user', lazy='dynamic')
    tokens = db.relationship('Token', back_populates='user', cascade="all, delete-orphan")
    preferences = db.relationship('UserPreference', uselist=False, back_populates='user', 
                                  cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check user password"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
        
    def is_active_user(self):
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
        
    def generate_api_key(self):
        """Generate a new API key for the user"""
        self.api_key = uuid.uuid4().hex
        return self.api_key
        
    def to_dict(self):
        """Convert user to dictionary representation"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'role': self.role.value,
            'status': self.status.value,
            'report_count': self.reports.count()
        }

class Report(db.Model):
    """Analysis report model"""
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    cv_filename = db.Column(db.String(255), nullable=False)
    jd_filename = db.Column(db.String(255), nullable=True)
    analysis_type = db.Column(db.Enum(AnalysisType), nullable=False, default=AnalysisType.CV_ONLY)
    result = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=True)  # Extracted score from the analysis
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    user = db.relationship('User', back_populates='reports')
    keywords = db.relationship('ReportKeyword', back_populates='report', cascade="all, delete-orphan")
    feedback = db.relationship('ReportFeedback', back_populates='report', uselist=False, 
                              cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert report to dictionary representation"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'cv_filename': self.cv_filename,
            'jd_filename': self.jd_filename,
            'analysis_type': self.analysis_type.value,
            'result': self.result,
            'score': self.score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_public': self.is_public
        }
    
    def extract_score(self):
        """Extract score from the analysis result"""
        import re
        if not self.result:
            return None
            
        # Look for patterns like "Match Score: 72%" or "Compatibility Score: 72%"
        score_pattern = r'(Match|Compatibility|Overall)\s+(?:Score|Compatibility|Match):?\s*(\d+)[%\s]'
        match = re.search(score_pattern, self.result, re.IGNORECASE)
        
        if match and match.group(2):
            return int(match.group(2))
        
        # Try a more general pattern
        fallback_pattern = r'Score:?\s*(\d+)[%\s]'
        fallback_match = re.search(fallback_pattern, self.result, re.IGNORECASE)
        
        if fallback_match and fallback_match.group(1):
            return int(fallback_match.group(1))
            
        return None

class ReportKeyword(db.Model):
    """Keywords extracted from reports for better search"""
    __tablename__ = 'report_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(36), db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True)  # e.g., skill, experience, education
    frequency = db.Column(db.Integer, default=1)
    report = db.relationship('Report', back_populates='keywords')
    
    __table_args__ = (
        db.UniqueConstraint('report_id', 'keyword', name='unique_keyword_per_report'),
    )

class ReportFeedback(db.Model):
    """User feedback on reports"""
    __tablename__ = 'report_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(36), db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # 1-5 star rating
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    report = db.relationship('Report', back_populates='feedback')

class ApiRequest(db.Model):
    """API request tracking for rate limiting"""
    __tablename__ = 'api_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    success = db.Column(db.Boolean, default=True)
    response_time = db.Column(db.Float, nullable=True)  # in milliseconds
    user = db.relationship('User', back_populates='api_requests')
    
    @classmethod
    def count_recent_requests(cls, user_id, endpoint, minutes=60):
        """Count recent API requests for rate limiting"""
        cutoff = datetime.utcnow() - datetime.timedelta(minutes=minutes)
        return cls.query.filter(
            cls.user_id == user_id,
            cls.endpoint == endpoint,
            cls.timestamp >= cutoff
        ).count()

class LoginAttempt(db.Model):
    """Login attempt tracking for security monitoring"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    success = db.Column(db.Boolean, default=False)
    user = db.relationship('User', back_populates='login_attempts')
    
    @classmethod
    def count_recent_failures(cls, email, minutes=30):
        """Count recent failed login attempts"""
        cutoff = datetime.utcnow() - datetime.timedelta(minutes=minutes)
        return cls.query.filter(
            cls.email == email,
            cls.success == False,
            cls.timestamp >= cutoff
        ).count()

class Token(db.Model):
    """Authentication tokens for password reset, email verification, etc."""
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'reset', 'verify', 'invite', etc.
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)
    user = db.relationship('User', back_populates='tokens')
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at

class UserPreference(db.Model):
    """User preferences for application settings"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    language = db.Column(db.String(10), default='en')
    theme = db.Column(db.String(20), default='light')
    notification_email = db.Column(db.Boolean, default=True)
    notification_web = db.Column(db.Boolean, default=True)
    user = db.relationship('User', back_populates='preferences')

class ActivityLog(db.Model):
    """User activity logging"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resource_type = db.Column(db.String(50), nullable=True)  # e.g., 'report', 'user'
    resource_id = db.Column(db.String(50), nullable=True)
    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic'))

def migrate_json_to_db(app):
    """Migrate existing JSON data to the database"""
    from flask import current_app
    import os
    
    # Migrate users
    users_file = os.path.join(app.root_path, 'data', 'users.json')
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users_data = json.load(f)
                
            for email, user_data in users_data.items():
                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if not existing_user:
                    new_user = User(
                        email=email,
                        name=user_data.get('name', ''),
                        password_hash=user_data.get('password', ''),
                        role=UserRole.ADMIN if user_data.get('is_admin', False) else UserRole.USER,
                        status=UserStatus.ACTIVE,
                        created_at=datetime.fromisoformat(user_data.get('created_at', datetime.utcnow().isoformat()))
                    )
                    db.session.add(new_user)
            
            db.session.commit()
            current_app.logger.info(f"Migrated users from JSON to database")
        except Exception as e:
            current_app.logger.error(f"Error migrating users: {e}")
            db.session.rollback()
    
    # Migrate reports
    reports_dir = app.config['REPORTS_FOLDER']
    if os.path.exists(reports_dir):
        try:
            for filename in os.listdir(reports_dir):
                if filename.endswith('.json'):
                    report_id = filename.split('.')[0]
                    
                    # Check if report already exists
                    existing_report = Report.query.get(report_id)
                    if existing_report:
                        continue
                    
                    report_path = os.path.join(reports_dir, filename)
                    with open(report_path, 'r') as f:
                        report_data = json.load(f)
                    
                    # Find user for this report
                    user = None
                    if 'users_data' in locals():
                        for email, u_data in users_data.items():
                            if 'reports' in u_data and report_id in u_data['reports']:
                                user = User.query.filter_by(email=email).first()
                                break
                    
                    # If no user found, assign to the first user as fallback
                    if not user:
                        user = User.query.first()
                    
                    if user:
                        analysis_type_str = report_data.get('analysis_type', 'cv_only')
                        analysis_type_enum = AnalysisType.CV_ONLY
                        
                        # Convert string to enum
                        for at in AnalysisType:
                            if at.value == analysis_type_str:
                                analysis_type_enum = at
                                break
                        
                        new_report = Report(
                            id=report_id,
                            user_id=user.id,
                            cv_filename=report_data.get('cv_filename', 'unknown.pdf'),
                            jd_filename=report_data.get('jd_filename'),
                            analysis_type=analysis_type_enum,
                            result=report_data.get('result', ''),
                            created_at=datetime.fromisoformat(report_data.get('timestamp', datetime.utcnow().isoformat())),
                            updated_at=datetime.fromisoformat(report_data.get('timestamp', datetime.utcnow().isoformat())),
                            is_public=False
                        )
                        
                        # Extract score if possible
                        new_report.score = new_report.extract_score()
                        
                        # Extract and save keywords
                        if new_report.result:
                            extract_keywords_from_report(new_report)
                            
                        db.session.add(new_report)
            
            db.session.commit()
            current_app.logger.info(f"Migrated reports from JSON to database")
        except Exception as e:
            current_app.logger.error(f"Error migrating reports: {e}")
            db.session.rollback()

def extract_keywords_from_report(report):
    """Extract keywords from a report and save them to the database"""
    import re
    
    if not report.result:
        return
    
    # Define keyword categories
    categories = {
        'skill': ['programming', 'software', 'technical', 'language', 'framework', 'tool', 'technology'],
        'experience': ['experience', 'work', 'project', 'job', 'professional', 'career'],
        'education': ['education', 'degree', 'university', 'certification', 'course', 'training']
    }
    
    # Clean and extract words from the report (basic approach)
    text = report.result.lower()
    words = re.findall(r'\b[a-z][a-z-]{3,}\b', text)
    
    # Count word frequencies
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Filter out common words
    common_words = {'this', 'that', 'with', 'from', 'have', 'your', 'which', 'will', 'more', 'what',
                   'them', 'when', 'been', 'were', 'they', 'some', 'than', 'into', 'other', 'about'}
    
    # Process each word and assign category
    for word, count in word_counts.items():
        if word in common_words or count < 2 or len(word) < 4:
            continue
        
        # Determine category
        category = 'other'
        for cat, keywords in categories.items():
            if any(kw in word or word in kw for kw in keywords):
                category = cat
                break
        
        # Create keyword record
        keyword = ReportKeyword(
            report=report,
            keyword=word,
            category=category,
            frequency=count
        )
        db.session.add(keyword)

def init_app(app):
    """Initialize the database with the app"""
    db.init_app(app)
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Migrate data if needed
        if app.config.get('MIGRATE_JSON_TO_DB', False):
            migrate_json_to_db(app)
            
        # Create admin user if none exists
        if not User.query.filter(User.role == UserRole.ADMIN).first():
            admin = User(
                email=app.config.get('ADMIN_EMAIL', 'admin@appop-demo.com'),
                name='Admin User',
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True
            )
            admin.set_password(app.config.get('ADMIN_PASSWORD', 'admin123!'))
            db.session.add(admin)
            
            # Create default preferences for admin
            pref = UserPreference(user=admin)
            db.session.add(pref)
            
            db.session.commit()
            app.logger.info("Created admin user")