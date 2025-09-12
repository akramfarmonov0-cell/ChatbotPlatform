"""
Messaging platformlar uchun webhook API routes
"""
from flask import Blueprint, request, jsonify
from models.user import User, db
from models.messaging import MessagingPlatform, PlatformCredentials  
from models.conversation import Conversation, Message
from utils.ai_handler import AIHandler
from utils.crypto_utils import CryptoUtils
from utils.messaging_utils import MessagingUtils
from datetime import datetime
import uuid
import json
import hashlib
import hmac

api_webhooks_bp = Blueprint('api_webhooks', __name__, url_prefix='/api/webhooks')

def verify_telegram_webhook(data, token):
    """Telegram webhook uchun security tekshiruvi"""
    try:
        # Telegram bot API webhook verification
        # Haqiqiy ilovada to'liq verification amalga oshiriladi
        return True
    except:
        return False

def verify_whatsapp_webhook(signature, payload, verify_token):
    """WhatsApp webhook uchun security tekshiruvi"""
    try:
        # WhatsApp webhook signature verification
        expected_signature = hmac.new(
            verify_token.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, f"sha256={expected_signature}")
    except:
        return False

@api_webhooks_bp.route('/telegram/<platform_id>', methods=['POST'])
def telegram_webhook(platform_id):
    """Telegram webhook handler"""
    try:
        # Platform mavjudligini tekshirish
        platform = MessagingPlatform.query.filter_by(
            id=platform_id,
            platform_type='telegram',
            is_active=True
        ).first()
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        # Webhook data olish
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'status': 'ok'})  # Telegram requires 200 response
        
        message_data = data['message']
        
        # Foydalanuvchi ma'lumotlari
        telegram_user = message_data.get('from', {})
        telegram_user_id = telegram_user.get('id')
        telegram_username = telegram_user.get('username', '')
        telegram_first_name = telegram_user.get('first_name', '')
        telegram_last_name = telegram_user.get('last_name', '')
        full_name = f"{telegram_first_name} {telegram_last_name}".strip()
        
        # Chat ma'lumotlari
        chat = message_data.get('chat', {})
        chat_id = chat.get('id')
        
        # Xabar matni
        message_text = message_data.get('text', '').strip()
        
        if not message_text:
            return jsonify({'status': 'ok'})
        
        # Platform foydalanuvchisini topish/yaratish
        user = platform.user
        
        # Suhbat yaratish/topish
        conversation_title = f"Telegram: {full_name or telegram_username or chat_id}"
        conversation = Conversation.query.filter_by(
            user_id=user.id,
            platform_specific_id=str(chat_id)
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=conversation_title,
                platform_type='telegram',
                platform_specific_id=str(chat_id),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.flush()
        
        # Foydalanuvchi xabarini saqlash
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role='user',
            content=message_text,
            platform_message_id=str(message_data.get('message_id')),
            sender_info={
                'telegram_user_id': telegram_user_id,
                'username': telegram_username,
                'full_name': full_name
            },
            created_at=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # AI javob olish
        try:
            ai_handler = AIHandler()
            
            # Knowledge base ma'lumotlari
            knowledge_content = ""
            from models.knowledge_base import KnowledgeBase
            knowledge_files = KnowledgeBase.query.filter_by(
                user_id=user.id, is_active=True
            ).all()
            for kb_file in knowledge_files:
                if kb_file.content:
                    knowledge_content += f"\n\n{kb_file.filename}:\n{kb_file.content}"
            
            # AI config olish
            ai_config = user.ai_configs.filter_by(is_active=True).first()
            ai_provider = ai_config.provider if ai_config else "gemini"
            model = ai_config.model if ai_config else None
            
            ai_response = ai_handler.generate_response(
                message=message_text,
                knowledge_base_content=knowledge_content,
                ai_provider=ai_provider,
                model=model,
                language='uz'  # Default til
            )
            
            if ai_response.get('success'):
                response_text = ai_response['response']
                
                # AI javobini saqlash
                ai_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    role='assistant',
                    content=response_text,
                    metadata={
                        'model_used': ai_response.get('model_used'),
                        'response_time': ai_response.get('response_time')
                    },
                    created_at=datetime.utcnow()
                )
                db.session.add(ai_message)
                
                # Telegram orqali javob yuborish
                messaging_utils = MessagingUtils()
                success = messaging_utils.send_telegram_message(
                    platform, chat_id, response_text
                )
                
                if success:
                    ai_message.sent_at = datetime.utcnow()
                    ai_message.delivery_status = 'sent'
                else:
                    ai_message.delivery_status = 'failed'
                
                # Conversation statistikasini yangilash
                conversation.message_count = conversation.message_count + 2
                conversation.updated_at = datetime.utcnow()
                
                db.session.commit()
                
            else:
                # AI xatosi - xato xabarini yuborish
                error_message = "Kechirasiz, hozirda javob bera olmayapman. Keyinroq qayta urinib ko'ring."
                messaging_utils = MessagingUtils()
                messaging_utils.send_telegram_message(platform, chat_id, error_message)
                
                db.session.commit()
                
        except Exception as ai_error:
            print(f"AI error in Telegram webhook: {str(ai_error)}")
            db.session.rollback()
            
            # Xato xabarini yuborish
            error_message = "Texnik xatolik yuz berdi. Iltimos, administratorga murojaat qiling."
            try:
                messaging_utils = MessagingUtils()
                messaging_utils.send_telegram_message(platform, chat_id, error_message)
            except:
                pass
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"Telegram webhook error: {str(e)}")
        return jsonify({'status': 'error'}), 500

