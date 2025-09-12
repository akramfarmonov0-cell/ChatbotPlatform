"""
Foydalanuvchi dashboard routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.user import User, db
from models.conversation import Conversation, Message
from models.knowledge_base import KnowledgeBase
from models.messaging import MessagingPlatform, PlatformCredentials
from utils.ai_handler import AIHandler
from utils.crypto_utils import CryptoUtils
from datetime import datetime, timedelta
import uuid
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def login_required(f):
    """Login talab qiluvchi decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Tizimga kirish talab qilinadi'}), 401
            return redirect(url_for('auth.login'))
        
        # Foydalanuvchi mavjudligini tekshirish
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            if request.is_json:
                return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'}), 401
            return redirect(url_for('auth.login'))
        
        # Trial muddatini tekshirish
        if user.is_trial and user.trial_end_date and user.trial_end_date < datetime.utcnow():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Trial muddati tugagan', 'trial_expired': True}), 403
            return redirect(url_for('main.trial_expired'))
        
        return f(*args, **kwargs)
    
    return decorated_function

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard asosiy sahifa"""
    user = User.query.get(session['user_id'])
    
    # Statistikalar
    total_conversations = Conversation.query.filter_by(user_id=user.id).count()
    total_messages = Message.query.join(Conversation).filter(Conversation.user_id == user.id).count()
    knowledge_files = KnowledgeBase.query.filter_by(user_id=user.id).count()
    
    # Connected platforms
    connected_platforms = MessagingPlatform.query.filter_by(user_id=user.id, is_active=True).count()
    
    # Recent conversations
    recent_conversations = Conversation.query.filter_by(user_id=user.id) \
        .order_by(Conversation.updated_at.desc()) \
        .limit(5).all()
    
    # Trial ma'lumoti
    trial_info = {}
    if user.is_trial and user.trial_end_date:
        days_left = (user.trial_end_date - datetime.utcnow()).days
        trial_info = {
            'is_trial': True,
            'days_left': max(0, days_left),
            'trial_end_date': user.trial_end_date.strftime('%d.%m.%Y')
        }
    
    return render_template('dashboard/index.html', 
                         user=user,
                         stats={
                             'conversations': total_conversations,
                             'messages': total_messages,
                             'knowledge_files': knowledge_files,
                             'connected_platforms': connected_platforms
                         },
                         recent_conversations=recent_conversations,
                         trial_info=trial_info)

@dashboard_bp.route('/chat')
@login_required
def chat():
    """Chat interfeysi"""
    user = User.query.get(session['user_id'])
    
    # Foydalanuvchi suhbatlari
    conversations = Conversation.query.filter_by(user_id=user.id) \
        .order_by(Conversation.updated_at.desc()).all()
    
    return render_template('dashboard/chat.html', 
                         user=user,
                         conversations=conversations)

@dashboard_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    """Xabar yuborish API"""
    try:
        data = request.get_json()
        message_text = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not message_text:
            return jsonify({'success': False, 'error': "Xabar matni bo'sh bo'lishi mumkin emas"}), 400
        
        user = User.query.get(session['user_id'])
        
        # Suhbat yaratish yoki topish
        if conversation_id:
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
            if not conversation:
                return jsonify({'success': False, 'error': 'Suhbat topilmadi'}), 404
        else:
            # Yangi suhbat yaratish
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=message_text[:50] + ('...' if len(message_text) > 50 else ''),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.flush()  # ID olish uchun
        
        # Foydalanuvchi xabarini saqlash
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role='user',
            content=message_text,
            created_at=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # AI javob olish
        try:
            # Knowledge base ma'lumotlarini olish
            knowledge_content = ""
            knowledge_files = KnowledgeBase.query.filter_by(user_id=user.id, is_active=True).all()
            for kb_file in knowledge_files:
                if kb_file.content:
                    knowledge_content += f"\\n\\n{kb_file.filename}:\\n{kb_file.content}"
            
            # AI handler orqali javob olish
            ai_handler = AIHandler()
            ai_response = ai_handler.generate_response(
                message=message_text,
                knowledge_base_content=knowledge_content,
                ai_provider="gemini",  # Default
                language=session.get('language', 'uz')
            )
            
            if ai_response.get('success'):
                # AI javobini saqlash
                ai_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    role='assistant',
                    content=ai_response['response'],
                    created_at=datetime.utcnow(),
                    metadata={
                        'model_used': ai_response.get('model_used'),
                        'response_time': ai_response.get('response_time'),
                        'knowledge_used': bool(knowledge_content)
                    }
                )
                db.session.add(ai_message)
                
                # Suhbat vaqtini yangilash
                conversation.updated_at = datetime.utcnow()
                conversation.message_count = conversation.message_count + 2
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'conversation_id': conversation.id,
                    'user_message': {
                        'id': user_message.id,
                        'content': user_message.content,
                        'created_at': user_message.created_at.isoformat()
                    },
                    'ai_response': {
                        'id': ai_message.id,
                        'content': ai_message.content,
                        'created_at': ai_message.created_at.isoformat(),
                        'model_used': ai_response.get('model_used'),
                        'response_time': ai_response.get('response_time')
                    }
                })
            else:
                # AI xatosi
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f"AI xatosi: {ai_response.get('error', 'Nomalum xato')}"
                }), 500
                
        except Exception as ai_error:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'AI bilan muloqotda xato: {str(ai_error)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Server xatosi yuz berdi'}), 500

@dashboard_bp.route('/api/conversations')
@login_required
def get_conversations():
    """Foydalanuvchi suhbatlari ro'yxati"""
    user = User.query.get(session['user_id'])
    
    conversations = Conversation.query.filter_by(user_id=user.id) \
        .order_by(Conversation.updated_at.desc()).all()
    
    result = []
    for conv in conversations:
        result.append({
            'id': conv.id,
            'title': conv.title,
            'message_count': conv.message_count,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat()
        })
    
    return jsonify({'success': True, 'conversations': result})

