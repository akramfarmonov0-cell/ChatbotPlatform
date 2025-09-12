from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)  # +998...
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    trial_ends_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=3))
    plan = db.Column(db.String(20), default="free")  # free, monthly, quarterly, annual
    plan_expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_uzbek_phone(phone):
        """Validate Uzbekistan phone number format: +998XX XXX XX XX"""
        pattern = r'^\+998[0-9]{9}$'
        return re.match(pattern, phone.replace(' ', '')) is not None
    
    @property
    def is_trial_expired(self):
        """Check if trial period has expired"""
        return self.trial_ends_at and datetime.utcnow() > self.trial_ends_at
    
    @property
    def is_plan_active(self):
        """Check if paid plan is active"""
        if self.plan == 'free':
            return not self.is_trial_expired
        return self.plan_expires_at and datetime.utcnow() < self.plan_expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'plan': self.plan,
            'is_trial_expired': self.is_trial_expired,
            'is_plan_active': self.is_plan_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }