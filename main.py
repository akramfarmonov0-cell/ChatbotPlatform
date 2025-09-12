from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, current_user
from flask_babel import Babel
from models.user import db, User
from routes.main_routes import main_bp
from routes.admin_routes import admin_bp
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Iltimos, avval tizimga kiring.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Define locale selector function
    def get_locale():
        # Check if language is in session
        if 'language' in session:
            return session['language']
        # Default to Uzbek
        return 'uz'
    
    # Babel for internationalization
    babel = Babel(app, locale_selector=get_locale)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Language switching route
    @app.route('/set_language/<language>')
    def set_language(language=None):
        if language in app.config['LANGUAGES']:
            session['language'] = language
        return redirect(request.referrer or url_for('main.index'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Make uploads directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)