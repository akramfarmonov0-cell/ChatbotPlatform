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
    
    # Validate critical environment variables
    @classmethod
    def validate_environment(cls):
        """Validate required environment variables for production."""
        if os.getenv('FLASK_ENV') == 'production':
            if not os.getenv('SECRET_KEY'):
                raise ValueError("SECRET_KEY must be set in production environment")
            if not os.getenv('GEMINI_API_KEY'):
                raise ValueError("GEMINI_API_KEY must be set in production environment")