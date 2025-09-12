from models.user import db
from datetime import datetime
from cryptography.fernet import Fernet
from flask import current_app
import os

class TelegramBot(db.Model):
    __tablename__ = 'telegram_bots'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bot_name = db.Column(db.String(100), nullable=False)
    encrypted_token = db.Column(db.Text, nullable=False)  # Encrypted bot token
    webhook_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=False)
    last_activity = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='telegram_bots')
    
    def set_token(self, token):
        """Encrypt and store telegram bot token."""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            self.encrypted_token = fernet.encrypt(token.encode()).decode()
        else:
            # Fallback for development - still not plain text
            import base64
            self.encrypted_token = base64.b64encode(token.encode()).decode()
    
    def get_token(self):
        """Decrypt and return telegram bot token."""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            return fernet.decrypt(self.encrypted_token.encode()).decode()
        else:
            # Fallback for development
            import base64
            return base64.b64decode(self.encrypted_token.encode()).decode()

class WhatsAppAccount(db.Model):
    __tablename__ = 'whatsapp_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    business_name = db.Column(db.String(100), nullable=False)
    encrypted_app_id = db.Column(db.Text, nullable=False)
    encrypted_app_secret = db.Column(db.Text, nullable=False)
    encrypted_verify_token = db.Column(db.Text, nullable=False)
    phone_number_id = db.Column(db.String(50), nullable=False)
    webhook_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=False)
    last_activity = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='whatsapp_accounts')
    
    def set_credentials(self, app_id, app_secret, verify_token):
        """Encrypt and store WhatsApp credentials."""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            self.encrypted_app_id = fernet.encrypt(app_id.encode()).decode()
            self.encrypted_app_secret = fernet.encrypt(app_secret.encode()).decode()
            self.encrypted_verify_token = fernet.encrypt(verify_token.encode()).decode()
        else:
            # Fallback for development
            import base64
            self.encrypted_app_id = base64.b64encode(app_id.encode()).decode()
            self.encrypted_app_secret = base64.b64encode(app_secret.encode()).decode()
            self.encrypted_verify_token = base64.b64encode(verify_token.encode()).decode()
    
    def get_credentials(self):
        """Decrypt and return WhatsApp credentials."""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            return {
                'app_id': fernet.decrypt(self.encrypted_app_id.encode()).decode(),
                'app_secret': fernet.decrypt(self.encrypted_app_secret.encode()).decode(),
                'verify_token': fernet.decrypt(self.encrypted_verify_token.encode()).decode()
            }
        else:
            # Fallback for development
            import base64
            return {
                'app_id': base64.b64decode(self.encrypted_app_id.encode()).decode(),
                'app_secret': base64.b64decode(self.encrypted_app_secret.encode()).decode(),
                'verify_token': base64.b64decode(self.encrypted_verify_token.encode()).decode()
            }

class InstagramAccount(db.Model):
    __tablename__ = 'instagram_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    encrypted_access_token = db.Column(db.Text, nullable=False)
    page_id = db.Column(db.String(50), nullable=False)
    webhook_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=False)
    last_activity = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='instagram_accounts')
    
    def set_access_token(self, access_token):
        """Encrypt and store Instagram access token."""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            self.encrypted_access_token = fernet.encrypt(access_token.encode()).decode()
        else:
            # Fallback for development
            import base64
            self.encrypted_access_token = base64.b64encode(access_token.encode()).decode()
    
    def get_access_token(self):
        """Decrypt and return Instagram access token."""
        if current_app.config.get('ENCRYPTION_KEY'):
            fernet = Fernet(current_app.config['ENCRYPTION_KEY'].encode())
            return fernet.decrypt(self.encrypted_access_token.encode()).decode()
        else:
            # Fallback for development
            import base64
            return base64.b64decode(self.encrypted_access_token.encode()).decode()

# Conversation tracking models
class TelegramConversation(db.Model):
    __tablename__ = 'telegram_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('telegram_bots.id'), nullable=False)
    telegram_user_id = db.Column(db.String(50), nullable=False)  # Telegram user ID
    telegram_username = db.Column(db.String(100))  # Optional username
    message_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)
    message_type = db.Column(db.String(20), default='text')  # text, photo, document, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    bot = db.relationship('TelegramBot', backref='conversations')

class WhatsAppConversation(db.Model):
    __tablename__ = 'whatsapp_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('whatsapp_accounts.id'), nullable=False)
    whatsapp_user_id = db.Column(db.String(50), nullable=False)  # WhatsApp user phone number
    message_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)
    message_type = db.Column(db.String(20), default='text')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    account = db.relationship('WhatsAppAccount', backref='conversations')

class InstagramConversation(db.Model):
    __tablename__ = 'instagram_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('instagram_accounts.id'), nullable=False)
    instagram_user_id = db.Column(db.String(50), nullable=False)  # Instagram user ID
    instagram_username = db.Column(db.String(100))  # Optional username
    message_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)
    message_type = db.Column(db.String(20), default='comment')  # comment, direct_message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    account = db.relationship('InstagramAccount', backref='conversations')