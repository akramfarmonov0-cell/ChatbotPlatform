from datetime import datetime
from models.user import db
from cryptography.fernet import Fernet
from flask import current_app
import base64

class AIConfig(db.Model):
    """AI konfiguratsiya - Gemini yoki OpenAI tanlovi"""
    __tablename__ = 'ai_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ai_provider = db.Column(db.String(20), default='gemini')  # gemini, openai
    encrypted_openai_api_key = db.Column(db.Text)  # shifrlangan
    use_openai = db.Column(db.Boolean, default=False)
    openai_model = db.Column(db.String(50), default='gpt-3.5-turbo')
    gemini_model = db.Column(db.String(50), default='gemini-1.5-flash')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_configs')
    
    def set_openai_key(self, api_key):
        """OpenAI API kalitini shifrlash va saqlash"""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            self.encrypted_openai_api_key = fernet.encrypt(api_key.encode()).decode()
        else:
            # Development uchun fallback
            self.encrypted_openai_api_key = base64.b64encode(api_key.encode()).decode()
        self.use_openai = True
        self.ai_provider = 'openai'
        self.updated_at = datetime.utcnow()
    
    def get_openai_key(self):
        """OpenAI API kalitini dekriptatsiya qilish"""
        if not self.encrypted_openai_api_key:
            return None
            
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            return fernet.decrypt(self.encrypted_openai_api_key.encode()).decode()
        else:
            # Development uchun fallback
            return base64.b64decode(self.encrypted_openai_api_key.encode()).decode()
    
    def switch_to_gemini(self):
        """Gemini AI ga o'tish"""
        self.ai_provider = 'gemini'
        self.use_openai = False
        self.updated_at = datetime.utcnow()
    
    def switch_to_openai(self):
        """OpenAI ga o'tish (agar kalit mavjud bo'lsa)"""
        if self.encrypted_openai_api_key:
            self.ai_provider = 'openai'
            self.use_openai = True
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_current_config(self):
        """Hozirgi AI konfiguratsiyasini olish"""
        return {
            'provider': self.ai_provider,
            'model': self.openai_model if self.use_openai else self.gemini_model,
            'has_openai_key': bool(self.encrypted_openai_api_key),
            'use_openai': self.use_openai
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'ai_provider': self.ai_provider,
            'use_openai': self.use_openai,
            'openai_model': self.openai_model,
            'gemini_model': self.gemini_model,
            'has_openai_key': bool(self.encrypted_openai_api_key),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_or_create_for_user(user_id):
        """Foydalanuvchi uchun AI config yaratish yoki olish"""
        config = AIConfig.query.filter_by(user_id=user_id).first()
        if not config:
            config = AIConfig(user_id=user_id)
            db.session.add(config)
            db.session.commit()
        return config