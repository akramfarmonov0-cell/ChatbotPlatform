import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads/knowledge/'  # Store outside static for security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    LANGUAGES = ['uz', 'ru', 'en']
    
    # Multi-channel bot integration settings
    WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'https://your-repl-name.repl.co')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Fernet encryption key
    
    # Telegram Bot API settings
    TELEGRAM_API_URL = 'https://api.telegram.org/bot'
    
    # WhatsApp Business API settings
    WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'
    
    # Instagram Graph API settings
    INSTAGRAM_API_URL = 'https://graph.facebook.com/v18.0'
    
    # Platform detection (Replit vs Production)
    IS_REPLIT = 'REPL_ID' in os.environ
    
    # Validate critical environment variables
    @classmethod
    def validate_environment(cls):
        """Validate required environment variables for production."""
        if os.getenv('FLASK_ENV') == 'production':
            if not os.getenv('SECRET_KEY'):
                raise ValueError("SECRET_KEY must be set in production environment")
            if not os.getenv('GEMINI_API_KEY'):
                raise ValueError("GEMINI_API_KEY must be set in production environment")
            if not os.getenv('ENCRYPTION_KEY'):
                raise ValueError("ENCRYPTION_KEY must be set for secure token storage")