@dashboard_bp.route('/api/conversation/<conversation_id>/messages')
@login_required
def get_conversation_messages(conversation_id):
    """Suhbat xabarlari"""
    user = User.query.get(session['user_id'])
    
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    if not conversation:
        return jsonify({'success': False, 'error': 'Suhbat topilmadi'}), 404
    
    messages = Message.query.filter_by(conversation_id=conversation_id) \
        .order_by(Message.created_at.asc()).all()
    
    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'metadata': msg.metadata
        })
    
    return jsonify({'success': True, 'messages': result})

@dashboard_bp.route('/api/conversation/<conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Suhbatni o'chirish"""
    user = User.query.get(session['user_id'])
    
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    if not conversation:
        return jsonify({'success': False, 'error': 'Suhbat topilmadi'}), 404
    
    try:
        # Barcha xabarlarni o'chirish
        Message.query.filter_by(conversation_id=conversation_id).delete()
        
        # Suhbatni o'chirish
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Suhbat ochirildi'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Suhbatni ochirishda xato'}), 500

@dashboard_bp.route('/knowledge')
@login_required
def knowledge_base():
    """Knowledge base boshqaruvi"""
    user = User.query.get(session['user_id'])
    
    knowledge_files = KnowledgeBase.query.filter_by(user_id=user.id) \
        .order_by(KnowledgeBase.created_at.desc()).all()
    
    return render_template('dashboard/knowledge.html', 
                         user=user,
                         knowledge_files=knowledge_files)

@dashboard_bp.route('/platforms')
@login_required
def messaging_platforms():
    """Messaging platformlar boshqaruvi"""
    user = User.query.get(session['user_id'])
    
    platforms = MessagingPlatform.query.filter_by(user_id=user.id).all()
    
    return render_template('dashboard/platforms.html', 
                         user=user,
                         platforms=platforms)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Sozlamalar"""
    user = User.query.get(session['user_id'])
    
    return render_template('dashboard/settings.html', user=user)