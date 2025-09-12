"""
Foydalanuvchi autentifikatsiya routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from models.user import User
from models.user import db
from utils.crypto_utils import CryptoUtils
from werkzeug.security import check_password_hash
import re
import uuid
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def validate_uzbek_phone(phone):
    """O'zbekiston telefon raqamini tekshirish"""
    # O'zbekiston telefon raqamlari: +998 XX XXX XX XX
    uzbek_phone_pattern = r'^(\+998|998)?[0-9]{9}$'
    
    # Raqamni normalizatsiya qilish
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    if clean_phone.startswith('+998'):
        clean_phone = clean_phone[4:]
    elif clean_phone.startswith('998'):
        clean_phone = clean_phone[3:]
    
    # 9 ta raqam bo'lishi kerak
    if len(clean_phone) != 9:
        return None
    
    # O'zbekiston operatorlari kodi: 90, 91, 93, 94, 95, 97, 98, 99, 77, 88
    valid_prefixes = ['90', '91', '93', '94', '95', '97', '98', '99', '77', '88']
    
    if clean_phone[:2] not in valid_prefixes:
        return None
    
    return f"+998{clean_phone}"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Ro'yxatdan o'tish"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            full_name = data.get('full_name', '').strip()
            phone = data.get('phone', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
            
            # Validatsiya
            errors = []
            
            if not full_name or len(full_name) < 2:
                errors.append("To'liq ism kamida 2 ta belgidan iborat bo'lishi kerak")
            
            if not phone:
                errors.append("Telefon raqam talab qilinadi")
            else:
                normalized_phone = validate_uzbek_phone(phone)
                if not normalized_phone:
                    errors.append("O'zbekiston telefon raqami formatida kiriting (+998XXXXXXXXX)")
                phone = normalized_phone
            
            if not password or len(password) < 6:
                errors.append("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
            
            if password != confirm_password:
                errors.append("Parollar mos kelmaydi")
            
            # Telefon raqam mavjudligini tekshirish
            if phone:
                existing_user = User.query.filter_by(phone=phone).first()
                if existing_user:
                    errors.append("Bu telefon raqam allaqachon ro'yxatdan o'tgan")
            
            if errors:
                return jsonify({'success': False, 'errors': errors}), 400
            
            # Yangi foydalanuvchi yaratish
            user = User(
                id=str(uuid.uuid4()),
                full_name=full_name,
                phone=phone,
                password_hash=CryptoUtils.hash_password(password),
                is_active=True,   # Sinov foydalanuvchilari avtomatik faol
                is_trial=True,   # 3 kunlik trial
                trial_end_date=datetime.utcnow() + timedelta(days=3),
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': "Ro'yxatdan o'tish muvaffaqiyatli! 3 kunlik sinov muddati boshlandi.",
                'trial_days': 3
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Server xatosi yuz berdi'}), 500
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Tizimga kirish"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            phone = data.get('phone', '').strip()
            password = data.get('password', '')
            
            if not phone or not password:
                return jsonify({
                    'success': False,
                    'error': 'Telefon raqam va parol talab qilinadi'
                }), 400
            
            # Telefon raqamni normalizatsiya qilish
            normalized_phone = validate_uzbek_phone(phone)
            if not normalized_phone:
                return jsonify({
                    'success': False,
                    'error': "Telefon raqam formati noto'g'ri"
                }), 400
            
            # Foydalanuvchini topish
            user = User.query.filter_by(phone=normalized_phone).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                return jsonify({
                    'success': False,
                    'error': "Telefon raqam yoki parol noto'g'ri"
                }), 401
            
            if not user.is_active:
                return jsonify({
                    'success': False,
                    'error': "Akkauntingiz hali tasdiqlanmagan. Admin bilan bog'laning.",
                    'pending_approval': True
                }), 403
            
            # Trial muddatini tekshirish
            if user.is_trial and user.trial_end_date and user.trial_end_date < datetime.utcnow():
                return jsonify({
                    'success': False,
                    'error': "Trial muddati tugagan. To'lov qiling.",
                    'trial_expired': True
                }), 403
            
            # Sessionga saqlash
            session['user_id'] = user.id
            session['user_phone'] = user.phone
            session['user_name'] = user.full_name
            session['is_admin'] = user.is_admin
            session['is_trial'] = user.is_trial
            
            # Oxirgi kirish vaqtini yangilash
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Trial holati haqida ma'lumot
            trial_info = {}
            if user.is_trial and user.trial_end_date:
                days_left = (user.trial_end_date - datetime.utcnow()).days
                trial_info = {
                    'is_trial': True,
                    'days_left': max(0, days_left),
                    'trial_end_date': user.trial_end_date.isoformat()
                }
            
            return jsonify({
                'success': True,
                'message': 'Muvaffaqiyatli tizimga kirdingiz',
                'user': {
                    'id': user.id,
                    'full_name': user.full_name,
                    'phone': user.phone,
                    'is_admin': user.is_admin
                },
                'trial_info': trial_info,
                'redirect_url': url_for('dashboard.index') if not user.is_admin else url_for('admin.dashboard')
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': 'Server xatosi yuz berdi'}), 500
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Tizimdan chiqish"""
    session.clear()
    flash('Tizimdan muvaffaqiyatli chiqdingiz', 'success')
    return redirect(url_for('main.home'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Parolni unutgan"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            phone = data.get('phone', '').strip()
            
            normalized_phone = validate_uzbek_phone(phone)
            if not normalized_phone:
                return jsonify({
                    'success': False,
                    'error': "Telefon raqam formati noto'g'ri"
                }), 400
            
            user = User.query.filter_by(phone=normalized_phone).first()
            
            if user:
                # Haqiqiy ilovada SMS yuborish kerak
                # Hozircha faqat log yozamiz
                print(f"Password reset requested for {normalized_phone}")
                
            # Xavfsizlik uchun har doim muvaffaqiyatli javob qaytaramiz
            return jsonify({
                'success': True,
                'message': 'Agar bu telefon raqam tizimda mavjud bo\'lsa, parolni tiklash bo\'yicha SMS yuboriladi.'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': 'Server xatosi yuz berdi'}), 500
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/check-session')
def check_session():
    """Session holatini tekshirish (AJAX)"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.is_active:
            # Trial holati tekshirish
            trial_info = {}
            if user.is_trial and user.trial_end_date:
                if user.trial_end_date < datetime.utcnow():
                    # Trial tugagan
                    session.clear()
                    return jsonify({'success': False, 'trial_expired': True}), 403
                
                days_left = (user.trial_end_date - datetime.utcnow()).days
                trial_info = {
                    'is_trial': True,
                    'days_left': max(0, days_left)
                }
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'full_name': user.full_name,
                    'phone': user.phone,
                    'is_admin': user.is_admin
                },
                'trial_info': trial_info
            })
    
    return jsonify({'success': False}), 401