@api_webhooks_bp.route('/whatsapp/<platform_id>', methods=['GET', 'POST'])
def whatsapp_webhook(platform_id):
    """WhatsApp webhook handler"""
    if request.method == 'GET':
        # WhatsApp webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        platform = MessagingPlatform.query.filter_by(
            id=platform_id,
            platform_type='whatsapp',
            is_active=True
        ).first()
        
        if platform:
            credentials = platform.credentials.first()
            if credentials and verify_token == CryptoUtils.decrypt_text(credentials.webhook_verify_token):
                return challenge
        
        return 'Verification failed', 403
    
    try:
        # Platform tekshirish
        platform = MessagingPlatform.query.filter_by(
            id=platform_id,
            platform_type='whatsapp',
            is_active=True
        ).first()
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        data = request.get_json()
        
        if not data or 'entry' not in data:
            return jsonify({'status': 'ok'})
        
        for entry in data['entry']:
            if 'changes' in entry:
                for change in entry['changes']:
                    if change.get('field') == 'messages' and 'value' in change:
                        value = change['value']
                        
                        if 'messages' in value:
                            for message in value['messages']:
                                # Xabar ma'lumotlari
                                wa_message_id = message.get('id')
                                from_number = message.get('from')
                                message_type = message.get('type')
                                timestamp = message.get('timestamp')
                                
                                # Faqat text xabarlarni qayta ishlaymiz
                                if message_type == 'text' and 'text' in message:
                                    message_text = message['text'].get('body', '').strip()
                                    
                                    if message_text:
                                        # Xabarni qayta ishlash
                                        process_whatsapp_message(
                                            platform, from_number, message_text,
                                            wa_message_id, timestamp
                                        )
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"WhatsApp webhook error: {str(e)}")
        return jsonify({'status': 'error'}), 500

def process_whatsapp_message(platform, from_number, message_text, wa_message_id, timestamp):
    """WhatsApp xabarini qayta ishlash"""
    try:
        user = platform.user
        
        # Suhbat yaratish/topish
        conversation_title = f"WhatsApp: {from_number}"
        conversation = Conversation.query.filter_by(
            user_id=user.id,
            platform_specific_id=from_number
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=conversation_title,
                platform_type='whatsapp',
                platform_specific_id=from_number,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.flush()
        
        # Foydalanuvchi xabarini saqlash
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role='user',
            content=message_text,
            platform_message_id=wa_message_id,
            sender_info={'phone_number': from_number},
            created_at=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # AI javob olish va yuborish
        ai_handler = AIHandler()
        
        # Knowledge base
        knowledge_content = ""
        from models.knowledge_base import KnowledgeBase
        knowledge_files = KnowledgeBase.query.filter_by(
            user_id=user.id, is_active=True
        ).all()
        for kb_file in knowledge_files:
            if kb_file.content:
                knowledge_content += f"\n\n{kb_file.filename}:\n{kb_file.content}"
        
        ai_response = ai_handler.generate_response(
            message=message_text,
            knowledge_base_content=knowledge_content,
            ai_provider="gemini",
            language='uz'
        )
        
        if ai_response.get('success'):
            response_text = ai_response['response']
            
            # AI javobini saqlash
            ai_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role='assistant',
                content=response_text,
                created_at=datetime.utcnow()
            )
            db.session.add(ai_message)
            
            # WhatsApp orqali yuborish
            messaging_utils = MessagingUtils()
            success = messaging_utils.send_whatsapp_message(
                platform, from_number, response_text
            )
            
            if success:
                ai_message.sent_at = datetime.utcnow()
                ai_message.delivery_status = 'sent'
            else:
                ai_message.delivery_status = 'failed'
            
            conversation.message_count = conversation.message_count + 2
            conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
    except Exception as e:
        print(f"WhatsApp message processing error: {str(e)}")
        db.session.rollback()

@api_webhooks_bp.route('/instagram/<platform_id>', methods=['GET', 'POST'])
def instagram_webhook(platform_id):
    """Instagram webhook handler"""
    if request.method == 'GET':
        # Instagram webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        platform = MessagingPlatform.query.filter_by(
            id=platform_id,
            platform_type='instagram',
            is_active=True
        ).first()
        
        if platform:
            credentials = platform.credentials.first()
            if credentials and verify_token == CryptoUtils.decrypt_text(credentials.webhook_verify_token):
                return challenge
        
        return 'Verification failed', 403
    
    try:
        # Instagram messaging webhook logic
        # Similar to WhatsApp but for Instagram Direct Messages
        
        platform = MessagingPlatform.query.filter_by(
            id=platform_id,
            platform_type='instagram',
            is_active=True
        ).first()
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        data = request.get_json()
        
        # Instagram webhook ma'lumotlarini qayta ishlash
        # Haqiqiy implementation Instagram Graph API documentation asosida amalga oshiriladi
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"Instagram webhook error: {str(e)}")
        return jsonify({'status': 'error'}), 500

@api_webhooks_bp.route('/status')
def webhook_status():
    """Webhook holatini tekshirish"""
    return jsonify({
        'status': 'active',
        'timestamp': datetime.utcnow().isoformat(),
        'supported_platforms': ['telegram', 'whatsapp', 'instagram']
    })