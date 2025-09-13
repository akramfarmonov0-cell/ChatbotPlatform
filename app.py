"""
AI Chatbot SaaS Platform - Asosiy Flask ilovasi
"""
import os
from datetime import timedelta, datetime
from werkzeug.security import generate_password_hash
import uuid

def init_default_data():
    """Production uchun boshlang'ich foydalanuvchilarni yaratish"""
    try:
        from models.user import User, db
        
        print("🔄 Initializing default users...")
        
        # Admin foydalanuvchini tekshirish
        admin_user = User.query.filter_by(phone='+998901234567').first()
        
        if not admin_user:
            print("👤 Creating admin user...")
            admin_user = User(
                id=str(uuid.uuid4()),
                full_name='Admin User',
                phone='+998901234567',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_active=True,
                is_trial=False,
                created_at=datetime.utcnow()
            )
            db.session.add(admin_user)
            print("✅ Admin user created: +998901234567 / admin123")
        
        db.session.commit()
        print("🎉 Default users initialized successfully!")
        
    except Exception as e:
        print(f"❌ Default data initialization failed: {e}")

def create_app():
    """Flask ilovasi yaratish"""
    from flask import Flask
    from flask_login import LoginManager
    from config import Config
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Iltimos, avval tizimga kiring.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login uchun user yuklash funksiyasi"""
        try:
            from models.user import User
            return User.query.get(int(user_id))
        except:
            return None
    
    # Database setup
    try:
        # Import all models to ensure they are registered with SQLAlchemy
        from models import db
        db.init_app(app)
        
        # Create tables
        with app.app_context():
            db.create_all()
            
            # Initialize default users for production
            if os.getenv('FLASK_ENV') == 'production' or not os.path.exists('app.db'):
                init_default_data()
                
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database setup error: {e}")
    
    # Routes registration
    register_blueprints(app)
    
    # Error handlers
    register_error_handlers(app)
    
    # Before request handlers 
    register_before_request_handlers(app)
    
    # Context processors
    register_context_processors(app)
    
    # Initialize i18n
    register_i18n(app)
    
    # Validate environment for production
    try:
        if os.getenv('FLASK_ENV') == 'production':
            Config.validate_environment()
            print("Production environment validated successfully!")
    except ValueError as e:
        print(f"Environment validation failed: {e}")
        if os.getenv('FLASK_ENV') == 'production':
            raise  # Fail startup in production
    
    print("Flask app created successfully!")
    return app

def register_blueprints(app):
    """Blueprintlarni ro'yxatga olish"""
    # Main routes - asosiy sahifalar
    try:
        from routes.main import main_bp
        app.register_blueprint(main_bp)
        print("Main routes registered successfully!")
    except Exception as e:
        print(f"Error registering main routes: {e}")
        # Fallback main route
        @app.route('/')
        def index():
            return '<h1>AI Chatbot SaaS Platform</h1><p>Tizim ishlamoqda...</p>'
    
    # Auth routes - autentifikatsiya
    try:
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp)
        print("Auth routes registered successfully!")
    except Exception as e:
        print(f"Error registering auth routes: {e}")
    
    # Dashboard routes - foydalanuvchi paneli  
    try:
        from routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp)
        print("Dashboard routes registered successfully!")
    except Exception as e:
        print(f"Error registering dashboard routes: {e}")
    
    # Admin routes - admin panel
    try:
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp)
        print("Admin routes registered successfully!")
    except Exception as e:
        print(f"Error registering admin routes: {e}")
    
    # API Webhooks - messaging platformlar
    try:
        from routes.api_webhooks import api_webhooks_bp  
        app.register_blueprint(api_webhooks_bp)
        print("API Webhooks routes registered successfully!")
    except Exception as e:
        print(f"Error registering API webhooks routes: {e}")
    
    # Messaging routes - bot management
    try:
        from routes.messaging import messaging_bp
        app.register_blueprint(messaging_bp)  
        print("Messaging routes registered successfully!")
    except Exception as e:
        print(f"Error registering messaging routes: {e}")

