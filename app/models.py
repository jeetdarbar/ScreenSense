import secrets
from datetime import datetime
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    api_token = db.Column(db.String(64), unique=True, index=True, default=lambda: secrets.token_hex(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Global Settings
    target_bedtime = db.Column(db.String(10), nullable=False, default='23:00')
    target_wake_time = db.Column(db.String(10), nullable=False, default='07:00')
    
    # Relationship
    logs = db.relationship('DailyLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class DailyLog(db.Model):
    __tablename__ = 'daily_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    
    # Refactored Input Features
    target_bedtime = db.Column(db.String(10), nullable=False) # Snapshot of settings at cycle start
    target_wake_time = db.Column(db.String(10), nullable=False, default='07:00')
    
    # After Bedtime Breakdown
    app_usage_json = db.Column(db.Text, nullable=True) # Full Daily Usage for List Display
    risk_usage_json = db.Column(db.Text, nullable=True) # Subset for Risk Calculation
    
    academic_minutes_after_bedtime = db.Column(db.Integer, default=0, nullable=False) # Productive/Study
    pickups_after_bedtime = db.Column(db.Integer, nullable=False) # Unlock count
    
    # Calculated / Risk Fields
    risk_score = db.Column(db.Float, nullable=True) # 0-100
    risk_level = db.Column(db.String(20), nullable=True) # Safe, Moderate, High
    
    # Phase 4: Caffeine Engine
    caffeine_type = db.Column(db.String(50), nullable=True, default="None")
    caffeine_modifiers = db.Column(db.Boolean, nullable=True, default=False)
    caffeine_time = db.Column(db.String(10), nullable=True) # HH:MM format
    active_caffeine_mg = db.Column(db.Float, nullable=True, default=0.0)
    
    # Store the Gemini Generated Analysis for high-speed historical browsing
    report_json = db.Column(db.Text, nullable=True) # JSON: {"reinforcement": "...", "analysis": "...", "action_plan": "..."}
    
    # Relationship for feedback
    feedback = db.relationship('InterventionFeedback', backref='daily_log', uselist=False, lazy=True)

    def get_usage_list(self):
        import json
        if not self.app_usage_json: return []
        try: return json.loads(self.app_usage_json)
        except: return []

    def get_risk_usage_list(self):
        import json
        if not self.risk_usage_json: return []
        try: return json.loads(self.risk_usage_json)
        except: return []

    def __repr__(self):
        return f'<DailyLog {self.date} Score:{self.risk_score}>'


class InterventionFeedback(db.Model):
    __tablename__ = 'intervention_feedback'
    id = db.Column(db.Integer, primary_key=True)
    daily_log_id = db.Column(db.Integer, db.ForeignKey('daily_log.id'), nullable=False)
    
    # Compliance Data
    time_to_fall_asleep_mins = db.Column(db.Integer, nullable=False) # User reported minutes
    morning_grogginess_score = db.Column(db.Integer, nullable=True) # Phase 4: 1-10 scale
    actual_wake_time = db.Column(db.String(10), nullable=True) # HH:MM format
    
    compliance_score = db.Column(db.Float, nullable=True) # Normalized score of compliance
    intervention_type = db.Column(db.String(50), nullable=True) # E.g., "5-min breathing", "10-min journaling"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Feedback {self.daily_log_id} Time:{self.time_to_fall_asleep_mins}>'

class AppCategoryMap(db.Model):
    __tablename__ = 'app_category_map'
    id = db.Column(db.Integer, primary_key=True)
    package_name = db.Column(db.String(150), unique=True, nullable=False, index=True) # e.g. com.instagram.android
    category = db.Column(db.String(50), nullable=False) # e.g. "Social Media", "Game", "Other"
    readable_name = db.Column(db.String(100), nullable=True) # e.g. "Instagram"
    
    def __repr__(self):
        return f'<AppCategoryMap {self.package_name}:{self.category}>'
