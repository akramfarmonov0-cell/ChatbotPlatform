import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-for-development-only')
    
    # AI Service configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Normalize DATABASE_URL for SQLAlchemy 2.x compatibility
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads/knowledge/'  # Store outside static for security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    LANGUAGES = ['uz', 'ru', 'en']
    
    # Multi-channel bot integration settings - Auto-detect URL for production
    if os.environ.get('RENDER_SERVICE_NAME'):
        # Render.com deployment
        WEBHOOK_BASE_URL = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com"
    elif os.environ.get('REPLIT_DEV_DOMAIN'):
        # Replit development
        WEBHOOK_BASE_URL = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}"
    else:
        # Manual override or fallback
        WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'https://localhost:5000')
    
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Fernet encryption key
    
    # Telegram Bot API settings
    TELEGRAM_API_URL = 'https://api.telegram.org/bot'
    
    # WhatsApp Business API settings
    WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'
    
    # Instagram Graph API settings
    INSTAGRAM_API_URL = 'https://graph.facebook.com/v18.0'
    
    # Platform detection (Replit vs Production)
    IS_REPLIT = bool(os.environ.get('REPLIT_DEV_DOMAIN')) or bool(os.environ.get('REPL_ID'))
    IS_PRODUCTION = os.environ.get('RENDER') or os.environ.get('FLASK_ENV') == 'production'
    
    # Validate critical environment variables
    @classmethod
    def validate_environment(cls):
        """Validate required environment variables for production."""
        # Always validate core requirements
        if not os.getenv('GEMINI_API_KEY'):
            raise ValueError("GEMINI_API_KEY must be set for AI functionality")
        
        # Stricter validation for production
        if os.getenv('FLASK_ENV') == 'production':
            if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'dev-secret-key-for-development-only':
                raise ValueError("SECRET_KEY must be set to a secure value in production environment")
            if not os.getenv('ENCRYPTION_KEY'):
                raise ValueError("ENCRYPTION_KEY must be set for secure token storage")
            if cls.WEBHOOK_BASE_URL == 'https://your-repl-name.repl.co':
                raise ValueError("WEBHOOK_BASE_URL must be properly configured for production")