def register_error_handlers(app):
    """Xato ishlovchilarni ro'yxatga olish"""
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import request, jsonify
        if request.is_json:
            return jsonify({'error': 'Sahifa topilmadi'}), 404
        return '<h1>404 - Sahifa topilmadi</h1><a href="/">Bosh sahifa</a>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import request, jsonify
        if request.is_json:
            return jsonify({'error': 'Server xatosi'}), 500
        return '<h1>500 - Server xatosi</h1><a href="/">Bosh sahifa</a>', 500
    
    @app.errorhandler(403)
    def forbidden(error):
        from flask import request, jsonify
        if request.is_json:
            return jsonify({'error': 'Ruxsat etilmagan'}), 403
        return '<h1>403 - Ruxsat etilmagan</h1><a href="/">Bosh sahifa</a>', 403

def register_before_request_handlers(app):
    """So'rov oldi ishlovchilarni ro'yxatga olish"""
    
    @app.before_request
    def load_user():
        """Har bir so'rovda foydalanuvchini yuklash"""
        from flask import g, session
        g.user = None
        if 'user_id' in session:
            try:
                # Import faqat kerak bo'lganda
                from models.user import User
                g.user = User.query.get(session['user_id'])
                if g.user and not g.user.is_active:
                    session.clear()
                    g.user = None
            except Exception as e:
                print(f"User loading error: {e}")
                session.clear()
    
    @app.before_request
    def set_language():
        """Tilni belgilash"""
        from flask import g, session
        if 'language' not in session:
            session['language'] = 'uz'  # Default til
        g.language = session['language']

def register_context_processors(app):
    """Context processors for templates"""
    
    @app.context_processor
    def inject_current_user():
        """Template larda current_user obyektini taqdim etish"""
        from flask import session
        
        # Session dan user ma'lumotlarini olish
        user_id = session.get('user_id')
        is_authenticated = bool(user_id)
        username = session.get('username', '')
        is_admin = session.get('is_admin', False)
        
        # current_user obyekti yaratish
        class CurrentUser:
            def __init__(self):
                self.is_authenticated = is_authenticated
                self.username = username  
                self.is_admin = is_admin
                self.id = user_id
        
        return dict(current_user=CurrentUser())

def register_i18n(app):
    """i18n (internationalization) setup"""
    
    @app.context_processor
    def inject_i18n():
        """Template larda _ funksiyasini taqdim etish"""
        # Oddiy i18n fallback - keyinchalik Flask-Babel bilan almashtiriladi
        def _(text):
            return text  # Hozircha matn o'zgarishsiz qaytariladi
        
        return dict(_=_)

# Error template functions
def render_template(template_name, **kwargs):
    """Template render qilish (xato sahifalar uchun)"""
    # Oddiy HTML qaytarish (templatelar mavjud bo'lganda almashtiriladiu)
    if '404' in template_name:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>404 - Sahifa topilmadi</title></head>
        <body>
            <h1>404 - Sahifa topilmadi</h1>
            <p>Siz qidirayotgan sahifa mavjud emas.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        '''
    elif '500' in template_name:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>500 - Server xatosi</title></head>
        <body>
            <h1>500 - Server xatosi</h1>
            <p>Server xatosi yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        '''
    elif '403' in template_name:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>403 - Ruxsat etilmagan</title></head>
        <body>
            <h1>403 - Ruxsat etilmagan</h1>
            <p>Bu sahifaga kirish uchun ruxsatingiz yo'q.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        '''
    
    # Boshqa templatelar uchun oddiy HTML
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Chatbot SaaS</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>AI Chatbot SaaS Platform</h1>
            <p>Template yaratilmoqda...</p>
            <p>Template: {template_name}</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app = create_app()
    
    # Development server settings
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )