"""
Admin panel routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from models.user import User, db
from models.conversation import Conversation, Message
from models.knowledge_base import KnowledgeBase
from models.messaging import MessagingPlatform, PlatformCredentials
from models.ai_config import AIConfig
from utils.crypto_utils import CryptoUtils
from datetime import datetime, timedelta
import uuid
from functools import wraps
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Admin huquqi talab qiluvchi decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Tizimga kirish talab qilinadi'}), 401
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_active or not user.is_admin:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Admin huquqi talab qilinadi'}), 403
            flash('Admin huquqi talab qilinadi', 'error')
            return redirect(url_for('main.home'))
        
        return f(*args, **kwargs)
    
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Umumiy statistikalar
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    trial_users = User.query.filter_by(is_trial=True, is_active=True).count()
    paid_users = User.query.filter_by(is_trial=False, is_active=True).count()
    
    # Pending foydalanuvchilar
    pending_users = User.query.filter_by(is_active=False).count()
    
    # Suhbatlar statistikasi
    total_conversations = Conversation.query.count()
    total_messages = Message.query.count()
    
    # Knowledge base statistikasi
    total_knowledge_files = KnowledgeBase.query.count()
    
    # Messaging platformlar
    total_platforms = MessagingPlatform.query.count()
    active_platforms = MessagingPlatform.query.filter_by(is_active=True).count()
    
    # Oxirgi 30 kun ichida qo'shilgan foydalanuvchilar
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_month = User.query.filter(User.created_at >= thirty_days_ago).count()
    
    # Trial muddati tugagan foydalanuvchilar
    expired_trials = User.query.filter(
        User.is_trial == True,
        User.trial_end_date < datetime.utcnow()
    ).count()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'trial_users': trial_users,
        'paid_users': paid_users,
        'pending_users': pending_users,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_knowledge_files': total_knowledge_files,
        'total_platforms': total_platforms,
        'active_platforms': active_platforms,
        'new_users_month': new_users_month,
        'expired_trials': expired_trials
    }
    
    # So'nggi faoliyat
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_conversations = Conversation.query.order_by(desc(Conversation.created_at)).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_conversations=recent_conversations)

@admin_bp.route('/users')
@admin_required
def users():
    """Foydalanuvchilar boshqaruvi"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = User.query
    
    # Status filtri
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'pending':
        query = query.filter_by(is_active=False)
    elif status == 'trial':
        query = query.filter_by(is_trial=True, is_active=True)
    elif status == 'paid':
        query = query.filter_by(is_trial=False, is_active=True)
    
    # Qidiruv
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.phone.contains(search))
        )
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', 
                         users=users,
                         status=status,
                         search=search)

@admin_bp.route('/api/users/<user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Foydalanuvchini tasdiqlash"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        
        user.is_active = True
        user.approved_at = datetime.utcnow()
        user.approved_by = session['user_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{user.full_name} tasdiqlandi'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Tasdiqlanshda xato'}), 500

@admin_bp.route('/api/users/<user_id>/block', methods=['POST'])
@admin_required
def block_user(user_id):
    """Foydalanuvchini bloklash"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        
        if user.is_admin:
            return jsonify({'success': False, 'error': "Adminni bloklab bo'lmaydi"}), 400
        
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{user.full_name} bloklandi'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Bloklashda xato'}), 500

@admin_bp.route('/api/users/<user_id>/upgrade', methods=['POST'])
@admin_required
def upgrade_user(user_id):
    """Foydalanuvchini to'lovli rejaga o'tkazish"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        
        user.is_trial = False
        user.trial_end_date = None
        user.paid_until = datetime.utcnow() + timedelta(days=30)  # 1 oylik to'lov
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"{user.full_name} to'lovli rejaga o'tkazildi"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': "To'lovli rejaga o'tkazishda xato"}), 500

@admin_bp.route('/conversations')
@admin_required
def conversations():
    """Barcha suhbatlar"""
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', '')
    
    query = Conversation.query.join(User)
    
    if user_id:
        query = query.filter(Conversation.user_id == user_id)
    
    conversations = query.order_by(desc(Conversation.updated_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/conversations.html', 
                         conversations=conversations,
                         user_id=user_id)

@admin_bp.route('/knowledge-base')
@admin_required
def knowledge_base():
    """Knowledge base fayllar boshqaruvi"""
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', '')
    
    query = KnowledgeBase.query.join(User)
    
    if user_id:
        query = query.filter(KnowledgeBase.user_id == user_id)
    
    files = query.order_by(desc(KnowledgeBase.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/knowledge_base.html', 
                         files=files,
                         user_id=user_id)

@admin_bp.route('/messaging')
@admin_required
def messaging():
    """Messaging platformlar boshqaruvi"""
    platforms = MessagingPlatform.query.join(User).order_by(desc(MessagingPlatform.created_at)).all()
    
    return render_template('admin/messaging.html', platforms=platforms)

@admin_bp.route('/ai-config')
@admin_required
def ai_config():
    """AI sozlamalari"""
    configs = AIConfig.query.join(User).order_by(desc(AIConfig.created_at)).all()
    
    return render_template('admin/ai_config.html', configs=configs)

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Analitika va hisobotlar"""
    # 30 kunlik statistika
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Kunlik ro'yxatdan o'tgan foydalanuvchilar
    daily_registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(
        func.date(User.created_at)
    ).order_by('date').all()
    
    # Kunlik suhbatlar
    daily_conversations = db.session.query(
        func.date(Conversation.created_at).label('date'),
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.created_at >= thirty_days_ago
    ).group_by(
        func.date(Conversation.created_at)
    ).order_by('date').all()
    
    # Eng faol foydalanuvchilar
    active_users = db.session.query(
        User.full_name,
        User.phone,
        func.count(Conversation.id).label('conversation_count')
    ).join(
        Conversation
    ).group_by(
        User.id
    ).order_by(
        desc('conversation_count')
    ).limit(10).all()
    
    return render_template('admin/analytics.html',
                         daily_registrations=daily_registrations,
                         daily_conversations=daily_conversations,
                         active_users=active_users)

@admin_bp.route('/settings')
@admin_required
def settings():
    """Tizim sozlamalari"""
    return render_template('admin/settings.html')

@admin_bp.route('/api/broadcast', methods=['POST'])
@admin_required
def broadcast_message():
    """Barcha foydalanuvchilarga xabar yuborish"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        target = data.get('target', 'all')  # all, trial, paid
        
        if not message:
            return jsonify({'success': False, 'error': 'Xabar matni bo\\'sh'}), 400
        
        # Maqsadli foydalanuvchilar
        query = User.query.filter_by(is_active=True)
        
        if target == 'trial':
            query = query.filter_by(is_trial=True)
        elif target == 'paid':
            query = query.filter_by(is_trial=False)
        
        users = query.all()
        
        # Haqiqiy ilovada messaging platform orqali yuboriladi
        # Hozircha faqat log yozamiz
        for user in users:
            print(f"Broadcasting to {user.phone}: {message}")
        
        return jsonify({
            'success': True,
            'message': f'{len(users)} ta foydalanuvchiga xabar yuborildi',
            'count': len(users)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Xabar yuborishda xato'}), 500