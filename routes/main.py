"""
Asosiy sahifalar routes
"""
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from models.user import User
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Asosiy sahifa"""
    # Agar foydalanuvchi tizimga kirgan bo'lsa, dashboardga yo'naltirish
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.is_active:
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('dashboard.index'))
    
    return render_template('main/home.html')

@main_bp.route('/features')
def features():
    """Xususiyatlar sahifasi"""
    return render_template('main/features.html')

@main_bp.route('/pricing')
def pricing():
    """Narxlar sahifasi"""
    return render_template('main/pricing.html')

@main_bp.route('/trial-expired')
def trial_expired():
    """Trial muddati tugagan sahifa"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Agar trial hali tugamagan bo'lsa, dashboardga yo'naltirish
    if not user.is_trial or (user.trial_end_date and user.trial_end_date > datetime.utcnow()):
        return redirect(url_for('dashboard.index'))
    
    return render_template('main/trial_expired.html', user=user)

@main_bp.route('/payment')
def payment():
    """To'lov sahifasi"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    return render_template('main/payment.html', user=user)

@main_bp.route('/contact')
def contact():
    """Aloqa sahifasi"""
    return render_template('main/contact.html')

@main_bp.route('/api/language', methods=['POST'])
def set_language():
    """Tilni o'zgartirish API"""
    try:
        data = request.get_json()
        language = data.get('language', 'uz')
        
        # Qo'llab-quvvatlanadigan tillar
        supported_languages = ['uz', 'ru', 'en']
        
        if language not in supported_languages:
            language = 'uz'
        
        session['language'] = language
        
        return jsonify({
            'success': True,
            'language': language,
            'message': "Til muvaffaqiyatli o'zgartirildi"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': "Tilni o'zgartirishda xato"}), 500

@main_bp.route('/health')
def health_check():
    """Tizim holati tekshirish"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@main_bp.route('/api')
def api_index():
    """API index endpoint"""
    return jsonify({
        'message': 'AI Chatbot API',
        'version': '1.0',
        'status': 'active',
        'endpoints': ['/api/language', '/health']
    })