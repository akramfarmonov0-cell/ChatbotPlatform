from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID string
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)  # +998...
    email = db.Column(db.String(120), unique=True, nullable=True)  # Optional
    password_hash = db.Column(db.String(200), nullable=False)
    is_trial = db.Column(db.Boolean, default=True)
    trial_end_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=3))
    paid_until = db.Column(db.DateTime, nullable=True)  # For paid users
    is_active = db.Column(db.Boolean, default=False)  # Admin approval needed
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
        return self.trial_end_date and datetime.utcnow() > self.trial_end_date
    
    @property 
    def is_plan_active(self):
        """Check if user has active subscription"""
        if self.is_trial and not self.is_trial_expired:
            return True
        return self.paid_until and datetime.utcnow() < self.paid_until
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'is_trial': self.is_trial,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'paid_until': self.paid_until.isoformat() if self.paid_until else None,
            'is_active': self.is_active,
            'is_trial_expired': self.is_trial_expired,
            'is_plan_active': self.is_plan_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }